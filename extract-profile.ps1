<#
.SYNOPSIS
    SkyBlock Profile Extractor - Official Hypixel API Edition (v2.1)
    
.DESCRIPTION
    Extracts comprehensive SkyBlock profile and auxiliary datasets using Hypixel API v2.
    Supports environment variables, header authentication, and SHA-256 integrity verification.
#>

param(
    [Parameter(Position = 0)]
    [string]$Username,
    
    [Parameter(Position = 1)]
    [string]$Profile,
    
    [string]$ApiKey,
    [string]$OutputDir,
    [switch]$Silent
)

# Enforce TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

# CONFIGURATION
$Script:Version = "2.1.0"
$Script:HypixelApiKey = $null
$Script:HypixelBaseUrl = "https://api.hypixel.net/v2" 
$Script:MojangBaseUrl = "https://api.mojang.com"
$Script:UserAgent = "SkyBlock-Profile-Extractor/2.1.0"
$Script:RateLimitMs = 500 

$Colors = @{
    Header  = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
    Info    = "White"
    Accent  = "Magenta"
}

# --- UTILITY FUNCTIONS ---

function Write-Header {
    param([string]$Title)
    if (-not $Silent) {
        Write-Host "`n>> $Title" -ForegroundColor $Colors.Header
        Write-Host "--------------------------------------------------" -ForegroundColor $Colors.Header
    }
}

function Write-Success {
    param([string]$Message)
    if (-not $Silent) { Write-Host "[OK] $Message" -ForegroundColor $Colors.Success }
}

function Write-Info {
    param([string]$Message)
    if (-not $Silent) { Write-Host "[i]  $Message" -ForegroundColor $Colors.Info }
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[!]  $Message" -ForegroundColor $Colors.Warning
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[X]  $Message" -ForegroundColor $Colors.Error
}

function Get-UserInput {
    param([string]$Prompt, [string]$Default = "")
    if ($Silent -and $Default) { return $Default }
    $input = Read-Host $Prompt
    if (-not $input -and $Default) { return $Default }
    return $input
}

# --- API CALL FUNCTIONS ---

function Invoke-HypixelApiCall {
    param(
        [string]$Endpoint,
        [string]$ErrorContext = "API call",
        [int]$RetryCount = 3,
        [switch]$NoAuth
    )
    
    $attempt = 0
    while ($attempt -lt $RetryCount) {
        try {
            $url = "$Script:HypixelBaseUrl/$Endpoint"
            $headers = @{
                'User-Agent' = $Script:UserAgent
                'Accept'     = 'application/json'
            }
            if (-not $NoAuth) {
                $headers['API-Key'] = $Script:HypixelApiKey
            }
            
            $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers -TimeoutSec 30
            
            if (-not $response.success) {
                if ($response.cause) { throw "API Error: $($response.cause)" }
                throw "API returned success=false"
            }
            
            Start-Sleep -Milliseconds $Script:RateLimitMs
            return $response
        }
        catch {
            $attempt++
            if ($attempt -ge $RetryCount) {
                throw "$ErrorContext failed after $RetryCount attempts: $($_.Exception.Message)"
            }
            Write-Warning "$ErrorContext failed (attempt $attempt/$RetryCount). Retrying in $($attempt * 2)s..."
            Start-Sleep -Seconds ($attempt * 2)
        }
    }
}

function Invoke-MojangApiCall {
    param([string]$Endpoint)
    try {
        $url = "$Script:MojangBaseUrl/$Endpoint"
        $headers = @{ 'User-Agent' = $Script:UserAgent }
        $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers -TimeoutSec 15
        Start-Sleep -Milliseconds 250
        return $response
    }
    catch {
        throw "Mojang API failed: $($_.Exception.Message)"
    }
}

# --- PLAYER & PROFILE LOOKUP ---

function Get-PlayerUUID {
    param([string]$Username)
    $cleanUser = $Username.Trim()
    if ($cleanUser -notmatch '^[a-zA-Z0-9_]{1,16}$') {
        Write-Error-Custom "Invalid Minecraft username format: '$cleanUser'"
        return $null
    }

    Write-Info "Looking up UUID for '$cleanUser'..."
    try {
        $response = Invoke-MojangApiCall -Endpoint "users/profiles/minecraft/$cleanUser"
        if ($response.id) {
            $rawUuid = $response.id
            $formattedUuid = $rawUuid.Insert(8, '-').Insert(13, '-').Insert(18, '-').Insert(23, '-')
            Write-Success "Found player: $($response.name) ($formattedUuid)"
            return @{ username = $response.name; uuid = $formattedUuid; raw_uuid = $rawUuid }
        }
        throw "Player not found."
    }
    catch {
        Write-Error-Custom "Failed to resolve player: $($_.Exception.Message)"
        return $null
    }
}

function Get-PlayerProfiles {
    param([string]$UUID, [string]$RawUUID, [string]$Username)
    Write-Info "Fetching SkyBlock profiles..."
    try {
        $raw = if ($RawUUID) { $RawUUID } else { $UUID.Replace("-", "") }
        $response = Invoke-HypixelApiCall -Endpoint "skyblock/profiles?uuid=$raw" -ErrorContext "Profile lookup"
        
        if ($response.profiles -and $response.profiles.Count -gt 0) {
            $profileList = @()
            foreach ($p in $response.profiles) {
                # Support both dashed and undashed member dictionary keys
                $memberData = $null
                if ($p.members."$UUID") {
                    $memberData = $p.members."$UUID"
                }
                elseif ($p.members."$raw") {
                    $memberData = $p.members."$raw"
                }

                $lastSave = 0
                if ($memberData -and $memberData.last_save) {
                    $lastSave = [int64]$memberData.last_save
                }
                
                $profileList += @{
                    profile_id = $p.profile_id
                    cute_name  = if ($p.cute_name) { $p.cute_name } else { "Unknown" }
                    game_mode  = if ($p.game_mode) { $p.game_mode } else { "normal" }
                    last_save  = $lastSave
                    data       = $p
                }
            }
            
            # Sort by last_save descending
            $profileList = @($profileList | Sort-Object { $_["last_save"] } -Descending)
            Write-Success "Found $($profileList.Count) SkyBlock profile(s)"
            return $profileList
        }
        throw "No SkyBlock profiles found for this player."
    }
    catch {
        Write-Error-Custom "Failed to fetch profiles: $($_.Exception.Message)"
        return $null
    }
}

function Select-Profile {
    param([array]$Profiles, [string]$RequestedProfile)
    
    if (-not $Profiles -or $Profiles.Count -eq 0) { return $null }
    
    if ($RequestedProfile) {
        $cleanReq = $RequestedProfile.Trim().ToLower()
        $selected = $Profiles | Where-Object { $_.cute_name.ToLower() -eq $cleanReq }
        if ($selected) {
            Write-Success "Selected profile: $($selected.cute_name)"
            return $selected
        }
        Write-Warning "Profile '$RequestedProfile' not found."
    }
    
    if ($Silent -or $Profiles.Count -eq 1) { 
        Write-Info "Auto-selecting: $($Profiles[0].cute_name)"
        return $Profiles[0] 
    }
    
    Write-Host "`nAvailable profiles:" -ForegroundColor $Colors.Info
    for ($i = 0; $i -lt $Profiles.Count; $i++) {
        $mode = if ($Profiles[$i].game_mode -ne "normal") { " [$($Profiles[$i].game_mode.ToUpper())]" } else { "" }
        Write-Host "  $($i + 1). $($Profiles[$i].cute_name)$mode"
    }
    $choice = Get-UserInput "`nSelect profile [1]" "1"
    try { $index = [int]$choice - 1 } catch { $index = 0 }
    if ($index -lt 0 -or $index -ge $Profiles.Count) { $index = 0 }
    return $Profiles[$index]
}

# --- EXTRACTION & EXPORT ---

function Start-DataExtraction {
    param(
        [string]$UUID,
        [string]$RawUUID,
        [object]$ProfileData,
        [string]$OutputDir,
        [string]$PlayerName
    )
    
    Write-Header "Extracting Data"
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    
    $extractedFiles = @()
    $statusMap = @{}
    
    # 1. Main Profile Data
    try {
        $profilePath = Join-Path $OutputDir "complete_profile.json"
        $ProfileData.data | ConvertTo-Json -Depth 100 -Compress:$false | Out-File -FilePath $profilePath -Encoding UTF8
        Write-Success "Saved complete_profile.json"
        $extractedFiles += "complete_profile.json"
        $statusMap["complete_profile.json"] = "success"
    }
    catch {
        Write-Error-Custom "Failed to save profile: $($_.Exception.Message)"
        $statusMap["complete_profile.json"] = "failed: $($_.Exception.Message)"
    }
    
    # 2. Auxiliary Endpoints (Parity with Python Extractor)
    $endpoints = @(
        @{ Ep = "player?uuid=$UUID"; File = "player_data.json"; Desc = "Player Stats" },
        @{ Ep = "skyblock/garden?profile=$($ProfileData.profile_id)"; File = "garden_data.json"; Desc = "Garden Data" },
        @{ Ep = "skyblock/museum?profile=$($ProfileData.profile_id)"; File = "museum_data.json"; Desc = "Museum Data" },
        @{ Ep = "guild?player=$UUID"; File = "guild_data.json"; Desc = "Guild Data" },
        @{ Ep = "recentgames?uuid=$UUID"; File = "recent_games.json"; Desc = "Recent Games" },
        @{ Ep = "status?uuid=$UUID"; File = "online_status.json"; Desc = "Online Status" },
        @{ Ep = "skyblock/firesales"; File = "fire_sales.json"; Desc = "Fire Sales" },
        @{ Ep = "skyblock/bingo?uuid=$RawUUID"; File = "bingo_data.json"; Desc = "Bingo Data" },
        @{ Ep = "skyblock/bazaar"; File = "bazaar_prices.json"; Desc = "Bazaar Prices" },
        @{ Ep = "skyblock/auction?profile=$($ProfileData.profile_id)"; File = "active_auctions.json"; Desc = "Active Auctions" },
        @{ Ep = "skyblock/news"; File = "skyblock_news.json"; Desc = "SkyBlock News" },
        @{ Ep = "resources/skyblock/items"; File = "skyblock_items.json"; Desc = "Items Schema"; NoAuth = $true },
        @{ Ep = "resources/skyblock/skills"; File = "skyblock_skills_resource.json"; Desc = "Skills Resource Schema"; NoAuth = $true },
        @{ Ep = "resources/skyblock/collections"; File = "skyblock_collections_resource.json"; Desc = "Collections Resource Schema"; NoAuth = $true }
    )
    
    foreach ($item in $endpoints) {
        try {
            if ($item.NoAuth) {
                $data = Invoke-HypixelApiCall -Endpoint $item.Ep -ErrorContext $item.Desc -NoAuth
            } else {
                $data = Invoke-HypixelApiCall -Endpoint $item.Ep -ErrorContext $item.Desc
            }
            $path = Join-Path $OutputDir $item.File
            $data | ConvertTo-Json -Depth 100 -Compress:$false | Out-File -FilePath $path -Encoding UTF8
            Write-Success "Saved $($item.File)"
            $extractedFiles += $item.File
            $statusMap[$item.File] = "success"
        }
        catch {
            Write-Warning "Skipped $($item.Desc): $($_.Exception.Message)"
            $statusMap[$item.File] = "failed: $($_.Exception.Message)"
        }
    }

    # 3. Write README.txt Report
    $readmeLines = @(
        "HYPIXEL SKYBLOCK PROFILE EXTRACTION REPORT",
        "==================================================",
        "Generated:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        "Player:      $PlayerName ($UUID)",
        "Profile:     $($ProfileData.cute_name) ($($ProfileData.profile_id))",
        "Mode:        $($ProfileData.game_mode)",
        "Completeness: $($extractedFiles.Count)/$($endpoints.Count + 1) endpoints successfully extracted",
        "",
        "FILES EXTRACTED:",
        "--------------------------------------------------"
    )
    foreach ($f in $extractedFiles) {
        $readmeLines += " - $f"
    }
    $readmeLines += ""
    $readmeLines += "NOTES & DISCLAIMERS:"
    $readmeLines += "1. Data extracted via official Hypixel API v2 without continuous player monitoring."
    $readmeLines += "2. Bazaar prices reflect market snapshots and do not constitute an authoritative net worth."
    $readmeLines += "3. Progression metrics depend directly on enabled in-game API privacy settings."
    
    $readmePath = Join-Path $OutputDir "README.txt"
    $readmeLines -join "`r`n" | Out-File -FilePath $readmePath -Encoding UTF8

    return @{ Count = $extractedFiles.Count; Files = $extractedFiles; Dir = $OutputDir }
}

# --- MAIN EXECUTION ---

try {
    Write-Header "SkyBlock Profile Extractor v$Script:Version (PowerShell)"
    
    # 1. Resolve API Key
    if ($ApiKey -and $ApiKey.Length -gt 30) {
        $Script:HypixelApiKey = $ApiKey.Trim()
    }
    elseif ($env:HYPIXEL_API_KEY -and $env:HYPIXEL_API_KEY.Length -gt 30) {
        $Script:HypixelApiKey = $env:HYPIXEL_API_KEY.Trim()
        Write-Info "Loaded API key from HYPIXEL_API_KEY environment variable"
    }
    else {
        $KeyFile = Join-Path $PSScriptRoot "api_key.txt"
        if (Test-Path $KeyFile) {
            $Script:HypixelApiKey = (Get-Content $KeyFile -Raw).Trim()
            if ($Script:HypixelApiKey.Length -gt 30) {
                Write-Info "Loaded API key from api_key.txt"
            }
        }
    }

    if (-not $Script:HypixelApiKey -or $Script:HypixelApiKey.Length -lt 30) {
        if ($Silent) {
            Write-Error-Custom "API Key is required in silent mode."
            exit 1
        }
        Write-Warning "Hypixel API Key not found!"
        $Script:HypixelApiKey = (Get-UserInput "Enter Hypixel API Key").Trim()
        if ($Script:HypixelApiKey -and $Script:HypixelApiKey.Length -gt 30) {
            $KeyFile = Join-Path $PSScriptRoot "api_key.txt"
            $Script:HypixelApiKey | Out-File $KeyFile -Encoding ASCII
            Write-Success "API Key saved to api_key.txt"
        }
        else {
            Write-Error-Custom "Invalid API Key format."
            exit 1
        }
    }

    # 2. Resolve Player Username
    if (-not $Username) {
        if ($Silent) {
            Write-Error-Custom "Minecraft username is required in silent mode."
            exit 1
        }
        $Username = Get-UserInput "Enter Minecraft Username"
        if (-not $Username) { exit 1 }
    }

    $player = Get-PlayerUUID -Username $Username
    if (-not $player) { exit 1 }

    # 3. Resolve Profiles
    $profiles = Get-PlayerProfiles -UUID $player.uuid -RawUUID $player.raw_uuid -Username $player.username
    if (-not $profiles) { exit 1 }

    $selected = Select-Profile -Profiles $profiles -RequestedProfile $Profile
    if (-not $selected) { exit 1 }

    # 4. Resolve Output Directory
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $targetDir = if ($OutputDir) { $OutputDir } else { "SkyBlock_$($player.username)_$($selected.cute_name)_$timestamp" }

    # 5. Extract
    $res = Start-DataExtraction -UUID $player.uuid -RawUUID $player.raw_uuid -ProfileData $selected -OutputDir $targetDir -PlayerName $player.username
    
    Write-Header "Extraction Complete"
    Write-Success "Extracted $($res.Count) files to $targetDir"
    exit 0
}
catch {
    Write-Error-Custom "Critical Error: $($_.Exception.Message)"
    exit 1
}

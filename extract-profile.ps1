<#
.SYNOPSIS
    SkyBlock Profile Extractor - Official Hypixel API Edition (v2)
    
.NOTES
    Fixed for Hypixel API v2 
    Added correct Header Auth & Robust JSON handling
#>

param(
    [Parameter(Position = 0)]
    [string]$Username,
    
    [Parameter(Position = 1)]
    [string]$Profile,
    
    [switch]$Silent
)

[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

# CONFIGURATION
$Script:Version = "2.1"
$Script:HypixelApiKey = $null
# FIXED: Updated to v2 base URL
$Script:HypixelBaseUrl = "https://api.hypixel.net/v2" 
$Script:MojangBaseUrl = "https://api.mojang.com"
$Script:UserAgent = "SkyBlock-Profile-Extractor/2.1"
$Script:RateLimit = 1200 

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
        Write-Host "`n╔═══════════════════════════════════════════════════╗" -ForegroundColor $Colors.Header
        Write-Host "  $Title" -ForegroundColor $Colors.Header
        Write-Host "╚═══════════════════════════════════════════════════╝" -ForegroundColor $Colors.Header
    }
}

function Write-Success {
    param([string]$Message)
    if (-not $Silent) { Write-Host "[✓] $Message" -ForegroundColor $Colors.Success }
}

function Write-Info {
    param([string]$Message)
    if (-not $Silent) { Write-Host "[i] $Message" -ForegroundColor $Colors.Info }
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor $Colors.Warning
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[✗] $Message" -ForegroundColor $Colors.Error
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
        [int]$RetryCount = 3
    )
    
    $attempt = 0
    while ($attempt -lt $RetryCount) {
        try {
            $url = "$Script:HypixelBaseUrl/$Endpoint"
            $headers = @{
                'API-Key'    = $Script:HypixelApiKey
                'User-Agent' = $Script:UserAgent
            }
            
            $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers -TimeoutSec 30
            
            if (-not $response.success) {
                if ($response.cause) { throw "API Error: $($response.cause)" }
                throw "API returned success=false"
            }
            
            Start-Sleep -Milliseconds $Script:RateLimit
            return $response
        }
        catch {
            $attempt++
            if ($attempt -ge $RetryCount) {
                throw "$ErrorContext failed after $RetryCount attempts: $($_.Exception.Message)"
            }
            Write-Warning "$ErrorContext failed (attempt $attempt/$RetryCount). Retrying..."
            Start-Sleep -Seconds ($attempt * 2)
        }
    }
}

function Invoke-MojangApiCall {
    param([string]$Endpoint)
    try {
        $url = "$Script:MojangBaseUrl/$Endpoint"
        $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
        Start-Sleep -Milliseconds 500
        return $response
    }
    catch {
        throw "Mojang API failed: $($_.Exception.Message)"
    }
}

# --- PLAYER LOOKUP ---

function Get-PlayerUUID {
    param([string]$Username)
    Write-Info "Looking up UUID for '$Username'..."
    try {
        $response = Invoke-MojangApiCall -Endpoint "users/profiles/minecraft/$Username"
        if ($response.id) {
            $uuid = $response.id
            # Standardize UUID format (dashed)
            $formattedUuid = $uuid.Insert(8, '-').Insert(13, '-').Insert(18, '-').Insert(23, '-')
            Write-Success "Found player: $($response.name)"
            return @{ username = $response.name; uuid = $formattedUuid }
        }
        throw "Player not found"
    }
    catch {
        Write-Error-Custom "Failed to find player: $($_.Exception.Message)"
        return $null
    }
}

function Get-PlayerProfiles {
    param([string]$UUID, [string]$Username)
    Write-Info "Fetching SkyBlock profiles..."
    try {
        # Endpoint is now correct due to BaseUrl change
        $response = Invoke-HypixelApiCall -Endpoint "skyblock/profiles?uuid=$UUID" -ErrorContext "Profile lookup"
        
        if ($response.profiles -and $response.profiles.Count -gt 0) {
            $profileList = @()
            foreach ($profile in $response.profiles) {
                # FIXED: Robust dictionary access for dashed UUID keys
                $memberData = $profile.members."$UUID" 
                
                $profileList += @{
                    profile_id = $profile.profile_id
                    cute_name  = $profile.cute_name
                    game_mode  = if ($profile.game_mode) { $profile.game_mode } else { "normal" }
                    last_save  = if ($memberData.last_save) { $memberData.last_save } else { 0 }
                    data       = $profile
                }
            }
            
            # Sort by last_save to auto-select most recent
            $profileList = @($profileList | Sort-Object { $_["last_save"] } -Descending)
            if ($profileList.Count -gt 0) { $profileList[0].add("selected", $true) }
            
            Write-Success "Found $($profileList.Count) SkyBlock profile(s)"
            return $profileList
        }
        throw "No SkyBlock profiles found."
    }
    catch {
        Write-Error-Custom "Failed to fetch profiles: $($_.Exception.Message)"
        return $null
    }
}

# --- PROFILE SELECTION ---

function Select-Profile {
    param([array]$Profiles, [string]$RequestedProfile)
    
    if ($Profiles.Count -eq 0) { return $null }
    if ($Profiles.Count -eq 1) { 
        Write-Info "Auto-selecting: $($Profiles[0].cute_name)"
        return $Profiles[0] 
    }
    
    if ($RequestedProfile) {
        $selected = $Profiles | Where-Object { $_.cute_name -eq $RequestedProfile }
        if ($selected) { return $selected }
        Write-Warning "Profile '$RequestedProfile' not found."
    }
    
    if (-not $Silent) {
        Write-Host "`n[i] Available profiles:" -ForegroundColor $Colors.Info
        for ($i = 0; $i -lt $Profiles.Count; $i++) {
            $mark = if ($i -eq 0) { "★" } else { "☆" }
            Write-Host "  $($i + 1). $mark $($Profiles[$i].cute_name) [$($Profiles[$i].game_mode)]"
        }
        $choice = Get-UserInput "`nSelect profile [1]" "1"
        try { $index = [int]$choice - 1 } catch { $index = 0 }
        if ($index -lt 0 -or $index -ge $Profiles.Count) { $index = 0 }
        return $Profiles[$index]
    }
    return $Profiles[0]
}

# --- EXTRACTION ---

function New-OutputDirectory {
    param([string]$Username, [string]$ProfileName)
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputDir = "SkyBlock_${Username}_${ProfileName}_${timestamp}"
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    return $outputDir
}

function Start-DataExtraction {
    param([string]$UUID, [object]$ProfileData, [string]$OutputDir)
    
    Write-Header "Extracting Data"
    $extractedFiles = @()
    
    # 1. Main Profile Data
    try {
        $profilePath = Join-Path $OutputDir "complete_profile.json"
        $ProfileData.data | ConvertTo-Json -Depth 100 -Compress:$false | Out-File -FilePath $profilePath -Encoding UTF8
        Write-Success "Saved complete_profile.json"
        $extractedFiles += "complete_profile.json"
    }
    catch { Write-Error-Custom "Failed to save profile: $($_.Exception.Message)" }
    
    # 2. Additional Endpoints (Updated for v2)
    $endpoints = @(
        @{ Ep = "player?uuid=$UUID"; File = "player_data.json"; Desc = "Player Stats" },
        @{ Ep = "skyblock/garden?profile=$($ProfileData.profile_id)"; File = "garden_data.json"; Desc = "Garden Data" },
        @{ Ep = "skyblock/museum?profile=$($ProfileData.profile_id)"; File = "museum_data.json"; Desc = "Museum Data" },
        @{ Ep = "guild?player=$UUID"; File = "guild_data.json"; Desc = "Guild Data" },
        @{ Ep = "recentgames?uuid=$UUID"; File = "recent_games.json"; Desc = "Recent Games" },
        @{ Ep = "status?uuid=$UUID"; File = "online_status.json"; Desc = "Online Status" },
        @{ Ep = "skyblock/bingo?uuid=$UUID"; File = "bingo_data.json"; Desc = "Bingo Data" },
        @{ Ep = "skyblock/bazaar"; File = "bazaar_prices.json"; Desc = "Bazaar" },
        @{ Ep = "skyblock/auction?profile=$($ProfileData.profile_id)"; File = "active_auctions.json"; Desc = "Active Auctions" },
        @{ Ep = "skyblock/news"; File = "skyblock_news.json"; Desc = "News" }
    )
    
    foreach ($item in $endpoints) {
        try {
            # Note: Endpoint strings here are appended to the v2 BaseURL
            $data = Invoke-HypixelApiCall -Endpoint $item.Ep -ErrorContext $item.Desc
            $path = Join-Path $OutputDir $item.File
            $data | ConvertTo-Json -Depth 100 -Compress:$false | Out-File -FilePath $path -Encoding UTF8
            Write-Success "Saved $($item.File)"
            $extractedFiles += $item.File
        }
        catch { Write-Warning "Skipping $($item.Desc): $($_.Exception.Message)" }
    }
    
    return @{ Count = $extractedFiles.Count; Files = $extractedFiles }
}

function Test-Prerequisites {
    Write-Info "Testing prerequisites..."
    if ($PSVersionTable.PSVersion.Major -lt 3) { return $false }
    
    if (-not $Script:HypixelApiKey -or $Script:HypixelApiKey.Length -lt 30) {
        Write-Error-Custom "Invalid Key format."
        return $false
    }
    
    # FIXED: Use /punishmentstats to verify key instead of /key (which is deprecated/removed)
    # PunishmentStats requires a key but no UUID, making it perfect for auth testing
    try {
        $null = Invoke-HypixelApiCall -Endpoint "punishmentstats" -ErrorContext "Key Validation"
        Write-Success "API Key Validated"
        return $true
    }
    catch {
        Write-Error-Custom "API Key Invalid or Connection Failed."
        return $false
    }
}

# --- MAIN ---

try {
    Clear-Host
    Write-Header "SkyBlock Profile Extractor v$Script:Version"
    
    $KeyFile = Join-Path $PSScriptRoot "api_key.txt"
    if (Test-Path $KeyFile) {
        $Script:HypixelApiKey = (Get-Content $KeyFile -Raw).Trim()
        Write-Info "Loaded API key"
    }
    else {
        Write-Warning "API Key not found in api_key.txt"
        $Script:HypixelApiKey = (Get-UserInput "Enter Hypixel API Key").Trim()
        if ($Script:HypixelApiKey) { $Script:HypixelApiKey | Out-File $KeyFile -Encoding ASCII }
    }

    if (-not (Test-Prerequisites)) { exit 1 }

    if (-not $Username) {
        $Username = Get-UserInput "Enter Minecraft Username"
        if (-not $Username) { exit 1 }
    }

    $player = Get-PlayerUUID -Username $Username
    if (-not $player) { exit 1 }

    $profiles = Get-PlayerProfiles -UUID $player.uuid -Username $player.username
    if (-not $profiles) { exit 1 }

    $selected = Select-Profile -Profiles $profiles -RequestedProfile $Profile
    
    $dir = New-OutputDirectory -Username $player.username -ProfileName $selected.cute_name
    
    $res = Start-DataExtraction -UUID $player.uuid -ProfileData $selected -OutputDir $dir
    
    Write-Header "Done! Saved $($res.Count) files to $dir"
    if (-not $Silent) { Read-Host "Press Enter to exit" }
}
catch {
    Write-Error-Custom "Critical Error: $($_.Exception.Message)"
    if (-not $Silent) { Read-Host "Press Enter to exit" }
    exit 1
}
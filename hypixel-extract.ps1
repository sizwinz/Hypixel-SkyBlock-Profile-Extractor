<#
.SYNOPSIS
    SkyBlock Profile Extractor - Official Hypixel API Edition
    Extract complete Hypixel SkyBlock profile data using official API

.DESCRIPTION
    This script extracts comprehensive profile data from Hypixel SkyBlock using the official Hypixel API.
    Provides complete access to all profile data including inventories, skills, collections, and more.

.PARAMETER Username
    Minecraft username to extract data for

.PARAMETER Profile
    Specific profile name to extract (optional)

.PARAMETER Silent
    Run in silent mode without interactive prompts

.EXAMPLE
    .\extract-profile-v2.ps1
    
.EXAMPLE
    .\extract-profile-v2.ps1 -Username "Technoblade"
    
.EXAMPLE
    .\extract-profile-v2.ps1 -Username "Technoblade" -Profile "Coconut" -Silent

.NOTES
    Version: 2.0 - Official Hypixel API
    Author: SkyBlock Profile Extractor Team
    API Documentation: https://api.hypixel.net
#>

param(
    [Parameter(Position = 0)]
    [string]$Username,
    
    [Parameter(Position = 1)]
    [string]$Profile,
    
    [switch]$Silent
)

# Enable TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

# ============================================================================
# CONFIGURATION
# ============================================================================

$Script:Version = "2.0"
$Script:HypixelApiKey = $null
$Script:HypixelBaseUrl = "https://api.hypixel.net"
$Script:MojangBaseUrl = "https://api.mojang.com"
$Script:UserAgent = "SkyBlock-Profile-Extractor/2.0"
$Script:RateLimit = 1200  # 1.2 seconds between requests (safe for 300/5min limit)

# Color scheme
$Colors = @{
    Header  = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
    Info    = "White"
    Accent  = "Magenta"
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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
    if (-not $Silent) {
        Write-Host "[✓] $Message" -ForegroundColor $Colors.Success
    }
}

function Write-Info {
    param([string]$Message)
    if (-not $Silent) {
        Write-Host "[i] $Message" -ForegroundColor $Colors.Info
    }
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
    param(
        [string]$Prompt,
        [string]$Default = ""
    )
    
    if ($Silent -and $Default) {
        return $Default
    }
    
    $input = Read-Host $Prompt
    if (-not $input -and $Default) {
        return $Default
    }
    return $input
}

# ============================================================================
# API CALL FUNCTIONS
# ============================================================================

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
                if ($response.cause) {
                    throw "API Error: $($response.cause)"
                }
                throw "API returned success=false"
            }
            
            # Rate limiting
            Start-Sleep -Milliseconds $Script:RateLimit
            return $response
        }
        catch {
            $attempt++
            if ($attempt -ge $RetryCount) {
                throw "$ErrorContext failed after $RetryCount attempts: $($_.Exception.Message)"
            }
            
            Write-Warning "$ErrorContext failed (attempt $attempt/$RetryCount). Retrying in $($attempt * 2) seconds..."
            Start-Sleep -Seconds ($attempt * 2)
        }
    }
}

function Invoke-MojangApiCall {
    param(
        [string]$Endpoint,
        [string]$ErrorContext = "Mojang API call"
    )
    
    try {
        $url = "$Script:MojangBaseUrl/$Endpoint"
        $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
        Start-Sleep -Milliseconds 500
        return $response
    }
    catch {
        throw "$ErrorContext failed: $($_.Exception.Message)"
    }
}

# ============================================================================
# PLAYER LOOKUP FUNCTIONS
# ============================================================================

function Get-PlayerUUID {
    param([string]$Username)
    
    Write-Info "Looking up UUID for '$Username'..."
    
    try {
        # Use Mojang API to get UUID
        $response = Invoke-MojangApiCall -Endpoint "users/profiles/minecraft/$Username" -ErrorContext "UUID lookup"
        
        if ($response.id) {
            # Format UUID with dashes
            $uuid = $response.id
            $formattedUuid = $uuid.Insert(8, '-').Insert(13, '-').Insert(18, '-').Insert(23, '-')
            
            Write-Success "Found player: $($response.name) ($($uuid.Substring(0,8))...)"
            
            return @{
                username     = $response.name
                uuid         = $formattedUuid
                uuid_trimmed = $uuid
            }
        }
        else {
            throw "Player not found"
        }
    }
    catch {
        Write-Error-Custom "Failed to find player '$Username': $($_.Exception.Message)"
        Write-Warning "Verify the username is correct and the player has joined Minecraft before."
        return $null
    }
}

function Get-PlayerProfiles {
    param(
        [string]$UUID,
        [string]$Username
    )
    
    Write-Info "Fetching SkyBlock profiles from Hypixel API..."
    
    try {
        $response = Invoke-HypixelApiCall -Endpoint "skyblock/profiles?uuid=$UUID" -ErrorContext "Profile lookup"
        
        if ($response.profiles -and $response.profiles.Count -gt 0) {
            $profileList = @()
            
            foreach ($profile in $response.profiles) {
                # Determine if this profile is selected (check member data)
                $memberData = $profile.members.$UUID
                $isSelected = $false
                
                # The selected profile is usually indicated by having the most recent last_save
                if ($memberData) {
                    $isSelected = $true  # We'll determine the actual selected one by last_save later
                }
                
                $profileList += @{
                    profile_id = $profile.profile_id
                    cute_name  = $profile.cute_name
                    game_mode  = if ($profile.game_mode) { $profile.game_mode } else { "normal" }
                    selected   = $isSelected
                    last_save  = if ($memberData.last_save) { $memberData.last_save } else { 0 }
                    data       = $profile
                }
            }
            
            # Sort by last_save to find the most recently used profile
            $profileList = $profileList | Sort-Object -Property last_save -Descending
            
            # Mark the first one as selected
            if ($profileList.Count -gt 0) {
                $profileList[0].selected = $true
            }
            
            Write-Success "Found $($profileList.Count) SkyBlock profile(s)"
            return $profileList
        }
        else {
            throw "No SkyBlock profiles found for this player"
        }
    }
    catch {
        Write-Error-Custom "Failed to fetch profiles: $($_.Exception.Message)"
        Write-Warning "Possible causes:"
        Write-Warning "  1. Player has never played SkyBlock"
        Write-Warning "  2. All profiles are deleted"
        Write-Warning "  3. Temporary API issue - try again in a few seconds"
        return $null
    }
}

# ============================================================================
# PROFILE SELECTION
# ============================================================================

function Select-Profile {
    param(
        [array]$Profiles,
        [string]$RequestedProfile
    )
    
    if ($Profiles.Count -eq 0) {
        return $null
    }
    
    if ($Profiles.Count -eq 1) {
        Write-Info "Only one profile found, auto-selecting: $($Profiles[0].cute_name)"
        return $Profiles[0]
    }
    
    # If specific profile requested
    if ($RequestedProfile) {
        $selectedProfile = $Profiles | Where-Object { $_.cute_name -eq $RequestedProfile }
        if ($selectedProfile) {
            Write-Success "Selected profile: $RequestedProfile"
            return $selectedProfile
        }
        else {
            Write-Warning "Profile '$RequestedProfile' not found."
        }
    }
    
    # Interactive selection
    if (-not $Silent) {
        Write-Host "`n[i] Available profiles:" -ForegroundColor $Colors.Info
        for ($i = 0; $i -lt $Profiles.Count; $i++) {
            $emoji = if ($Profiles[$i].selected) { "★" } else { "☆" }
            $mode = if ($Profiles[$i].game_mode -ne "normal") { " [$($Profiles[$i].game_mode.ToUpper())]" } else { "" }
            Write-Host "  $($i + 1). $emoji $($Profiles[$i].cute_name)$mode"
        }
        
        do {
            $choice = Get-UserInput "`nSelect profile number [1]" "1"
            try {
                $index = [int]$choice - 1
            }
            catch {
                $index = -1
            }
        } while ($index -lt 0 -or $index -ge $Profiles.Count)
        
        return $Profiles[$index]
    }
    else {
        # In silent mode, return the selected (most recent) profile
        return $Profiles[0]
    }
}

# ============================================================================
# DATA EXTRACTION
# ============================================================================

function New-OutputDirectory {
    param(
        [string]$Username,
        [string]$ProfileName
    )
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $safeProfileName = $ProfileName -replace '[\\/:*?"<>|]', '_'
    $outputDir = "SkyBlock_${Username}_${safeProfileName}_${timestamp}"
    
    try {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        Write-Success "Created output directory: $outputDir"
        return $outputDir
    }
    catch {
        Write-Error-Custom "Failed to create output directory: $($_.Exception.Message)"
        return $null
    }
}

function Start-DataExtraction {
    param(
        [string]$UUID,
        [object]$ProfileData,
        [string]$OutputDir
    )
    
    Write-Header "Extracting Profile Data"
    
    $extractedFiles = @()
    
    # 1. Save complete profile data (most important!)
    try {
        Write-Info "Saving complete profile data..."
        $profilePath = Join-Path $OutputDir "complete_profile.json"
        $ProfileData.data | ConvertTo-Json -Depth 100 -Compress:$false | Out-File -FilePath $profilePath -Encoding UTF8
        Write-Success "Saved complete profile (contains all inventories, skills, collections, banking, etc.)"
        $extractedFiles += "complete_profile.json"
    }
    catch {
        Write-Error-Custom "Failed to save complete profile: $($_.Exception.Message)"
    }
    
    # 2. Extract additional Hypixel API endpoints
    $additionalEndpoints = @(
        @{ 
            Endpoint    = "player?uuid=$UUID"
            File        = "player_data.json"
            Description = "General player data (achievements, network level, etc.)"
        },
        @{ 
            Endpoint    = "skyblock/bingo?uuid=$UUID"
            File        = "bingo_data.json"
            Description = "Bingo event data"
        },
        @{ 
            Endpoint    = "skyblock/bazaar"
            File        = "bazaar_prices.json"
            Description = "Current bazaar prices"
        },
        @{ 
            Endpoint    = "skyblock/auctions?profile=$($ProfileData.profile_id)"
            File        = "active_auctions.json"
            Description = "Active auctions for this profile"
        },
        @{ 
            Endpoint    = "skyblock/news"
            File        = "skyblock_news.json"
            Description = "SkyBlock news"
        }
    )
    
    foreach ($endpoint in $additionalEndpoints) {
        try {
            Write-Info "Extracting: $($endpoint.Description)..."
            $data = Invoke-HypixelApiCall -Endpoint $endpoint.Endpoint -ErrorContext $endpoint.Description
            
            $filePath = Join-Path $OutputDir $endpoint.File
            $data | ConvertTo-Json -Depth 100 -Compress:$false | Out-File -FilePath $filePath -Encoding UTF8
            
            Write-Success "Saved: $($endpoint.File)"
            $extractedFiles += $endpoint.File
        }
        catch {
            Write-Warning "Failed to extract $($endpoint.Description): $($_.Exception.Message)"
        }
    }
    
    # 3. Create a README file
    try {
        $readmePath = Join-Path $OutputDir "README.txt"
        $readmeContent = @"
SKYBLOCK PROFILE EXTRACTION REPORT
===================================
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Player: $($ProfileData.data.members.$UUID.profile.display_name)
Profile: $($ProfileData.cute_name) [$($ProfileData.game_mode)]
Profile ID: $($ProfileData.profile_id)

FILES EXTRACTED:
----------------
$($extractedFiles | ForEach-Object { "- $_" } | Out-String)

IMPORTANT NOTES:
----------------
1. complete_profile.json contains ALL your SkyBlock data:
   - All inventories (main, ender chest, backpacks, etc.)
   - Skills, collections, and slayer progress
   - Pets, minions, and accessories
   - Banking, objectives, and quests
   - Dungeon and crimson isle progress
   - Garden, museum, and rift data

2. This data respects your in-game API settings.
   If certain data is missing, ensure all API options are
   enabled in: SkyBlock Menu → Settings → API Settings

3. Data is extracted using Official Hypixel API
   API Documentation: https://api.hypixel.net

USING THIS DATA:
----------------
- Upload to AI assistants (ChatGPT, Claude) for analysis
- Import into data visualization tools
- Use for personal progress tracking
- Share with SkyBlock helper applications

PRIVACY WARNING:
----------------
This data contains sensitive information about your SkyBlock
progress. Only share with trusted sources!

Script Version: $Script:Version
Extraction Tool: SkyBlock Profile Extractor
"@
        $readmeContent | Out-File -FilePath $readmePath -Encoding UTF8
        Write-Success "Created README.txt with extraction details"
    }
    catch {
        Write-Warning "Failed to create README file"
    }
    
    return @{
        Success     = $extractedFiles.Count
        Total       = $additionalEndpoints.Count + 1
        SuccessRate = [math]::Round(($extractedFiles.Count / ($additionalEndpoints.Count + 1)) * 100, 1)
        Files       = $extractedFiles
    }
}

# ============================================================================
# SUMMARY AND COMPLETION
# ============================================================================

function Show-Summary {
    param(
        [hashtable]$Results,
        [string]$OutputDir,
        [string]$Username,
        [string]$ProfileName
    )
    
    Write-Header "Extraction Complete!"
    
    Write-Host "`n📦 Output Directory: " -NoNewline -ForegroundColor $Colors.Info
    Write-Host $OutputDir -ForegroundColor $Colors.Accent
    
    Write-Host "📊 Files Extracted: " -NoNewline -ForegroundColor $Colors.Info
    Write-Host "$($Results.Success)/$($Results.Total)" -ForegroundColor $Colors.Success
    
    Write-Host "✅ Success Rate: " -NoNewline -ForegroundColor $Colors.Info
    Write-Host "$($Results.SuccessRate)%" -ForegroundColor $Colors.Success
    
    # Calculate directory size
    $dirInfo = Get-ChildItem $OutputDir | Measure-Object -Property Length -Sum
    $sizeMB = [math]::Round($dirInfo.Sum / 1MB, 2)
    $sizeKB = [math]::Round($dirInfo.Sum / 1KB, 2)
    
    $sizeDisplay = if ($sizeMB -gt 0.1) { "$sizeMB MB" } else { "$sizeKB KB" }
    Write-Host "💾 Total Size: " -NoNewline -ForegroundColor $Colors.Info
    Write-Host $sizeDisplay -ForegroundColor $Colors.Accent
    
    Write-Host "`n" -NoNewline
    Write-Host "═══════════════════════════════════════════════════" -ForegroundColor $Colors.Header
    Write-Host "🎯 NEXT STEPS:" -ForegroundColor $Colors.Accent
    Write-Host "═══════════════════════════════════════════════════" -ForegroundColor $Colors.Header
    
    Write-Host "`n1. " -NoNewline -ForegroundColor $Colors.Info
    Write-Host "Review 'complete_profile.json' for all your data"
    
    Write-Host "2. " -NoNewline -ForegroundColor $Colors.Info
    Write-Host "Compress the folder for easy sharing:"
    Write-Host "   Compress-Archive -Path '$OutputDir' -DestinationPath '${OutputDir}.zip'" -ForegroundColor $Colors.Accent
    
    Write-Host "`n3. " -NoNewline -ForegroundColor $Colors.Info
    Write-Host "Upload to AI for analysis and ask questions like:"
    Write-Host "   - 'Analyze my skill progression and suggest improvements'" -ForegroundColor $Colors.Accent
    Write-Host "   - 'What should I focus on to increase my networth?'" -ForegroundColor $Colors.Accent
    Write-Host "   - 'Review my gear and recommend upgrades'" -ForegroundColor $Colors.Accent
    
    Write-Host "`n4. " -NoNewline -ForegroundColor $Colors.Info
    Write-Host "Check README.txt for detailed information"
    
    Write-Host "`n" -NoNewline
    Write-Host "═══════════════════════════════════════════════════" -ForegroundColor $Colors.Header
    
    if (-not $Silent) {
        Write-Host "`nPress any key to exit..." -ForegroundColor $Colors.Info
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

function Test-Prerequisites {
    Write-Info "Testing prerequisites..."
    
    # Check PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 3) {
        Write-Error-Custom "PowerShell 3.0+ required. Current: $($PSVersionTable.PSVersion)"
        return $false
    }
    Write-Success "PowerShell version OK ($($PSVersionTable.PSVersion))"
    
    # Check API key
    if (-not $Script:HypixelApiKey -or $Script:HypixelApiKey.Length -ne 36) {
        Write-Error-Custom "Invalid Hypixel API key. Get one by typing '/api new' on Hypixel"
        return $false
    }
    Write-Success "API key configured"
    
    # Test internet connectivity
    try {
        $null = Invoke-RestMethod -Uri "https://api.hypixel.net/key" -Headers @{'API-Key' = $Script:HypixelApiKey } -Method Get -TimeoutSec 5
        Write-Success "API connection successful"
    }
    catch {
        Write-Error-Custom "Cannot connect to Hypixel API. Check your internet connection."
        return $false
    }
    
    return $true
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

try {
    Clear-Host
    Write-Header "SkyBlock Profile Extractor v$Script:Version"
    Write-Host "Using Official Hypixel API for maximum compatibility`n" -ForegroundColor $Colors.Accent
    
    $KeyFile = Join-Path $PSScriptRoot "api_key.txt"
        
        if (Test-Path $KeyFile) {
            $Script:HypixelApiKey = Get-Content $KeyFile -Raw
            $Script:HypixelApiKey = $Script:HypixelApiKey.Trim()
            Write-Info "Loaded API key from api_key.txt"
        }
        else {
            Write-Warning "Hypixel API Key not found!"
            Write-Host "1. Go to https://developer.hypixel.net"
            Write-Host "2. Login and copy your 'Development Key'"
            
            $InputKey = Get-UserInput "Enter your Hypixel API Key"
            
            if ($InputKey -and $InputKey.Length -gt 30) {
                $Script:HypixelApiKey = $InputKey.Trim()
                $Script:HypixelApiKey | Out-File -FilePath $KeyFile -Encoding ASCII
                Write-Success "API Key saved to api_key.txt"
            }
            else {
                Write-Error-Custom "Invalid API Key provided. Exiting."
                exit 1
            }
        }

    # Test prerequisites
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    Write-Host ""
    
    # Get username
    if (-not $Username) {
        $Username = Get-UserInput "Enter Minecraft username"
        if (-not $Username) {
            Write-Error-Custom "Username is required!"
            exit 1
        }
    }
    
    # Get player UUID
    $playerInfo = Get-PlayerUUID -Username $Username
    if (-not $playerInfo) {
        exit 1
    }
    
    # Get SkyBlock profiles
    $profiles = Get-PlayerProfiles -UUID $playerInfo.uuid -Username $Username
    if (-not $profiles) {
        exit 1
    }
    
    # Select profile
    $selectedProfile = Select-Profile -Profiles $profiles -RequestedProfile $Profile
    if (-not $selectedProfile) {
        Write-Error-Custom "No profile selected!"
        exit 1
    }
    
    Write-Success "Selected profile: $($selectedProfile.cute_name) [$($selectedProfile.game_mode)]"
    
    # Create output directory
    $outputDir = New-OutputDirectory -Username $Username -ProfileName $selectedProfile.cute_name
    if (-not $outputDir) {
        exit 1
    }
    
    # Extract all data
    $results = Start-DataExtraction -UUID $playerInfo.uuid -ProfileData $selectedProfile -OutputDir $outputDir
    
    # Show summary
    Show-Summary -Results $results -OutputDir $outputDir -Username $Username -ProfileName $selectedProfile.cute_name
    
    exit 0
}
catch {
    Write-Error-Custom "Unexpected error: $($_.Exception.Message)"
    Write-Host "Stack Trace: $($_.ScriptStackTrace)" -ForegroundColor $Colors.Error
    
    if (-not $Silent) {
        Write-Host "`nPress any key to exit..." -ForegroundColor $Colors.Info
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    
    exit 1
}

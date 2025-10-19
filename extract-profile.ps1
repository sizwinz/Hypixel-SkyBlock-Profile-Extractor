<#
.SYNOPSIS
    SkyBlock Profile Extractor - PowerShell Edition
    Extract complete Hypixel SkyBlock profile data for AI analysis

.DESCRIPTION
    This script extracts comprehensive profile data from Hypixel SkyBlock using the SkyCrypt API.
    Perfect for AI analysis, personal tracking, or data visualization.

.PARAMETER Username
    Minecraft username to extract data for

.PARAMETER Profile
    Specific profile name to extract (optional)

.PARAMETER Silent
    Run in silent mode without interactive prompts

.EXAMPLE
    .\extract-profile.ps1
    
.EXAMPLE
    .\extract-profile.ps1 -Username "TechnoBlade"
    
.EXAMPLE
    .\extract-profile.ps1 -Username "TechnoBlade" -Profile "Watermelon" -Silent

.NOTES
    Version: 1 - Hybrid profile fetching
    Author: SkyBlock Profile Extractor Team
    Repository: https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor
#>

param(
    [Parameter(Position=0)]
    [string]$Username,
    
    [Parameter(Position=1)]
    [string]$Profile,
    
    [switch]$Silent
)

# Script configuration
$Script:Version = "1"
$Script:BaseUrl = "https://cupcake.shiiyu.moe/api"
$Script:UserAgent = "SkyBlock-Profile-Extractor/1"
$Script:RateLimit = 500  # milliseconds between requests

# Color scheme
$Colors = @{
    Header = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "White"
    Accent = "Magenta"
}

function Write-Header {
    param([string]$Title)
    
    if (-not $Silent) {
        Write-Host "`n>> $Title" -ForegroundColor $Colors.Header
        Write-Host ("-" * 50) -ForegroundColor $Colors.Header
    }
}

function Write-Success {
    param([string]$Message)
    
    if (-not $Silent) {
        Write-Host "[+] $Message" -ForegroundColor $Colors.Success
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
    
    Write-Host "[X] $Message" -ForegroundColor $Colors.Error
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

function Invoke-ApiCall {
    param(
        [string]$Endpoint,
        [string]$ErrorContext = "API call",
        [switch]$Ignore403
    )
    
    try {
        $headers = @{
            'User-Agent' = $Script:UserAgent
        }
        
        $response = Invoke-RestMethod -Uri $Endpoint -Method Get -Headers $headers -TimeoutSec 30
        Start-Sleep -Milliseconds $Script:RateLimit
        return $response
    }
    catch {
        if ($Ignore403 -and $_.Exception.Response -and $_.Exception.Response.StatusCode -eq 403) {
            throw "403 Forbidden"
        }
        throw "$ErrorContext failed: $($_.Exception.Message)"
    }
}

function Get-PlayerUUID {
    param([string]$Username)
    
    Write-Info "Looking up UUID for $Username..."
    
    try {
        $response = Invoke-ApiCall -Endpoint "$Script:BaseUrl/uuid/$Username" -ErrorContext "UUID lookup"
        
        if ($response.uuid) {
            Write-Success "Found player: $($response.username) ($($response.uuid.Substring(0,8))...)"
            return $response
        }
        else {
            throw "Player not found"
        }
    }
    catch {
        Write-Error-Custom "Failed to find player '$Username': $($_.Exception.Message)"
        Write-Warning "Make sure the username is spelled correctly and the player exists."
        return $null
    }
}

function Get-PlayerProfiles {
    param(
        [string]$UUID,
        [string]$Username
    )
    
    Write-Info "Fetching SkyBlock profiles..."
    
    # Try the comprehensive endpoint first
    try {
        $response = Invoke-ApiCall -Endpoint "$Script:BaseUrl/profiles/$UUID" -ErrorContext "Full profile lookup" -Ignore403
        
        if ($response.profiles) {
            $profileList = @()
            foreach ($profileId in $response.profiles.Keys) {
                $profileData = $response.profiles[$profileId]
                $profileList += @{
                    profile_id = $profileData.profile_id
                    profile_cute_name = $profileData.cute_name
                    selected = $profileData.selected
                }
            }
            Write-Success "Found $($profileList.Count) profiles."
            return $profileList
        }
    }
    catch {
        if ($_.Exception.Message -eq "403 Forbidden") {
            Write-Warning "Could not fetch all profiles (API permissions likely restricted). Falling back to active profile only."
        } else {
            Write-Warning "Could not fetch all profiles: $($_.Exception.Message). Falling back to active profile only."
        }
    }
    
    # Fallback to the stats endpoint for the active profile
    try {
        $response = Invoke-ApiCall -Endpoint "$Script:BaseUrl/stats/$UUID" -ErrorContext "Active profile lookup"
        
        if ($response.stats) {
            $profile = @{
                profile_id = $response.stats.profile_id
                profile_cute_name = $response.stats.profile_cute_name
                selected = $true
            }
            
            Write-Success "Found active profile: (T) $($profile.profile_cute_name)"
            return @($profile)
        }
        else {
            throw "No SkyBlock profiles found"
        }
    }
    catch {
        Write-Error-Custom "Failed to fetch any profiles for '$Username': $($_.Exception.Message)"
        return $null
    }
}


function Select-Profile {
    param(
        [array]$Profiles,
        [string]$RequestedProfile
    )
    
    if ($Profiles.Count -eq 0) {
        return $null
    }
    if ($Profiles.Count -eq 1) {
        return $Profiles[0]
    }
    
    if ($RequestedProfile) {
        $selectedProfile = $Profiles | Where-Object { $_.profile_cute_name -eq $RequestedProfile }
        if ($selectedProfile) {
            return $selectedProfile
        }
        else {
            Write-Warning "Profile '$RequestedProfile' not found. Available profiles:"
            for ($i = 0; $i -lt $Profiles.Count; $i++) {
                Write-Host "  $($i + 1). $($Profiles[$i].profile_cute_name)"
            }
        }
    }
    
    if (-not $Silent) {
        Write-Host "`n[i] Available profiles:" -ForegroundColor $Colors.Info
        for ($i = 0; $i -lt $Profiles.Count; $i++) {
            $emoji = if ($Profiles[$i].selected) { "(T)" } else { "(C)" }
            $selected = if ($Profiles[$i].selected) { " (Selected)" } else { "" }
            Write-Host "  $($i + 1). $emoji $($Profiles[$i].profile_cute_name)$selected"
        }
        
        do {
            $choice = Get-UserInput "Select profile [1]" "1"
            try {
                $index = [int]$choice - 1
            } catch {
                $index = -1
            }
        } while ($index -lt 0 -or $index -ge $Profiles.Count)
        
        return $Profiles[$index]
    }
    else {
        # In silent mode, use the selected profile or the first one if none is selected
        $selected = $Profiles | Where-Object { $_.selected }
        if ($selected) {
            return $selected
        }
        return $Profiles[0]
    }
}

function New-OutputDirectory {
    param([string]$Username, [string]$ProfileName)
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    # Sanitize profile name for directory
    $safeProfileName = $ProfileName -replace '[\\/:*?"<>|]', ''
    $outputDir = "$($Username)_$($safeProfileName)_$timestamp"
    
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

function Save-ProfileData {
    param(
        [string]$Endpoint,
        [string]$OutputFile,
        [string]$OutputDir,
        [string]$Description
    )
    
    try {
        Write-Info "Extracting $Description..."
        $response = Invoke-ApiCall -Endpoint $Endpoint -ErrorContext $Description
        
        $filePath = Join-Path $OutputDir $OutputFile
        $response | ConvertTo-Json -Depth 10 | Out-File -FilePath $filePath -Encoding UTF8
        
        Write-Success "Saved $Description"
        return $true
    }
    catch {
        Write-Warning "Failed to extract $Description : $($_.Exception.Message)"
        return $false
    }
}

function Start-DataExtraction {
    param(
        [string]$UUID,
        [string]$ProfileId,
        [string]$OutputDir
    )
    
    Write-Header "Extracting Profile Data"
    
    $extractionPlan = @(
        @{ Endpoint = "stats/$UUID/$ProfileId"; File = "stats.json"; Description = "Profile Statistics" },
        @{ Endpoint = "playerStats/$UUID/$ProfileId"; File = "player_stats.json"; Description = "Player Performance" },
        @{ Endpoint = "networth/$UUID/$ProfileId"; File = "networth.json"; Description = "Networth Analysis" },
        @{ Endpoint = "skills/$UUID/$ProfileId"; File = "skills.json"; Description = "Skills & XP" },
        @{ Endpoint = "dungeons/$UUID/$ProfileId"; File = "dungeons.json"; Description = "Dungeon Progress" },
        @{ Endpoint = "slayer/$UUID/$ProfileId"; File = "slayer.json"; Description = "Slayer Statistics" },
        @{ Endpoint = "collections/$UUID/$ProfileId"; File = "collections.json"; Description = "Collection Progress" },
        @{ Endpoint = "gear/$UUID/$ProfileId"; File = "gear.json"; Description = "Equipment & Gear" },
        @{ Endpoint = "accessories/$UUID/$ProfileId"; File = "accessories.json"; Description = "Accessories & Talismans" },
        @{ Endpoint = "pets/$UUID/$ProfileId"; File = "pets.json"; Description = "Pet Collection" },
        @{ Endpoint = "minions/$UUID/$ProfileId"; File = "minions.json"; Description = "Minion Data" },
        @{ Endpoint = "bestiary/$UUID/$ProfileId"; File = "bestiary.json"; Description = "Bestiary Progress" },
        @{ Endpoint = "crimson_isle/$UUID/$ProfileId"; File = "crimson_isle.json"; Description = "Crimson Isle Progress" },
        @{ Endpoint = "rift/$UUID/$ProfileId"; File = "rift.json"; Description = "Rift Dimension" },
        @{ Endpoint = "misc/$UUID/$ProfileId"; File = "misc.json"; Description = "Miscellaneous Data" },
        @{ Endpoint = "garden/$ProfileId"; File = "garden.json"; Description = "Garden Progress" }
    )
    
    # Inventory endpoints
    $inventoryTypes = @(
        @{ Type = "inv_contents"; Description = "Main Inventory" },
        @{ Type = "ender_chest_contents"; Description = "Ender Chest" },
        @{ Type = "wardrobe_contents"; Description = "Wardrobe" },
        @{ Type = "personal_vault_contents"; Description = "Personal Vault" },
        @{ Type = "bag_contents"; Description = "All Bags" },
        @{ Type = "fishing_bag"; Description = "Fishing Bag" },
        @{ Type = "potion_bag"; Description = "Potion Bag" },
        @{ Type = "candy_inventory_contents"; Description = "Candy Inventory" },
        @{ Type = "quiver"; Description = "Quiver" }
    )
    
    foreach ($inv in $inventoryTypes) {
        $extractionPlan += @{
            Endpoint = "inventory/$UUID/$ProfileId/$($inv.Type)"
            File = "inventory_$($inv.Type).json"
            Description = $inv.Description
        }
    }
    
    $successCount = 0
    $totalCount = $extractionPlan.Count
    
    foreach ($item in $extractionPlan) {
        $endpoint = "$Script:BaseUrl/$($item.Endpoint)"
        $success = Save-ProfileData -Endpoint $endpoint -OutputFile $item.File -OutputDir $outputDir -Description $item.Description
        if ($success) { $successCount++ }
    }
    
    return @{
        Success = $successCount
        Total = $totalCount
        SuccessRate = [math]::Round(($successCount / $totalCount) * 100, 1)
    }
}

function Show-Summary {
    param(
        [hashtable]$Results,
        [string]$OutputDir,
        [string]$Username
    )
    
    Write-Header "Extraction Summary"
    
    Write-Host "[*] Data extraction completed!" -ForegroundColor $Colors.Success
    Write-Host "[i] Output directory: $OutputDir" -ForegroundColor $Colors.Info
    Write-Host "[i] Files extracted: $($Results.Success)/$($Results.Total)" -ForegroundColor $Colors.Info
    Write-Host "[>] Success rate: $($Results.SuccessRate)%" -ForegroundColor $Colors.Success
    
    $dirInfo = Get-ChildItem $OutputDir | Measure-Object -Property Length -Sum
    $sizeKB = [math]::Round($dirInfo.Sum / 1KB, 1)
    $sizeMB = [math]::Round($dirInfo.Sum / 1MB, 1)
    
    $sizeDisplay = if ($sizeMB -gt 1) { "$sizeMB MB" } else { "$sizeKB KB" }
    Write-Host "[S] Total size: $sizeDisplay" -ForegroundColor $Colors.Info
    
    Write-Host "`n[A] Ready for AI analysis!" -ForegroundColor $Colors.Accent
    Write-Host "Your complete SkyBlock profile data is now available for:" -ForegroundColor $Colors.Info
    Write-Host "  - AI-powered progression analysis"
    Write-Host "  - Personal performance tracking"
    Write-Host "  - Data visualization projects"
    Write-Host "  - Optimization recommendations"
    
    Write-Host "`n[N] Next Steps:" -ForegroundColor $Colors.Header
    Write-Host "  1. Zip the '$OutputDir' folder for easy sharing"
    Write-Host "  2. Upload to your preferred AI assistant (ChatGPT, Claude, etc.)"
    Write-Host "  3. Ask for progression analysis and recommendations!"
    
    if (-not $Silent) {
        Write-Host "`nPress any key to continue..." -ForegroundColor $Colors.Info
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

function Test-Prerequisites {
    # Check PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 3) {
        Write-Error-Custom "PowerShell 3.0 or higher is required. Current version: $($PSVersionTable.PSVersion)"
        return $false
    }
    
    # Check internet connectivity
    try {
        $null = Invoke-RestMethod -Uri "https://cupcake.shiiyu.moe" -Method Head -TimeoutSec 5
    }
    catch {
        Write-Error-Custom "Cannot connect to SkyCrypt API. Please check your internet connection."
        return $false
    }
    
    return $true
}

# Main execution
try {
    Write-Header "SkyBlock Profile Extractor v$Script:Version"
    
    # Test prerequisites
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    # Get username
    if (-not $Username) {
        $Username = Get-UserInput "Enter your Minecraft username"
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
    
    # Get profiles
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
    
    # Create output directory
    $outputDir = New-OutputDirectory -Username $Username -ProfileName $selectedProfile.profile_cute_name
    if (-not $outputDir) {
        exit 1
    }
    
    # Extract data
    $results = Start-DataExtraction -UUID $playerInfo.uuid -ProfileId $selectedProfile.profile_id -OutputDir $outputDir
    
    # Show summary
    Show-Summary -Results $results -OutputDir $outputDir -Username $Username
    
    Write-Success "SkyBlock Profile extraction completed successfully!"
}
catch {
    Write-Error-Custom "An unexpected error occurred: $($_.Exception.Message)"
    Write-Host "Stack Trace: $($_.ScriptStackTrace)" -ForegroundColor $Colors.Error
    exit 1
}

# Windows Service Management for Super Agent Dashboard
# Run as Administrator to install/remove Windows service

param(
    [string]$Action = "install",  # install, remove, start, stop, status
    [string]$ServiceName = "SuperAgentDashboard"
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = "C:\Jarvis\AI Workspace\Super Agent"

function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Write-Status {
    param([string]$Message, [string]$Color = "Green")
    Write-Host "==> $Message" -ForegroundColor $Color
}

function Write-Error {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Install-Service {
    Write-Status "Installing Windows Service: $ServiceName"
    
    # Check if NSSM is available
    try {
        nssm version | Out-Null
        $useNSSM = $true
    } catch {
        Write-Status "NSSM not found, using PowerShell approach" -Color "Yellow"
        $useNSSM = $false
    }
    
    if ($useNSSM) {
        Install-ServiceWithNSSM
    } else {
        Install-ServiceWithPowerShell
    }
}

function Install-ServiceWithNSSM {
    Write-Status "Installing service with NSSM..."
    
    # Remove existing service if it exists
    nssm remove $ServiceName confirm 2>$null
    
    # Install new service
    nssm install $ServiceName "node" "$WorkspaceRoot\agent-dashboard\server\index-robust.js"
    nssm set $ServiceName AppDirectory "$WorkspaceRoot\agent-dashboard"
    nssm set $ServiceName DisplayName "Super Agent Dashboard"
    nssm set $ServiceName Description "Super Agent System Dashboard Server"
    nssm set $ServiceName Start SERVICE_AUTO_START
    
    # Set environment variables
    nssm set $ServiceName AppEnvironmentExtra "NODE_ENV=production" "PORT=3001"
    
    # Set logging
    nssm set $ServiceName AppStdout "$WorkspaceRoot\logs\service-out.log"
    nssm set $ServiceName AppStderr "$WorkspaceRoot\logs\service-error.log"
    nssm set $ServiceName AppRotateFiles 1
    nssm set $ServiceName AppRotateOnline 1
    nssm set $ServiceName AppRotateSeconds 86400
    nssm set $ServiceName AppRotateBytes 10485760
    
    # Set failure actions
    nssm set $ServiceName AppExit Default Restart
    nssm set $ServiceName AppRestartDelay 5000
    
    Write-Status "Service installed with NSSM"
}

function Install-ServiceWithPowerShell {
    Write-Status "Creating service wrapper script..."
    
    $serviceScript = @"
# Super Agent Dashboard Service Wrapper
`$ErrorActionPreference = "Stop"

# Change to dashboard directory
Set-Location "$WorkspaceRoot\agent-dashboard"

# Set environment variables
`$env:NODE_ENV = "production"
`$env:PORT = "3001"

# Start the dashboard server
try {
    Write-EventLog -LogName Application -Source "SuperAgentDashboard" -EventId 1001 -Message "Starting Super Agent Dashboard"
    node server/index-robust.js
} catch {
    Write-EventLog -LogName Application -Source "SuperAgentDashboard" -EventId 1002 -EntryType Error -Message "Failed to start: `$(`$_.Exception.Message)"
    exit 1
}
"@
    
    $scriptPath = "$WorkspaceRoot\.claude\production\service-wrapper.ps1"
    $serviceScript | Out-File -FilePath $scriptPath -Encoding UTF8
    
    # Create Windows service
    $serviceBinary = "powershell.exe -ExecutionPolicy Bypass -File `"$scriptPath`""
    
    New-Service -Name $ServiceName `
                -BinaryPathName $serviceBinary `
                -DisplayName "Super Agent Dashboard" `
                -Description "Super Agent System Dashboard Server" `
                -StartupType Automatic
    
    Write-Status "Service installed with PowerShell wrapper"
}

function Remove-Service {
    Write-Status "Removing Windows Service: $ServiceName"
    
    # Stop service first
    try {
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    } catch {}
    
    # Remove service
    try {
        # Try NSSM first
        nssm remove $ServiceName confirm 2>$null
    } catch {
        # Fall back to PowerShell
        Remove-Service -Name $ServiceName -ErrorAction SilentlyContinue
    }
    
    Write-Status "Service removed"
}

function Start-ServiceSafe {
    Write-Status "Starting service: $ServiceName"
    
    try {
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 3
        
        $service = Get-Service -Name $ServiceName
        if ($service.Status -eq "Running") {
            Write-Status "Service started successfully"
        } else {
            Write-Error "Service failed to start properly. Status: $($service.Status)"
        }
    } catch {
        Write-Error "Failed to start service: $($_.Exception.Message)"
    }
}

function Stop-ServiceSafe {
    Write-Status "Stopping service: $ServiceName"
    
    try {
        Stop-Service -Name $ServiceName -Force
        Write-Status "Service stopped successfully"
    } catch {
        Write-Error "Failed to stop service: $($_.Exception.Message)"
    }
}

function Show-ServiceStatus {
    Write-Status "Service Status for: $ServiceName" -Color "Cyan"
    
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host "Name: $($service.Name)"
            Write-Host "Status: $($service.Status)"
            Write-Host "Start Type: $($service.StartType)"
            Write-Host "Display Name: $($service.DisplayName)"
            
            # Check if dashboard is actually responding
            try {
                $health = Invoke-RestMethod -Uri "http://localhost:3001/health" -TimeoutSec 5
                Write-Status "Dashboard Health: $($health.status)"
            } catch {
                Write-Status "Dashboard Health: Not responding" -Color "Red"
            }
        } else {
            Write-Status "Service not found: $ServiceName" -Color "Yellow"
        }
    } catch {
        Write-Error "Failed to get service status: $($_.Exception.Message)"
    }
}

# Main execution
if (!(Test-AdminRights)) {
    Write-Error "This script must be run as Administrator"
    exit 1
}

Write-Status "Super Agent Dashboard - Windows Service Manager" -Color "Cyan"

# Ensure logs directory exists
$logsDir = "$WorkspaceRoot\logs"
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Create event log source if it doesn't exist
try {
    if (![System.Diagnostics.EventLog]::SourceExists("SuperAgentDashboard")) {
        New-EventLog -LogName Application -Source "SuperAgentDashboard"
    }
} catch {
    # Ignore if we can't create event log source
}

switch ($Action.ToLower()) {
    "install" {
        Install-Service
    }
    "remove" {
        Remove-Service
    }
    "start" {
        Start-ServiceSafe
    }
    "stop" {
        Stop-ServiceSafe
    }
    "status" {
        Show-ServiceStatus
    }
    "restart" {
        Stop-ServiceSafe
        Start-Sleep -Seconds 2
        Start-ServiceSafe
    }
    default {
        Write-Error "Invalid action: $Action. Use: install, remove, start, stop, status, restart"
        exit 1
    }
}

Write-Status "Operation completed!"
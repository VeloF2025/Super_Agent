# Super Agent Dashboard - Production Deployment Script
# PowerShell script for Windows deployment

param(
    [string]$Mode = "local",  # local, docker, pm2
    [switch]$Build = $false,
    [switch]$Force = $false,
    [switch]$Monitor = $false
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = "C:\Jarvis\AI Workspace\Super Agent"
$ProductionDir = "$WorkspaceRoot\.claude\production"

function Write-Status {
    param([string]$Message, [string]$Color = "Green")
    Write-Host "==> $Message" -ForegroundColor $Color
}

function Write-Error {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check Node.js
    try {
        $nodeVersion = node --version
        Write-Status "Node.js: $nodeVersion"
    } catch {
        Write-Error "Node.js is not installed or not in PATH"
        exit 1
    }
    
    # Check Python
    try {
        $pythonVersion = python --version
        Write-Status "Python: $pythonVersion"
    } catch {
        Write-Error "Python is not installed or not in PATH"
        exit 1
    }
    
    # Check if workspace exists
    if (!(Test-Path $WorkspaceRoot)) {
        Write-Error "Workspace not found: $WorkspaceRoot"
        exit 1
    }
}

function Stop-ExistingProcesses {
    Write-Status "Stopping existing processes..."
    
    # Stop dashboard processes
    Get-Process | Where-Object { $_.Name -eq "node" -and $_.CommandLine -like "*dashboard*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Stop Python monitors
    Get-Process | Where-Object { $_.Name -eq "python" -and $_.CommandLine -like "*monitor*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Kill processes on port 3001
    $portProcess = netstat -ano | Select-String ":3001" | Select-String "LISTENING"
    if ($portProcess) {
        $processId = ($portProcess -split '\s+')[-1]
        if ($processId -and $processId -ne "0") {
            Write-Status "Killing process on port 3001 (PID: $processId)"
            taskkill /F /PID $processId 2>$null
        }
    }
    
    Start-Sleep -Seconds 2
}

function Build-Frontend {
    Write-Status "Building frontend..."
    
    Push-Location "$WorkspaceRoot\agent-dashboard\client"
    try {
        npm install
        npm run build
        Write-Status "Frontend build completed"
    } catch {
        Write-Error "Frontend build failed"
        exit 1
    } finally {
        Pop-Location
    }
}

function Deploy-Local {
    Write-Status "Deploying in local mode..."
    
    if ($Build) {
        Build-Frontend
    }
    
    # Create necessary directories
    $dirs = @("data", "logs", "shared\heartbeats", "shared\messages", "shared\queue")
    foreach ($dir in $dirs) {
        $fullPath = "$WorkspaceRoot\$dir"
        if (!(Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Status "Created directory: $dir"
        }
    }
    
    # Start dashboard server
    Write-Status "Starting dashboard server..."
    Push-Location "$WorkspaceRoot\agent-dashboard"
    try {
        Start-Process powershell -ArgumentList "-Command", "cd '$WorkspaceRoot\agent-dashboard'; node server/index-robust.js" -WindowStyle Minimized
        Start-Sleep -Seconds 3
        Write-Status "Dashboard server started"
    } finally {
        Pop-Location
    }
    
    # Start monitoring if requested
    if ($Monitor) {
        Write-Status "Starting dashboard monitor..."
        Push-Location $WorkspaceRoot
        try {
            Start-Process python -ArgumentList ".claude\dashboard-monitor.py", "start" -WindowStyle Minimized
            Write-Status "Dashboard monitor started"
        } finally {
            Pop-Location
        }
    }
    
    # Test deployment
    Start-Sleep -Seconds 5
    Test-Deployment
}

function Deploy-PM2 {
    Write-Status "Deploying with PM2..."
    
    # Check if PM2 is installed
    try {
        pm2 --version | Out-Null
    } catch {
        Write-Status "Installing PM2..."
        npm install -g pm2
    }
    
    if ($Build) {
        Build-Frontend
    }
    
    # Stop existing PM2 processes
    pm2 delete all 2>$null
    
    # Start with PM2
    Push-Location $WorkspaceRoot
    try {
        pm2 start ".claude\production\pm2.config.js"
        pm2 save
        Write-Status "PM2 deployment completed"
        
        # Show status
        pm2 status
    } finally {
        Pop-Location
    }
    
    Start-Sleep -Seconds 5
    Test-Deployment
}

function Deploy-Docker {
    Write-Status "Deploying with Docker..."
    
    # Check if Docker is installed
    try {
        docker --version | Out-Null
    } catch {
        Write-Error "Docker is not installed or not running"
        exit 1
    }
    
    # Check if Docker Compose is available
    try {
        docker-compose --version | Out-Null
    } catch {
        Write-Error "Docker Compose is not installed"
        exit 1
    }
    
    Push-Location $ProductionDir
    try {
        # Stop existing containers
        docker-compose down --remove-orphans 2>$null
        
        # Build and start
        if ($Build) {
            docker-compose build --no-cache
        }
        
        docker-compose up -d
        
        Write-Status "Docker deployment completed"
        
        # Show status
        docker-compose ps
    } finally {
        Pop-Location
    }
    
    Start-Sleep -Seconds 10
    Test-Deployment
}

function Test-Deployment {
    Write-Status "Testing deployment..."
    
    $healthUrl = "http://localhost:3001/health"
    $dashboardUrl = "http://localhost:3001/api/dashboard"
    
    try {
        $healthResponse = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 10
        if ($healthResponse.status -eq "healthy") {
            Write-Status "Health check: PASSED"
        } else {
            Write-Error "Health check failed: $($healthResponse.status)"
        }
        
        $dashboardResponse = Invoke-RestMethod -Uri $dashboardUrl -TimeoutSec 10
        if ($dashboardResponse.agents) {
            Write-Status "Dashboard API: PASSED (${$dashboardResponse.agents.Count} agents)"
        } else {
            Write-Error "Dashboard API test failed"
        }
        
        Write-Status "Deployment test completed successfully!" -Color "Cyan"
        Write-Status "Dashboard available at: http://localhost:3001" -Color "Yellow"
        
    } catch {
        Write-Error "Deployment test failed: $($_.Exception.Message)"
        Write-Status "Check logs for more details"
    }
}

function Show-Status {
    Write-Status "Production Deployment Status" -Color "Cyan"
    Write-Status "================================" -Color "Cyan"
    
    # Check processes
    $nodeProcesses = Get-Process | Where-Object { $_.Name -eq "node" -and $_.CommandLine -like "*dashboard*" }
    if ($nodeProcesses) {
        Write-Status "Dashboard processes: $($nodeProcesses.Count) running"
    } else {
        Write-Status "Dashboard processes: Not running" -Color "Yellow"
    }
    
    # Check port 3001
    $portCheck = netstat -ano | Select-String ":3001" | Select-String "LISTENING"
    if ($portCheck) {
        Write-Status "Port 3001: In use"
    } else {
        Write-Status "Port 3001: Available" -Color "Yellow"
    }
    
    # Test health endpoint
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:3001/health" -TimeoutSec 5
        Write-Status "Health check: $($health.status) (uptime: $([math]::Round($health.uptime, 1))s)"
    } catch {
        Write-Status "Health check: Failed" -Color "Red"
    }
}

# Main execution
Write-Status "Super Agent Dashboard - Production Deployment" -Color "Cyan"
Write-Status "Mode: $Mode" -Color "Yellow"

Test-Prerequisites

if (!$Force) {
    Show-Status
    $confirm = Read-Host "Continue with deployment? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Status "Deployment cancelled"
        exit 0
    }
}

Stop-ExistingProcesses

switch ($Mode.ToLower()) {
    "local" {
        Deploy-Local
    }
    "pm2" {
        Deploy-PM2
    }
    "docker" {
        Deploy-Docker
    }
    default {
        Write-Error "Invalid mode: $Mode. Use: local, pm2, or docker"
        exit 1
    }
}

Write-Status "Deployment completed!" -Color "Green"
Show-Status
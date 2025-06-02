# AI Agent App Builder Startup Script for Windows PowerShell

function Start-Application {
    param (
        [switch]$Development = $false
    )

    # Colors for console output
    $colors = @{
        Success = "Green"
        Info = "Cyan"
        Warning = "Yellow"
        Error = "Red"
    }

    # Print header
    Write-Host "`n==================================" -ForegroundColor $colors.Info
    Write-Host "   AI Agent App Builder Startup   " -ForegroundColor $colors.Info
    Write-Host "==================================`n" -ForegroundColor $colors.Info

    # Check for required tools
    Write-Host "Checking for required tools..." -ForegroundColor $colors.Info
    
    $nodePath = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodePath) {
        Write-Host "Node.js is not installed. Please install Node.js 16+ and try again." -ForegroundColor $colors.Error
        return
    }
    
    $pythonPath = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonPath) {
        Write-Host "Python is not installed. Please install Python 3.10+ and try again." -ForegroundColor $colors.Error
        return
    }

    # Display version info
    Write-Host "Node.js version: " -NoNewline
    node --version
    Write-Host "Python version: " -NoNewline
    python --version

    # Check for Ollama
    Write-Host "`nChecking for Ollama..." -ForegroundColor $colors.Info
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction SilentlyContinue
    
    if ($ollamaCheck) {
        Write-Host "✓ Ollama is running" -ForegroundColor $colors.Success
        Write-Host "Available models: "
        $ollamaCheck.models | ForEach-Object {
            Write-Host "  - $($_.name)" -ForegroundColor $colors.Info
        }
    } else {
        Write-Host "! Ollama is not running. Please start Ollama before using the application." -ForegroundColor $colors.Warning
        Write-Host "  The app will run in mock mode without real AI capabilities." -ForegroundColor $colors.Warning
    }

    # Set up environment based on mode
    if ($Development) {
        Write-Host "`nStarting in DEVELOPMENT mode..." -ForegroundColor $colors.Info
        
        # Update .env file to use mock data in development
        $envPath = ".\backend\.env"
        if (Test-Path $envPath) {
            $envContent = Get-Content $envPath -Raw
            $envContent = $envContent -replace "USE_MOCK_DATA=false", "USE_MOCK_DATA=true"
            $envContent | Set-Content $envPath
            Write-Host "✓ Updated .env file to use mock data" -ForegroundColor $colors.Success
        }

        # Start backend (first install dependencies if needed)
        Write-Host "Installing backend dependencies..." -ForegroundColor $colors.Info
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd backend && pip install -r requirements.txt" -Wait -NoNewWindow
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd backend && python run.py" -NoNewWindow
        Write-Host "✓ Started backend server on http://localhost:8000" -ForegroundColor $colors.Success
        
        # Start frontend (first install dependencies)
        Write-Host "Installing frontend dependencies..." -ForegroundColor $colors.Info
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd frontend && npm install" -Wait -NoNewWindow
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd frontend && npm start" -NoNewWindow
        Write-Host "✓ Started frontend server on http://localhost:3000" -ForegroundColor $colors.Success
        
        # Open browser
        Start-Process "http://localhost:3000"
        
    } else {
        # Production mode uses Docker Compose
        Write-Host "`nStarting in PRODUCTION mode with Docker..." -ForegroundColor $colors.Info
        
        # Check for Docker
        $dockerPath = Get-Command docker -ErrorAction SilentlyContinue
        if (-not $dockerPath) {
            Write-Host "Docker is not installed. Please install Docker and try again." -ForegroundColor $colors.Error
            return
        }
        
        # Build and start containers
        docker-compose up --build -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Application is running at http://localhost:3000" -ForegroundColor $colors.Success
            Start-Process "http://localhost:3000"
        } else {
            Write-Host "! Error starting Docker containers. Check logs for details." -ForegroundColor $colors.Error
        }
    }
    
    Write-Host "`nApplication is ready. Press Ctrl+C to stop the servers.`n" -ForegroundColor $colors.Info
}

# Parse command line arguments
param (
    [switch]$dev = $false
)

# Start the application
Start-Application -Development:$dev

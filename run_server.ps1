# Django Car Management API - Server Startup Script
# This script helps you easily start the Django development server for network access

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Django Car Management API Server" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get the server's local IP address
Write-Host "Finding your server's IP address..." -ForegroundColor Yellow
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -eq "Dhcp" -or $_.PrefixOrigin -eq "Manual" } | Select-Object -First 1).IPAddress

if ($ipAddress) {
    Write-Host "Server IP Address: $ipAddress" -ForegroundColor Green
} else {
    Write-Host "Could not detect IP address automatically." -ForegroundColor Red
    Write-Host "Please run 'ipconfig' to find your IP address manually." -ForegroundColor Yellow
    $ipAddress = "YOUR_SERVER_IP"
}

Write-Host ""
Write-Host "Setting up environment..." -ForegroundColor Yellow

# Set environment variables
$env:ALLOWED_HOSTS = "localhost,127.0.0.1,0.0.0.0,$ipAddress"
$env:DEBUG = "True"  # Set to False for production
$env:CORS_ALLOW_ALL = "True"  # Allow CORS from all origins

Write-Host "Environment configured:" -ForegroundColor Green
Write-Host "  - ALLOWED_HOSTS: $env:ALLOWED_HOSTS" -ForegroundColor White
Write-Host "  - DEBUG: $env:DEBUG" -ForegroundColor White
Write-Host "  - CORS_ALLOW_ALL: $env:CORS_ALLOW_ALL" -ForegroundColor White
Write-Host ""

Write-Host "Starting Django development server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Access your API from:" -ForegroundColor Cyan
Write-Host "  - Local: http://localhost:8000/api/" -ForegroundColor White
Write-Host "  - Network: http://${ipAddress}:8000/api/" -ForegroundColor White
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Start the Django server
python manage.py runserver 0.0.0.0:8000

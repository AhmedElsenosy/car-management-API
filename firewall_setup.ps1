# Django Car Management API - Windows Firewall Setup Script
# This script creates a firewall rule to allow incoming connections on port 8000
# REQUIRES ADMINISTRATOR PRIVILEGES

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Windows Firewall Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor White
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host "Checking for existing firewall rule..." -ForegroundColor Yellow

# Check if rule already exists
$existingRule = Get-NetFirewallRule -DisplayName "Django Car Management API" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "Firewall rule already exists. Removing old rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "Django Car Management API"
    Write-Host "Old rule removed." -ForegroundColor Green
}

Write-Host "Creating new firewall rule..." -ForegroundColor Yellow

try {
    # Create new firewall rule
    New-NetFirewallRule `
        -DisplayName "Django Car Management API" `
        -Description "Allow incoming connections to Django Car Management API on port 8000" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 8000 `
        -Action Allow `
        -Profile Domain,Private,Public `
        -Enabled True

    Write-Host ""
    Write-Host "SUCCESS! Firewall rule created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Configuration Details:" -ForegroundColor Cyan
    Write-Host "  - Rule Name: Django Car Management API" -ForegroundColor White
    Write-Host "  - Port: 8000 (TCP)" -ForegroundColor White
    Write-Host "  - Direction: Inbound" -ForegroundColor White
    Write-Host "  - Action: Allow" -ForegroundColor White
    Write-Host "  - Profiles: Domain, Private, Public" -ForegroundColor White
    Write-Host ""
    Write-Host "Your Django server can now accept connections from other devices!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create firewall rule!" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "You can create the rule manually:" -ForegroundColor Yellow
    Write-Host "  1. Open 'Windows Defender Firewall with Advanced Security' (wf.msc)" -ForegroundColor White
    Write-Host "  2. Click 'Inbound Rules' > 'New Rule'" -ForegroundColor White
    Write-Host "  3. Select 'Port' > TCP port 8000" -ForegroundColor White
    Write-Host "  4. Select 'Allow the connection'" -ForegroundColor White
    Write-Host "  5. Check all profiles and name it 'Django Car Management API'" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "Press any key to exit..."
pause

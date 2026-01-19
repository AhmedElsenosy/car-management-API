# Django Car Management API - Windows Network Deployment Guide

## Overview
This guide will help you deploy your Django Car Management API on a Windows server so it can be accessed from other devices on your local network.

## Prerequisites
- Windows Server with Python installed
- Project already set up in `c:\Users\asome\Desktop\car\venv\src`
- Virtual environment activated
- Remote Desktop access to the server

---

## Quick Start

### Step 1: Get Your Server's IP Address

1. Connect to your Windows server via Remote Desktop
2. Open PowerShell or Command Prompt
3. Run the following command:

```powershell
ipconfig
```

4. Look for **IPv4 Address** under your active network adapter (usually "Ethernet" or "Wi-Fi")
5. Note this IP address (e.g., `192.168.1.100` or `10.0.0.50`)

---

### Step 2: Configure Environment (Optional but Recommended)

Create a `.env` file in your project directory:

```powershell
cd c:\Users\asome\Desktop\car\venv\src
Copy-Item .env.example .env
notepad .env
```

Update the `.env` file with your settings:
- Set `DEBUG=False` for better security
- Add your server IP to `ALLOWED_HOSTS`
- Set `CORS_ALLOW_ALL=True` if you need to access from browsers on other devices

**Note**: The current settings work without a `.env` file, but using one is more secure.

---

### Step 3: Run the Server

**Option A: Use the PowerShell Script (Easiest)**

```powershell
cd c:\Users\asome\Desktop\car\venv\src
.\run_server.ps1
```

The script will:
- Display your server's IP address
- Set up environment variables
- Start the server on port 8000
- Show you the access URL

**Option B: Manual Start**

```powershell
cd c:\Users\asome\Desktop\car\venv\src

# Activate virtual environment
..\Scripts\Activate.ps1

# Set environment variables (optional)
$env:ALLOWED_HOSTS="localhost,127.0.0.1,YOUR_SERVER_IP"

# Run the server
python manage.py runserver 0.0.0.0:8000
```

Replace `YOUR_SERVER_IP` with the IP from Step 1.

**Expected Output:**
```
Starting development server at http://0.0.0.0:8000/
Quit the server with CTRL-BREAK.
```

---

### Step 4: Configure Windows Firewall

The firewall must allow incoming connections on port 8000.

**Option A: Use PowerShell Script (Requires Administrator)**

Right-click PowerShell and select "Run as Administrator", then:

```powershell
cd c:\Users\asome\Desktop\car\venv\src
.\firewall_setup.ps1
```

**Option B: Manually Configure Firewall**

1. Open **Windows Defender Firewall with Advanced Security**
   - Press `Win+R`, type `wf.msc`, press Enter
   
2. Click **Inbound Rules** → **New Rule**

3. Choose **Port** → Click Next

4. Select **TCP** and enter port **8000** → Click Next

5. Select **Allow the connection** → Click Next

6. Check all profiles (Domain, Private, Public) → Click Next

7. Name it "Django Car Management API" → Click Finish

**Verify Firewall Rule:**
```powershell
netsh advfirewall firewall show rule name="Django Car Management API"
```

---

### Step 5: Test from Server

While still connected via Remote Desktop, test the API locally:

```powershell
# Test localhost
curl http://localhost:8000/api/cars/

# Test network interface
curl http://YOUR_SERVER_IP:8000/api/cars/
```

Both commands should return JSON data with car information.

---

### Step 6: Test from Another Device

From any device on the **same local network** (laptop, phone, tablet):

**Via Browser:**
1. Open your browser
2. Navigate to: `http://YOUR_SERVER_IP:8000/api/cars/`
3. You should see JSON data

**Via Command Line (if available):**
```bash
curl http://YOUR_SERVER_IP:8000/api/cars/
```

**Example URLs:**
- http://192.168.1.100:8000/api/cars/
- http://192.168.1.100:8000/admin/
- http://192.168.1.100:8000/api/weekly/detail/?car_id=1&date=2025-10-02

---

## Troubleshooting

### Problem: Connection Refused or Timeout

**Causes:**
- Firewall not configured → Go back to Step 4
- Devices on different networks → Ensure both on same WiFi/LAN
- Server not running → Check Step 3

**Solution:**
```powershell
# Check if firewall rule exists
netsh advfirewall firewall show rule name="Django Car Management API"

# Check if port is listening
netstat -an | findstr :8000
```

---

### Problem: Bad Request (400) Error

**Cause:** Your server IP is not in `ALLOWED_HOSTS`

**Solution:**
```powershell
# Add your IP to environment variable before running server
$env:ALLOWED_HOSTS="localhost,127.0.0.1,YOUR_ACTUAL_IP"
python manage.py runserver 0.0.0.0:8000
```

Or update the `.env` file with your IP address.

---

### Problem: CORS Error in Browser

**Cause:** Browser security blocking cross-origin requests

**Solution:**
```powershell
# Set CORS to allow all origins (for testing)
$env:CORS_ALLOW_ALL="True"
python manage.py runserver 0.0.0.0:8000
```

Or add to `.env` file: `CORS_ALLOW_ALL=True`

**Warning:** Only use `CORS_ALLOW_ALL=True` in trusted network environments.

---

### Problem: Server Stops When Remote Desktop Disconnects

**Solution:** Run server as a Windows Service or use a process manager like NSSM (Non-Sucking Service Manager).

For development, keep Remote Desktop connected while server is running.

---

## Important Notes

### Security Considerations

> [!WARNING]
> **When exposing your API to the network:**
> - Change `SECRET_KEY` in production (don't use the default)
> - Set `DEBUG=False` to hide sensitive error information
> - Consider adding API authentication
> - Only allow access from trusted devices/networks
> - Keep Windows Firewall enabled

### Port Configuration

- Default port: **8000**
- To use a different port: `python manage.py runserver 0.0.0.0:YOUR_PORT`
- Remember to update firewall rules for the new port

### Accessing via Domain Name (Optional)

If you have a local DNS or hosts file:
1. Map your server IP to a domain name
2. Add the domain to `ALLOWED_HOSTS` in `.env`
3. Access via `http://myserver.local:8000/api/cars/`

---

## Production Deployment (Future)

For a production environment, consider:
- Using **Gunicorn** or **Waitress** as WSGI server
- Setting up **Nginx** as reverse proxy
- Using **PostgreSQL** instead of SQLite
- Enabling **HTTPS** with SSL certificates
- Running as a **Windows Service** for auto-start
- Setting up automated backups

---

## Quick Reference Commands

```powershell
# Get server IP
ipconfig

# Run server (simple)
python manage.py runserver 0.0.0.0:8000

# Run server with environment variables
$env:ALLOWED_HOSTS="localhost,127.0.0.1,192.168.1.100"
$env:DEBUG="False"
python manage.py runserver 0.0.0.0:8000

# Check firewall rule
netsh advfirewall firewall show rule name="Django Car Management API"

# Check if port is listening
netstat -an | findstr :8000

# Test API locally
curl http://localhost:8000/api/cars/
```

---

## Need Help?

Common issues and solutions are in the Troubleshooting section above. If you encounter other problems, check:
1. Server is running (see Terminal output)
2. Firewall rule is active
3. Devices are on the same network
4. IP address is correct (use `ipconfig` to verify)

---

**That's it! Your Django Car Management API is now accessible on your local network! 🚗**

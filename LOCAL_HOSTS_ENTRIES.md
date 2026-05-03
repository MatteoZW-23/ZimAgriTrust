# Local Hosts File Entries for Subdomain Testing

## Windows Hosts File Location
```
C:\Windows\System32\drivers\etc\hosts
```

## Required Entries
Add these lines to your hosts file to enable subdomain routing locally:

```
127.0.0.1 admin.localhost
127.0.0.1 agent.localhost
127.0.0.1 agric.localhost
```

## How to Edit (Windows)

### Method 1: Using Notepad as Administrator
1. Open Notepad as Administrator (Right-click → Run as Administrator)
2. File → Open → Navigate to `C:\Windows\System32\drivers\etc\hosts`
3. Add the entries at the end of the file
4. Save the file

### Method 2: Using PowerShell as Administrator
```powershell
# Open PowerShell as Administrator
Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "`r`n127.0.0.1 admin.localhost"
Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "127.0.0.1 agent.localhost"
Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value "127.0.0.1 agric.localhost"
```

### Method 3: Using Command Prompt as Administrator
```cmd
# Open Command Prompt as Administrator
echo 127.0.0.1 admin.localhost >> C:\Windows\System32\drivers\etc\hosts
echo 127.0.0.1 agent.localhost >> C:\Windows\System32\drivers\etc\hosts
echo 127.0.0.1 agric.localhost >> C:\Windows\System32\drivers\etc\hosts
```

## Verification

After adding the entries, verify they work:

```powershell
# Test admin subdomain
Test-NetConnection -ComputerName admin.localhost -Port 80

# Test agent subdomain
Test-NetConnection -ComputerName agent.localhost -Port 80

# Or use ping
ping admin.localhost
ping agent.localhost
```

## Testing Subdomain Routing

Once hosts file is updated, test the routing:

```bash
# Start services with nginx
docker-compose -f docker-compose.subdomains.yml up -d

# Test admin subdomain
curl -H "Host: admin.localhost" http://localhost/

# Test agent subdomain
curl -H "Host: agent.localhost" http://localhost/

# Test main domain
curl http://localhost/

# Test dashboard route
curl http://localhost/dashboard
```

## Removing Entries (Cleanup)

If you need to remove the entries later:

1. Open hosts file in Notepad as Administrator
2. Remove the lines you added
3. Save the file
4. Flush DNS cache: `ipconfig /flushdns`

## Notes

- Changes to hosts file take effect immediately
- No need to restart computer
- Browser may cache DNS, so try clearing browser cache or using incognito mode
- These entries only work on the local machine

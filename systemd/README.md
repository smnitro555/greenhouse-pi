# Systemd Service Installation

This directory contains systemd service files for running the greenhouse manager and webserver as services on the Raspberry Pi.

## Installation

### 1. Copy service files to systemd directory

```bash
sudo cp systemd/greenhouse-manager.service /etc/systemd/system/
sudo cp systemd/greenhouse-webserver.service /etc/systemd/system/
```

### 2. Update service files (if needed)

Edit the service files to match your installation path:

```bash
sudo nano /etc/systemd/system/greenhouse-manager.service
sudo nano /etc/systemd/system/greenhouse-webserver.service
```

Update these fields if your paths differ:
- `User` and `Group` (default: pi)
- `WorkingDirectory` (default: /home/pi/greenhouse-pi)
- Environment variables for authentication

### 3. Reload systemd daemon

```bash
sudo systemctl daemon-reload
```

### 4. Enable services to start on boot

```bash
sudo systemctl enable greenhouse-manager.service
sudo systemctl enable greenhouse-webserver.service
```

### 5. Start the services

```bash
sudo systemctl start greenhouse-manager.service
sudo systemctl start greenhouse-webserver.service
```

## Service Management

### Check service status

```bash
sudo systemctl status greenhouse-manager.service
sudo systemctl status greenhouse-webserver.service
```

### View service logs

```bash
# Real-time logs
sudo journalctl -u greenhouse-manager.service -f
sudo journalctl -u greenhouse-webserver.service -f

# Last 100 lines
sudo journalctl -u greenhouse-manager.service -n 100
sudo journalctl -u greenhouse-webserver.service -n 100

# Logs since boot
sudo journalctl -u greenhouse-manager.service -b
sudo journalctl -u greenhouse-webserver.service -b
```

### Restart services

```bash
sudo systemctl restart greenhouse-manager.service
sudo systemctl restart greenhouse-webserver.service
```

### Stop services

```bash
sudo systemctl stop greenhouse-manager.service
sudo systemctl stop greenhouse-webserver.service
```

### Disable services (prevent auto-start on boot)

```bash
sudo systemctl disable greenhouse-manager.service
sudo systemctl disable greenhouse-webserver.service
```

## Service Features

Both services are configured with:

- **Automatic restart**: Services will restart if they crash
- **RestartSec=10**: Wait 10 seconds before restarting
- **Resource limits**:
  - Memory limit: 512MB
  - CPU quota: 50%
- **Logging**: Output is sent to systemd journal
- **After=network.target**: Services start after network is available

## Security Notes

1. **Change default credentials**: Update the `GREENHOUSE_USERNAME` and `GREENHOUSE_PASSWORD` environment variables in the webserver service file

2. **File permissions**: Ensure service files have correct permissions:
   ```bash
   sudo chmod 644 /etc/systemd/system/greenhouse-*.service
   ```

3. **Private configuration**: Store sensitive credentials in `/home/pi/greenhouse-pi/config/private-data/` instead of environment variables for better security

## Troubleshooting

### Service fails to start

1. Check the logs:
   ```bash
   sudo journalctl -u greenhouse-manager.service -n 50
   ```

2. Verify Python path:
   ```bash
   ls -la /home/pi/greenhouse-pi/.venv/bin/python
   ```

3. Test manually:
   ```bash
   cd /home/pi/greenhouse-pi
   .venv/bin/python -m greenhouse_manager.greenhouse_manager
   ```

### Permission errors

Ensure the `pi` user has access to GPIO and I2C:

```bash
sudo usermod -a -G gpio,i2c pi
```

### Dependencies not found

Make sure the virtual environment is properly set up:

```bash
cd /home/pi/greenhouse-pi
python build.py build-env
```

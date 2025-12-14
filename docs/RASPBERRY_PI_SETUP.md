# Raspberry Pi 4 Setup Guide

Complete guide for setting up your Raspberry Pi 4, including hardware connections, display access, and initial configuration.

## 📋 What You'll Need

### Hardware Requirements
- **Raspberry Pi 4** (2GB, 4GB, or 8GB RAM)
- **Power Supply:** USB-C 5V 3A (official Raspberry Pi power supply recommended)
- **MicroSD Card:** 16GB minimum, 32GB+ recommended (Class 10 or UHS-I)
- **MicroSD Card Reader** (for flashing OS from your computer)

### Optional Hardware
- **Monitor:** HDMI display with micro-HDMI cable
- **Keyboard & Mouse:** USB or wireless
- **Ethernet Cable:** For wired network connection
- **Case:** For protection and cooling
- **Heatsinks/Fan:** For better cooling (recommended for heavy workloads)

---

## 🔌 Hardware Connection Guide

### Step 1: Prepare the MicroSD Card

#### Option A: Using Raspberry Pi Imager (Recommended)

1. **Download Raspberry Pi Imager:**
   - Windows/Mac/Linux: https://www.raspberrypi.com/software/

2. **Flash the OS:**
   ```
   1. Insert microSD card into your computer
   2. Open Raspberry Pi Imager
   3. Click "Choose Device" → Select "Raspberry Pi 4"
   4. Click "Choose OS" → Select "Raspberry Pi OS (64-bit)" recommended
   5. Click "Choose Storage" → Select your microSD card
   6. Click "Next"
   ```

3. **Configure Settings (Important for Headless Setup):**
   ```
   Click "Edit Settings" when prompted:
   
   GENERAL TAB:
   ✓ Set hostname: raspberrypi (or custom name)
   ✓ Set username and password
     Username: pi
     Password: [your secure password]
   ✓ Configure wireless LAN
     SSID: [Your WiFi Name]
     Password: [Your WiFi Password]
     Country: [Your Country Code, e.g., US, UK, etc.]
   ✓ Set locale settings
     Timezone: [Your timezone]
     Keyboard layout: [Your layout]
   
   SERVICES TAB:
   ✓ Enable SSH
     ☑ Use password authentication
   ```

4. **Write to SD Card:**
   ```
   1. Click "Save"
   2. Click "Yes" to apply OS customization settings
   3. Click "Yes" to confirm erase
   4. Wait for writing and verification to complete
   5. Eject the microSD card safely
   ```

#### Option B: Manual SSH Enable (If you already flashed without settings)

1. After flashing, re-insert the microSD card
2. Open the `boot` partition (should auto-mount)
3. Create an empty file named `ssh` (no extension) in the boot partition
4. For WiFi, create `wpa_supplicant.conf` with:
   ```
   country=US
   ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
   update_config=1

   network={
       ssid="YOUR_WIFI_SSID"
       psk="YOUR_WIFI_PASSWORD"
       key_mgmt=WPA-PSK
   }
   ```

---

### Step 2: Physical Connections

#### Connection Diagram
```
Raspberry Pi 4 Model B
═══════════════════════════════════════════
                  [Ethernet] [USB 3.0 x2]
    ┌──────────────────────────────────┐
    │                                  │ [USB 2.0 x2]
    │   [CPU]  [RAM]                   │
    │                                  │ [Audio/Video]
    │   [Storage: microSD]             │
    │                                  │ [micro-HDMI 0]
    │   [GPIO 40-pin]                  │ [micro-HDMI 1]
    │                                  │
    │                                  │ [USB-C Power]
    └──────────────────────────────────┘

Ports Overview:
┌────────────────┬──────────────────────────────┐
│ Port           │ Purpose                      │
├────────────────┼──────────────────────────────┤
│ USB-C          │ Power input (5V 3A min)      │
│ micro-HDMI 0   │ Primary display output       │
│ micro-HDMI 1   │ Secondary display (optional) │
│ USB 3.0 (blue) │ Fast peripherals, storage    │
│ USB 2.0        │ Keyboard, mouse              │
│ Ethernet (RJ45)│ Wired network connection     │
│ 3.5mm Jack     │ Audio/composite video out    │
│ GPIO Header    │ Electronics/sensors          │
│ microSD Slot   │ Operating system storage     │
└────────────────┴──────────────────────────────┘
```

#### Connection Steps

**For Headless Setup (No Monitor - SSH Only):**
```
1. ☐ Insert flashed microSD card into Pi (bottom slot)
2. ☐ Connect Ethernet cable (optional, if not using WiFi)
3. ☐ Connect USB-C power supply LAST
4. ☐ Wait 60-90 seconds for first boot
5. ☐ Proceed to "Accessing Display" → SSH section
```

**For Desktop Setup (With Monitor):**
```
1. ☐ Insert flashed microSD card into Pi
2. ☐ Connect micro-HDMI to HDMI cable to HDMI 0 port
3. ☐ Connect HDMI cable to monitor
4. ☐ Connect USB keyboard and mouse
5. ☐ Connect Ethernet cable (optional)
6. ☐ Turn on monitor
7. ☐ Connect USB-C power supply LAST
8. ☐ Watch monitor for boot screen (rainbow square → boot text)
```

#### Power Connection
```
⚠️ IMPORTANT: Connect power LAST after all other connections!

Recommended Power Supply Specifications:
- Voltage: 5V DC
- Current: 3A minimum (15W)
- Connector: USB-C
- Use OFFICIAL Raspberry Pi power supply or quality alternative

Signs of insufficient power:
- Lightning bolt icon on screen
- Random reboots
- USB devices not working
- Sluggish performance
```

---

## 🖥️ Accessing the Display

You have **three main options** to access your Raspberry Pi:

### Option 1: Direct HDMI Display (Easiest for Beginners)

**Requirements:**
- Monitor with HDMI input
- Micro-HDMI to HDMI cable/adapter
- USB keyboard and mouse

**Steps:**
1. Connect monitor via micro-HDMI port (labeled "HDMI 0")
2. Power on the Raspberry Pi
3. You'll see the desktop environment boot directly
4. Complete the welcome wizard on first boot

**Advantages:**
- ✅ Easiest for beginners
- ✅ Full desktop experience
- ✅ No network configuration needed

**Disadvantages:**
- ❌ Requires dedicated monitor, keyboard, mouse
- ❌ Less portable setup

---

### Option 2: SSH (Command Line Access - Headless)

**Requirements:**
- Raspberry Pi connected to same network as your computer
- SSH enabled (done in Imager settings)
- SSH client (built into Windows 10+, Mac, Linux)

#### Finding Your Raspberry Pi's IP Address

**Method A: Using Hostname (Easiest)**
```bash
# From your computer's terminal/PowerShell:
ping raspberrypi.local

# Should respond with IP address like:
# Reply from 192.168.1.100: bytes=32 time=2ms TTL=64
```

**Method B: Check Router DHCP**
```
1. Login to your router admin panel (usually 192.168.1.1)
2. Look for "Connected Devices" or "DHCP Clients"
3. Find device named "raspberrypi" or with MAC starting with B8:27:EB, DC:A6:32, or E4:5F:01
4. Note the IP address
```

**Method C: Network Scanner**
```bash
# Windows (install Advanced IP Scanner)
# Download from: https://www.advanced-ip-scanner.com/

# Mac/Linux (install nmap)
sudo nmap -sn 192.168.1.0/24

# Look for "Raspberry Pi Foundation" in manufacturer
```

#### Connecting via SSH

**From Windows PowerShell / Mac Terminal / Linux Terminal:**
```bash
# Basic connection (default password authentication):
ssh pi@raspberrypi.local

# Or using IP address:
ssh pi@192.168.1.100

# First time connection:
# Answer "yes" to fingerprint prompt
# Enter password you set during imaging

# Successful connection shows:
# pi@raspberrypi:~ $
```

**Common SSH Commands:**
```bash
# Update system:
sudo apt update && sudo apt upgrade -y

# Check system info:
uname -a

# Check temperature:
vcgencmd measure_temp

# Check memory:
free -h

# Check disk space:
df -h

# Shutdown:
sudo shutdown -h now

# Reboot:
sudo reboot

# Exit SSH session:
exit
```

**Advantages:**
- ✅ No monitor needed
- ✅ Access from anywhere on network
- ✅ Lightweight and fast
- ✅ Great for servers/headless projects

**Disadvantages:**
- ❌ Command line only (no GUI)
- ❌ Requires familiarity with Linux commands

---

### Option 3: VNC (Remote Desktop - GUI)

VNC provides full graphical desktop access over the network.

#### Enable VNC on Raspberry Pi

**Via SSH:**
```bash
# Connect via SSH first
ssh pi@raspberrypi.local

# Enable VNC using raspi-config:
sudo raspi-config

# Navigate:
# 3. Interface Options
#   → I3 VNC
#     → Yes (Enable VNC)
#   → Finish
#   → Reboot? Yes

# Alternative: Enable via command:
sudo systemctl enable vncserver-x11-serviced
sudo systemctl start vncserver-x11-serviced
```

**Via Desktop (if using HDMI):**
```
1. Click Raspberry Pi menu (top left)
2. Preferences → Raspberry Pi Configuration
3. Click "Interfaces" tab
4. Enable VNC → OK
```

#### Setting VNC Resolution (Important for Headless)

If running headless (no monitor), set a fixed resolution:
```bash
sudo raspi-config

# Navigate:
# 2. Display Options
#   → D5 VNC Resolution
#     → Select: 1920x1080 (or your preference)
#   → OK → Finish
```

#### Connect from Your Computer

**Step 1: Install VNC Viewer**
- Download from: https://www.realvnc.com/en/connect/download/viewer/
- Available for Windows, Mac, Linux, iOS, Android

**Step 2: Connect**
```
1. Open VNC Viewer
2. Enter address: raspberrypi.local (or IP like 192.168.1.100)
3. Click Connect
4. Enter credentials:
   Username: pi
   Password: [your password]
5. Click OK
6. You'll see the full Raspberry Pi desktop!
```

**Advantages:**
- ✅ Full GUI desktop remotely
- ✅ No monitor needed
- ✅ Access from any device (phone, tablet, PC)
- ✅ Best of both worlds

**Disadvantages:**
- ❌ Requires network connection
- ❌ Slight performance overhead
- ❌ Limited by network bandwidth

---

## 📋 Quick Comparison Table

| Method | Use Case | Difficulty | Hardware Needed | Best For |
|--------|----------|------------|-----------------|----------|
| **HDMI** | Desktop use | ⭐ Easy | Monitor, keyboard, mouse | Beginners, desktop projects |
| **SSH** | Headless server | ⭐⭐ Medium | None (network only) | Servers, IoT, remote management |
| **VNC** | Remote desktop | ⭐⭐ Medium | None (network only) | Remote GUI access, development |

---

## 🚀 Initial Setup Checklist

After first boot, complete these essential setup steps:

### 1. System Update (Critical)
```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

### 2. Change Default Password (Security)
```bash
passwd
# Enter current password
# Enter new password twice
```

### 3. Configure System
```bash
sudo raspi-config

# Recommended configurations:
# 1. System Options → S4 Hostname → Set unique name
# 2. System Options → S5 Boot / Auto Login → Console (for servers)
# 3. Performance Options → P2 GPU Memory → 16 (for headless)
# 4. Localisation Options → Set timezone, locale, keyboard
# 5. Advanced Options → A1 Expand Filesystem
```

### 4. Install Essential Packages
```bash
# Version control:
sudo apt install git -y

# Python and pip (usually pre-installed):
sudo apt install python3 python3-pip -y

# Build tools:
sudo apt install build-essential -y

# Network tools:
sudo apt install net-tools nmap -y
```

### 5. Enable Helpful Services
```bash
# Enable SSH (if not already):
sudo systemctl enable ssh
sudo systemctl start ssh

# Enable VNC (for GUI access):
sudo systemctl enable vncserver-x11-serviced
sudo systemctl start vncserver-x11-serviced
```

---

## 🔧 Troubleshooting

### Can't Find Raspberry Pi on Network

**Problem:** `ping raspberrypi.local` fails or SSH connection refused

**Solutions:**
```
☐ Wait 2-3 minutes after power on (first boot is slow)
☐ Check WiFi credentials in wpa_supplicant.conf
☐ Verify 2.4GHz WiFi (Pi 4 supports 5GHz, but check router)
☐ Connect Ethernet cable for guaranteed connection
☐ Check router's connected devices list
☐ Try IP address directly instead of .local hostname
☐ Ensure SSH file was created in boot partition
☐ Re-flash SD card with correct settings
```

### No Display via HDMI

**Problem:** Monitor shows "No Signal" when Pi is powered on

**Solutions:**
```
☐ Ensure micro-HDMI cable in HDMI 0 port (closest to USB-C)
☐ Connect cable BEFORE powering on Pi
☐ Check monitor is on correct input source
☐ Try different HDMI cable
☐ Test with different monitor/TV
☐ Check for rainbow square on boot (confirms video output)
☐ Add to config.txt: hdmi_safe=1
  1. Remove SD card
  2. Open boot partition on computer
  3. Edit config.txt
  4. Add: hdmi_safe=1
  5. Save and re-insert into Pi
```

### Low Power / Lightning Bolt Warning

**Problem:** Lightning bolt icon appears on screen or random instability

**Solutions:**
```
☐ Use official Raspberry Pi PSU (5V 3A USB-C)
☐ Replace power cable (check for damage)
☐ Reduce USB device load
☐ Use powered USB hub for peripherals
☐ Check power outlet with another device
☐ Measure voltage at test points (TP1/TP2: should be ~5V)
```

### SSH Connection Refused

**Problem:** `ssh: connect to host raspberrypi.local port 22: Connection refused`

**Solutions:**
```
☐ Verify SSH is enabled (ssh file in boot partition)
☐ Check Pi is actually booted (green LED activity)
☐ Try IP address: ssh pi@192.168.1.100
☐ Check firewall on your computer
☐ Regenerate SSH keys if previously connected:
  ssh-keygen -R raspberrypi.local
☐ Connect via HDMI and enable SSH:
  sudo systemctl enable ssh
  sudo systemctl start ssh
```

### VNC Grey Screen / Cannot Currently Show Desktop

**Problem:** VNC connects but shows grey screen or error

**Solutions:**
```bash
# Set a fixed resolution:
sudo raspi-config
# → Display Options → VNC Resolution → 1920x1080

# Or edit config.txt:
sudo nano /boot/config.txt

# Add these lines:
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=82

# Save (Ctrl+O, Enter, Ctrl+X) and reboot:
sudo reboot
```

### SD Card Not Recognized

**Problem:** Pi doesn't boot, no activity LED

**Solutions:**
```
☐ Re-flash SD card (may be corrupted)
☐ Try different SD card (ensure SDHC/SDXC Class 10+)
☐ Format as FAT32 before flashing
☐ Check SD card is fully inserted (click sound)
☐ Test SD card on computer to verify files present
☐ Clean SD card contacts with isopropyl alcohol
```

### Overheating / Thermal Throttling

**Problem:** `vcgencmd get_throttled` shows throttling or temperature >80°C

**Solutions:**
```
☐ Add heatsinks to CPU and RAM
☐ Install cooling fan (5V from GPIO pins 4 & 6)
☐ Improve airflow around Pi
☐ Reduce CPU load / optimize code
☐ Lower overclock settings if modified
☐ Use case with built-in fan
☐ Check temperature:
  vcgencmd measure_temp
```

---

## 📝 Useful Commands Reference

### System Information
```bash
# Raspberry Pi model:
cat /proc/device-tree/model

# OS version:
cat /etc/os-release

# CPU info:
lscpu

# Memory usage:
free -h

# Disk usage:
df -h

# Temperature:
vcgencmd measure_temp

# Voltage (under-voltage detection):
vcgencmd get_throttled
# 0x0 = OK, anything else = throttling occurred
```

### Network Commands
```bash
# Show IP address:
hostname -I

# Network interfaces:
ifconfig
# or
ip addr show

# WiFi status:
iwconfig

# Test internet:
ping google.com

# Show active connections:
netstat -tuln
```

### File Transfer

**From Computer to Pi:**
```bash
# SCP (Secure Copy):
scp /path/to/local/file.txt pi@raspberrypi.local:/home/pi/

# SCP entire folder:
scp -r /path/to/folder pi@raspberrypi.local:/home/pi/

# Example for your project:
scp mqtt_ids_model.joblib pi@raspberrypi.local:~/raspberry-pi-gateway/
```

**From Pi to Computer:**
```bash
scp pi@raspberrypi.local:/home/pi/file.txt /path/to/local/destination/
```

---

## 🎯 Recommended Setup for Your IoT Project

Based on your MQTT encryption framework project, here's the optimal setup:

### 1. **Initial Access Method:**
   - Use **SSH** for lightweight, efficient setup
   - Enable **VNC** as backup for troubleshooting

### 2. **Network Configuration:**
   - Use **Ethernet** for stable MQTT broker connection
   - WiFi as fallback if Ethernet not available

### 3. **Install MQTT Broker:**
   ```bash
   ssh pi@raspberrypi.local
   
   # Install Mosquitto:
   sudo apt update
   sudo apt install mosquitto mosquitto-clients -y
   
   # Enable Mosquitto:
   sudo systemctl enable mosquitto
   sudo systemctl start mosquitto
   
   # Test:
   mosquitto -v
   ```

### 4. **Transfer Your Gateway Files:**
   ```bash
   # From your computer (in project directory):
   cd "c:\Users\Farhan\Desktop\IOT-IS Project\Mqtt_Encryption_Framework"
   
   # If using ml-training folder:
   cd ml-training
   scp mqtt_ids_model.joblib pi@raspberrypi.local:~/raspberry-pi-gateway/
   
   # Copy entire gateway folder:
   scp -r raspberry-pi-gateway pi@raspberrypi.local:~/
   ```

### 5. **Find Pi IP for Dashboard Configuration:**
   ```bash
   ssh pi@raspberrypi.local
   hostname -I
   # Note the IP (e.g., 192.168.1.15)
   # Use this in your ESP32 and dashboard configs
   ```

---

## 🔗 Helpful Resources

- **Official Documentation:** https://www.raspberrypi.com/documentation/
- **Forums:** https://forums.raspberrypi.com/
- **Raspberry Pi OS Guide:** https://www.raspberrypi.com/documentation/computers/getting-started.html
- **SSH Documentation:** https://www.raspberrypi.com/documentation/computers/remote-access.html#ssh
- **GPIO Pinout:** https://pinout.xyz/

---

## 📌 Quick Start Summary

**For Headless Setup (Recommended for Servers):**
1. Flash SD card with Raspberry Pi Imager
2. Enable SSH and configure WiFi in settings
3. Insert SD card and power on Pi
4. SSH from computer: `ssh pi@raspberrypi.local`
5. Update system: `sudo apt update && sudo apt upgrade -y`
6. Install your project requirements

**For Desktop Setup:**
1. Flash SD card
2. Connect HDMI, keyboard, mouse
3. Power on and follow setup wizard
4. Install your applications

**Getting Your Raspberry Pi IP:**
```bash
# Method 1: Ping hostname
ping raspberrypi.local

# Method 2: SSH and check
ssh pi@raspberrypi.local
hostname -I
```

🎉 **You're ready to start developing on your Raspberry Pi 4!**

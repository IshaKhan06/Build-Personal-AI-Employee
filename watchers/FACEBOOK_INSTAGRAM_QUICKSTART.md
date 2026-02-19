# Facebook/Instagram Watcher - Quick Start

## ✓ Fixed: Browser Close Behavior (Windows)

**Latest Fix:** Added Windows-specific window detection using PowerShell to detect when Chrome window is closed.

**How it works now:** When you close the browser window on Windows, the watcher detects it within 2 seconds using multiple methods:
1. Checks if browser pages array is empty
2. Checks if page.is_closed() returns true
3. Tries to evaluate JavaScript on the page (fails if closed)
4. **Windows-specific:** Uses PowerShell to check if Chrome window handle exists

**PM2 Configuration:** Set to `restart_on_exit: false` so when you close the browser normally, PM2 will NOT restart the watcher.

---

## How to Stop the Watcher

### Method 1: Close Browser Window (Recommended)
Simply **close the browser window** (click X button) that opened for Facebook/Instagram. The watcher will:
1. Detect window closure within 2 seconds
2. Print: "✓ Browser window closed by user."
3. Clean up resources
4. Exit with code 0 (PM2 will NOT restart)

### Method 2: Press Ctrl+C
Press `Ctrl+C` in the terminal to stop the watcher.

### Method 3: PM2 Stop Command
```bash
pm2 stop facebook_instagram_watcher
pm2 stop instagram_watcher
```

---

## Running the Watchers

### With PM2 (Recommended)

```bash
# Start Facebook Watcher
pm2 start ecosystem.config.js --only facebook_instagram_watcher

# Start Instagram Watcher
pm2 start ecosystem.config.js --only instagram_watcher

# Check status
pm2 status

# View logs
pm2 logs facebook_instagram_watcher --lines 50

# Stop watchers (manual stop)
pm2 stop facebook_instagram_watcher
pm2 stop instagram_watcher

# Delete from PM2
pm2 delete facebook_instagram_watcher
pm2 delete instagram_watcher
```

### Direct Python Execution

```bash
# Facebook only
python watchers\facebook_instagram_watcher.py facebook

# Instagram only
python watchers\facebook_instagram_watcher.py instagram

# Both (sequential)
python watchers\facebook_instagram_watcher.py both
```

**To Stop:** Close the browser window or press `Ctrl+C`.

---

## Testing the Fix

1. **First, reload PM2 with new config:**
   ```bash
   pm2 delete facebook_instagram_watcher
   pm2 delete instagram_watcher
   pm2 start ecosystem.config.js --only facebook_instagram_watcher
   ```

2. **Wait for browser to open** and login (if needed)

3. **Close the browser window** by clicking the X button

4. **Wait 2-3 seconds** (detection happens within 2 seconds)

5. **Check status:**
   ```bash
   pm2 status
   ```
   
   You should see the watcher is **stopped** (not restarting).

6. **Check logs:**
   ```bash
   pm2 logs facebook_instagram_watcher --lines 20
   ```
   
   You should see:
   ```
   ✓ Browser window closed by user.
   Stopping watcher gracefully...
   ```

7. **To restart the watcher** (if you want to monitor again):
   ```bash
   pm2 restart facebook_instagram_watcher
   ```

8. **Alternative: Run without PM2 for testing:**
   ```bash
   # Run directly (easier to test)
   python watchers\facebook_instagram_watcher.py facebook
   
   # Close the browser window
   # Script should exit immediately and return to command prompt
   ```

---

## How It Works

The fix includes 4 detection methods:

1. **Page Array Check:** Every 2 seconds, checks if `browser.pages` is empty
2. **Page Closed Flag:** Checks if `page.is_closed()` returns true
3. **JavaScript Evaluation:** Tries to run `document.title` - fails if page is closed
4. **Windows Process Check:** Uses PowerShell to check if Chrome window handle exists:
   ```powershell
   Get-Process chrome | Where-Object {$_.MainWindowHandle -ne 0}
   ```

**Graceful Exit Process:**
- When any method detects window closure:
  - Prints confirmation message
  - Cleans up resources (Playwright, browser context)
  - Exits with code 0 (success)
  - PM2 sees exit code 0 and does NOT restart (because `restart_on_exit: false`)

**Detection Speed:** Window closure is detected within 2 seconds.

---

## Troubleshooting

### Watcher Still Restarts?

This could happen if PM2 cached the old config. To fix:

```bash
# Delete old PM2 config
pm2 delete facebook_instagram_watcher
pm2 delete instagram_watcher

# Reload with new config
pm2 start ecosystem.config.js --only facebook_instagram_watcher
pm2 start ecosystem.config.js --only instagram_watcher
```

### Check PM2 Config

Verify the config is loaded correctly:
```bash
pm2 show facebook_instagram_watcher
```

Look for `restart on exit` - it should be `false`.

### Force Stop

If the watcher won't stop:
```bash
# Stop by name
pm2 stop facebook_instagram_watcher

# Stop all
pm2 stop all

# Kill all PM2 processes
pm2 kill

# Restart PM2
pm2 resurrect
```

### Manual Test (without PM2)

To test the browser close behavior without PM2:
```bash
# Run directly
python watchers\facebook_instagram_watcher.py facebook

# Now close the browser window
# The script should exit immediately
```

---

## File Locations

- **Script:** `watchers/facebook_instagram_watcher.py`
- **Facebook Session:** `session/facebook/`
- **Instagram Session:** `session/instagram/`
- **Detected Items:** `Needs_Action/facebook_*.md` / `instagram_*.md`
- **Logs:** `Logs/pm2_facebook_watcher_*.log`

---

## Keywords Monitored

- **sales** - Sales inquiries, purchase requests (high priority)
- **client** - Client communications, support requests (medium priority)
- **project** - Project opportunities, collaborations (medium priority)

Check interval: **Every 60 seconds**

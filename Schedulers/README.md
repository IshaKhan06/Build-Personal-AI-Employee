# Scheduler Setup Guide

This guide explains how to set up the daily and weekly schedulers for automated briefings.

## Schedulers Available

| Scheduler | Frequency | Output |
|-----------|-----------|--------|
| Daily Scheduler | Daily at 8 AM | `/Logs/daily_summary_[date].md` |
| Weekly Audit Briefer | Monday 8 AM or 1st of month | `/Briefings/ceo_briefing_[date].md` |

---

## Daily Scheduler Setup

### Linux/Mac Setup (Cron)

1. Make the script executable:
   ```bash
   chmod +x schedulers/daily_scheduler.sh
   ```

2. Open your crontab for editing:
   ```bash
   crontab -e
   ```

3. Add the following line to run the scheduler daily at 8 AM:
   ```bash
   0 8 * * * cd /path/to/your/project && /path/to/schedulers/daily_scheduler.sh
   ```

### Windows Setup (Task Scheduler)

1. Open Task Scheduler

2. Click "Create Basic Task..."

3. Follow the wizard:
   - Name: "Daily Scheduler"
   - Trigger: "Daily" at "8:00 AM"
   - Action: "Start a program"
   - Program/script: "powershell.exe"
   - Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\your\project\schedulers\daily_scheduler.ps1"`

---

## Weekly Audit Briefer Setup

The Weekly Audit Briefer runs automatically on:
- **Every Monday at 8 AM**, OR
- **1st day of each month at 8 AM**

### Linux/Mac Setup (Cron)

1. Make the script executable:
   ```bash
   chmod +x schedulers/weekly_audit_scheduler.sh
   ```

2. Open your crontab for editing:
   ```bash
   crontab -e
   ```

3. Add lines for Monday AND 1st of month:
   ```bash
   # Every Monday at 8 AM
   0 8 * * 1 cd /path/to/your/project && /path/to/schedulers/weekly_audit_scheduler.sh
   
   # 1st of every month at 8 AM
   0 8 1 * * cd /path/to/your/project && /path/to/schedulers/weekly_audit_scheduler.sh
   ```

### Windows Setup (Task Scheduler)

1. Open Task Scheduler

2. Click "Create Basic Task..."

3. Follow the wizard:
   - Name: "Weekly Audit Briefer"
   - Trigger: "Weekly" on "Monday" at "8:00 AM"
   - Action: "Start a program"
   - Program/script: "powershell.exe"
   - Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\your\project\schedulers\weekly_audit_scheduler.ps1"`

### PowerShell Method (Advanced)

```powershell
# Run every Monday at 8 AM
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$PWD\schedulers\weekly_audit_scheduler.ps1`""
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am
Register-ScheduledTask -TaskName "WeeklyAuditBriefer" -Action $Action -Trigger $Trigger
```

---

## Testing Manually

### Weekly Audit Briefer (Force Run)

```bash
# Direct execution (bypasses day check)
python skills/weekly_audit_briefer/weekly_audit_briefer.py

# Via scheduler (checks if Monday or 1st)
.\Schedulers\weekly_audit_scheduler.ps1  # Windows
./Schedulers/weekly_audit_scheduler.sh   # Linux/Mac
```

---

## Files Created

| File | Description |
|------|-------------|
| `Schedulers/daily_scheduler.ps1` | Daily scheduler (Windows) |
| `Schedulers/daily_scheduler.sh` | Daily scheduler (Linux/Mac) |
| `Schedulers/weekly_audit_scheduler.ps1` | Weekly audit (Windows) |
| `Schedulers/weekly_audit_scheduler.sh` | Weekly audit (Linux/Mac) |
| `skills/weekly_audit_briefer/weekly_audit_briefer.py` | Audit script |
| `Briefings/ceo_briefing_YYYYMMDD.md` | Generated briefing |
| `Logs/audit_scheduler/audit_scheduler_log.md` | Audit execution log |

---

## PM2 Integration

```bash
# Start the weekly audit via PM2 (runs once, exits)
pm2 start ecosystem.config.js --only weekly_audit_briefer

# View logs
pm2 logs weekly_audit_briefer
```

---

## Verifying Scheduled Tasks

### Windows
```powershell
# List scheduled tasks
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Audit*"}

# Get task info
Get-ScheduledTaskInfo -TaskName "WeeklyAuditBriefer"
```

### Linux/Mac
```bash
# List cron jobs
crontab -l

# Check cron logs
grep CRON /var/log/syslog
```

---

## Troubleshooting

### Task Not Running
1. Check if task is registered
2. Check task history/logs
3. Run manually to test: `python skills/weekly_audit_briefer/weekly_audit_briefer.py`

### Python Not Found
Ensure Python is in PATH or use full path in scheduler script.

### Permission Denied
- Linux: `chmod +x schedulers/*.sh`
- Windows: Run PowerShell as Administrator

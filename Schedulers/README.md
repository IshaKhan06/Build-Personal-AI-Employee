# Daily Scheduler Setup Guide

This guide explains how to set up the daily scheduler to run Claude at 8AM to generate daily summaries.

## Linux/Mac Setup (Cron)

### Setting up the Cron Job

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
   
   Or if you want to log the output:
   ```bash
   0 8 * * * cd /path/to/your/project && /path/to/schedulers/daily_scheduler.sh >> /path/to/logfile.log 2>&1
   ```

4. Save and exit the editor.

### Crontab Format
- `0 8 * * *` means "at 8:00 AM, every day"
- The five fields represent: minute, hour, day of month, month, day of week

## Windows Setup (Task Scheduler)

### Setting up the Task Scheduler

1. Open Task Scheduler (search for "Task Scheduler" in the Start menu)

2. Click "Create Basic Task..." in the right panel

3. Follow the wizard:
   - Name: "Daily Scheduler"
   - Description: "Runs Claude daily at 8AM to generate daily summary"
   - Trigger: "Daily"
   - Time: "8:00 AM"
   - Action: "Start a program"
   - Program/script: "powershell.exe"
   - Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\your\project\schedulers\daily_scheduler.ps1"`

4. Complete the wizard

### Alternative PowerShell Method

You can also create the scheduled task using PowerShell:

```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$PWD\schedulers\daily_scheduler.ps1`""
$Trigger = New-ScheduledTaskTrigger -Daily -At 8am
$Settings = New-ScheduledTaskSettingsSet
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

Register-ScheduledTask -TaskName "DailyScheduler" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal
```

## Testing Manually

### Linux/Mac:
```bash
./schedulers/daily_scheduler.sh
```

### Windows:
```powershell
.\schedulers\daily_scheduler.ps1
```

## Files Created

- `schedulers/daily_scheduler.sh` - Bash script for Linux/Mac
- `schedulers/daily_scheduler.ps1` - PowerShell script for Windows

Both scripts will:
- Scan the `/Done` directory for processed files
- Generate a daily summary in `/Logs/daily_summary_[date].md`
- Include YAML frontmatter with metadata
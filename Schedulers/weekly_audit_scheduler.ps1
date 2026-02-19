# PowerShell Weekly Audit Briefer Scheduler
# Runs every Monday at 8 AM to generate CEO weekly briefing
# Also runs on the 1st of each month

param(
    [string]$ProjectRoot = $(Get-Location)
)

# Set the project root directory
Set-Location $ProjectRoot

# Function to check if today is Monday or 1st of month
function Test-ShouldRunAudit {
    $today = Get-Date
    $isMonday = $today.DayOfWeek -eq [DayOfWeek]::Monday
    $isFirstOfMonth = $today.Day -eq 1
    
    Write-Host "Today: $today"
    Write-Host "Day of Week: $($today.DayOfWeek)"
    Write-Host "Day of Month: $($today.Day)"
    Write-Host "Is Monday: $isMonday"
    Write-Host "Is 1st of Month: $isFirstOfMonth"
    
    return $isMonday -or $isFirstOfMonth
}

# Function to run the weekly audit briefer
function Run-WeeklyAudit {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "Running Weekly Audit Briefer" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
    
    # Check if Python is available
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-Error "Python is not installed or not in PATH"
        return $false
    }
    
    # Run the audit briefer script
    $scriptPath = Join-Path "skills" "weekly_audit_briefer" "weekly_audit_briefer.py"
    
    if (!(Test-Path $scriptPath)) {
        Write-Error "Weekly Audit Briefer script not found: $scriptPath"
        return $false
    }
    
    Write-Host "Executing: python $scriptPath" -ForegroundColor Cyan
    
    # Execute the Python script
    $output = & python $scriptPath 2>&1
    
    # Display output
    $output | ForEach-Object { Write-Host $_ }
    
    # Check for success
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[SUCCESS] Weekly Audit completed successfully" -ForegroundColor Green
        return $true
    } else {
        Write-Error "Weekly Audit failed with exit code $LASTEXITCODE"
        return $false
    }
}

# Function to log the execution
function Write-AuditLog {
    param(
        [string]$Status,
        [string]$Message,
        [string]$BriefingPath
    )
    
    $logDir = Join-Path "Logs" "audit_scheduler"
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force
    }
    
    $logFile = Join-Path $logDir "audit_scheduler_log.md"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    $logEntry = @"

## $timestamp

- **Status:** $Status
- **Message:** $Message
$(if ($BriefingPath) { "- **Briefing:** $BriefingPath" })

"@
    
    # Append to log file
    Add-Content -Path $logFile -Value $logEntry -Encoding UTF8
}

# Main execution
try {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Weekly Audit Scheduler" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Check if we should run the audit
    $shouldRun = Test-ShouldRunAudit
    
    if ($shouldRun) {
        Write-Host "`n[INFO] Running audit (Monday or 1st of month)" -ForegroundColor Yellow
        
        $success = Run-WeeklyAudit
        
        if ($success) {
            # Try to find the generated briefing
            $today = Get-Date -Format "yyyyMMdd"
            $briefingPath = Join-Path "Briefings" "ceo_briefing_$today.md"
            
            if (Test-Path $briefingPath) {
                Write-Host "`nBriefing generated: $briefingPath" -ForegroundColor Green
                Write-AuditLog -Status "Success" -Message "Weekly audit completed" -BriefingPath $briefingPath
            } else {
                Write-AuditLog -Status "Success" -Message "Weekly audit completed (briefing path unknown)"
            }
        } else {
            Write-AuditLog -Status "Failed" -Message "Weekly audit failed"
        }
    } else {
        Write-Host "`n[INFO] Skipping audit (not Monday or 1st of month)" -ForegroundColor Gray
        Write-AuditLog -Status "Skipped" -Message "Not Monday or 1st of month"
        
        # Exit gracefully (don't fail the scheduled task)
        exit 0
    }
} catch {
    Write-Error "Error in weekly audit scheduler: $_"
    Write-AuditLog -Status "Error" -Message $_.Exception.Message
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Scheduler Complete" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

exit 0

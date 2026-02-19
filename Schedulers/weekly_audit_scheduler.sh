#!/bin/bash
# Weekly Audit Briefer Scheduler
# Runs every Monday at 8 AM to generate CEO weekly briefing
# Also runs on the 1st of each month

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "========================================"
echo "Weekly Audit Scheduler"
echo "========================================"
echo ""

# Get current date info
TODAY=$(date +"%Y-%m-%d")
DAY_OF_WEEK=$(date +%u)  # 1 = Monday, 7 = Sunday
DAY_OF_MONTH=$(date +%d)

echo "Today: $TODAY"
echo "Day of Week: $DAY_OF_WEEK (1=Monday)"
echo "Day of Month: $DAY_OF_MONTH"

# Check if Monday (1) or 1st of month (01)
if [ "$DAY_OF_WEEK" -eq 1 ] || [ "$DAY_OF_MONTH" -eq "01" ]; then
    echo ""
    echo "[INFO] Running audit (Monday or 1st of month)"
    
    echo ""
    echo "========================================"
    echo "Running Weekly Audit Briefer"
    echo "========================================"
    echo ""
    
    # Check if Python is available
    if ! command -v python &> /dev/null; then
        echo "Error: Python is not installed or not in PATH"
        exit 1
    fi
    
    # Run the audit briefer script
    SCRIPT_PATH="skills/weekly_audit_briefer/weekly_audit_briefer.py"
    
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo "Error: Weekly Audit Briefer script not found: $SCRIPT_PATH"
        exit 1
    fi
    
    echo "Executing: python $SCRIPT_PATH"
    python "$SCRIPT_PATH"
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "[SUCCESS] Weekly Audit completed successfully"
        
        # Log the execution
        LOG_DIR="Logs/audit_scheduler"
        mkdir -p "$LOG_DIR"
        
        LOG_FILE="$LOG_DIR/audit_scheduler_log.md"
        TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
        BRIEFING_PATH="Briefings/ceo_briefing_$(date +%Y%m%d).md"
        
        echo "" >> "$LOG_FILE"
        echo "## $TIMESTAMP" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
        echo "- **Status:** Success" >> "$LOG_FILE"
        echo "- **Briefing:** $BRIEFING_PATH" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
        
        exit 0
    else
        echo "Weekly Audit failed with exit code $EXIT_CODE"
        
        # Log the failure
        LOG_DIR="Logs/audit_scheduler"
        mkdir -p "$LOG_DIR"
        LOG_FILE="$LOG_DIR/audit_scheduler_log.md"
        TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
        
        echo "" >> "$LOG_FILE"
        echo "## $TIMESTAMP" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
        echo "- **Status:** Failed" >> "$LOG_FILE"
        echo "- **Exit Code:** $EXIT_CODE" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
        
        exit 1
    fi
else
    echo ""
    echo "[INFO] Skipping audit (not Monday or 1st of month)"
    
    # Log the skip
    LOG_DIR="Logs/audit_scheduler"
    mkdir -p "$LOG_DIR"
    LOG_FILE="$LOG_DIR/audit_scheduler_log.md"
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    
    echo "" >> "$LOG_FILE"
    echo "## $TIMESTAMP" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    echo "- **Status:** Skipped" >> "$LOG_FILE"
    echo "- **Reason:** Not Monday or 1st of month" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    exit 0
fi

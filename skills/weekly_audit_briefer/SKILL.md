# Weekly Audit Briefer Skill (Gold Tier)

## Description
Runs weekly to audit completed tasks, revenue, expenses, and bottlenecks. Generates a comprehensive CEO Briefing with executive summary, financial analysis, and actionable recommendations. Integrates with the scheduler for automatic weekly execution.

## Functionality
- Runs weekly (Mondays) or on the 1st of each month
- Reads completed files from `/Done` directory
- Analyzes log files from `/Logs` directory
- Reads company documents (Company_Handbook.md, Business_Goals.md)
- Uses pattern matching to extract:
  - Revenue amounts ($1,000, sales: $500, etc.)
  - Expenses/subscriptions (monthly: $99, cost: $200, etc.)
  - Bottleneck indicators (blocked, waiting, pending, etc.)
- Generates CEO Briefing with:
  - Executive Summary
  - Task Completion Analysis (by type, platform, priority)
  - Revenue Analysis
  - Expense Analysis
  - Bottlenecks & Issues
  - Business Goals Alignment
  - Recommended Actions
- Saves briefing to `/Briefings/ceo_briefing_[date].md`

## Configuration
```json
{
  "name": "Weekly Audit Briefer",
  "version": "1.0",
  "tier": "Gold",
  "description": "Generates weekly CEO briefings from operational data",
  "author": "AI Employee System",
  "schedule": {
    "frequency": "weekly",
    "day": "monday",
    "time": "08:00",
    "alternative": "1st of month"
  },
  "patterns": {
    "revenue": [
      "$\\d+", "USD", "dollars", "revenue:", "sales:", "payment:", "invoice:"
    ],
    "expenses": [
      "subscription:", "monthly:", "cost:", "expense:", "paid:", "charged:"
    ],
    "bottlenecks": [
      "blocked", "waiting", "pending", "delay", "issue", "problem", "stuck"
    ]
  },
  "output": {
    "briefings_folder": "Briefings",
    "filename_format": "ceo_briefing_YYYYMMDD.md"
  }
}
```

## Instructions
1. Ensure `/Done` contains completed task files
2. Ensure `/Logs` contains activity logs
3. (Optional) Create `Company_Handbook.md` and `Business_Goals.md`
4. Run the Weekly Audit Briefer
5. Review generated briefing in `/Briefings/`

## Example Usage

### Manual Execution
```bash
@Weekly Audit Briefer run
python skills\weekly_audit_briefer\weekly_audit_briefer.py
```

### Scheduled Execution (Windows Task Scheduler)
```powershell
# Run every Monday at 8 AM
$Action = New-ScheduledTaskAction -Execute "Python.exe" -Argument "skills\weekly_audit_briefer\weekly_audit_briefer.py"
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am
Register-ScheduledTask -TaskName "WeeklyAuditBriefer" -Action $Action -Trigger $Trigger
```

### Scheduled Execution (Linux Cron)
```bash
# Run every Monday at 8 AM
0 8 * * 1 cd /path/to/project && python skills/weekly_audit_briefer/weekly_audit_briefer.py
```

## Output Format

The CEO Briefing includes:

### Executive Summary
- Total tasks completed
- Revenue identified
- Expenses identified
- Net position
- Bottlenecks detected

### Task Completion Analysis
- Breakdown by type (email, whatsapp, linkedin, etc.)
- Breakdown by platform (gmail, facebook, twitter, etc.)
- Breakdown by priority (high, medium, low)

### Revenue Analysis
- Total revenue found via pattern matching
- List of files containing revenue mentions
- Amounts extracted from each source

### Expense Analysis
- Total expenses found via pattern matching
- Subscription costs identified
- Recurring expenses flagged

### Bottlenecks & Issues
- Blocked tasks
- Pending approvals
- Waiting items
- Problems/issues detected

### Business Goals Alignment
- Alignment score (% of high-priority tasks)
- Goals referenced in completed work
- Recommendations for better alignment

### Recommended Actions
- Revenue-positive continuation
- Expense review alerts
- Bottleneck resolution priorities
- Resource allocation suggestions

## Pattern Matching Examples

### Revenue Patterns
```
$1,000.00 → $1000.00
500 USD → $500.00
revenue: $2500 → $2500.00
sales: 1500 dollars → $1500.00
invoice: $750 → $750.00
```

### Expense Patterns
```
subscription: $99 → $99.00
monthly: $299 → $299.00
cost: $150 → $150.00
expense: $500 → $500.00
paid: $1200 → $1200.00
```

### Bottleneck Detection
```
"blocked on client response" → detected
"waiting for approval" → detected
"pending review" → detected
"issue with payment" → detected
```

## Integration

This skill integrates with:
- **Daily Scheduler** - Can be triggered weekly from the scheduler
- **HITL Approval Handler** - Briefing can be routed for CEO review
- **Cross Domain Integrator** - Aggregates data from all platforms

## Example Briefing Output

```markdown
# CEO Weekly Briefing

**Period:** 2026-02-17 to 2026-02-23
**Generated:** 2026-02-24 08:00:00

## Executive Summary

This week's operational audit covers **45 completed tasks**.

**Key Metrics:**
- **Tasks Completed:** 45
- **Revenue Identified:** $12,500.00
- **Expenses Identified:** $1,297.00
- **Net Position:** $11,203.00
- **Bottlenecks Detected:** 3

## Task Completion Analysis

### By Type
- **Email:** 20
- **WhatsApp:** 15
- **LinkedIn:** 10

### By Priority
- **High:** 12
- **Medium:** 25
- **Low:** 8

## Recommended Actions

- ✅ **Revenue Positive:** Continue current sales strategies
- ⚠️ **Bottleneck Alert:** 3 blockers detected - prioritize resolution
- 📈 **High Volume:** Many high-priority tasks - ensure adequate resources
```

## Files Created

| File | Description |
|------|-------------|
| `skills/weekly_audit_briefer/weekly_audit_briefer.py` | Main skill script |
| `skills/weekly_audit_briefer/SKILL.md` | This documentation |
| `Briefings/ceo_briefing_YYYYMMDD.md` | Generated CEO briefing |

## Success Criteria

✓ Runs automatically on Mondays or 1st of month
✓ Reads all files from `/Done` and `/Logs`
✓ Extracts revenue using pattern matching
✓ Extracts expenses/subscriptions using pattern matching
✓ Detects bottlenecks from keyword analysis
✓ Generates comprehensive CEO Briefing
✓ Saves to `/Briefings/ceo_briefing_[date].md`
✓ Includes executive summary and recommendations

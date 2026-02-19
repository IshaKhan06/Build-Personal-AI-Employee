# Audit Logger Skill (Gold Tier)

## Description
Comprehensive audit logging utility that tracks every action across the Gold Tier system. Logs include timestamp, action_type, actor, target, parameters, approval_status, and result. Automatically retains logs for 90 days and generates weekly summaries for CEO Briefing.

## Functionality
- Logs every action to `/Logs/audit_[date].json`
- Automatic log retention management (90 days)
- Thread-safe concurrent writes
- Weekly summary generation for CEO Briefing
- Support for approval tracking
- Error logging with full context

## Log Entry Format

```json
{
  "timestamp": "2026-02-20T10:30:45.123456",
  "date": "2026-02-20",
  "action_type": "file_processed",
  "actor": "AI_Employee_System",
  "target": "Needs_Action/facebook_message_test.md",
  "parameters": {
    "keyword": "sales",
    "priority": "high"
  },
  "approval_status": "not_required",
  "result": "success",
  "message": "Processed Facebook message and created draft",
  "metadata": {
    "draft_path": "Pending_Approval/facebook_draft_20260220_103045.md",
    "processing_time_ms": 245
  }
}
```

## Configuration

```json
{
  "name": "Audit Logger",
  "version": "1.0",
  "tier": "Gold",
  "description": "Centralized audit logging for compliance and tracking",
  "retention_days": 90,
  "log_format": "JSON",
  "thread_safe": true,
  "output": {
    "logs_folder": "Logs",
    "filename_format": "audit_YYYYMMDD.json"
  }
}
```

## Usage

### Import and Initialize
```python
from utils.audit_logger import AuditLogger

# Initialize
logger = AuditLogger()

# Or get global instance
logger = get_audit_logger()
```

### Log Action Start
```python
logger.log_start(
    action_type="skill_execution",
    target="social_summary_generator",
    parameters={"files_to_process": 5},
    message="Starting social summary generation"
)
```

### Log Action End
```python
logger.log_end(
    action_type="skill_execution",
    target="social_summary_generator",
    result="success",
    metadata={"files_processed": 5, "drafts_created": 3}
)
```

### Log Approval
```python
logger.log_approval(
    action_type="email_send",
    target="client@example.com",
    approval_status="approved",
    actor="CEO",
    message="Approved by CEO for sending"
)
```

### Log Error
```python
logger.log_error(
    action_type="file_processing",
    target="Needs_Action/test.md",
    error_message="Invalid YAML frontmatter",
    metadata={"line": 5, "column": 10}
)
```

### Get Weekly Summary
```python
summary_text = logger.get_weekly_summary_for_briefing()
```

## Integration Points

### Skills
All Gold Tier skills should call the audit logger:
- On start: `logger.log_start(...)`
- On end: `logger.log_end(...)`
- On error: `logger.log_error(...)`
- On approval: `logger.log_approval(...)`

### Watchers
Watchers log:
- Monitoring start/stop
- Items detected
- Errors encountered

### Weekly Audit Briefer
The Weekly Audit Briefer includes audit log summary in CEO Briefing:
```python
from utils.audit_logger import get_audit_logger

logger = get_audit_logger()
audit_summary = logger.get_weekly_summary_for_briefing()
```

## Example Log Entries

### Skill Execution
```json
{
  "timestamp": "2026-02-20T10:30:45.123456",
  "action_type": "skill_execution",
  "actor": "AI_Employee_System",
  "target": "social_summary_generator",
  "parameters": {"input_files": 5},
  "approval_status": "not_required",
  "result": "success",
  "message": "Social summary generation completed",
  "metadata": {"drafts_created": 3, "errors": 0}
}
```

### File Processed
```json
{
  "timestamp": "2026-02-20T10:31:00.456789",
  "action_type": "file_processed",
  "actor": "social_summary_generator",
  "target": "Needs_Action/facebook_message_123.md",
  "parameters": {"platform": "facebook", "keyword": "sales"},
  "approval_status": "not_required",
  "result": "success",
  "message": "Created draft response",
  "metadata": {"draft_path": "Pending_Approval/facebook_draft_*.md"}
}
```

### Approval Required
```json
{
  "timestamp": "2026-02-20T10:32:15.789012",
  "action_type": "draft_created",
  "actor": "twitter_post_generator",
  "target": "Pending_Approval/twitter_draft_*.md",
  "parameters": {"keyword": "sales", "character_count": 245},
  "approval_status": "pending",
  "result": "success",
  "message": "Draft created, awaiting HITL approval"
}
```

### Approval Granted
```json
{
  "timestamp": "2026-02-20T14:00:00.123456",
  "action_type": "approval_granted",
  "actor": "HITL_Handler",
  "target": "Pending_Approval/twitter_draft_*.md",
  "parameters": {"moved_to": "Approved"},
  "approval_status": "approved",
  "result": "success",
  "message": "Draft approved for posting"
}
```

### Error
```json
{
  "timestamp": "2026-02-20T10:33:30.345678",
  "action_type": "file_processing",
  "actor": "social_summary_generator",
  "target": "Needs_Action/corrupted_file.md",
  "parameters": {},
  "approval_status": "not_required",
  "result": "failed",
  "message": "Invalid YAML frontmatter: expected --- at line 1",
  "metadata": {"error_type": "YAMLError", "line": 1}
}
```

### Watcher Detection
```json
{
  "timestamp": "2026-02-20T10:35:00.567890",
  "action_type": "item_detected",
  "actor": "facebook_instagram_watcher",
  "target": "Facebook Message from John Doe",
  "parameters": {"keyword": "sales", "platform": "facebook"},
  "approval_status": "not_required",
  "result": "success",
  "message": "Saved to Needs_Action/facebook_message_*.md"
}
```

## Log Retention

- **Retention Period:** 90 days
- **Cleanup:** Automatic on initialization
- **Deleted:** Logs older than 90 days
- **Preserved:** Recent logs for compliance

## Weekly Summary in CEO Briefing

The Weekly Audit Briefer includes:

```markdown
## Audit Log Summary (Last 7 Days)

**Period:** 2026-02-13 to 2026-02-20

### Activity Overview
- **Total Actions:** 245
- **Successful:** 238
- **Failed:** 5
- **Started/In Progress:** 2

### Actions by Type
- **file_processed:** 150
- **skill_execution:** 45
- **draft_created:** 30
- **item_detected:** 20

### Approval Status
- **Pending Approval:** 12
- **Approved:** 28
- **Rejected:** 2

### Recent Errors
- [2026-02-20T10:33:30] file_processing: Invalid YAML frontmatter
- [2026-02-19T15:22:10] api_call: Network timeout
```

## Files

| File | Purpose |
|------|---------|
| `utils/audit_logger.py` | Main audit logger utility |
| `Logs/audit_YYYYMMDD.json` | Daily audit logs |
| `Briefings/ceo_briefing_*.md` | CEO briefings with audit summary |

## Success Criteria

✓ All skills log start/end actions
✓ All errors logged with full context
✓ Approval actions tracked
✓ Logs retained for 90 days
✓ Old logs automatically deleted
✓ Weekly summary in CEO Briefing
✓ Thread-safe concurrent writes

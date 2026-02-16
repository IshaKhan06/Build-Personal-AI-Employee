# HITL Approval Handler Skill

This skill handles human-in-the-loop (HITL) approvals for sensitive actions like emails, social media posts, and payments.

## Functionality
- For sensitive actions (emails, posts, payments), writes request to /Pending_Approval/[action_type]_[date].md with YAML: type, details, status
- Monitors /Approved folder for moved files
- On approval, executes via MCP (e.g., send email from draft)
- If rejected, moves to /Rejected and logs
- Integrates with other skills (LinkedIn Poster, Email MCP)
- Logs all activities to /Logs/hitl_[date].md

## Commands
- `check`: Check for approved and rejected requests once
- `monitor [seconds]`: Run continuous monitoring with specified interval

## Example Usage
```
@HITL Approval Handler check Pending_Approval
```

## Integration
This skill integrates with:
- Auto LinkedIn Poster skill
- Email MCP server
- Other skills that require human approval for sensitive actions
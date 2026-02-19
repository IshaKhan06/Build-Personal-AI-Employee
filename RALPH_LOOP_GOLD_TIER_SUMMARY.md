# Ralph Wiggum Loop (Gold Tier) - Implementation Summary

## Overview

The Gold Tier Ralph Wiggum Loop is an autonomous multi-step task processor that handles complete workflows from initial detection to final completion.

---

## Command to Run

```bash
./ralph-loop "Process multi-step task in Needs_Action" --max-iterations 20
```

Or on Windows:
```bash
python tools\ralph_loop_runner.py "Process multi-step task in Needs_Action" --max-iterations 20
```

---

## Files Updated

| File | Status |
|------|--------|
| `tools/ralph_loop_runner.py` | ✅ Updated (Gold Tier multi-step) |
| `tools/ralph-loop` | ✅ Updated (shell script) |
| `tools/ralph-loop.bat` | ⏳ Existing (Windows batch) |
| `tools/RALPH_LOOP_TEST_GUIDE.md` | ✅ Created (test documentation) |

---

## Multi-Step Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Gold Tier Workflow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Needs_Action/                                                   │
│       ↓                                                          │
│  ┌─────────────┐                                                 │
│  │  ANALYSIS   │ ← Parse frontmatter, determine task type       │
│  └──────┬──────┘                                                 │
│         ↓                                                        │
│  ┌─────────────────┐                                             │
│  │ SKILL EXECUTION │ ← Trigger skill, create draft              │
│  └──────┬──────────┘                                             │
│         ↓                                                        │
│  ┌─────────────────┐                                             │
│  │ HITL APPROVAL   │ ← Wait for human approval                  │
│  └──────┬──────────┘                                             │
│         ↓                                                        │
│  ┌─────────────────┐                                             │
│  │ MCP EXECUTION   │ ← Execute via MCP server                   │
│  └──────┬──────────┘                                             │
│         ↓                                                        │
│  ┌─────────────────┐                                             │
│  │ AUDIT LOGGING   │ ← Log to audit_*.json                      │
│  └──────┬──────────┘                                             │
│         ↓                                                        │
│  ┌─────────────┐                                                 │
│  │ COMPLETION  │ ← Move to Done/, TASK_COMPLETE                 │
│  └─────────────┘                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Example Multi-Step Task

### Input File (Needs_Action/)
```markdown
---
type: facebook_message
platform: facebook
from: "John Doe"
keyword: sales
priority: high
---

# Sales Lead

Hi! I'm interested in your sales services for my project.
Can you provide pricing information?
```

### Workflow Execution

```
Iteration 1:
  Stage: analysis → skill_execution
  - Task analyzed: facebook_message
  - Skill triggered: social_summary_generator
  - Draft created: Pending_Approval/draft_file.md
  Status: Awaiting HITL approval

[HUMAN ACTION: Move draft to Approved/]

Iteration 2:
  Stage: hitl_approval → mcp_execution → audit_logging → completion
  - Approval detected
  - MCP execution simulated
  - Audit log written
  - File moved to Done/
  Status: TASK_COMPLETE
```

---

## Integration Points

### Cross Domain Integrator
- Task type determination uses Cross Domain patterns
- Routes personal vs business items appropriately

### Audit Logger
- Every action logged to `/Logs/audit_[date].json`
- Includes: loop start, task analysis, skill execution, HITL, MCP, completion

### Skills
- `social_summary_generator` - Facebook/Instagram leads
- `twitter_post_generator` - Twitter leads
- `auto_linkedin_poster` - LinkedIn leads

---

## Example Log Entries

### Loop Start
```json
{
  "timestamp": "2026-02-20T10:30:00",
  "action_type": "ralph_loop_started",
  "target": "ralph_loop_runner",
  "parameters": {"max_iterations": 20, "prompt": "Process sales leads"},
  "result": "success"
}
```

### Task Analyzed
```json
{
  "timestamp": "2026-02-20T10:30:01",
  "action_type": "task_analyzed",
  "target": "Needs_Action/sales_lead.md",
  "parameters": {
    "task_type": "facebook_message",
    "is_multi_step": true,
    "workflow_stages": 6
  },
  "result": "success"
}
```

### HITL Approved
```json
{
  "timestamp": "2026-02-20T10:35:00",
  "action_type": "hitl_approved",
  "target": "Pending_Approval/draft_sales_lead.md",
  "result": "success",
  "message": "HITL approval granted"
}
```

### Task Completed
```json
{
  "timestamp": "2026-02-20T10:35:05",
  "action_type": "task_completed",
  "target": "Needs_Action/sales_lead.md",
  "parameters": {
    "task_type": "facebook_message",
    "workflow_stages": 6
  },
  "result": "success"
}
```

---

## Test Guide

### Quick Test

```bash
# 1. Create test file
cat > Needs_Action/test_multi_step.md << 'EOF'
---
type: facebook_message
platform: facebook
keyword: sales
priority: high
---

# Sales Lead

Interested in your services. Please contact me.
EOF

# 2. Run loop
./ralph-loop "Process sales leads" --max-iterations 20

# 3. Simulate approval (after draft created)
mv Pending_Approval/draft_test_multi_step.md Approved/

# 4. Continue loop
./ralph-loop "Continue processing" --max-iterations 20

# 5. Verify completion
ls Done/test_multi_step.md
cat Logs/audit_$(date +%Y%m%d).json | tail -20
```

### Full Test Guide

See `tools/RALPH_LOOP_TEST_GUIDE.md` for comprehensive testing.

---

## Command Reference

| Command | Description |
|---------|-------------|
| `./ralph-loop "Process all"` | Process all files (default 20 iterations) |
| `./ralph-loop "Sales" --max-iterations 15` | Process with custom iterations |
| `./ralph-loop --no-audit` | Run without audit logging |
| `./ralph-loop --help` | Show help |

---

## Output Summary

```
============================================================
RALPH WIGGUM LOOP SUMMARY
============================================================
Iterations Run: 3
Tasks Processed: 5

Tasks by Stage:
  analysis: 5
  skill_execution: 5
  hitl_approval: 5
  mcp_execution: 3
  audit_logging: 3
  completion: 3

Tasks by Result:
  TASK_COMPLETE: 3
  draft_created: 2
  pending: 2
============================================================
```

---

## Success Criteria

✓ Max iterations: 20 (Gold Tier)
✓ Multi-step workflow supported
✓ Integrates with Cross Domain Integrator
✓ Integrates with Audit Logger
✓ TASK_COMPLETE message on finish
✓ Files moved to Done/ on completion
✓ Drafts created in Pending_Approval
✓ HITL approval detection works
✓ Audit logs written for all actions

---

*Generated by Gold Tier Ralph Wiggum Loop*
*Autonomous multi-step task processing with full workflow integration*

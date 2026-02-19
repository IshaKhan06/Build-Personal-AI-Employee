# Gold Tier Architecture Documentation

**Tier:** Gold Tier  
**Version:** 1.0  
**Last Updated:** 2026-02-20

---

## Executive Summary

The Gold Tier system is an autonomous AI employee platform that monitors multiple communication channels, processes incoming messages using AI skills, requires human approval for sensitive actions, and executes approved tasks via MCP servers. This tier adds comprehensive error recovery, audit logging, and multi-step autonomous task processing.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           GOLD TIER ARCHITECTURE                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INPUT LAYER (Watchers)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │    Gmail     │  │   WhatsApp   │  │   LinkedIn   │  │   Twitter    │        │
│  │   Watcher    │  │   Watcher    │  │   Watcher    │  │   Watcher    │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                 │                 │                 │
│         └─────────────────┴────────┬────────┴─────────────────┘                 │
│                                    │                                            │
│                          (Keywords: sales, client, project)                     │
└────────────────────────────────────┼────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING LAYER (Skills)                              │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         /Needs_Action/ Directory                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │  Detected Items (markdown with YAML frontmatter)                │    │   │
│  │  │  - type, platform, from, keyword, priority, status              │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│         ┌──────────────────────────┼──────────────────────────┐                 │
│         │                          │                          │                 │
│         ▼                          ▼                          ▼                 │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │     Social      │     │     Twitter     │     │    Weekly       │           │
│  │    Summary      │     │     Post        │     │    Audit        │           │
│  │   Generator     │     │   Generator     │     │    Briefer      │           │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘           │
│           │                       │                       │                     │
└───────────┼───────────────────────┼───────────────────────┼─────────────────────┘
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          APPROVAL LAYER (HITL)                                   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                      /Pending_Approval/ Directory                        │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │  Drafts awaiting human approval                                 │    │   │
│  │  │  - Generated summaries                                          │    │   │
│  │  │  - Drafted responses (tweets, posts, emails)                    │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                    [HUMAN ACTION: Review & Approve]                            │
│                                    │                                            │
│                                    ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                        /Approved/ Directory                              │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │  Approved items ready for execution                             │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┼────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION LAYER (MCP)                                   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                        MCP Servers                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │   │
│  │  │    Email     │  │   LinkedIn   │  │   Twitter    │                   │   │
│  │  │     MCP      │  │     MCP      │  │     MCP      │                   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┼────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          COMPLETION LAYER                                        │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         /Done/ Directory                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │  Completed tasks (audit trail)                                  │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          CROSS-CUTTING CONCERNS                                  │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  Error Recovery System                                                   │   │
│  │  - Exponential backoff retry (max 3, 1-60s)                              │   │
│  │  - Error logging to /Logs/error_*                                        │   │
│  │  - Skill error reports to /Errors/                                       │   │
│  │  - Manual action drafts to /Plans/                                       │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  Audit Logger                                                            │   │
│  │  - Every action logged to /Logs/audit_*.json                             │   │
│  │  - 90-day retention with auto-cleanup                                    │   │
│  │  - Weekly summary in CEO Briefing                                        │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  Ralph Wiggum Loop (Autonomous Multi-Step)                               │   │
│  │  - Max 20 iterations                                                     │   │
│  │  - Full workflow: analysis → skill → HITL → MCP → audit → completion     │   │
│  │  - Integrates with all components                                        │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Watchers (Input Layer)

**Purpose:** Monitor external communication channels for relevant content.

| Watcher | File | Interval | Keywords |
|---------|------|----------|----------|
| Gmail | `watchers/gmail_watcher.py` | 120s | urgent, invoice, payment, sales |
| WhatsApp | `watchers/whatsapp_watcher.py` | 30s | sales, client, project |
| LinkedIn | `watchers/linkedin_watcher.py` | 60s | sales, client, project |
| Twitter | `watchers/twitter_watcher.py` | 60s | sales, client, project |
| Facebook/Instagram | `watchers/facebook_instagram_watcher.py` | 60s | sales, client, project |

**Features:**
- Playwright-based browser automation
- Persistent session storage (`/session/`)
- Error recovery with exponential backoff
- Browser close detection (graceful shutdown)
- Error logging to `/Logs/error_[watcher]_[date].log`

**Output:** Markdown files in `/Needs_Action/` with YAML frontmatter

---

### 2. Skills (Processing Layer)

**Purpose:** Process detected items and generate responses.

| Skill | File | Input | Output |
|-------|------|-------|--------|
| Social Summary Generator | `skills/social_summary_generator/` | Facebook/Instagram files | Drafts in Pending_Approval |
| Twitter Post Generator | `skills/twitter_post_generator/` | Twitter files | Tweet drafts |
| Weekly Audit Briefer | `skills/weekly_audit_briefer/` | /Done, /Logs | CEO Briefing |

**Features:**
- Try-except error handling
- Error reports to `/Errors/skill_error_*.md`
- Manual action drafts to `/Plans/`
- Audit logging for all operations

---

### 3. HITL Approval (Approval Layer)

**Purpose:** Human-in-the-Loop approval for sensitive actions.

**Workflow:**
1. Skills create drafts in `/Pending_Approval/`
2. Human reviews and moves to `/Approved/`
3. HITL Handler executes approved items

**Files:**
- `skills/hitl_approval_handler/hitl_approval_handler.py`
- `skills/hitl_approval_handler/SKILL.md`

---

### 4. MCP Servers (Execution Layer)

**Purpose:** Execute approved actions via external APIs.

| Server | Purpose |
|--------|---------|
| Email MCP | Send emails via Gmail API |
| LinkedIn MCP | Post to LinkedIn |
| Twitter MCP | Post tweets |

**Features:**
- REST API interface
- Draft/send functionality
- Error handling and logging

---

### 5. Error Recovery System

**Purpose:** Handle failures gracefully with retry and degradation.

**Features:**
- Exponential backoff retry (max 3, 1-60s delay)
- Error logging to `/Logs/error_[component]_[date].log`
- Skill error reports to `/Errors/skill_error_*.md`
- Manual action drafts to `/Plans/manual_action_*.md`

**Utility:** `utils/error_recovery.py`

---

### 6. Audit Logger

**Purpose:** Comprehensive audit trail for compliance.

**Features:**
- JSON log format (`/Logs/audit_[date].json`)
- 90-day retention with auto-cleanup
- Weekly summary in CEO Briefing
- Thread-safe concurrent writes

**Log Entry Format:**
```json
{
  "timestamp": "2026-02-20T10:30:45.123456",
  "action_type": "file_processed",
  "actor": "social_summary_generator",
  "target": "Needs_Action/file.md",
  "parameters": {"keyword": "sales"},
  "approval_status": "not_required",
  "result": "success",
  "message": "Created draft response"
}
```

**Utility:** `utils/audit_logger.py`

---

### 7. Ralph Wiggum Loop (Autonomous Processing)

**Purpose:** Autonomous multi-step task processing.

**Workflow:**
```
analysis → skill_execution → hitl_approval → mcp_execution → audit_logging → completion
```

**Features:**
- Max 20 iterations (Gold Tier)
- Integrates with all components
- TASK_COMPLETE promise
- Audit logging throughout

**Command:**
```bash
./ralph-loop "Process multi-step task" --max-iterations 20
```

---

## Data Flow

### Complete Flow (New Message → Completed Task)

```
1. Gmail Watcher detects email with "urgent invoice" keyword
   ↓
2. Saves to /Needs_Action/gmail_*.md with YAML frontmatter
   ↓
3. Ralph Wiggum Loop scans /Needs_Action/
   ↓
4. Task Analyzer determines: financial_task, multi-step
   ↓
5. Skill Execution: Social Summary Generator processes file
   ↓
6. Draft created in /Pending_Approval/
   ↓
7. HITL Approval: Human reviews and moves to /Approved/
   ↓
8. Ralph Wiggum Loop detects approval
   ↓
9. MCP Execution: Email MCP sends response
   ↓
10. Audit Logging: All actions logged to /Logs/audit_*.json
    ↓
11. Completion: File moved to /Done/
    ↓
12. TASK_COMPLETE
```

---

## Directory Structure

```
Hackathon_0/
├── watchers/                    # Input layer (watchers)
│   ├── gmail_watcher.py
│   ├── whatsapp_watcher.py
│   ├── linkedin_watcher.py
│   ├── twitter_watcher.py
│   └── facebook_instagram_watcher.py
├── skills/                      # Processing layer (skills)
│   ├── social_summary_generator/
│   ├── twitter_post_generator/
│   ├── weekly_audit_briefer/
│   └── hitl_approval_handler/
├── mcp_servers/                 # Execution layer (MCP)
│   └── email-mcp/
├── tools/                       # Utilities
│   ├── ralph_loop_runner.py
│   └── ralph-loop
├── utils/                       # Shared utilities
│   ├── error_recovery.py
│   └── audit_logger.py
├── session/                     # Browser sessions
│   ├── gmail/
│   ├── whatsapp/
│   ├── linkedin/
│   ├── twitter/
│   └── facebook/
├── Needs_Action/                # Input queue
├── Pending_Approval/            # Awaiting HITL
├── Approved/                    # Ready for execution
├── Done/                        # Completed tasks
├── Plans/                       # Drafts & manual actions
├── Logs/                        # Audit & error logs
├── Errors/                      # Skill error reports
├── Briefings/                   # CEO briefings
└── ecosystem.config.js          # PM2 configuration
```

---

## Configuration

### PM2 Configuration

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'facebook_instagram_watcher',
      script: 'python',
      args: 'watchers/facebook_instagram_watcher.py facebook',
      restart_on_exit: false,  // Don't restart on browser close
      max_restarts: 5
    },
    // ... other watchers and skills
  ]
};
```

### Error Recovery Configuration

```python
# Default settings
max_retries = 3
base_delay = 1  # second
max_delay = 60  # seconds
exponential_base = 2
# Retry sequence: 1s → 2s → 4s → 8s → 16s → 32s (capped at 60s)
```

### Audit Log Retention

```python
RETENTION_DAYS = 90  # Logs older than 90 days auto-deleted
```

---

## Monitoring & Observability

### Log Files

| Log Type | Location | Format |
|----------|----------|--------|
| Audit Logs | `/Logs/audit_*.json` | JSON |
| Error Logs | `/Logs/error_*.log` | Text |
| Skill Errors | `/Errors/skill_error_*.md` | Markdown |
| PM2 Logs | `/Logs/pm2_*.log` | Text |
| Activity Logs | `/Logs/*_summary_*.md` | Markdown |

### Key Metrics

- **Tasks Processed:** Count of files moved to /Done/
- **Drafts Created:** Count of files in /Pending_Approval/
- **Approvals Pending:** Files waiting in /Pending_Approval/
- **Errors:** Count in /Errors/ and error logs
- **Audit Events:** Daily count in audit logs

---

## Security Considerations

1. **Session Storage:** Browser sessions stored in `/session/` with credentials
2. **API Credentials:** OAuth tokens stored securely (token.json)
3. **Access Control:** HITL approval required for sensitive actions
4. **Audit Trail:** All actions logged for compliance

---

## Scalability

### Horizontal Scaling

- Multiple watcher instances (different accounts)
- Separate skill instances per task type
- Load-balanced MCP servers

### Vertical Scaling

- Increase watcher check intervals
- Batch process files in skills
- Parallel MCP executions

---

## Disaster Recovery

1. **Session Recovery:** Re-authenticate if session expired
2. **Error Recovery:** Automatic retry with backoff
3. **Manual Fallback:** Manual action drafts in /Plans/
4. **Audit Trail:** Complete history in audit logs

---

## Future Enhancements

1. **Additional Watchers:** Slack, Teams, SMS
2. **More Skills:** Content generation, data analysis
3. **Enhanced HITL:** Web interface for approvals
4. **Analytics Dashboard:** Real-time metrics visualization
5. **ML Classification:** Better task type detection

---

*Gold Tier Architecture Documentation*
*Version 1.0 - 2026-02-20*

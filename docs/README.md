# Gold Tier Documentation Index

**Tier:** Gold Tier  
**Status:** Complete  
**Date:** 2026-02-20

---

## Documentation Files

### Core Documentation

| File | Purpose | Path |
|------|---------|------|
| **Architecture** | System architecture, components, data flow | `docs/architecture.md` |
| **Lessons Learned** | What worked, challenges, improvements | `docs/lessons_learned.md` |
| **System Guide** | Complete system usage guide | `guide.md` |

### Component Documentation

| Component | Documentation | Path |
|-----------|--------------|------|
| Facebook/Instagram Watcher | Setup & usage guide | `watchers/FACEBOOK_INSTAGRAM_GUIDE.md` |
| Facebook/Instagram Watcher | Quick start | `watchers/FACEBOOK_INSTAGRAM_QUICKSTART.md` |
| Twitter Watcher | Setup & usage guide | `watchers/TWITTER_GUIDE.md` |
| Social Summary Generator | Skill documentation | `skills/social_summary_generator/SKILL.md` |
| Twitter Post Generator | Skill documentation | `skills/twitter_post_generator/SKILL.md` |
| Weekly Audit Briefer | Skill documentation | `skills/weekly_audit_briefer/SKILL.md` |
| Audit Logger | Skill documentation | `skills/audit_logger/SKILL.md` |
| Error Recovery | Test guide | `ERROR_RECOVERY_TEST_GUIDE.md` |
| Error Recovery | Summary | `ERROR_RECOVERY_SUMMARY.md` |
| Ralph Wiggum Loop | Test guide | `tools/RALPH_LOOP_TEST_GUIDE.md` |
| Ralph Wiggum Loop | Summary | `RALPH_LOOP_GOLD_TIER_SUMMARY.md` |
| Scheduler | Setup guide | `Schedulers/README.md` |

---

## Quick Reference

### Run Watchers

```bash
# Facebook/Instagram
pm2 start ecosystem.config.js --only facebook_instagram_watcher

# Twitter
pm2 start ecosystem.config.js --only twitter_watcher

# All watchers
pm2 start ecosystem.config.js
```

### Run Skills

```bash
# Social Summary Generator
python skills\social_summary_generator\social_summary_generator.py

# Twitter Post Generator
python skills\twitter_post_generator\twitter_post_generator.py

# Weekly Audit Briefer
python skills\weekly_audit_briefer\weekly_audit_briefer.py
```

### Run Ralph Wiggum Loop

```bash
# Process multi-step tasks
./ralph-loop "Process multi-step task in Needs_Action" --max-iterations 20
```

### View Logs

```bash
# PM2 logs
pm2 logs

# Audit logs
type Logs\audit_*.json

# Error logs
type Logs\error_*.log
```

---

## Directory Structure

```
├── docs/                      # Documentation
│   ├── architecture.md        # System architecture
│   └── lessons_learned.md     # Lessons learned
├── watchers/                  # Input layer
├── skills/                    # Processing layer
├── mcp_servers/               # Execution layer
├── tools/                     # Utilities (Ralph Loop)
├── utils/                     # Shared utilities
│   ├── error_recovery.py      # Error recovery
│   └── audit_logger.py        # Audit logging
├── session/                   # Browser sessions
├── Needs_Action/              # Input queue
├── Pending_Approval/          # Awaiting HITL
├── Approved/                  # Ready for execution
├── Done/                      # Completed
├── Plans/                     # Drafts & manual actions
├── Logs/                      # Audit & error logs
├── Errors/                    # Skill error reports
└── Briefings/                 # CEO briefings
```

---

## Gold Tier Features

### ✅ Implemented

1. **Multi-Channel Monitoring**
   - Gmail, WhatsApp, LinkedIn, Twitter, Facebook/Instagram watchers
   - Keyword detection (sales, client, project)
   - 30-120 second check intervals

2. **AI Skills**
   - Social Summary Generator (Facebook/Instagram)
   - Twitter Post Generator
   - Weekly Audit Briefer (CEO reports)

3. **Human-in-the-Loop**
   - Draft creation in Pending_Approval
   - Human approval workflow
   - Manual action fallbacks

4. **Error Recovery**
   - Exponential backoff retry (max 3, 1-60s)
   - Error logging to /Logs/
   - Skill error reports to /Errors/
   - Manual action drafts to /Plans/

5. **Audit Logging**
   - JSON logs to /Logs/audit_*.json
   - 90-day retention with auto-cleanup
   - Weekly summary in CEO Briefing
   - Thread-safe concurrent writes

6. **Autonomous Processing**
   - Ralph Wiggum Loop (max 20 iterations)
   - Multi-step workflow (analysis → skill → HITL → MCP → audit → completion)
   - TASK_COMPLETE promise

---

## Success Criteria (Gold Tier)

- ✅ All watchers running with error recovery
- ✅ All skills logging to audit system
- ✅ Multi-step task processing working
- ✅ HITL approval workflow functional
- ✅ Error reports created on failures
- ✅ Manual action drafts created on MCP failure
- ✅ Weekly audit summary in CEO briefing
- ✅ 90-day audit log retention working
- ✅ Ralph Loop completes tasks autonomously

---

## Contact & Support

For questions about Gold Tier:
1. Check `docs/architecture.md` for system overview
2. Check `docs/lessons_learned.md` for common issues
3. Check component-specific SKILL.md files
4. Review test guides for troubleshooting

---

*Gold Tier Documentation Index*
*Last Updated: 2026-02-20*

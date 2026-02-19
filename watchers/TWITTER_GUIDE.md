# Twitter (X) Watcher & Twitter Post Generator - Quick Start

## Gold Tier Twitter Integration

This guide explains how to set up and run the Twitter (X) monitoring system with automated tweet response generation.

---

## Components

### 1. Twitter (X) Watcher (`watchers/twitter_watcher.py`)
- Monitors Twitter DMs, tweets, and notifications
- Detects keywords: **sales**, **client**, **project**
- Saves detected items as `.md` files in `/Needs_Action`
- Checks every **60 seconds**
- Uses persistent session in `/session/twitter`

### 2. Twitter Post Generator (`skills/twitter_post_generator/`)
- Processes Twitter files from `/Needs_Action`
- Generates comprehensive summaries
- Drafts tweet responses (under 280 characters)
- Moves drafts to `/Pending_Approval` for HITL review

---

## Installation

### Prerequisites
```bash
# Install Playwright
pip install playwright

# Install browser
playwright install chromium
```

---

## Running with PM2 (Recommended)

### Start Twitter Watcher
```bash
pm2 start ecosystem.config.js --only twitter_watcher
```

### Run Twitter Post Generator (Manual)
```bash
python skills\twitter_post_generator\twitter_post_generator.py
```

### Run Twitter Post Generator (PM2 - On Demand)
```bash
pm2 start ecosystem.config.js --only twitter_post_generator
# Will run once and exit (autorestart: false)
```

### Check Status
```bash
pm2 status
pm2 logs twitter_watcher
```

### Stop Twitter Watcher
```bash
pm2 stop twitter_watcher
pm2 delete twitter_watcher
```

---

## Running Directly (Without PM2)

### Twitter Watcher
```bash
cd C:\Users\pc\Desktop\Hackathon_0
python watchers\twitter_watcher.py
```

**To Stop:** Close the browser window or press `Ctrl+C`.

### Twitter Post Generator
```bash
python skills\twitter_post_generator\twitter_post_generator.py
```

---

## First-Time Setup

### Twitter Login
1. Run the Twitter watcher:
   ```bash
   pm2 start ecosystem.config.js --only twitter_watcher
   ```

2. A browser window will open

3. Log in to your Twitter (X) account

4. The session will be saved to `/session/twitter`

5. Future runs will use the saved session

---

## Testing Guide

### Test 1: Send a Test Twitter DM

1. **Start the Twitter Watcher:**
   ```bash
   pm2 start ecosystem.config.js --only twitter_watcher
   ```

2. **Send a test DM:**
   - Open Twitter in the browser window
   - Go to Messages (DMs)
   - Send yourself a message or ask someone to send:
     ```
     Hi! I'm interested in your sales services. Can you help with my project?
     ```

3. **Wait for detection (60 seconds):**
   The watcher checks every 60 seconds. You should see output like:
   ```
   [10:30:45] Checking Twitter...
     Saved: twitter_dm_20260219_103045_TestUser_sales.md
     Found 1 matching items
   ```

4. **Verify file created in /Needs_Action:**
   ```bash
   dir Needs_Action\twitter_*.md
   ```

5. **Run Twitter Post Generator:**
   ```bash
   python skills\twitter_post_generator\twitter_post_generator.py
   ```

6. **Check outputs:**
   - Summary and draft in `/Pending_Approval/twitter_draft_*.md`
   - Activity log in `/Logs/twitter_post_generator_*.md`

---

### Test 2: Create Manual Test File

If you can't send a real Twitter DM, create a test file:

```bash
echo ---
type: twitter_dm
platform: twitter
from: "TestClient"
subject: "Twitter DM - sales keyword found"
received: "2026-02-19T10:00:00"
priority: high
status: pending
keyword: sales
---

# Twitter DM Alert

## Summary
New sales-related DM received from TestClient on Twitter.

## Original Content
Hi! I'm interested in your sales services for my new project.
Can you provide pricing information? This is urgent.

## Detection Details
- **Keyword Found:** sales
- **Platform:** twitter
- **Type:** dm
- **Detected At:** 2026-02-19 10:00:00
" > Needs_Action\twitter_dm_test_sales.md
```

Then run the Twitter Post Generator:
```bash
python skills\twitter_post_generator\twitter_post_generator.py
```

---

## Output Files

### Detected Item (`/Needs_Action/twitter_*.md`)
```markdown
---
type: twitter_dm
platform: twitter
from: "John Doe"
subject: "Twitter DM - sales keyword found"
received: "2026-02-19T10:30:45"
priority: high
status: pending
keyword: sales
---

# Twitter DM Alert

## Summary
New sales-related DM received from John Doe on Twitter.
Message preview: 'Hi! I'm interested in your sales services...'
This appears to be a sales inquiry - consider prompt response.

## Original Content
Hi! I'm interested in your sales services for my new project.
Can you provide pricing information?

## Detection Details
- **Keyword Found:** sales
- **Platform:** twitter
- **Type:** dm
- **Detected At:** 2026-02-19 10:30:45
```

### Generated Draft (`/Pending_Approval/twitter_draft_*.md`)
```markdown
---
type: twitter_response_draft
platform: twitter
keyword: sales
status: draft
created: "2026-02-19T10:31:00"
source_file: "Needs_Action/twitter_dm_20260219_103045_JohnDoe_sales.md"
requires_hitl: true
generated_by: Twitter Post Generator
---

# Twitter Response Draft

## Summary
[Generated summary with intent, sentiment, key points]

## Drafted Tweet/Response
```
Hi @JohnDoe! Thanks for your interest in our services! 🚀

We'd love to help you with your needs. Could you DM us more details about:
1. What you're looking for
2. Your timeline
3. Budget range

We'll get back to you ASAP with a customized solution! 💼

#Sales #CustomerService
```

**Character Count:** 245 / 280

## Action Required
- [ ] Review the summary above
- [ ] Edit the drafted response if needed
- [ ] Move to /Approved for posting (via HITL)
- [ ] Or move to /Rejected if not appropriate
```

---

## Keywords Detected

| Keyword | Priority | Response Type |
|---------|----------|---------------|
| **sales** | High | Sales inquiry template |
| **client** | Medium | Client support template |
| **project** | Medium | Business opportunity template |

**Check Interval:** Every 60 seconds

---

## File Structure

```
C:\Users\pc\Desktop\Hackathon_0\
├── watchers/
│   └── twitter_watcher.py              # Main watcher script
├── skills/
│   └── twitter_post_generator/
│       ├── SKILL.md                     # Skill documentation
│       └── twitter_post_generator.py    # Tweet generator
├── session/
│   └── twitter/                         # Twitter browser session
├── Needs_Action/
│   └── twitter_*.md                     # Detected items
├── Plans/
│   └── twitter_draft_*.md               # Generated drafts
├── Pending_Approval/
│   └── twitter_draft_*.md               # Drafts awaiting HITL
└── Logs/
    ├── twitter_post_generator_*.md      # Activity logs
    └── pm2_twitter_watcher_*.log        # PM2 logs
```

---

## Monitoring & Troubleshooting

### Check PM2 Status
```bash
pm2 status
pm2 logs twitter_watcher --lines 50
```

### Session Issues
If login fails, clear the session:
```bash
rmdir /s /q session\twitter
```
Then re-run the watcher to re-authenticate.

### No Files Detected
- Ensure you're logged in to Twitter
- Check that DMs/mentions contain keywords: sales, client, project
- Verify the watcher is running: `pm2 status`

### Browser Close Issue
If closing the browser doesn't stop the watcher:
```bash
# Force stop
pm2 stop twitter_watcher
pm2 delete twitter_watcher

# Restart fresh
pm2 start ecosystem.config.js --only twitter_watcher
```

---

## Quick Start Commands

```bash
# 1. Start Twitter Watcher with PM2
pm2 start ecosystem.config.js --only twitter_watcher

# 2. Run Twitter Post Generator (manual)
python skills\twitter_post_generator\twitter_post_generator.py

# 3. Check logs
pm2 logs twitter_watcher
type Logs\twitter_post_generator_*.md

# 4. Check pending approvals
dir Pending_Approval\twitter_draft_*.md

# 5. Stop watcher (close browser or use command)
pm2 stop twitter_watcher
```

---

## Success Criteria

✓ Watcher running (PM2 status: online)
✓ Session files created in `/session/twitter`
✓ Test DM detected and saved to `/Needs_Action`
✓ Summary generated with intent and sentiment analysis
✓ Draft tweet response created in `/Pending_Approval`
✓ Activity logged in `/Logs/twitter_post_generator_[date].md`
✓ Tweet under 280 characters with emojis and hashtags

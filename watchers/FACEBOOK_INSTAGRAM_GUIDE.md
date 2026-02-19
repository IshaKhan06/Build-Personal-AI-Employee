# Facebook/Instagram Watcher & Social Summary Generator

## Gold Tier Social Media Integration

This guide explains how to set up and run the Facebook/Instagram monitoring system with automated summary generation.

## Components

### 1. Facebook/Instagram Watcher (`watchers/facebook_instagram_watcher.py`)
- Monitors Facebook and Instagram for messages/posts
- Detects keywords: **sales**, **client**, **project**
- Saves detected items as `.md` files in `/Needs_Action`
- Checks every **60 seconds**
- Uses persistent sessions in `/session/facebook` and `/session/instagram`

### 2. Social Summary Generator (`skills/social_summary_generator/`)
- Processes Facebook/Instagram files from `/Needs_Action`
- Generates comprehensive summaries
- Drafts responses for sales leads
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

## Running the Watcher

### Option 1: Direct Python Execution
```bash
# Facebook only
cd C:\Users\pc\Desktop\Hackathon_0
python watchers\facebook_instagram_watcher.py facebook

# Instagram only
python watchers\facebook_instagram_watcher.py instagram

# Both platforms (sequential)
python watchers\facebook_instagram_watcher.py both
```

**To Stop:** Close the browser window or press `Ctrl+C`. The watcher will detect browser closure and stop automatically.

### Option 2: PM2 (Process Manager 2) - Recommended for Production

First, install PM2:
```bash
npm install -g pm2
```

Then start the watcher:
```bash
# Facebook watcher
pm2 start watchers\facebook_instagram_watcher.py --name "fb-watcher" --interpreter python

# Instagram watcher
pm2 start watchers\facebook_instagram_watcher.py --name "ig-watcher" --args "instagram" --interpreter python

# View status
pm2 status

# View logs
pm2 logs fb-watcher
pm2 logs ig-watcher

# Stop watchers
pm2 stop fb-watcher
pm2 stop ig-watcher

# Restart watchers
pm2 restart fb-watcher

# Delete from PM2
pm2 delete fb-watcher
```

**Note:** When using PM2, the process will auto-restart if it crashes. To prevent auto-restart when you close the browser, use the `--no-auto-restart` flag or stop the PM2 process first with `pm2 stop`.

### Option 3: PM2 with Ecosystem Config
Create `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [
    {
      name: "fb-watcher",
      script: "watchers/facebook_instagram_watcher.py",
      interpreter: "python",
      args: "facebook",
      watch: false,
      max_restarts: 5,
      restart_delay: 4000
    },
    {
      name: "ig-watcher",
      script: "watchers/facebook_instagram_watcher.py",
      interpreter: "python",
      args: "instagram",
      watch: false,
      max_restarts: 5,
      restart_delay: 4000
    }
  ]
};
```

Run with:
```bash
pm2 start ecosystem.config.js
```

---

## Running the Social Summary Generator

### Manual Execution
```bash
cd C:\Users\pc\Desktop\Hackathon_0
python skills\social_summary_generator\social_summary_generator.py
```

### With PM2 (Scheduled)
```bash
# Run every 5 minutes
pm2 start skills\social_summary_generator\social_summary_generator.py --name "social-summarizer" --interpreter python --cron "*/5 * * * *"
```

---

## First-Time Setup

### Facebook Login
1. Run the Facebook watcher:
   ```bash
   python watchers\facebook_instagram_watcher.py facebook
   ```
2. A browser window will open
3. Log in to your Facebook account
4. The session will be saved to `/session/facebook`
5. Future runs will use the saved session

### Instagram Login
1. Run the Instagram watcher:
   ```bash
   python watchers\facebook_instagram_watcher.py instagram
   ```
2. A browser window will open
3. Log in to your Instagram account
4. The session will be saved to `/session/instagram`
5. Future runs will use the saved session

---

## Testing Guide

### Test 1: Send a Test Facebook Message

1. **Start the Facebook Watcher:**
   ```bash
   python watchers\facebook_instagram_watcher.py facebook
   ```

2. **Send a test message:**
   - Open Facebook Messenger
   - Send yourself a message or ask a friend to send:
     ```
     Hi! I'm interested in your sales services. Can you help with my project?
     ```

3. **Wait for detection (60 seconds):**
   The watcher checks every 60 seconds. You should see output like:
   ```
   [10:30:45] Checking Facebook...
     Saved: facebook_message_20260219_103045_TestUser_sales.md
     Found 1 matching items
   ```

4. **Verify file created in /Needs_Action:**
   ```bash
   dir Needs_Action\facebook_*.md
   ```

5. **Run Social Summary Generator:**
   ```bash
   python skills\social_summary_generator\social_summary_generator.py
   ```

6. **Check outputs:**
   - Summary and draft in `/Pending_Approval/facebook_draft_*.md`
   - Activity log in `/Logs/social_summary_20260219.md`

### Test 2: Create Manual Test File

If you can't send a real Facebook message, create a test file:

```bash
echo ---
type: facebook_message
platform: facebook
from: "Test Client"
subject: "Facebook Message - sales keyword found"
received: "2026-02-19T10:00:00"
priority: high
status: pending
keyword: sales
---

# Facebook Message Alert

## Summary
New sales-related message received from Test Client on Facebook.

## Original Content
Hi! I'm interested in your sales services for my new project. 
Can you provide pricing information? This is urgent.

## Detection Details
- **Keyword Found:** sales
- **Platform:** facebook
- **Type:** message
- **Detected At:** 2026-02-19 10:00:00
" > Needs_Action\facebook_message_test_sales.md
```

Then run the Social Summary Generator:
```bash
python skills\social_summary_generator\social_summary_generator.py
```

---

## File Structure

```
C:\Users\pc\Desktop\Hackathon_0\
├── watchers/
│   └── facebook_instagram_watcher.py    # Main watcher script
├── skills/
│   └── social_summary_generator/
│       ├── SKILL.md                      # Skill documentation
│       └── social_summary_generator.py   # Summary generator
├── session/
│   ├── facebook/                         # Facebook browser session
│   └── instagram/                        # Instagram browser session
├── Needs_Action/
│   └── facebook_*.md                     # Detected items
├── Plans/
│   └── facebook_draft_*.md               # Generated drafts
├── Pending_Approval/
│   └── facebook_draft_*.md               # Drafts awaiting HITL
└── Logs/
    ├── social_summary_*.md               # Activity logs
    └── cross_domain_*.md                 # Cross-domain summaries
```

---

## Output File Examples

### Detected Item (`/Needs_Action/facebook_message_*.md`)
```markdown
---
type: facebook_message
platform: facebook
from: "John Doe"
subject: "Facebook Message - sales keyword found"
received: "2026-02-19T10:30:45"
priority: high
status: pending
keyword: sales
---

# Facebook Message Alert

## Summary
New sales-related message received from John Doe on Facebook. 
Message preview: 'Hi! I'm interested in your sales services...'
This appears to be a sales inquiry - consider prompt response.

## Original Content
Hi! I'm interested in your sales services for my new project.
Can you provide pricing information?

## Detection Details
- **Keyword Found:** sales
- **Platform:** facebook
- **Type:** message
- **Detected At:** 2026-02-19 10:30:45
```

### Generated Draft (`/Pending_Approval/facebook_draft_*.md`)
```markdown
---
type: social_response_draft
platform: facebook
keyword: sales
status: draft
created: "2026-02-19T10:31:00"
source_file: "Needs_Action/facebook_message_20260219_103045_JohnDoe_sales.md"
requires_hitl: true
generated_by: Social Summary Generator
---

# Social Media Response Draft

## Summary
[Generated summary with intent, sentiment, key points]

## Drafted Response
Hi John Doe,

Thank you for your interest in our services! We'd love to help...

## Action Required
- [ ] Review the summary above
- [ ] Edit the drafted response if needed
- [ ] Move to /Approved for sending (via HITL)
- [ ] Or move to /Rejected if not appropriate
```

---

## Monitoring & Troubleshooting

### Check PM2 Status
```bash
pm2 status
pm2 logs fb-watcher --lines 50
```

### Session Issues
If login fails, clear the session:
```bash
rmdir /s /q session\facebook
rmdir /s /q session\instagram
```
Then re-run the watcher to re-authenticate.

### No Files Detected
- Ensure you're logged in to Facebook/Instagram
- Check that messages contain keywords: sales, client, project
- Verify the watcher is running: `pm2 status`

### Keyword Detection
The watcher detects these keywords (case-insensitive):
- **sales** - Sales inquiries, purchase requests
- **client** - Client communications, support requests
- **project** - Project opportunities, collaborations

---

## Integration with Cross Domain Integrator

The Facebook/Instagram Watcher integrates with the Cross Domain Integrator:

```bash
# Process all Needs_Action including social media
@Cross Domain Integrator process Needs_Action

# Then generate summaries for social items
@Social Summary Generator process
```

Social media items are classified as:
- **Personal** (WhatsApp, Gmail) → HITL routing
- **Business** (Facebook, Instagram, LinkedIn) → Auto LinkedIn Poster or Social Summary Generator

---

## Quick Start Commands

```bash
# 1. Start Facebook Watcher with PM2
pm2 start watchers\facebook_instagram_watcher.py --name "fb-watcher" --interpreter python

# 2. Start Instagram Watcher with PM2
pm2 start watchers\facebook_instagram_watcher.py --name "ig-watcher" --args "instagram" --interpreter python

# 3. Run Social Summary Generator
python skills\social_summary_generator\social_summary_generator.py

# 4. Check logs
pm2 logs fb-watcher
type Logs\social_summary_*.md

# 5. Check pending approvals
dir Pending_Approval\facebook_draft_*.md
```

---

## Success Criteria

✓ Watcher running (PM2 status: online)
✓ Session files created in `/session/facebook` and `/session/instagram`
✓ Test message detected and saved to `/Needs_Action`
✓ Summary generated with intent and sentiment analysis
✓ Draft response created in `/Pending_Approval`
✓ Activity logged in `/Logs/social_summary_[date].md`

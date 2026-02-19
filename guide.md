# Silver/Gold Tier System Guide

This guide explains how to run and monitor all components of the Silver and Gold Tier systems in real-time.

## Table of Contents
1. [System Overview](#system-overview)
2. [Setting Up Watchers](#setting-up-watchers)
3. [Gold Tier: Facebook/Instagram Watcher](#gold-tier-facebookinstagram-watcher)
4. [Gold Tier: Twitter (X) Watcher](#gold-tier-twitter-x-watcher)
5. [Running the Reasoning Loop](#running-the-reasoning-loop)
6. [Running the HITL Approval Handler](#running-the-hitl-approval-handler)
7. [Running the Email MCP Server](#running-the-email-mcp-server)
8. [Real-Time Monitoring Process](#real-time-monitoring-process)
9. [Testing Individual Components](#testing-individual-components)
10. [Monitoring Logs](#monitoring-logs)
11. [Running the Scheduler](#running-the-scheduler)

## System Overview

The Silver Tier system consists of:
- Three real-time watchers (Gmail, WhatsApp, LinkedIn)
- A reasoning loop (Ralph Wiggum pattern)
- An HITL (Human-in-the-Loop) approval system
- An Email MCP server
- A scheduling system

## Prerequisites and Setup

Before running the system, install the required dependencies:

1. **Python dependencies**:
   ```bash
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
   pip install playwright pyyaml
   playwright install chromium
   ```

2. **Node.js dependencies**:
   ```bash
   cd mcp_servers/email-mcp
   npm install
   ```

3. **Gmail API credentials** (optional but required for full Gmail functionality):
   - You need a `credentials.json` file in the root directory with Gmail API credentials
   - This requires setting up a Google Cloud Project with Gmail API enabled

## Setting Up Watchers

### A. Gmail Watcher
1. **Prerequisites**: 
   - You need a properly configured `credentials.json` file in the root directory with Gmail API credentials
   - Install dependencies: `pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client`
   - **Note**: To use the Gmail Watcher, you need to set up Google API credentials with Gmail access enabled. This involves creating a Google Cloud Project, enabling the Gmail API, and downloading OAuth credentials.

2. **Run the Gmail Watcher**:
   ```bash
   cd C:\Users\pc\Desktop\Hackathon_0
   python watchers/gmail_watcher.py
   ```
   
   This will continuously monitor your Gmail for unread important emails with keywords: urgent, invoice, payment, sales every 120 seconds.
   
   **Important**: The first time you run the Gmail Watcher, you need to authenticate once to generate the token. The script will:
   
   a. Open a browser window automatically (or provide an authentication URL)
   b. You sign in to your Google account and authorize the application
   c. The script will automatically generate a token.json file with your refresh token
   d. After this one-time setup, the Gmail Watcher will run continuously
   
   **Note**: Keep your client secret file (client_secret_*.json) in the root directory. The script will automatically find it and use it for authentication.
   
   **If your client secret file is missing**: You need to download it again from Google Cloud Console:
   1. Go to https://console.cloud.google.com/
   2. Select your project
   3. Go to APIs & Services > Credentials
   4. Download the OAuth 2.0 Client ID file
   5. Place it in the root directory: `C:\Users\pc\Desktop\Hackathon_0\`

   **For testing without actual Gmail access**, you can create mock files in the `/Needs_Action` folder that mimic what the Gmail Watcher would create:
   ```bash
   # Create a test file that mimics what the Gmail Watcher would create
   echo "--- 
   type: gmail
   from: 'client@example.com'
   subject: 'Urgent invoice needed'
   received: '2026-02-16T10:00:00'
   priority: high
   status: pending
   ---
   
   # Urgent Invoice Request
   
   Client needs immediate assistance with an invoice." > Needs_Action/test_gmail_invoice.md
   ```

### B. WhatsApp Watcher
1. **Prerequisites**:
   - Install Playwright: `pip install playwright`
   - Install browser: `playwright install chromium`
   - **Note**: The WhatsApp Watcher requires manual login to WhatsApp Web via the browser that opens when you run the script.

2. **Run the WhatsApp Watcher**:
   ```bash
   cd C:\Users\pc\Desktop\Hackathon_0
   python watchers/whatsapp_watcher.py
   ```
   
   Note: You'll need to manually scan the QR code in the browser window to log in to WhatsApp Web. The watcher will then monitor for unread messages with keywords every 30 seconds.
   
   **To stop the watcher**: Press `Ctrl+C` and you should see "WhatsApp Watcher stopped by user".

### C. LinkedIn Watcher
1. **Prerequisites**:
   - Install Playwright: `pip install playwright`
   - Install browser: `playwright install chromium`
   - **Note**: The LinkedIn Watcher requires manual login to LinkedIn via the browser that opens when you run the script.

2. **Run the LinkedIn Watcher**:
   ```bash
   cd C:\Users\pc\Desktop\Hackathon_0
   python watchers\linkedin_watcher.py
   ```
   
   Note: You'll need to manually log in to LinkedIn in the browser window when prompted.
   
   **To stop the watcher**: Press `Ctrl+C` and you should see "LinkedIn Watcher stopped by user".

## Gold Tier: Facebook/Instagram Watcher

### Overview
The Gold Tier adds social media monitoring for Facebook and Instagram with automated summary generation:

- **Facebook/Instagram Watcher**: Monitors messages and posts for keywords (sales, client, project)
- **Social Summary Generator**: Generates summaries and drafts responses for HITL approval

### Prerequisites
```bash
# Install Playwright
pip install playwright

# Install browser
playwright install chromium
```

### Running with PM2 (Recommended)

```bash
# Install PM2 globally
npm install -g pm2

# Start Facebook Watcher
pm2 start ecosystem.config.js --only facebook_instagram_watcher

# Start Instagram Watcher  
pm2 start ecosystem.config.js --only instagram_watcher

# View status
pm2 status

# View logs
pm2 logs facebook_instagram_watcher
pm2 logs instagram_watcher

# Stop watchers
pm2 stop facebook_instagram_watcher
pm2 stop instagram_watcher
```

### Running Directly

```bash
# Facebook only
python watchers\facebook_instagram_watcher.py facebook

# Instagram only
python watchers\facebook_instagram_watcher.py instagram

# Both platforms (sequential)
python watchers\facebook_instagram_watcher.py both
```

**To Stop:** Close the browser window or press `Ctrl+C`.

### Running the Social Summary Generator

```bash
# Manual execution
python skills\social_summary_generator\social_summary_generator.py

# With PM2 (run periodically)
pm2 start ecosystem.config.js --only social_summary_generator
```

### Testing Guide

**Test 1: Send a Test Facebook Message**

1. Start the Facebook Watcher:
   ```bash
   pm2 start ecosystem.config.js --only facebook_instagram_watcher
   ```

2. Send a test message on Facebook Messenger containing keywords:
   ```
   Hi! I'm interested in your sales services. Can you help with my project?
   ```

3. Wait for detection (checks every 60 seconds):
   ```bash
   pm2 logs facebook_instagram_watcher
   ```

4. Verify file created:
   ```bash
   dir Needs_Action\facebook_*.md
   ```

5. Run Social Summary Generator:
   ```bash
   python skills\social_summary_generator\social_summary_generator.py
   ```

6. Check outputs:
   - Draft in `/Pending_Approval/facebook_draft_*.md`
   - Log in `/Logs/social_summary_*.md`

**Test 2: Create Manual Test File**

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
New sales-related message from Test Client on Facebook.

## Original Content
Hi! I'm interested in your sales services for my new project.
Can you provide pricing information?

## Detection Details
- **Keyword Found:** sales
- **Platform:** facebook
- **Type:** message
- **Detected At:** 2026-02-19 10:00:00
" > Needs_Action\facebook_test_sales.md
```

Then run:
```bash
python skills\social_summary_generator\social_summary_generator.py
```

### Output Files

- **Detected Items:** `/Needs_Action/facebook_*.md` or `/Needs_Action/instagram_*.md`
- **Generated Drafts:** `/Pending_Approval/facebook_draft_*.md`
- **Activity Logs:** `/Logs/social_summary_*.md`

### Keywords Detected
- **sales** - Sales inquiries, purchase requests (high priority)
- **client** - Client communications, support requests (medium priority)
- **project** - Project opportunities, collaborations (medium priority)

---

## Gold Tier: Twitter (X) Watcher

### Overview
The Gold Tier adds Twitter monitoring for DMs, mentions, and notifications with automated tweet response generation:

- **Twitter Watcher**: Monitors DMs, tweets, and notifications for keywords (sales, client, project)
- **Twitter Post Generator**: Generates summaries and drafts tweet responses for HITL approval

### Prerequisites
```bash
# Install Playwright
pip install playwright

# Install browser
playwright install chromium
```

### Running with PM2 (Recommended)

```bash
# Start Twitter Watcher
pm2 start ecosystem.config.js --only twitter_watcher

# View status
pm2 status

# View logs
pm2 logs twitter_watcher

# Stop watcher
pm2 stop twitter_watcher
```

### Running Directly

```bash
# Twitter watcher
python watchers\twitter_watcher.py

# Twitter Post Generator (manual)
python skills\twitter_post_generator\twitter_post_generator.py
```

**To Stop:** Close the browser window or press `Ctrl+C`.

### Testing Guide

**Test 1: Send a Test Twitter DM**

1. Start the Twitter Watcher:
   ```bash
   pm2 start ecosystem.config.js --only twitter_watcher
   ```

2. Send a test DM on Twitter containing keywords:
   ```
   Hi! I'm interested in your sales services. Can you help with my project?
   ```

3. Wait for detection (checks every 60 seconds):
   ```bash
   pm2 logs twitter_watcher
   ```

4. Verify file created:
   ```bash
   dir Needs_Action\twitter_*.md
   ```

5. Run Twitter Post Generator:
   ```bash
   python skills\twitter_post_generator\twitter_post_generator.py
   ```

6. Check outputs:
   - Draft in `/Pending_Approval/twitter_draft_*.md`
   - Log in `/Logs/twitter_post_generator_*.md`

**Test 2: Create Manual Test File**

```bash
echo ---
type: twitter_dm
platform: twitter
from: "Test Client"
subject: "Twitter DM - sales keyword found"
received: "2026-02-19T10:00:00"
priority: high
status: pending
keyword: sales
---

# Twitter DM Alert

## Summary
New sales-related DM from Test Client on Twitter.

## Original Content
Hi! I'm interested in your sales services for my new project.
Can you provide pricing information?

## Detection Details
- **Keyword Found:** sales
- **Platform:** twitter
- **Type:** dm
- **Detected At:** 2026-02-19 10:00:00
" > Needs_Action\twitter_test_sales.md
```

Then run:
```bash
python skills\twitter_post_generator\twitter_post_generator.py
```

### Output Files

- **Detected Items:** `/Needs_Action/twitter_*.md` (DMs, mentions, notifications)
- **Generated Drafts:** `/Pending_Approval/twitter_draft_*.md`
- **Activity Logs:** `/Logs/twitter_post_generator_*.md`

### Keywords Detected
- **sales** - Sales inquiries, purchase requests (high priority)
- **client** - Client communications, support requests (medium priority)
- **project** - Project opportunities, collaborations (medium priority)

**Check Interval:** Every 60 seconds

### Tweet Response Features
- Automatically generated responses based on keyword type
- Includes emojis and hashtags
- Character count verification (max 280 characters)
- HITL approval required before posting

---

## Running the Reasoning Loop (Ralph Wiggum)

1. **Run the Claude reasoning loop**:
   ```bash
   cd C:\Users\pc\Desktop\Hackathon_0
   python tools/ralph_loop_runner.py "Process all files in /Needs_Action" --max-iterations 10
   ```
   
   This will process any files in the `/Needs_Action` folder, analyze them, and create plans.

## Running the HITL Approval Handler

1. **Run the HITL Approval Handler**:
   ```bash
   cd C:\Users\pc\Desktop\Hackathon_0
   python skills/hitl_approval_handler/hitl_approval_handler.py check
   ```
   
   Or for continuous monitoring:
   ```bash
   python skills/hitl_approval_handler/hitl_approval_handler.py monitor 30
   ```

## Running the Email MCP Server

1. **Prerequisites**:
   - Navigate to the email-mcp directory: `cd mcp_servers/email-mcp`
   - Install dependencies: `npm install`
   - You need `credentials.json` for Gmail API (for full functionality)

2. **Run the Email MCP Server**:
   ```bash
   cd C:\Users\pc\Desktop\Hackathon_0
   node mcp_servers/email-mcp/index.js
   ```
   
   The server will start on port 3000 and listen for requests to draft and send emails.
   
   **Note**: Without proper Gmail API credentials, the server will run but email sending functionality will be limited.

## Real-Time Monitoring Process

Here's how the complete workflow works in real-time:

1. **Drop a test file** in the `/Needs_Action` folder:
   ```bash
   # Create a test file with keywords that will trigger actions
   echo "--- 
   type: business_lead
   from: 'client@example.com'
   subject: 'Urgent sales inquiry'
   priority: high
   ---
   
   # Urgent Sales Inquiry
   
   Client needs immediate assistance with a sales project." > Needs_Action/test_sales_inquiry.md
   ```

2. **Watchers** continuously monitor external sources (Gmail, WhatsApp, LinkedIn) and add files to `/Needs_Action` when they detect relevant keywords.

3. **Reasoning Loop** periodically processes files in `/Needs_Action`:
   - Analyzes the content
   - Determines if human approval is needed
   - Moves sensitive actions to `/Pending_Approval`

4. **Manual Approval**: Move files from `/Pending_Approval` to `/Approved` when you want to approve them.

5. **HITL Handler** monitors `/Approved` folder and executes the approved actions via MCP servers.

6. **Completed files** are moved to `/Done` folder.

## Stopping the Watchers

To properly stop any of the running watchers:

- **Gmail Watcher**: Press `Ctrl+C` - you should see "Gmail Watcher stopped by user"
- **WhatsApp Watcher**: Press `Ctrl+C` - you should see "WhatsApp Watcher stopped by user"  
- **LinkedIn Watcher**: Press `Ctrl+C` - you should see "LinkedIn Watcher stopped by user"

The watchers will clean up properly and close all browser instances when stopped this way.

## Testing Individual Components

### Test Watchers:
1. Send yourself an email with keywords like "urgent" or "invoice"
2. Send yourself a WhatsApp message with keywords
3. Check if files appear in `/Needs_Action`

### Test Reasoning Loop:
1. Create a test file in `/Needs_Action`
2. Run the Ralph Wiggum loop
3. Check if it gets processed and moved appropriately

### Test Email MCP:
1. Make an HTTP request to draft an email:
   ```bash
   curl -X POST http://localhost:3000/draft \
     -H "Content-Type: application/json" \
     -d '{"to": "recipient@example.com", "subject": "Test", "body": "Test email"}'
   ```

## Testing All Watchers Together

To run all three watchers simultaneously for testing:

### On Windows:
1. **Using the batch script**:
   ```bash
   cd C:\Users\pc\Desktop\Hackathon_0
   test_watchers.bat
   ```

2. **Or using PowerShell**:
   ```bash
   cd C:\Users\pc\Desktop\Hackathon_0
   powershell -ExecutionPolicy Bypass -File test_watchers.ps1
   ```

This will open separate windows for each watcher. You'll need to:
- Scan the QR code for WhatsApp when prompted
- Login to LinkedIn when prompted  
- Complete the Gmail OAuth flow if this is your first time

## Testing the Complete Workflow

To verify the entire system works:

1. Create a test file in `/Needs_Action` with relevant keywords:
   ```bash
   echo "--- 
   type: linkedin_post
   from: 'test@example.com'
   subject: 'Sales opportunity'
   priority: high
   ---
   
   # Sales Opportunity
   
   New business lead for sales project." > Needs_Action/test_full_workflow.md
   ```

2. Run the reasoning loop:
   ```bash
   python tools/ralph_loop_runner.py "Process test file" --max-iterations 1
   ```

3. Move the file from `/Pending_Approval` to `/Approved`:
   ```bash
   move Pending_Approval\test_full_workflow.md Approved\test_full_workflow.md
   ```

4. Run the HITL handler:
   ```bash
   python skills/hitl_approval_handler/hitl_approval_handler.py check
   ```

5. Verify the file appears in `/Done` folder.

## Monitoring Logs

Check the `/Logs` folder for:
- `Silver_Complete.md` - Validation results
- `hitl_YYYY-MM-DD.md` - HITL approval logs
- Daily summary files created by the scheduler

## Running the Scheduler

For Windows, you can set up the PowerShell script to run daily at 8 AM using Task Scheduler as described in the `Schedulers/README.md`.

This system works continuously to monitor, process, and execute tasks based on your defined rules and keywords. Each component runs independently but works together in the complete workflow.
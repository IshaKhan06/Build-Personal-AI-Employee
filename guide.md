# Silver Tier System Guide

This guide explains how to run and monitor all components of the Silver Tier system in real-time.

## Table of Contents
1. [System Overview](#system-overview)
2. [Setting Up Watchers](#setting-up-watchers)
3. [Running the Reasoning Loop](#running-the-reasoning-loop)
4. [Running the HITL Approval Handler](#running-the-hitl-approval-handler)
5. [Running the Email MCP Server](#running-the-email-mcp-server)
6. [Real-Time Monitoring Process](#real-time-monitoring-process)
7. [Testing Individual Components](#testing-individual-components)
8. [Monitoring Logs](#monitoring-logs)
9. [Running the Scheduler](#running-the-scheduler)

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
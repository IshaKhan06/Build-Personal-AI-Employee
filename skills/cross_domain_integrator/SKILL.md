# Cross Domain Integrator Skill (Gold Tier)

## Description
Integrates personal (Gmail, WhatsApp) and business (LinkedIn, Twitter, Facebook) communications in one unified flow. Classifies files from /Needs_Action as personal (email/message) or business (sales/project), routes personal to HITL for human handling, and business to Auto LinkedIn Poster or similar automation. Creates unified summary in /Logs/cross_domain_[date].md with both domains.

## Functionality
- Scans /Needs_Action folder for incoming communications
- Classifies each item as:
  - **Personal**: Gmail emails, WhatsApp messages (keywords: personal, family, friend, invoice, payment, urgent)
  - **Business**: LinkedIn, Twitter, Facebook, sales leads, projects (keywords: sales, client, project, business, lead, opportunity)
- Routes personal items to /Pending_Approval for HITL handling
- Routes business items to Auto LinkedIn Poster for automated processing
- Creates unified cross-domain summary log at /Logs/cross_domain_[date].md
- Integrates with Task Analyzer for initial analysis
- Integrates with HITL Approval Handler for personal item approvals

## Configuration
```json
{
  "name": "Cross Domain Integrator",
  "version": "1.0",
  "tier": "Gold",
  "description": "Unified personal and business communication integrator",
  "author": "AI Employee System",
  "parameters": {
    "action": {
      "type": "string",
      "description": "Action to perform: process, classify, summarize",
      "default": "process"
    },
    "source_folder": {
      "type": "string",
      "description": "Source folder to process",
      "default": "Needs_Action"
    }
  },
  "classification": {
    "personal_keywords": ["gmail", "whatsapp", "personal", "family", "friend", "invoice", "payment", "urgent", "email", "message"],
    "business_keywords": ["linkedin", "twitter", "facebook", "sales", "client", "project", "business", "lead", "opportunity", "partnership"]
  },
  "routing": {
    "personal": "Pending_Approval",
    "business": "Plans"
  },
  "output": {
    "log_folder": "Logs",
    "log_prefix": "cross_domain_"
  }
}
```

## Instructions
1. Scan /Needs_Action for all markdown files
2. For each file, analyze content and metadata
3. Classify as personal or business based on keywords and type
4. Route personal items to /Pending_Approval for HITL
5. Route business items to Auto LinkedIn Poster workflow
6. Create unified summary in /Logs/cross_domain_[date].md
7. Output success message with log path

## Example Usage
```
@Cross Domain Integrator process Needs_Action
```

## Integration
This skill integrates with:
- Task Analyzer skill for initial file analysis
- HITL Approval Handler skill for personal item approvals
- Auto LinkedIn Poster skill for business lead processing
- Gmail Watcher for personal email monitoring
- WhatsApp Watcher for personal message monitoring
- LinkedIn Watcher for business lead monitoring

## Output Format
The unified summary log includes:
- Date and time of processing
- Total items processed
- Personal items count and details
- Business items count and details
- Routing decisions and destinations
- Success/failure status for each item

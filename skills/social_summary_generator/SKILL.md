# Social Summary Generator Skill (Gold Tier)

## Description
Processes Facebook/Instagram files from /Needs_Action, generates comprehensive summaries, drafts responses for sales leads, and routes to HITL for approval. Integrates with the Facebook/Instagram Watcher for seamless social media monitoring.

## Functionality
- Scans /Needs_Action for Facebook/Instagram markdown files
- Parses YAML frontmatter to extract metadata (platform, sender, keyword, priority)
- Generates comprehensive summaries including:
  - Item details (platform, type, sender, keyword)
  - Content analysis with intent detection
  - Sentiment analysis (positive/negative/neutral/urgent)
  - Key points extraction
  - Original content preview
- Drafts context-aware responses based on keyword type:
  - Sales inquiries → Sales response template
  - Client communications → Client support template
  - Project opportunities → Business proposal template
  - General inquiries → Generic response template
- Saves drafts to /Plans with YAML frontmatter
- Moves drafts to /Pending_Approval for HITL review
- Logs all activity to /Logs/social_summary_[date].md

## Configuration
```json
{
  "name": "Social Summary Generator",
  "version": "1.0",
  "tier": "Gold",
  "description": "Generates summaries and drafts for social media communications",
  "author": "AI Employee System",
  "parameters": {
    "action": {
      "type": "string",
      "description": "Action to perform: process, summarize, draft",
      "default": "process"
    }
  },
  "keywords": {
    "sales": ["sales", "buy", "purchase", "order", "pricing", "quote"],
    "client": ["client", "customer", "account", "service"],
    "project": ["project", "collaboration", "partnership", "opportunity"]
  },
  "output": {
    "drafts_folder": "Plans",
    "approval_folder": "Pending_Approval",
    "logs_folder": "Logs"
  }
}
```

## Instructions
1. Ensure Facebook/Instagram Watcher has created files in /Needs_Action
2. Run the Social Summary Generator
3. Review generated summaries and drafts in /Pending_Approval
4. Approve drafts by moving to /Approved (HITL will execute)
5. Check logs in /Logs/social_summary_[date].md

## Example Usage
```
@Social Summary Generator process
python skills/social_summary_generator/social_summary_generator.py
```

## Integration
This skill integrates with:
- Facebook/Instagram Watcher (watchers/facebook_instagram_watcher.py)
- HITL Approval Handler skill for draft approvals
- Cross Domain Integrator for unified communication handling

## Output Format
Drafts include:
- YAML frontmatter with metadata
- Generated summary section
- Drafted response section
- Action checklist for HITL review

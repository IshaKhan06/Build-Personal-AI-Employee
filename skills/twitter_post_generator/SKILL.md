# Twitter Post Generator Skill (Gold Tier)

## Description
Processes Twitter (X) files from /Needs_Action, generates comprehensive summaries, drafts tweet responses for sales leads, and routes to HITL for approval. Integrates with the Twitter Watcher for seamless social media monitoring.

## Functionality
- Scans /Needs_Action for Twitter markdown files (DMs, mentions, notifications)
- Parses YAML frontmatter to extract metadata (platform, sender, keyword, priority)
- Generates comprehensive summaries including:
  - Item details (platform, type, sender, keyword)
  - Content analysis with intent detection
  - Sentiment analysis (positive/negative/neutral/urgent)
  - Key points extraction
  - Original content preview
- Drafts context-aware tweet responses based on keyword type:
  - Sales inquiries → Sales response template (with emojis, hashtags)
  - Client communications → Client support template
  - Project opportunities → Business proposal template
  - General inquiries → Generic response template
- Ensures tweets are under 280 characters
- Saves drafts to /Plans with YAML frontmatter
- Moves drafts to /Pending_Approval for HITL review
- Logs all activity to /Logs/twitter_post_generator_[date].md

## Configuration
```json
{
  "name": "Twitter Post Generator",
  "version": "1.0",
  "tier": "Gold",
  "description": "Generates summaries and draft tweets for Twitter communications",
  "author": "AI Employee System",
  "parameters": {
    "action": {
      "type": "string",
      "description": "Action to perform: process, summarize, draft",
      "default": "process"
    }
  },
  "keywords": {
    "sales": ["sales", "buy", "purchase", "order", "pricing", "quote", "discount"],
    "client": ["client", "customer", "account", "service", "support"],
    "project": ["project", "collaboration", "partnership", "opportunity", "deal"]
  },
  "output": {
    "drafts_folder": "Plans",
    "approval_folder": "Pending_Approval",
    "logs_folder": "Logs"
  },
  "twitter_limits": {
    "max_characters": 280,
    "includes_hashtags": true,
    "includes_emojis": true
  }
}
```

## Instructions
1. Ensure Twitter Watcher has created files in /Needs_Action
2. Run the Twitter Post Generator
3. Review generated summaries and drafts in /Pending_Approval
4. Approve drafts by moving to /Approved (HITL will execute)
5. Check logs in /Logs/twitter_post_generator_[date].md

## Example Usage
```
@Twitter Post Generator process
python skills\twitter_post_generator\twitter_post_generator.py
```

## Integration
This skill integrates with:
- Twitter Watcher (watchers/twitter_watcher.py)
- HITL Approval Handler skill for draft approvals
- Cross Domain Integrator for unified communication handling

## Output Format
Drafts include:
- YAML frontmatter with metadata
- Generated summary section
- Drafted tweet response section (with character count)
- Action checklist for HITL review

## Tweet Response Templates

### Sales Inquiry
```
Hi @{sender}! Thanks for your interest in our services! 🚀

We'd love to help you with your needs. Could you DM us more details about:
1. What you're looking for
2. Your timeline
3. Budget range

We'll get back to you ASAP with a customized solution! 💼

#Sales #CustomerService
```

### Client Communication
```
Hi @{sender}! Thanks for reaching out! 🙌

We appreciate you being a valued client. We'd be happy to assist you!

Could you share a bit more about your request so we can help you better?

Looking forward to your response! 📩

#ClientSupport #CustomerCare
```

### Project Opportunity
```
Hi @{sender}! This sounds like an exciting opportunity! 🎯

We'd love to learn more about:
1. Project scope
2. Expected deliverables
3. Timeline & milestones
4. Budget

Would you be available for a quick call this week? 📞

#BusinessOpportunity #Partnership
```

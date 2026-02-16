# Auto LinkedIn Poster Skill

This skill automatically scans for sales and business leads in the Needs_Action folder and drafts LinkedIn posts based on them.

## Functionality
- Scans /Needs_Action for sales/business lead messages (keywords: sales, client, project)
- Drafts LinkedIn post: "Excited to offer [service] for [benefit]! DM for more."
- Saves draft to /Plans/linkedin_post_[date].md with YAML: type, content, status
- Requires HITL: Moves to /Pending_Approval for approval
- References Company_Handbook.md for polite language

## Example Usage
```
@Auto LinkedIn Poster process sales lead
```

## Configuration
- Check interval: Manual trigger
- Keywords: sales, client, project
- Output folder: /Plans
- Approval folder: /Pending_Approval
"""
Twitter Post Generator Skill (Gold Tier - Error Recovery + Audit Logging)
Processes Twitter files from /Needs_Action, generates summaries,
drafts tweets/responses for sales leads, and routes to HITL for approval.
Features: Try-except error handling, error logging, manual action drafts, audit logging
"""

import os
import re
import yaml
import sys
from datetime import datetime
from pathlib import Path

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils'))
from error_recovery import ErrorRecovery
from audit_logger import AuditLogger


class TwitterPostGenerator:
    """Gold Tier skill for generating Twitter summaries and draft tweets."""

    def __init__(self):
        """Initialize the Twitter Post Generator."""
        self.needs_action_dir = Path("Needs_Action")
        self.plans_dir = Path("Plans")
        self.pending_approval_dir = Path("Pending_Approval")
        self.logs_dir = Path("Logs")
        self.errors_dir = Path("Errors")

        # Ensure directories exist
        self.plans_dir.mkdir(exist_ok=True)
        self.pending_approval_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.errors_dir.mkdir(exist_ok=True)

        # Initialize error recovery utility
        self.error_recovery = ErrorRecovery(Path("."))
        self.skill_name = "twitter_post_generator"
        
        # Initialize audit logger
        self.audit_logger = AuditLogger(Path("."))

        # Keywords that indicate sales leads
        self.sales_keywords = ['sales', 'buy', 'purchase', 'order', 'pricing', 'quote', 'discount']
        self.client_keywords = ['client', 'customer', 'account', 'service', 'support']
        self.project_keywords = ['project', 'collaboration', 'partnership', 'opportunity', 'deal']

    def find_twitter_files(self):
        """
        Find Twitter files in /Needs_Action.

        Returns:
            list: List of file paths to process
        """
        twitter_files = []

        if not self.needs_action_dir.exists():
            print(f"Warning: {self.needs_action_dir} directory does not exist.")
            return twitter_files

        for file_path in self.needs_action_dir.glob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if it's a Twitter file
                if 'platform: twitter' in content.lower():
                    twitter_files.append(file_path)
                elif 'type: twitter_' in content.lower():
                    twitter_files.append(file_path)

            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        return twitter_files

    def parse_frontmatter(self, content):
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown content with YAML frontmatter

        Returns:
            dict: Parsed metadata
        """
        if not content.startswith('---'):
            return {}

        try:
            parts = content.split('---', 2)
            if len(parts) >= 2:
                yaml_content = parts[1].strip()
                return yaml.safe_load(yaml_content) or {}
        except Exception as e:
            print(f"Error parsing frontmatter: {e}")

        return {}

    def generate_summary(self, file_path, metadata, content):
        """
        Generate a comprehensive summary of the Twitter item.

        Args:
            file_path: Path to the file
            metadata: Parsed YAML frontmatter
            content: Full file content

        Returns:
            str: Generated summary
        """
        platform = metadata.get('platform', 'twitter')
        item_type = metadata.get('type', 'unknown')
        sender = metadata.get('from', 'Unknown')
        keyword = metadata.get('keyword', 'unknown')
        priority = metadata.get('priority', 'low')
        received = metadata.get('received', 'unknown')

        # Extract body content (after frontmatter)
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()

        # Extract original content from the file
        original_content = ""
        if "## Original Content" in body:
            original_content = body.split("## Original Content")[1].split("##")[0].strip()

        # Generate summary based on type and keyword
        summary_parts = []

        # Header
        summary_parts.append(f"# Twitter Summary")
        summary_parts.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_parts.append(f"\n---\n")

        # Item details
        summary_parts.append(f"## Item Details")
        summary_parts.append(f"- **Platform:** Twitter (X)")
        summary_parts.append(f"- **Type:** {item_type.replace('_', ' ').title()}")
        summary_parts.append(f"- **From:** @{sender}")
        summary_parts.append(f"- **Keyword Detected:** {keyword}")
        summary_parts.append(f"- **Priority:** {priority.upper()}")
        summary_parts.append(f"- **Received:** {received}")
        summary_parts.append(f"- **Source File:** {file_path.name}")

        # Content analysis
        summary_parts.append(f"\n---\n")
        summary_parts.append(f"## Content Analysis")

        # Determine intent based on keyword
        intent = self.determine_intent(keyword, original_content)
        summary_parts.append(f"\n**Detected Intent:** {intent}")

        # Sentiment analysis (simple keyword-based)
        sentiment = self.analyze_sentiment(original_content)
        summary_parts.append(f"\n**Sentiment:** {sentiment}")

        # Key points extraction
        key_points = self.extract_key_points(original_content)
        if key_points:
            summary_parts.append(f"\n**Key Points:**")
            for point in key_points:
                summary_parts.append(f"- {point}")

        # Original content preview
        summary_parts.append(f"\n---\n")
        summary_parts.append(f"## Original Content Preview")
        preview = original_content[:500] if len(original_content) > 500 else original_content
        summary_parts.append(f"\n{preview}")
        if len(original_content) > 500:
            summary_parts.append(f"\n\n*... ({len(original_content) - 500} more characters)*")

        return "\n".join(summary_parts)

    def determine_intent(self, keyword, content):
        """
        Determine the intent of the message/tweet.

        Args:
            keyword: Detected keyword
            content: Message content

        Returns:
            str: Intent description
        """
        content_lower = content.lower()

        if keyword == 'sales' or any(kw in content_lower for kw in self.sales_keywords):
            if 'help' in content_lower or 'need' in content_lower:
                return "Sales Inquiry - Customer needs assistance"
            elif 'price' in content_lower or 'cost' in content_lower:
                return "Sales Inquiry - Pricing request"
            elif 'buy' in content_lower or 'purchase' in content_lower:
                return "Sales Inquiry - Purchase intent"
            else:
                return "Sales Inquiry - General interest"

        elif keyword == 'client' or any(kw in content_lower for kw in self.client_keywords):
            if 'issue' in content_lower or 'problem' in content_lower:
                return "Client Support - Issue resolution needed"
            elif 'question' in content_lower or 'ask' in content_lower:
                return "Client Support - Information request"
            else:
                return "Client Communication - General inquiry"

        elif keyword == 'project' or any(kw in content_lower for kw in self.project_keywords):
            if 'collaborate' in content_lower or 'partner' in content_lower:
                return "Business Opportunity - Partnership proposal"
            elif 'deadline' in content_lower or 'timeline' in content_lower:
                return "Project Update - Timeline discussion"
            else:
                return "Business Opportunity - Project inquiry"

        return "General Inquiry - Review needed"

    def analyze_sentiment(self, content):
        """
        Simple sentiment analysis based on keywords.

        Args:
            content: Message content

        Returns:
            str: Sentiment label
        """
        content_lower = content.lower()

        positive_words = ['great', 'excellent', 'amazing', 'love', 'happy', 'excited', 'wonderful', 'fantastic', 'good', 'thanks', 'thank', 'awesome']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'angry', 'upset', 'disappointed', 'worst', 'problem', 'issue', 'wrong', 'frustrated']
        urgent_words = ['urgent', 'asap', 'immediately', 'emergency', 'critical', 'important', 'need now', 'help']

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        urgent_count = sum(1 for word in urgent_words if word in content_lower)

        if urgent_count > 0:
            return "Urgent - Immediate attention required"
        elif positive_count > negative_count:
            return "Positive - Favorable tone"
        elif negative_count > positive_count:
            return "Negative - Concerns expressed"
        else:
            return "Neutral - Standard communication"

    def extract_key_points(self, content):
        """
        Extract key points from the content.

        Args:
            content: Message content

        Returns:
            list: Key points
        """
        key_points = []

        # Look for sentences with important indicators
        sentences = re.split(r'[.!?]+', content)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_lower = sentence.lower()

            # Check for action items
            if any(kw in sentence_lower for kw in ['need to', 'should', 'must', 'please', 'can you', 'could you', 'dm me', 'contact']):
                key_points.append(f"Action: {sentence[:100]}")

            # Check for questions
            if '?' in sentence:
                key_points.append(f"Question: {sentence[:100]}")

            # Check for deadlines/timeline
            if any(kw in sentence_lower for kw in ['deadline', 'by', 'before', 'when', 'timeline', 'schedule', 'asap']):
                key_points.append(f"Timeline: {sentence[:100]}")

        return key_points[:5]  # Limit to 5 key points

    def draft_tweet_response(self, metadata, content):
        """
        Draft a tweet response based on the Twitter item.

        Args:
            metadata: Parsed YAML frontmatter
            content: Full file content

        Returns:
            str: Drafted tweet response (max 280 chars)
        """
        sender = metadata.get('from', 'Unknown')
        keyword = metadata.get('keyword', 'unknown')
        item_type = metadata.get('type', 'unknown')

        # Extract original content
        original_content = ""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                body = parts[2].strip()
                if "## Original Content" in body:
                    original_content = body.split("## Original Content")[1].split("##")[0].strip()

        # Generate response based on keyword type
        if keyword in self.sales_keywords or keyword == 'sales':
            response = self.draft_sales_tweet(sender, original_content)
        elif keyword in self.client_keywords or keyword == 'client':
            response = self.draft_client_tweet(sender, original_content)
        elif keyword in self.project_keywords or keyword == 'project':
            response = self.draft_project_tweet(sender, original_content)
        else:
            response = self.draft_general_tweet(sender, original_content, item_type)

        return response

    def draft_sales_tweet(self, sender, content):
        """Draft a tweet response for sales inquiries."""
        return f"""Hi @{sender}! Thanks for your interest in our services! 🚀

We'd love to help you with your needs. Could you DM us more details about:
1. What you're looking for
2. Your timeline
3. Budget range

We'll get back to you ASAP with a customized solution! 💼

#Sales #CustomerService"""

    def draft_client_tweet(self, sender, content):
        """Draft a tweet response for client communications."""
        return f"""Hi @{sender}! Thanks for reaching out! 🙌

We appreciate you being a valued client. We'd be happy to assist you!

Could you share a bit more about your request so we can help you better?

Looking forward to your response! 📩

#ClientSupport #CustomerCare"""

    def draft_project_tweet(self, sender, content):
        """Draft a tweet response for project inquiries."""
        return f"""Hi @{sender}! This sounds like an exciting opportunity! 🎯

We'd love to learn more about:
1. Project scope
2. Expected deliverables
3. Timeline & milestones
4. Budget

Would you be available for a quick call this week? 📞

#BusinessOpportunity #Partnership"""

    def draft_general_tweet(self, sender, content, item_type):
        """Draft a general tweet response."""
        if item_type == 'mention':
            return f"""Hi @{sender}! Thanks for the mention! 🙏

We've received your message and will get back to you shortly. If this is urgent, feel free to DM us!

#CustomerService #HereToHelp"""
        else:
            return f"""Hi @{sender}! Thanks for your message on Twitter! 📬

We've received your inquiry and will respond soon. If urgent, please DM us directly.

#Support #HereToHelp"""

    def save_draft(self, file_path, summary, draft_response, metadata):
        """
        Save the summary and draft to /Plans and move to /Pending_Approval.

        Args:
            file_path: Original file path
            summary: Generated summary
            draft_response: Drafted tweet response
            metadata: Original metadata

        Returns:
            str: Path to the saved draft
        """
        platform = metadata.get('platform', 'twitter')
        keyword = metadata.get('keyword', 'general')

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"twitter_draft_{timestamp}.md"
        draft_path = self.plans_dir / filename

        # Create full draft content
        draft_content = f"""---
type: twitter_response_draft
platform: twitter
keyword: {keyword}
status: draft
created: {datetime.now().isoformat()}
source_file: {file_path}
requires_hitl: true
generated_by: Twitter Post Generator
---

# Twitter Response Draft

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Platform:** Twitter (X)
**Keyword:** {keyword}

---

## Summary

{summary}

---

## Drafted Tweet/Response

```
{draft_response}
```

**Character Count:** {len(draft_response)} / 280

---

## Action Required

- [ ] Review the summary above
- [ ] Edit the drafted response if needed (keep under 280 characters)
- [ ] Move to /Approved for posting (via HITL)
- [ ] Or move to /Rejected if not appropriate

---
*Generated by Twitter Post Generator (Gold Tier)*
*Requires HITL approval before posting*
"""

        # Write the draft
        with open(draft_path, 'w', encoding='utf-8') as f:
            f.write(draft_content)

        # Move to Pending_Approval
        approval_path = self.pending_approval_dir / filename
        os.rename(draft_path, approval_path)

        return str(approval_path)

    def log_activity(self, processed_files, drafts_created):
        """
        Log the activity to /Logs/twitter_post_generator_[date].md.

        Args:
            processed_files: List of processed file paths
            drafts_created: List of created draft paths
        """
        date_str = datetime.now().strftime("%Y%m%d")
        log_path = self.logs_dir / f"twitter_post_generator_{date_str}.md"

        # Read existing log or create new
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        else:
            existing_content = f"# Twitter Post Generator Log\n\n---\n"

        # Append new entry
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_entry = f"""
## {timestamp}

**Files Processed:** {len(processed_files)}
**Drafts Created:** {len(drafts_created)}

### Processed Files
"""
        for file_path in processed_files:
            new_entry += f"- {file_path}\n"

        new_entry += "\n### Drafts Created\n"
        for draft_path in drafts_created:
            new_entry += f"- {draft_path}\n"

        new_entry += "\n---\n"

        # Write updated log
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(existing_content + new_entry)

        return str(log_path)

    def process_all(self):
        """
        Process all Twitter files in /Needs_Action.

        Returns:
            dict: Processing results
        """
        print("="*60)
        print("TWITTER POST GENERATOR")
        print("="*60)
        print(f"Error recovery: Enabled")
        print(f"Audit logging: Enabled (logs to /Logs/audit_*.json)")

        # Find Twitter files
        twitter_files = self.find_twitter_files()

        if not twitter_files:
            print("\nNo Twitter files found in /Needs_Action")
            self.audit_logger.log(
                action_type="skill_execution",
                target=self.skill_name,
                parameters={"files_found": 0},
                result="success",
                message="No Twitter files to process"
            )
            return {'processed': 0, 'drafts': [], 'log': None}

        print(f"\nFound {len(twitter_files)} Twitter file(s) to process")
        
        # Log start
        self.audit_logger.log_start(
            action_type="skill_execution",
            target=self.skill_name,
            parameters={"files_to_process": len(twitter_files)},
            message=f"Starting processing of {len(twitter_files)} Twitter files"
        )

        processed_files = []
        drafts_created = []
        errors = []

        for file_path in twitter_files:
            print(f"\nProcessing: {file_path.name}")

            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse frontmatter
                metadata = self.parse_frontmatter(content)

                # Generate summary
                summary = self.generate_summary(file_path, metadata, content)

                # Draft tweet response
                draft_response = self.draft_tweet_response(metadata, content)

                # Save draft and move to approval
                approval_path = self.save_draft(file_path, summary, draft_response, metadata)

                processed_files.append(str(file_path))
                drafts_created.append(approval_path)

                print(f"  -> Summary generated")
                print(f"  -> Draft created: {approval_path}")
                
                # Log file processed
                self.audit_logger.log(
                    action_type="file_processed",
                    target=str(file_path),
                    actor=self.skill_name,
                    parameters={
                        "keyword": metadata.get('keyword', 'unknown'),
                        "platform": "twitter"
                    },
                    result="success",
                    message="Created tweet draft",
                    metadata={"draft_path": str(approval_path)}
                )

            except Exception as e:
                error_msg = f"  -> Error: {type(e).__name__}: {e}"
                print(error_msg)
                errors.append({'file': str(file_path), 'error': e})
                
                # Log error
                self.audit_logger.log_error(
                    action_type="file_processing",
                    target=str(file_path),
                    error_message=error_msg,
                    actor=self.skill_name
                )

        # Log activity
        log_path = self.log_activity(processed_files, drafts_created, errors)
        
        # Log completion
        self.audit_logger.log_end(
            action_type="skill_execution",
            target=self.skill_name,
            result="success" if len(errors) == 0 else "partial_success",
            actor=self.skill_name,
            message=f"Processed {len(processed_files)} files, created {len(drafts_created)} drafts",
            metadata={
                "files_processed": len(processed_files),
                "drafts_created": len(drafts_created),
                "errors": len(errors)
            }
        )

        # Print summary
        print("\n" + "="*60)
        print("PROCESSING COMPLETE")
        print("="*60)
        print(f"Files Processed: {len(processed_files)}")
        print(f"Drafts Created: {len(drafts_created)}")
        print(f"Errors: {len(errors)}")
        print(f"Log File: {log_path}")

        return {
            'processed': len(processed_files),
            'drafts': drafts_created,
            'log': log_path,
            'errors': errors
        }


def main():
    """Main entry point."""
    generator = TwitterPostGenerator()
    results = generator.process_all()

    if results['processed'] > 0:
        print(f"\n[SUCCESS] Twitter Post Generator completed.")
        print(f"  Drafts moved to /Pending_Approval for HITL review")
        return 0
    else:
        print("\n[INFO] No files processed.")
        return 0


if __name__ == "__main__":
    exit(main())

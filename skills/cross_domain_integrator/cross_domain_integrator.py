"""
Cross Domain Integrator Skill (Gold Tier)
Integrates personal (Gmail, WhatsApp) and business (LinkedIn, Twitter, Facebook) communications
in one unified flow.
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path


class CrossDomainIntegrator:
    """Gold Tier skill for integrating personal and business communications."""

    def __init__(self, config_path=None):
        """Initialize the Cross Domain Integrator."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.personal_keywords = self.config['classification']['personal_keywords']
        self.business_keywords = self.config['classification']['business_keywords']
        self.personal_route = self.config['routing']['personal']
        self.business_route = self.config['routing']['business']
        self.log_folder = Path(self.config['output']['log_folder'])
        self.log_prefix = self.config['output']['log_prefix']

        # Ensure log folder exists
        self.log_folder.mkdir(exist_ok=True)

    def classify_item(self, content, filename):
        """
        Classify an item as personal or business based on content and filename.

        Args:
            content: The file content to analyze
            filename: The filename for additional context

        Returns:
            tuple: (classification, confidence, matched_keywords)
        """
        content_lower = content.lower()
        filename_lower = filename.lower()
        combined_text = f"{content_lower} {filename_lower}"

        personal_matches = []
        business_matches = []

        # Check for personal keywords
        for keyword in self.personal_keywords:
            if keyword in combined_text:
                personal_matches.append(keyword)

        # Check for business keywords
        for keyword in self.business_keywords:
            if keyword in combined_text:
                business_matches.append(keyword)

        # Check YAML frontmatter for type hints
        try:
            if content.startswith('---'):
                yaml_content = content.split('---')[1]
                metadata = yaml.safe_load(yaml_content)
                if metadata:
                    item_type = metadata.get('type', '').lower()
                    if item_type in ['gmail', 'whatsapp', 'personal', 'email']:
                        personal_matches.append(f"type:{item_type}")
                    elif item_type in ['linkedin', 'twitter', 'facebook', 'business_lead', 'sales']:
                        business_matches.append(f"type:{item_type}")
        except (yaml.YAMLError, IndexError):
            pass

        # Determine classification based on matches
        personal_score = len(personal_matches)
        business_score = len(business_matches)

        if personal_score > business_score:
            return ('personal', personal_score / max(len(self.personal_keywords), 1), personal_matches)
        elif business_score > personal_score:
            return ('business', business_score / max(len(self.business_keywords), 1), business_matches)
        else:
            # Default to business if tied
            return ('business', 0.5, business_matches if business_matches else personal_matches)

    def route_item(self, file_path, classification, confidence, matched_keywords):
        """
        Route an item to the appropriate destination folder.

        Args:
            file_path: Path to the file to route
            classification: 'personal' or 'business'
            confidence: Confidence score of classification
            matched_keywords: List of matched keywords

        Returns:
            dict: Routing result with destination and status
        """
        filename = Path(file_path).name
        source_dir = Path(file_path).parent

        if classification == 'personal':
            # Route to Pending_Approval for HITL
            dest_dir = Path(self.personal_route)
            dest_dir.mkdir(exist_ok=True)
            dest_path = dest_dir / filename

            # Add routing metadata
            self._add_routing_metadata(file_path, classification, confidence, matched_keywords)

        else:  # business
            # Route to Plans for Auto LinkedIn Poster
            dest_dir = Path(self.business_route)
            dest_dir.mkdir(exist_ok=True)
            dest_path = dest_dir / f"business_{filename}"

            # Add routing metadata
            self._add_routing_metadata(file_path, classification, confidence, matched_keywords)

        # Move the file
        try:
            os.rename(file_path, dest_path)
            return {
                'source': str(file_path),
                'destination': str(dest_path),
                'classification': classification,
                'confidence': confidence,
                'status': 'success',
                'matched_keywords': matched_keywords
            }
        except Exception as e:
            return {
                'source': str(file_path),
                'destination': str(dest_path),
                'classification': classification,
                'confidence': confidence,
                'status': 'failed',
                'error': str(e),
                'matched_keywords': matched_keywords
            }

    def _add_routing_metadata(self, file_path, classification, confidence, matched_keywords):
        """Add routing metadata to the file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse existing frontmatter or create new
            metadata = {
                'classified_by': 'Cross Domain Integrator',
                'classification': classification,
                'confidence': confidence,
                'matched_keywords': matched_keywords,
                'routed_at': datetime.now().isoformat(),
                'domain': 'personal' if classification == 'personal' else 'business'
            }

            if content.startswith('---'):
                # Update existing frontmatter
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    existing_yaml = parts[1]
                    existing_metadata = yaml.safe_load(existing_yaml)
                    if existing_metadata:
                        existing_metadata.update(metadata)
                        new_yaml = yaml.dump(existing_metadata, default_flow_style=False)
                        content = f"---\n{new_yaml}---\n{parts[2]}"
            else:
                # Add new frontmatter
                yaml_content = yaml.dump(metadata, default_flow_style=False)
                content = f"---\n{yaml_content}---\n\n{content}"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            print(f"Warning: Could not add metadata to {file_path}: {e}")

    def create_unified_summary(self, results):
        """
        Create a unified summary log of all processed items.

        Args:
            results: List of routing results

        Returns:
            str: Path to the created summary log
        """
        date_str = datetime.now().strftime("%Y%m%d")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_filename = f"{self.log_prefix}{date_str}.md"
        log_path = self.log_folder / log_filename

        # Separate results by classification
        personal_items = [r for r in results if r.get('classification') == 'personal']
        business_items = [r for r in results if r.get('classification') == 'business']
        failed_items = [r for r in results if r.get('status') == 'failed']

        # Build the summary content
        summary = f"""# Cross Domain Integration Summary

**Generated:** {timestamp}

## Overview
- **Total Items Processed:** {len(results)}
- **Personal Items:** {len(personal_items)}
- **Business Items:** {len(business_items)}
- **Failed Items:** {len(failed_items)}

---

## Personal Domain (HITL Routing)
**Destination:** /{self.personal_route}/

"""

        if personal_items:
            for i, item in enumerate(personal_items, 1):
                summary += f"""### {i}. {Path(item['source']).name}
- **Classification:** Personal
- **Confidence:** {item['confidence']:.2f}
- **Matched Keywords:** {', '.join(item.get('matched_keywords', []))}
- **Status:** {item['status']}
- **Destination:** `{item['destination']}`

"""
        else:
            summary += "*No personal items processed.*\n\n"

        summary += f"""---

## Business Domain (Auto LinkedIn Poster Routing)
**Destination:** /{self.business_route}/

"""

        if business_items:
            for i, item in enumerate(business_items, 1):
                summary += f"""### {i}. {Path(item['source']).name}
- **Classification:** Business
- **Confidence:** {item['confidence']:.2f}
- **Matched Keywords:** {', '.join(item.get('matched_keywords', []))}
- **Status:** {item['status']}
- **Destination:** `{item['destination']}`

"""
        else:
            summary += "*No business items processed.*\n\n"

        if failed_items:
            summary += """---

## Failed Items

"""
            for i, item in enumerate(failed_items, 1):
                summary += f"""### {i}. {Path(item['source']).name}
- **Classification:** {item['classification']}
- **Error:** {item.get('error', 'Unknown error')}

"""

        summary += """---

## Integration Notes
- Personal items routed to HITL Approval Handler for human review
- Business items routed to Auto LinkedIn Poster for automated processing
- Summary generated by Cross Domain Integrator (Gold Tier)
"""

        # Write the summary
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        return str(log_path)

    def process_needs_action(self, source_folder="Needs_Action"):
        """
        Process all files in the source folder.

        Args:
            source_folder: Folder to process (default: Needs_Action)

        Returns:
            str: Path to the unified summary log
        """
        source_dir = Path(source_folder)

        if not source_dir.exists():
            print(f"Error: Source folder '{source_folder}' does not exist.")
            return None

        # Find all markdown files
        files = list(source_dir.glob("*.md"))

        if not files:
            print(f"No markdown files found in {source_folder}")
            # Still create an empty summary
            return self.create_unified_summary([])

        print(f"Cross Domain Integrator: Found {len(files)} files to process in {source_folder}")

        results = []

        for file_path in files:
            print(f"Processing: {file_path.name}")

            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                results.append({
                    'source': str(file_path),
                    'destination': None,
                    'classification': 'unknown',
                    'confidence': 0,
                    'status': 'failed',
                    'error': f"Could not read file: {e}",
                    'matched_keywords': []
                })
                continue

            # Classify the item
            classification, confidence, matched_keywords = self.classify_item(content, file_path.name)
            print(f"  -> Classified as: {classification} (confidence: {confidence:.2f})")
            print(f"  -> Matched keywords: {', '.join(matched_keywords) if matched_keywords else 'none'}")

            # Route the item
            result = self.route_item(str(file_path), classification, confidence, matched_keywords)
            results.append(result)

            if result['status'] == 'success':
                print(f"  -> Routed to: {result['destination']}")
            else:
                print(f"  -> Failed: {result.get('error', 'Unknown error')}")

        # Create unified summary
        log_path = self.create_unified_summary(results)
        print(f"\nUnified summary created: {log_path}")

        # Print summary
        personal_count = sum(1 for r in results if r.get('classification') == 'personal')
        business_count = sum(1 for r in results if r.get('classification') == 'business')
        failed_count = sum(1 for r in results if r.get('status') == 'failed')

        print(f"\n=== Cross Domain Integration Complete ===")
        print(f"Total: {len(results)} | Personal: {personal_count} | Business: {business_count} | Failed: {failed_count}")
        print(f"Log path: {log_path}")

        return log_path


def main():
    """Main entry point for the Cross Domain Integrator skill."""
    import sys

    integrator = CrossDomainIntegrator()

    # Default to processing Needs_Action folder
    source_folder = "Needs_Action"

    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action in ['process', 'classify', 'summarize']:
            if len(sys.argv) > 2:
                source_folder = sys.argv[2]
        else:
            source_folder = action

    log_path = integrator.process_needs_action(source_folder)

    if log_path:
        print(f"\n[SUCCESS] Cross Domain Integration complete.")
        print(f"  Log file: {log_path}")
        return 0
    else:
        print("\n[FAILED] Cross Domain Integration failed.")
        return 1


if __name__ == "__main__":
    exit(main())

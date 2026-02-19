"""
Weekly Audit Briefer Skill (Gold Tier - Error Recovery + Audit Logging)
Runs weekly to audit tasks, revenue, and bottlenecks.
Generates CEO Briefing with executive summary.
Integrates with scheduler for weekly execution.
Features: Audit log summary in CEO briefing, 90-day log retention
"""

import os
import re
import yaml
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))
from audit_logger import AuditLogger


class WeeklyAuditBriefer:
    """Gold Tier skill for generating weekly CEO briefings."""

    def __init__(self):
        """Initialize the Weekly Audit Briefer."""
        self.base_dir = Path(".")
        self.done_dir = self.base_dir / "Done"
        self.logs_dir = self.base_dir / "Logs"
        self.briefings_dir = self.base_dir / "Briefings"
        self.pending_approval_dir = self.base_dir / "Pending_Approval"

        # Company documents
        self.company_handbook_path = self.base_dir / "Company_Handbook.md"
        self.business_goals_path = self.base_dir / "Business_Goals.md"

        # Ensure directories exist
        self.briefings_dir.mkdir(exist_ok=True)
        
        # Initialize audit logger
        self.audit_logger = AuditLogger(self.base_dir)

        # Revenue patterns for pattern matching
        self.revenue_patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,000.00 or $1000
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 1000 USD
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',  # 1000 dollars
            r'revenue[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # revenue: $1000
            r'sales[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # sales: $1000
            r'payment[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # payment: $1000
            r'invoice[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # invoice: $1000
        ]
        
        # Expense/subscription patterns
        self.expense_patterns = [
            r'subscription[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # subscription: $100
            r'monthly[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # monthly: $100
            r'cost[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # cost: $100
            r'expense[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # expense: $100
            r'paid[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # paid: $100
            r'charged[:\s]*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',  # charged: $100
        ]
        
        # Bottleneck indicators
        self.bottleneck_keywords = [
            'blocked', 'waiting', 'pending', 'delay', 'issue', 'problem',
            'stuck', 'hold', 'review', 'approval', 'todo', 'backlog'
        ]

    def get_week_range(self, date=None):
        """
        Get the start and end dates for the week.
        
        Args:
            date: Date to get week for (default: today)
            
        Returns:
            tuple: (start_date, end_date)
        """
        if date is None:
            date = datetime.now()
        
        # Get Monday of this week
        start_of_week = date - timedelta(days=date.weekday())
        # Get Sunday of this week
        end_of_week = start_of_week + timedelta(days=6)
        
        return start_of_week.date(), end_of_week.date()

    def read_done_files(self, week_start, week_end):
        """
        Read all files from /Done for the specified week.
        
        Args:
            week_start: Start date of the week
            week_end: End date of the week
            
        Returns:
            list: List of file data dictionaries
        """
        done_files = []
        
        if not self.done_dir.exists():
            print(f"Warning: {self.done_dir} directory does not exist.")
            return done_files
        
        for file_path in self.done_dir.glob("*.md"):
            try:
                # Check file modification time
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime).date()
                if week_start <= file_mtime <= week_end:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse frontmatter if exists
                    metadata = self.parse_frontmatter(content)
                    
                    done_files.append({
                        'path': str(file_path),
                        'name': file_path.name,
                        'content': content,
                        'metadata': metadata,
                        'date': file_mtime
                    })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return done_files

    def read_log_files(self, week_start, week_end):
        """
        Read all log files from /Logs for the specified week.
        
        Args:
            week_start: Start date of the week
            week_end: End date of the week
            
        Returns:
            list: List of log file data dictionaries
        """
        log_files = []
        
        if not self.logs_dir.exists():
            print(f"Warning: {self.logs_dir} directory does not exist.")
            return log_files
        
        for file_path in self.logs_dir.glob("*.md"):
            # Skip PM2 logs
            if 'pm2' in file_path.name.lower():
                continue
                
            try:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime).date()
                if week_start <= file_mtime <= week_end:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    log_files.append({
                        'path': str(file_path),
                        'name': file_path.name,
                        'content': content
                    })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return log_files

    def read_company_documents(self):
        """
        Read Company Handbook and Business Goals if they exist.
        
        Returns:
            dict: Company documents content
        """
        docs = {
            'handbook': None,
            'goals': None
        }
        
        if self.company_handbook_path.exists():
            try:
                with open(self.company_handbook_path, 'r', encoding='utf-8') as f:
                    docs['handbook'] = f.read()
            except Exception as e:
                print(f"Error reading company handbook: {e}")
        
        if self.business_goals_path.exists():
            try:
                with open(self.business_goals_path, 'r', encoding='utf-8') as f:
                    docs['goals'] = f.read()
            except Exception as e:
                print(f"Error reading business goals: {e}")
        
        return docs

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
            pass
        
        return {}

    def extract_revenue(self, content):
        """
        Extract revenue amounts from content using pattern matching.
        
        Args:
            content: Text content to search
            
        Returns:
            list: List of revenue amounts found
        """
        revenues = []
        for pattern in self.revenue_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    revenues.append(amount)
                except ValueError:
                    pass
        return revenues

    def extract_expenses(self, content):
        """
        Extract expense/subscription amounts from content using pattern matching.
        
        Args:
            content: Text content to search
            
        Returns:
            list: List of expense amounts found
        """
        expenses = []
        for pattern in self.expense_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    expenses.append(amount)
                except ValueError:
                    pass
        return expenses

    def detect_bottlenecks(self, content):
        """
        Detect potential bottlenecks from content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            list: List of bottleneck indicators found
        """
        bottlenecks = []
        content_lower = content.lower()
        
        for keyword in self.bottleneck_keywords:
            if keyword in content_lower:
                # Find the sentence containing the keyword
                sentences = re.split(r'[.!?]+', content_lower)
                for sentence in sentences:
                    if keyword in sentence:
                        bottlenecks.append(sentence.strip()[:150])
                        break
        
        return bottlenecks[:5]  # Limit to 5 bottlenecks

    def analyze_tasks(self, done_files):
        """
        Analyze completed tasks from /Done files.
        
        Args:
            done_files: List of done file data
            
        Returns:
            dict: Task analysis results
        """
        analysis = {
            'total_tasks': len(done_files),
            'by_type': defaultdict(int),
            'by_platform': defaultdict(int),
            'by_priority': defaultdict(int),
            'revenue_found': 0,
            'revenue_items': []
        }
        
        for file_data in done_files:
            metadata = file_data.get('metadata', {})
            content = file_data.get('content', '')
            
            # Count by type
            file_type = metadata.get('type', 'unknown')
            analysis['by_type'][file_type] += 1
            
            # Count by platform
            platform = metadata.get('platform', 'unknown')
            if platform:
                analysis['by_platform'][platform] += 1
            
            # Count by priority
            priority = metadata.get('priority', 'normal')
            analysis['by_priority'][priority] += 1
            
            # Extract revenue
            revenues = self.extract_revenue(content)
            if revenues:
                analysis['revenue_found'] += sum(revenues)
                analysis['revenue_items'].append({
                    'file': file_data['name'],
                    'amounts': revenues
                })
        
        return analysis

    def analyze_logs(self, log_files):
        """
        Analyze log files for insights.
        
        Args:
            log_files: List of log file data
            
        Returns:
            dict: Log analysis results
        """
        analysis = {
            'total_logs': len(log_files),
            'bottlenecks': [],
            'expenses_found': 0,
            'expense_items': []
        }
        
        for log_data in log_files:
            content = log_data.get('content', '')
            
            # Detect bottlenecks
            bottlenecks = self.detect_bottlenecks(content)
            analysis['bottlenecks'].extend(bottlenecks)
            
            # Extract expenses
            expenses = self.extract_expenses(content)
            if expenses:
                analysis['expenses_found'] += sum(expenses)
                analysis['expense_items'].append({
                    'file': log_data['name'],
                    'amounts': expenses
                })
        
        return analysis

    def align_with_goals(self, company_docs, task_analysis):
        """
        Analyze alignment with business goals.
        
        Args:
            company_docs: Company handbook and goals content
            task_analysis: Task analysis results
            
        Returns:
            dict: Goal alignment analysis
        """
        alignment = {
            'goals_referenced': [],
            'alignment_score': 'N/A',
            'recommendations': []
        }
        
        goals_content = company_docs.get('goals', '')
        if not goals_content:
            alignment['recommendations'].append(
                "Create Business_Goals.md to track goal alignment"
            )
            return alignment
        
        # Simple keyword matching for goal alignment
        goal_keywords = ['growth', 'revenue', 'customer', 'product', 'market', 'sales']
        
        for keyword in goal_keywords:
            if keyword.lower() in goals_content.lower():
                alignment['goals_referenced'].append(keyword)
        
        # Calculate simple alignment score
        if task_analysis['total_tasks'] > 0:
            high_priority = task_analysis['by_priority'].get('high', 0)
            alignment['alignment_score'] = f"{(high_priority / task_analysis['total_tasks']) * 100:.1f}% high priority tasks"
        
        return alignment

    def generate_ceo_briefing(self, task_analysis, log_analysis, goal_alignment, week_start, week_end):
        """
        Generate the CEO Briefing document.
        
        Args:
            task_analysis: Task analysis results
            log_analysis: Log analysis results
            goal_alignment: Goal alignment analysis
            week_start: Start date of the week
            week_end: End date of the week
            
        Returns:
            str: Path to the generated briefing
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"ceo_briefing_{timestamp}.md"
        filepath = self.briefings_dir / filename
        
        # Calculate totals
        total_revenue = task_analysis['revenue_found']
        total_expenses = log_analysis['expenses_found']
        net = total_revenue - total_expenses
        
        # Create briefing content
        briefing = f"""---
type: ceo_briefing
period: Weekly
week_start: {week_start}
week_end: {week_end}
generated: {datetime.now().isoformat()}
generated_by: Weekly Audit Briefer
status: final
---

# CEO Weekly Briefing

**Period:** {week_start} to {week_end}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Prepared By:** AI Employee System (Gold Tier)

---

## Executive Summary

This week's operational audit covers **{task_analysis['total_tasks']} completed tasks** across all platforms and channels.

**Key Metrics:**
- **Tasks Completed:** {task_analysis['total_tasks']}
- **Revenue Identified:** ${total_revenue:,.2f}
- **Expenses Identified:** ${total_expenses:,.2f}
- **Net Position:** ${net:,.2f}
- **Bottlenecks Detected:** {len(log_analysis['bottlenecks'])}

---

## Task Completion Analysis

### By Type
"""
        
        for task_type, count in sorted(task_analysis['by_type'].items()):
            briefing += f"- **{task_type.replace('_', ' ').title()}:** {count}\n"
        
        briefing += "\n### By Platform\n"
        for platform, count in sorted(task_analysis['by_platform'].items()):
            briefing += f"- **{platform.title()}:** {count}\n"
        
        briefing += "\n### By Priority\n"
        for priority, count in sorted(task_analysis['by_priority'].items()):
            briefing += f"- **{priority.title()}:** {count}\n"
        
        # Revenue section
        briefing += f"""
---

## Revenue Analysis

**Total Revenue Identified:** ${total_revenue:,.2f}

"""
        
        if task_analysis['revenue_items']:
            briefing += "### Revenue Sources\n\n"
            for item in task_analysis['revenue_items'][:10]:  # Top 10
                amounts = ', '.join([f"${a:,.2f}" for a in item['amounts']])
                briefing += f"- {item['file']}: {amounts}\n"
        else:
            briefing += "*No specific revenue items detected in completed tasks.*\n"
        
        # Expenses section
        briefing += f"""
---

## Expense Analysis

**Total Expenses Identified:** ${total_expenses:,.2f}

"""
        
        if log_analysis['expense_items']:
            briefing += "### Expense Items\n\n"
            for item in log_analysis['expense_items'][:10]:  # Top 10
                amounts = ', '.join([f"${a:,.2f}" for a in item['amounts']])
                briefing += f"- {item['file']}: {amounts}\n"
        else:
            briefing += "*No specific expense items detected in logs.*\n"
        
        # Bottlenecks section
        briefing += f"""
---

## Bottlenecks & Issues

**Total Bottlenecks Detected:** {len(log_analysis['bottlenecks'])}

"""
        
        if log_analysis['bottlenecks']:
            for i, bottleneck in enumerate(log_analysis['bottlenecks'][:10], 1):
                briefing += f"{i}. {bottleneck}\n"
        else:
            briefing += "*No significant bottlenecks detected this week.*\n"
        
        # Goal alignment section
        briefing += f"""
---

## Business Goals Alignment

**Alignment Score:** {goal_alignment['alignment_score']}

"""

        if goal_alignment['goals_referenced']:
            briefing += "### Referenced Goals\n\n"
            for goal in goal_alignment['goals_referenced']:
                briefing += f"- {goal.title()}\n"

        if goal_alignment['recommendations']:
            briefing += "\n### Recommendations\n\n"
            for rec in goal_alignment['recommendations']:
                briefing += f"- {rec}\n"

        # Add Audit Log Summary
        try:
            audit_summary = self.audit_logger.get_weekly_summary_for_briefing()
            briefing += f"""
---
{audit_summary}
"""
        except Exception as e:
            briefing += f"""
---

## Audit Log Summary

*Audit log summary unavailable: {e}*

"""

        # Action items section
        briefing += f"""
---

## Recommended Actions

Based on this week's audit, the following actions are recommended:

"""
        
        # Generate recommendations based on analysis
        recommendations = []
        
        if total_revenue > 0:
            recommendations.append("✅ **Revenue Positive:** Continue current sales and client engagement strategies")
        
        if total_expenses > total_revenue and total_revenue > 0:
            recommendations.append("⚠️ **Expense Review:** Expenses exceed revenue - review subscription costs")
        
        if len(log_analysis['bottlenecks']) > 5:
            recommendations.append("⚠️ **Bottleneck Alert:** High number of blockers detected - prioritize resolution")
        
        high_priority = task_analysis['by_priority'].get('high', 0)
        if high_priority > 10:
            recommendations.append("📈 **High Volume:** Many high-priority tasks - ensure adequate resources")
        
        if task_analysis['total_tasks'] < 5:
            recommendations.append("📉 **Low Activity:** Consider increasing outreach and engagement")
        
        if not recommendations:
            recommendations.append("✅ **Steady State:** Continue current operations and monitoring")
        
        for rec in recommendations:
            briefing += f"- {rec}\n"
        
        # Footer
        briefing += f"""
---

## Next Week Focus

1. Monitor revenue trends and client acquisition
2. Address identified bottlenecks promptly
3. Review subscription expenses for optimization opportunities
4. Align tasks with business goals

---

*Briefing generated automatically by Weekly Audit Briefer (Gold Tier)*
*For questions, review the source files in /Done and /Logs directories*
"""
        
        # Write the briefing
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(briefing)
        
        return str(filepath)

    def run_audit(self, date=None):
        """
        Run the weekly audit and generate CEO briefing.
        
        Args:
            date: Date to run audit for (default: today)
            
        Returns:
            str: Path to generated briefing
        """
        print("="*60)
        print("WEEKLY AUDIT BRIEFER")
        print("="*60)
        
        if date is None:
            date = datetime.now()
        
        # Get week range
        week_start, week_end = self.get_week_range(date)
        
        print(f"\nAudit Period: {week_start} to {week_end}")
        
        # Read source files
        print("\nReading /Done files...")
        done_files = self.read_done_files(week_start, week_end)
        print(f"  Found {len(done_files)} files")
        
        print("\nReading /Logs files...")
        log_files = self.read_log_files(week_start, week_end)
        print(f"  Found {len(log_files)} files")
        
        print("\nReading company documents...")
        company_docs = self.read_company_documents()
        print(f"  Handbook: {'Found' if company_docs['handbook'] else 'Not found'}")
        print(f"  Goals: {'Found' if company_docs['goals'] else 'Not found'}")
        
        # Analyze data
        print("\nAnalyzing tasks...")
        task_analysis = self.analyze_tasks(done_files)
        
        print("\nAnalyzing logs...")
        log_analysis = self.analyze_logs(log_files)
        
        print("\nChecking goal alignment...")
        goal_alignment = self.align_with_goals(company_docs, task_analysis)
        
        # Generate briefing
        print("\nGenerating CEO Briefing...")
        briefing_path = self.generate_ceo_briefing(
            task_analysis, log_analysis, goal_alignment, week_start, week_end
        )
        
        # Print summary
        print("\n" + "="*60)
        print("AUDIT COMPLETE")
        print("="*60)
        print(f"Tasks Analyzed: {task_analysis['total_tasks']}")
        print(f"Revenue Found: ${task_analysis['revenue_found']:,.2f}")
        print(f"Expenses Found: ${log_analysis['expenses_found']:,.2f}")
        print(f"Bottlenecks: {len(log_analysis['bottlenecks'])}")
        print(f"\nCEO Briefing: {briefing_path}")
        
        return briefing_path


def main():
    """Main entry point."""
    briefer = WeeklyAuditBriefer()
    
    # Check if running on Monday (day 0) or first of month
    today = datetime.now()
    is_monday = today.weekday() == 0  # Monday is 0
    is_first_of_month = today.day == 1
    
    if not (is_monday or is_first_of_month):
        print(f"Note: Today is not Monday or 1st of month (weekday={today.weekday()}, day={today.day})")
        print("Running audit anyway...")
    
    briefing_path = briefer.run_audit(today)
    
    print(f"\n[SUCCESS] Weekly Audit Briefer completed.")
    print(f"  Briefing saved to: {briefing_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())

"""
Audit Logger Utility (Gold Tier)
Logs every action with timestamp, action_type, actor, target, parameters, approval_status, result
Retains logs for 90 days with automatic cleanup
Generates weekly summaries for CEO Briefing
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import threading


class AuditLogger:
    """Gold Tier audit logging utility for compliance and tracking."""
    
    # Log retention period in days
    RETENTION_DAYS = 90
    
    def __init__(self, base_dir=None):
        """
        Initialize audit logger.
        
        Args:
            base_dir: Base directory for the project (default: current dir)
        """
        if base_dir is None:
            base_dir = Path(".")
        else:
            base_dir = Path(base_dir)
        
        self.base_dir = base_dir
        self.logs_dir = base_dir / "Logs"
        self.briefings_dir = base_dir / "Briefings"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.briefings_dir.mkdir(exist_ok=True)
        
        # Thread lock for concurrent writes
        self._lock = threading.Lock()
        
        # Default actor (can be overridden per action)
        self.default_actor = "AI_Employee_System"
        
        # Cleanup old logs on initialization
        self.cleanup_old_logs()
    
    def _get_audit_log_path(self, date=None):
        """
        Get the audit log file path for a specific date.
        
        Args:
            date: Date for the log (default: today)
            
        Returns:
            Path: Path to the audit log file
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y%m%d")
        return self.logs_dir / f"audit_{date_str}.json"
    
    def log(self, action_type: str, target: str, parameters: Optional[Dict[str, Any]] = None,
            approval_status: str = "not_required", result: str = "success",
            actor: Optional[str] = None, message: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None):
        """
        Log an action to the audit log.
        
        Args:
            action_type: Type of action (e.g., "file_processed", "draft_created", "email_sent")
            target: Target of the action (e.g., file path, email address)
            parameters: Parameters passed to the action
            approval_status: Approval status ("not_required", "pending", "approved", "rejected")
            result: Result of the action ("success", "failed", "skipped")
            actor: Who performed the action (default: default_actor)
            message: Optional human-readable message
            metadata: Additional metadata to include
            
        Returns:
            str: Path to the log file
        """
        timestamp = datetime.now().isoformat()
        date = datetime.now()
        
        # Build log entry
        log_entry = {
            "timestamp": timestamp,
            "date": date.strftime("%Y-%m-%d"),
            "action_type": action_type,
            "actor": actor or self.default_actor,
            "target": target,
            "parameters": parameters or {},
            "approval_status": approval_status,
            "result": result,
            "message": message or ""
        }
        
        # Add metadata if provided
        if metadata:
            log_entry["metadata"] = metadata
        
        # Write to log file
        log_path = self._get_audit_log_path(date)
        
        with self._lock:
            # Read existing entries
            entries = []
            if log_path.exists():
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            # Handle potential trailing comma issues
                            if content.startswith('[') and content.endswith(']'):
                                entries = json.loads(content)
                            elif content.startswith('['):
                                # Try to parse as array with potential issues
                                entries = json.loads(content.rstrip(',') + ']')
                except (json.JSONDecodeError, Exception) as e:
                    # If file is corrupted, start fresh
                    entries = []
            
            # Append new entry
            entries.append(log_entry)
            
            # Write back
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
        
        return str(log_path)
    
    def log_start(self, action_type: str, target: str, parameters: Optional[Dict[str, Any]] = None,
                  actor: Optional[str] = None, message: Optional[str] = None):
        """
        Log the start of an action.
        
        Args:
            action_type: Type of action
            target: Target of the action
            parameters: Parameters passed to the action
            actor: Who performed the action
            message: Optional message
            
        Returns:
            str: Path to the log file
        """
        return self.log(
            action_type=action_type,
            target=target,
            parameters=parameters,
            approval_status="not_required",
            result="started",
            actor=actor,
            message=message or f"Started {action_type}"
        )
    
    def log_end(self, action_type: str, target: str, result: str = "success",
                actor: Optional[str] = None, message: Optional[str] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Log the end of an action.
        
        Args:
            action_type: Type of action
            target: Target of the action
            result: Result of the action
            actor: Who performed the action
            message: Optional message
            metadata: Additional metadata
            
        Returns:
            str: Path to the log file
        """
        return self.log(
            action_type=action_type,
            target=target,
            approval_status="not_required",
            result=result,
            actor=actor,
            message=message or f"Completed {action_type}",
            metadata=metadata
        )
    
    def log_approval(self, action_type: str, target: str, approval_status: str,
                     actor: Optional[str] = None, message: Optional[str] = None):
        """
        Log an approval action.
        
        Args:
            action_type: Type of action requiring approval
            target: Target of the action
            approval_status: "approved" or "rejected"
            actor: Who approved/rejected
            message: Optional message
            
        Returns:
            str: Path to the log file
        """
        return self.log(
            action_type=action_type,
            target=target,
            approval_status=approval_status,
            result="pending" if approval_status == "pending" else "success",
            actor=actor,
            message=message or f"Approval {approval_status} for {action_type}"
        )
    
    def log_error(self, action_type: str, target: str, error_message: str,
                  actor: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Log an error.
        
        Args:
            action_type: Type of action that failed
            target: Target of the action
            error_message: Error message
            actor: Who performed the action
            metadata: Additional metadata
            
        Returns:
            str: Path to the log file
        """
        return self.log(
            action_type=action_type,
            target=target,
            approval_status="not_required",
            result="failed",
            actor=actor,
            message=error_message,
            metadata=metadata
        )
    
    def get_logs_for_date_range(self, start_date: datetime, end_date: datetime) -> list:
        """
        Get all logs for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            list: List of log entries
        """
        all_logs = []
        current_date = start_date
        
        while current_date <= end_date:
            log_path = self._get_audit_log_path(current_date)
            
            if log_path.exists():
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        entries = json.load(f)
                        all_logs.extend(entries)
                except (json.JSONDecodeError, Exception):
                    pass
            
            current_date += timedelta(days=1)
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x.get('timestamp', ''))
        
        return all_logs
    
    def generate_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate a summary of audit logs for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            dict: Summary statistics
        """
        logs = self.get_logs_for_date_range(start_date, end_date)
        
        summary = {
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "total_actions": len(logs),
            "by_result": {},
            "by_action_type": {},
            "by_approval_status": {},
            "by_actor": {},
            "errors": [],
            "approvals_pending": 0,
            "approvals_approved": 0,
            "approvals_rejected": 0
        }
        
        for log in logs:
            # Count by result
            result = log.get('result', 'unknown')
            summary['by_result'][result] = summary['by_result'].get(result, 0) + 1
            
            # Count by action type
            action_type = log.get('action_type', 'unknown')
            summary['by_action_type'][action_type] = summary['by_action_type'].get(action_type, 0) + 1
            
            # Count by approval status
            approval = log.get('approval_status', 'unknown')
            summary['by_approval_status'][approval] = summary['by_approval_status'].get(approval, 0) + 1
            
            # Count by actor
            actor = log.get('actor', 'unknown')
            summary['by_actor'][actor] = summary['by_actor'].get(actor, 0) + 1
            
            # Track errors
            if result == 'failed':
                summary['errors'].append({
                    'timestamp': log.get('timestamp'),
                    'action_type': action_type,
                    'target': log.get('target'),
                    'message': log.get('message', 'Unknown error')
                })
            
            # Track approvals
            if approval == 'pending':
                summary['approvals_pending'] += 1
            elif approval == 'approved':
                summary['approvals_approved'] += 1
            elif approval == 'rejected':
                summary['approvals_rejected'] += 1
        
        return summary
    
    def cleanup_old_logs(self):
        """Delete audit logs older than RETENTION_DAYS."""
        cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)
        deleted_count = 0
        
        for log_file in self.logs_dir.glob("audit_*.json"):
            try:
                # Extract date from filename (audit_YYYYMMDD.json)
                filename = log_file.name
                date_str = filename.replace('audit_', '').replace('.json', '')
                file_date = datetime.strptime(date_str, "%Y%m%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
            except (ValueError, Exception) as e:
                # Skip files that don't match the pattern
                pass
        
        return deleted_count
    
    def get_weekly_summary_for_briefing(self) -> str:
        """
        Generate a weekly audit summary formatted for CEO Briefing.
        
        Returns:
            str: Formatted summary text
        """
        # Get last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        summary = self.generate_summary(start_date, end_date)
        
        # Format for CEO Briefing
        briefing_text = f"""
## Audit Log Summary (Last 7 Days)

**Period:** {summary['period']['start']} to {summary['period']['end']}

### Activity Overview
- **Total Actions:** {summary['total_actions']}
- **Successful:** {summary['by_result'].get('success', 0)}
- **Failed:** {summary['by_result'].get('failed', 0)}
- **Started/In Progress:** {summary['by_result'].get('started', 0)}

### Actions by Type
"""
        
        for action_type, count in sorted(summary['by_action_type'].items(), key=lambda x: -x[1])[:10]:
            briefing_text += f"- **{action_type}:** {count}\n"
        
        briefing_text += "\n### Approval Status\n"
        briefing_text += f"- **Pending Approval:** {summary['approvals_pending']}\n"
        briefing_text += f"- **Approved:** {summary['approvals_approved']}\n"
        briefing_text += f"- **Rejected:** {summary['approvals_rejected']}\n"
        
        if summary['errors']:
            briefing_text += "\n### Recent Errors\n"
            for error in summary['errors'][:5]:  # Top 5 errors
                briefing_text += f"- [{error['timestamp']}] {error['action_type']}: {error['message'][:100]}\n"
        
        return briefing_text


# Global instance for convenience
_audit_logger = None

def get_audit_logger(base_dir=None):
    """Get or create global AuditLogger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(base_dir)
    return _audit_logger

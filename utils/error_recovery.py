"""
Error Recovery Utility for Gold Tier System
Provides exponential backoff retry, error logging, and graceful degradation.
"""

import os
import time
import asyncio
from datetime import datetime
from pathlib import Path
from functools import wraps


class ErrorRecovery:
    """Utility class for error recovery across watchers and skills."""
    
    def __init__(self, base_dir=None):
        """
        Initialize error recovery utility.
        
        Args:
            base_dir: Base directory for the project (default: current dir)
        """
        if base_dir is None:
            base_dir = Path(".")
        else:
            base_dir = Path(base_dir)
        
        self.base_dir = base_dir
        self.logs_dir = base_dir / "Logs"
        self.errors_dir = base_dir / "Errors"
        self.plans_dir = base_dir / "Plans"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.errors_dir.mkdir(exist_ok=True)
        self.plans_dir.mkdir(exist_ok=True)
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1  # seconds
        self.max_delay = 60  # seconds
        self.exponential_base = 2
    
    def calculate_delay(self, attempt):
        """
        Calculate delay for current attempt using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            float: Delay in seconds (capped at max_delay)
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    def log_error(self, component, error, context=None):
        """
        Log error to /Logs/error_[component]_[date].log.
        
        Args:
            component: Name of the component (watcher/skill name)
            error: Exception or error message
            context: Optional context dictionary
        """
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = self.logs_dir / f"error_{component}_{date_str}.log"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format error message
        if isinstance(error, Exception):
            error_type = type(error).__name__
            error_msg = str(error)
        else:
            error_type = "Error"
            error_msg = str(error)
        
        # Build log entry
        log_entry = f"""
---
Timestamp: {timestamp}
Component: {component}
Error Type: {error_type}
Error Message: {error_msg}
"""
        
        if context:
            log_entry += "Context:\n"
            for key, value in context.items():
                log_entry += f"  {key}: {value}\n"
        
        log_entry += "---\n\n"
        
        # Append to log file
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Failed to write error log: {e}")
    
    def write_skill_error(self, skill_name, error, input_data=None, recovery_action=None):
        """
        Write skill error to /Errors/skill_error_[date].md.
        
        Args:
            skill_name: Name of the skill
            error: Exception or error message
            input_data: Optional input data that caused the error
            recovery_action: Suggested recovery action
        """
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = self.errors_dir / f"skill_error_{skill_name}_{date_str}.md"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format error message
        if isinstance(error, Exception):
            error_type = type(error).__name__
            error_msg = str(error)
            traceback = getattr(error, '__traceback__', None)
        else:
            error_type = "Error"
            error_msg = str(error)
            traceback = None
        
        # Build error report
        error_report = f"""---
type: skill_error
skill: {skill_name}
timestamp: {timestamp}
error_type: {error_type}
status: needs_review
---

# Skill Error Report

**Skill:** {skill_name}  
**Timestamp:** {timestamp}  
**Error Type:** {error_type}

---

## Error Details

```
{error_msg}
```

"""
        
        if input_data:
            error_report += "## Input Data\n\n"
            if isinstance(input_data, dict):
                for key, value in input_data.items():
                    error_report += f"- **{key}:** {value}\n"
            elif isinstance(input_data, str):
                error_report += f"{input_data[:500]}\n"  # Truncate long strings
            error_report += "\n"
        
        if recovery_action:
            error_report += f"""## Suggested Recovery Action

{recovery_action}

"""
        
        error_report += f"""## Manual Review Required

- [ ] Review error details above
- [ ] Check input data for issues
- [ ] Retry the operation manually
- [ ] Update skill to handle this edge case
- [ ] Move to /Done after resolution

---
*Generated by Error Recovery System (Gold Tier)*
"""
        
        # Write error report
        try:
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(error_report)
            return str(error_file)
        except Exception as e:
            print(f"Failed to write error report: {e}")
            return None
    
    def write_manual_action(self, skill_name, action_type, description, original_input=None):
        """
        Write manual action draft to /Plans/manual_action_[skill]_[date].md.
        
        Args:
            skill_name: Name of the skill that failed
            action_type: Type of action needed (email, post, call, etc.)
            description: Description of what needs to be done
            original_input: Original input that triggered the action
            
        Returns:
            str: Path to the created file
        """
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        action_file = self.plans_dir / f"manual_action_{skill_name}_{date_str}.md"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build action draft
        action_draft = f"""---
type: manual_action
skill: {skill_name}
action_type: {action_type}
created: {timestamp}
status: pending
priority: high
---

# Manual Action Required

**Skill:** {skill_name}  
**Action Type:** {action_type}  
**Created:** {timestamp}  
**Status:** Pending Manual Execution

---

## Description

{description}

---

## Original Input

"""
        
        if original_input:
            if isinstance(original_input, dict):
                for key, value in original_input.items():
                    action_draft += f"- **{key}:** {value}\n"
            elif isinstance(original_input, str):
                action_draft += f"{original_input[:1000]}\n"
        else:
            action_draft += "*No original input available*\n"
        
        action_draft += f"""
---

## Manual Execution Steps

1. Review the description above
2. Gather any necessary information
3. Execute the {action_type} manually
4. Document the outcome below
5. Move this file to /Done after completion

---

## Outcome (Fill after execution)

**Executed At:** _______________  
**Executed By:** _______________  
**Result:** _______________

**Notes:**

---
*Generated by Error Recovery System (Gold Tier)*
*Skill failed to execute automatically - manual intervention required*
"""
        
        # Write action draft
        try:
            with open(action_file, 'w', encoding='utf-8') as f:
                f.write(action_draft)
            return str(action_file)
        except Exception as e:
            print(f"Failed to write manual action: {e}")
            return None
    
    def retry_async(self, max_retries=None, base_delay=None, exceptions=None):
        """
        Decorator for async functions with exponential backoff retry.
        
        Args:
            max_retries: Maximum retry attempts (default: self.max_retries)
            base_delay: Base delay in seconds (default: self.base_delay)
            exceptions: Tuple of exceptions to catch (default: Exception)
            
        Returns:
            Decorated function
        """
        if max_retries is None:
            max_retries = self.max_retries
        if base_delay is None:
            base_delay = self.base_delay
        if exceptions is None:
            exceptions = (Exception,)
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_error = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_error = e
                        
                        if attempt < max_retries:
                            delay = base_delay * (self.exponential_base ** attempt)
                            delay = min(delay, self.max_delay)
                            
                            print(f"  Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}")
                            await asyncio.sleep(delay)
                        else:
                            print(f"  Max retries ({max_retries}) exceeded")
                
                # All retries failed
                raise last_error
            
            return wrapper
        return decorator
    
    def retry_sync(self, max_retries=None, base_delay=None, exceptions=None):
        """
        Decorator for sync functions with exponential backoff retry.
        
        Args:
            max_retries: Maximum retry attempts (default: self.max_retries)
            base_delay: Base delay in seconds (default: self.base_delay)
            exceptions: Tuple of exceptions to catch (default: Exception)
            
        Returns:
            Decorated function
        """
        if max_retries is None:
            max_retries = self.max_retries
        if base_delay is None:
            base_delay = self.base_delay
        if exceptions is None:
            exceptions = (Exception,)
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_error = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_error = e
                        
                        if attempt < max_retries:
                            delay = base_delay * (self.exponential_base ** attempt)
                            delay = min(delay, self.max_delay)
                            
                            print(f"  Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}")
                            time.sleep(delay)
                        else:
                            print(f"  Max retries ({max_retries}) exceeded")
                
                # All retries failed
                raise last_error
            
            return wrapper
        return decorator


# Global instance for convenience
_error_recovery = None

def get_error_recovery(base_dir=None):
    """Get or create global ErrorRecovery instance."""
    global _error_recovery
    if _error_recovery is None:
        _error_recovery = ErrorRecovery(base_dir)
    return _error_recovery

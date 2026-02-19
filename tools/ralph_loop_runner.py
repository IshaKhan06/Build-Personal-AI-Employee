#!/usr/bin/env python3
"""
Ralph Wiggum Reasoning Loop for Gold Tier
Autonomous multi-step task handling with full workflow integration
Handles: sales lead -> draft post -> HITL -> MCP -> audit log
Max iterations: 20
Integrates with: Cross Domain Integrator, Audit Logger, Skills
"""

import os
import sys
import shutil
import glob
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import utilities
try:
    from utils.audit_logger import AuditLogger
    AUDIT_LOGGER_AVAILABLE = True
except ImportError:
    AUDIT_LOGGER_AVAILABLE = False
    print("Warning: AuditLogger not available, running without audit logging")


class RalphWiggumLoop:
    """
    Gold Tier Ralph Wiggum Reasoning Loop
    Handles multi-step autonomous tasks with full workflow integration
    """
    
    # Maximum iterations for Gold Tier
    DEFAULT_MAX_ITERATIONS = 20
    
    # Task workflow stages
    STAGES = {
        'analysis': 1,
        'skill_execution': 2,
        'hitl_approval': 3,
        'mcp_execution': 4,
        'audit_logging': 5,
        'completion': 6
    }
    
    def __init__(self, max_iterations: int = None, audit_enabled: bool = True):
        """
        Initialize the Ralph Wiggum Loop.
        
        Args:
            max_iterations: Maximum loop iterations (default: 20 for Gold Tier)
            audit_enabled: Enable audit logging (default: True)
        """
        self.max_iterations = max_iterations or self.DEFAULT_MAX_ITERATIONS
        self.iteration_count = 0
        self.processed_files = []
        self.task_history = []
        self.audit_enabled = audit_enabled and AUDIT_LOGGER_AVAILABLE
        
        # Initialize audit logger
        if self.audit_enabled:
            try:
                self.audit_logger = AuditLogger(project_root)
            except Exception as e:
                print(f"Warning: Failed to initialize AuditLogger: {e}")
                self.audit_enabled = False
        
        # Directories
        self.needs_action_dir = project_root / "Needs_Action"
        self.pending_approval_dir = project_root / "Pending_Approval"
        self.approved_dir = project_root / "Approved"
        self.done_dir = project_root / "Done"
        self.plans_dir = project_root / "Plans"
        self.logs_dir = project_root / "Logs"
        
        # Ensure directories exist
        for dir_path in [self.pending_approval_dir, self.approved_dir, 
                         self.done_dir, self.plans_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def log_audit(self, action_type: str, target: str, result: str = "success",
                  parameters: Dict = None, message: str = None):
        """Log action to audit logger if enabled"""
        if self.audit_enabled:
            try:
                self.audit_logger.log(
                    action_type=action_type,
                    target=target,
                    result=result,
                    parameters=parameters or {},
                    message=message or f"Ralph Loop: {action_type}"
                )
            except Exception as e:
                print(f"Warning: Audit log failed: {e}")
    
    def scan_needs_action(self) -> List[str]:
        """Scan /Needs_Action for files to process"""
        if not self.needs_action_dir.exists():
            print("Needs_Action directory does not exist")
            return []

        # Get all files in Needs_Action (excluding hidden files)
        files = [f for f in self.needs_action_dir.glob("*") if f.is_file() and not f.name.startswith('.')]
        return sorted([str(f) for f in files])
    
    def scan_pending_approval(self) -> List[str]:
        """Scan /Pending_Approval for files awaiting approval"""
        if not self.pending_approval_dir.exists():
            return []
        
        files = [f for f in self.pending_approval_dir.glob("*.md") if f.is_file()]
        return sorted([str(f) for f in files])
    
    def scan_approved(self) -> List[str]:
        """Scan /Approved for files ready for MCP execution"""
        if not self.approved_dir.exists():
            return []
        
        files = [f for f in self.approved_dir.glob("*.md") if f.is_file()]
        return sorted([str(f) for f in files])

    def task_analyzer(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a file and determine what task needs to be performed.
        Integrates with Cross Domain Integrator pattern matching.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            dict: Task analysis results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content_lower = content.lower()
            
            # Extract metadata from frontmatter if present
            metadata = self._parse_frontmatter(content)
            
            # Determine task type based on content and metadata
            task_type = self._determine_task_type(content_lower, metadata)
            
            # Determine if multi-step (requires HITL, MCP, etc.)
            is_multi_step = self._is_multi_step_task(task_type, metadata)
            
            # Determine workflow stages needed
            workflow = self._build_workflow(task_type, metadata)
            
            analysis = {
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'task_type': task_type,
                'is_multi_step': is_multi_step,
                'workflow': workflow,
                'current_stage': 'analysis',
                'metadata': metadata,
                'content_preview': content[:500],
                'priority': metadata.get('priority', 'normal'),
                'platform': metadata.get('platform', 'unknown'),
                'keyword': metadata.get('keyword', 'general')
            }
            
            # Log audit
            self.log_audit(
                action_type="task_analyzed",
                target=file_path,
                result="success",
                parameters={
                    'task_type': task_type,
                    'is_multi_step': is_multi_step,
                    'workflow_stages': len(workflow)
                },
                message=f"Analyzed {Path(file_path).name}: {task_type}"
            )
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            self.log_audit(
                action_type="task_analysis_failed",
                target=file_path,
                result="failed",
                parameters={'error': str(e)},
                message=f"Analysis failed: {e}"
            )
            return {
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'task_type': 'error',
                'is_multi_step': False,
                'workflow': ['completion'],
                'current_stage': 'analysis',
                'error': str(e)
            }
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from content"""
        metadata = {}
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 2:
                    yaml_content = parts[1].strip()
                    for line in yaml_content.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip().strip('"\'')
            except Exception:
                pass
        return metadata
    
    def _determine_task_type(self, content: str, metadata: Dict) -> str:
        """Determine task type based on content and metadata"""
        # Check metadata first
        task_type = metadata.get('type', '')
        
        if task_type:
            return task_type
        
        # Fall back to content analysis
        if any(kw in content for kw in ['sales', 'client', 'project']):
            if 'facebook' in content or 'instagram' in content:
                return 'facebook_instagram_lead'
            elif 'twitter' in content:
                return 'twitter_lead'
            elif 'linkedin' in content:
                return 'linkedin_lead'
            else:
                return 'social_media_lead'
        elif any(kw in content for kw in ['urgent', 'invoice', 'payment']):
            return 'financial_task'
        elif any(kw in content for kw in ['meeting', 'schedule', 'calendar']):
            return 'schedule_task'
        else:
            return 'general_task'
    
    def _is_multi_step_task(self, task_type: str, metadata: Dict) -> bool:
        """Determine if task requires multiple steps"""
        multi_step_types = [
            'facebook_instagram_lead', 'twitter_lead', 'linkedin_lead',
            'social_media_lead', 'email_response_required'
        ]
        return task_type in multi_step_types
    
    def _build_workflow(self, task_type: str, metadata: Dict) -> List[str]:
        """Build workflow stages for task type"""
        # Default workflow for social media leads
        if any(lead in task_type for lead in ['lead', 'social']):
            return [
                'analysis',
                'skill_execution',  # Generate draft
                'hitl_approval',    # Wait for approval
                'mcp_execution',    # Execute via MCP
                'audit_logging',
                'completion'
            ]
        
        # Financial tasks
        if 'financial' in task_type:
            return ['analysis', 'skill_execution', 'completion']
        
        # Schedule tasks
        if 'schedule' in task_type:
            return ['analysis', 'mcp_execution', 'completion']
        
        # Default
        return ['analysis', 'completion']

    def execute_task(self, task: Dict[str, Any]) -> bool:
        """
        Execute task through workflow stages.
        
        Args:
            task: Task analysis dict
            
        Returns:
            bool: True if task complete, False if requires further steps
        """
        print(f"\nExecuting task: {task['task_type']} for {task['file_name']}")
        print(f"  Workflow: {' -> '.join(task['workflow'])}")
        
        current_stage = task.get('current_stage', 'analysis')
        
        # Execute based on current stage
        if current_stage == 'analysis':
            return self._execute_analysis_stage(task)
        elif current_stage == 'skill_execution':
            return self._execute_skill_stage(task)
        elif current_stage == 'hitl_approval':
            return self._execute_hitl_stage(task)
        elif current_stage == 'mcp_execution':
            return self._execute_mcp_stage(task)
        elif current_stage == 'audit_logging':
            return self._execute_audit_stage(task)
        elif current_stage == 'completion':
            return self._execute_completion_stage(task)
        else:
            print(f"  Unknown stage: {current_stage}")
            return True
    
    def _execute_analysis_stage(self, task: Dict) -> bool:
        """Execute analysis stage"""
        print(f"  Stage: Analysis")
        print(f"  Task Type: {task['task_type']}")
        print(f"  Multi-step: {task['is_multi_step']}")
        
        # Move to next stage
        task['current_stage'] = 'skill_execution'
        self.task_history.append({
            'file': task['file_name'],
            'stage': 'analysis',
            'timestamp': datetime.now().isoformat(),
            'result': 'complete'
        })
        
        return False  # Continue to next stage
    
    def _execute_skill_stage(self, task: Dict) -> bool:
        """Execute skill execution stage (generate drafts, summaries, etc.)"""
        print(f"  Stage: Skill Execution")
        
        task_type = task['task_type']
        file_path = task['file_path']
        
        # Trigger appropriate skill based on task type
        skill_triggered = self._trigger_skill(task_type, file_path)
        
        if skill_triggered:
            print(f"  Skill triggered successfully")
            
            # Check if draft was created (move to Pending_Approval)
            draft_created = self._check_draft_created(task)
            
            if draft_created:
                print(f"  Draft created, moving to HITL approval")
                task['current_stage'] = 'hitl_approval'
                self.task_history.append({
                    'file': task['file_name'],
                    'stage': 'skill_execution',
                    'timestamp': datetime.now().isoformat(),
                    'result': 'draft_created'
                })
                return False  # Continue to HITL
            else:
                print(f"  No draft required, completing task")
                task['current_stage'] = 'completion'
                return False
        else:
            print(f"  Skill execution skipped")
            task['current_stage'] = 'completion'
            return False
    
    def _execute_hitl_stage(self, task: Dict) -> bool:
        """Execute HITL approval stage"""
        print(f"  Stage: HITL Approval")
        
        # Check if file has been approved (moved to /Approved)
        is_approved = self._check_approval_status(task)
        
        if is_approved:
            print(f"  Approval granted, proceeding to MCP execution")
            task['current_stage'] = 'mcp_execution'
            self.task_history.append({
                'file': task['file_name'],
                'stage': 'hitl_approval',
                'timestamp': datetime.now().isoformat(),
                'result': 'approved'
            })
            self.log_audit(
                action_type="hitl_approved",
                target=task['file_path'],
                result="success",
                message="HITL approval granted"
            )
            return False  # Continue to MCP
        else:
            print(f"  Awaiting HITL approval (file in Pending_Approval)")
            self.task_history.append({
                'file': task['file_name'],
                'stage': 'hitl_approval',
                'timestamp': datetime.now().isoformat(),
                'result': 'pending'
            })
            return True  # Task not complete, waiting for approval
    
    def _execute_mcp_stage(self, task: Dict) -> bool:
        """Execute MCP server stage"""
        print(f"  Stage: MCP Execution")
        
        # Trigger MCP server if available
        mcp_executed = self._trigger_mcp(task)
        
        if mcp_executed:
            print(f"  MCP execution successful")
            task['current_stage'] = 'audit_logging'
            self.task_history.append({
                'file': task['file_name'],
                'stage': 'mcp_execution',
                'timestamp': datetime.now().isoformat(),
                'result': 'success'
            })
            return False  # Continue to audit logging
        else:
            print(f"  MCP execution skipped (not available or not required)")
            task['current_stage'] = 'audit_logging'
            return False
    
    def _execute_audit_stage(self, task: Dict) -> bool:
        """Execute audit logging stage"""
        print(f"  Stage: Audit Logging")
        
        # Log completion
        self.log_audit(
            action_type="task_completed",
            target=task['file_path'],
            result="success",
            parameters={
                'task_type': task['task_type'],
                'workflow_stages': len(task['workflow'])
            },
            message=f"Task completed: {task['file_name']}"
        )
        
        task['current_stage'] = 'completion'
        self.task_history.append({
            'file': task['file_name'],
            'stage': 'audit_logging',
            'timestamp': datetime.now().isoformat(),
            'result': 'logged'
        })
        
        return False  # Continue to completion
    
    def _execute_completion_stage(self, task: Dict) -> bool:
        """Execute completion stage (move files, cleanup)"""
        print(f"  Stage: Completion")
        
        # Move file to Done
        self._move_to_done(task['file_path'])
        
        print(f"  TASK_COMPLETE: {task['file_name']}")
        
        self.log_audit(
            action_type="task_finalized",
            target=task['file_path'],
            result="success",
            message=f"Moved to Done: {task['file_name']}"
        )
        
        self.task_history.append({
            'file': task['file_name'],
            'stage': 'completion',
            'timestamp': datetime.now().isoformat(),
            'result': 'TASK_COMPLETE'
        })
        
        return True  # Task complete
    
    def _trigger_skill(self, task_type: str, file_path: str) -> bool:
        """Trigger appropriate skill based on task type"""
        # This would integrate with actual skills
        # For now, simulate skill execution
        
        skills_to_trigger = {
            'facebook_instagram_lead': 'social_summary_generator',
            'twitter_lead': 'twitter_post_generator',
            'linkedin_lead': 'auto_linkedin_poster',
            'social_media_lead': 'social_summary_generator'
        }
        
        skill = skills_to_trigger.get(task_type)
        
        if skill:
            print(f"  Triggering skill: {skill}")
            # In production, this would call the actual skill
            # For demo, we simulate the draft creation
            self._simulate_skill_execution(skill, file_path)
            return True
        
        return False
    
    def _simulate_skill_execution(self, skill: str, file_path: str):
        """Simulate skill execution and draft creation"""
        # Read source file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return
        
        # Create draft in Pending_Approval
        draft_name = f"draft_{Path(file_path).name}"
        draft_path = self.pending_approval_dir / draft_name
        
        draft_content = f"""---
type: skill_draft
source_file: {file_path}
skill: {skill}
status: pending_approval
created: {datetime.now().isoformat()}
requires_hitl: true
---

# Draft Generated by {skill}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Source:** {Path(file_path).name}

---

## Draft Content

[Skill would generate content here]

---

## Action Required

- [ ] Review and edit if needed
- [ ] Move to /Approved to execute
- [ ] Or move to /Rejected if not appropriate

---
*Generated by Ralph Wiggum Loop (Gold Tier)*
*Requires HITL approval*
"""
        
        with open(draft_path, 'w', encoding='utf-8') as f:
            f.write(draft_content)
        
        print(f"  Draft created: {draft_path}")
    
    def _check_draft_created(self, task: Dict) -> bool:
        """Check if draft was created in Pending_Approval"""
        # Check for any draft files related to this task
        draft_pattern = f"*{Path(task['file_path']).stem}*"
        drafts = list(self.pending_approval_dir.glob(draft_pattern))
        return len(drafts) > 0
    
    def _check_approval_status(self, task: Dict) -> bool:
        """Check if task has been approved (file moved to /Approved)"""
        # Check if corresponding file exists in Approved
        approved_pattern = f"*{Path(task['file_path']).stem}*"
        approved_files = list(self.approved_dir.glob(approved_pattern))
        return len(approved_files) > 0
    
    def _trigger_mcp(self, task: Dict) -> bool:
        """Trigger MCP server execution"""
        # This would integrate with actual MCP servers
        print(f"  MCP execution simulated")
        return True  # Simulate success
    
    def _move_to_done(self, file_path: str):
        """Move file to Done directory"""
        try:
            if Path(file_path).exists():
                dest_path = self.done_dir / Path(file_path).name
                shutil.move(file_path, dest_path)
                print(f"  Moved to Done: {dest_path}")
        except Exception as e:
            print(f"  Error moving file: {e}")

    def run_iteration(self) -> bool:
        """Run a single iteration of the loop"""
        self.iteration_count += 1
        print(f"\n{'='*60}")
        print(f"--- Ralph Wiggum Loop - Iteration {self.iteration_count}/{self.max_iterations} ---")
        print(f"{'='*60}")

        # Check for files needing processing in priority order
        files_to_process = []
        
        # 1. First check Approved (ready for MCP execution)
        approved_files = self.scan_approved()
        for f in approved_files:
            files_to_process.append({
                'path': f,
                'priority': 'high',  # Already approved
                'stage': 'mcp_execution'
            })
        
        # 2. Then check Pending_Approval (awaiting approval check)
        pending_files = self.scan_pending_approval()
        for f in pending_files:
            files_to_process.append({
                'path': f,
                'priority': 'medium',
                'stage': 'hitl_approval'
            })
        
        # 3. Finally check Needs_Action (new files)
        needs_action_files = self.scan_needs_action()
        for f in needs_action_files:
            files_to_process.append({
                'path': f,
                'priority': 'normal',
                'stage': 'analysis'
            })
        
        if not files_to_process:
            print("\nNo files to process in any directory")
            return True  # Nothing to do

        print(f"\nFound {len(files_to_process)} files to process")
        
        # Process each file
        tasks_completed = 0
        tasks_pending = 0
        
        for file_info in files_to_process:
            file_path = file_info['path']
            print(f"\nProcessing: {Path(file_path).name} (Stage: {file_info['stage']})")
            
            # Analyze the task
            task = self.task_analyzer(file_path)
            task['current_stage'] = file_info['stage']
            
            # Execute the task through workflow
            task_complete = self.execute_task(task)
            
            if task_complete:
                tasks_completed += 1
            else:
                tasks_pending += 1
        
        print(f"\n--- Iteration Summary ---")
        print(f"Tasks Completed: {tasks_completed}")
        print(f"Tasks Pending: {tasks_pending}")
        
        # Check if all tasks are complete
        all_complete = (tasks_pending == 0 and 
                       len(self.scan_needs_action()) == 0 and
                       len(self.scan_pending_approval()) == 0)
        
        if all_complete:
            print("\n✓ All tasks completed!")
            return True
        
        return False  # Continue loop

    def run(self, prompt: str = None) -> bool:
        """
        Run the Ralph Wiggum reasoning loop.
        
        Args:
            prompt: Optional prompt describing what to process
            
        Returns:
            bool: True if all tasks completed, False if max iterations reached
        """
        print("\n" + "="*60)
        print("RALPH WIGGUM REASONING LOOP (Gold Tier)")
        print("="*60)
        print(f"Prompt: {prompt or 'Process all files'}")
        print(f"Max Iterations: {self.max_iterations}")
        print(f"Audit Logging: {'Enabled' if self.audit_enabled else 'Disabled'}")
        print("="*60)
        
        # Log start
        self.log_audit(
            action_type="ralph_loop_started",
            target="ralph_loop_runner",
            result="success",
            parameters={
                'max_iterations': self.max_iterations,
                'prompt': prompt or 'Process all files'
            },
            message="Ralph Wiggum Loop started"
        )
        
        # Run iterations
        for i in range(self.max_iterations):
            completed = self.run_iteration()
            
            if completed:
                print("\n" + "="*60)
                print("TASK_COMPLETE: All tasks finished successfully!")
                print("="*60)
                
                # Log completion
                self.log_audit(
                    action_type="ralph_loop_completed",
                    target="ralph_loop_runner",
                    result="success",
                    parameters={
                        'iterations_run': self.iteration_count,
                        'tasks_processed': len(self.task_history)
                    },
                    message="Ralph Wiggum Loop completed"
                )
                
                return True
        
        print("\n" + "="*60)
        print(f"WARNING: Reached maximum iterations ({self.max_iterations})")
        print("="*60)
        
        # Log incomplete
        self.log_audit(
            action_type="ralph_loop_incomplete",
            target="ralph_loop_runner",
            result="partial",
            parameters={
                'iterations_run': self.iteration_count,
                'tasks_processed': len(self.task_history)
            },
            message=f"Loop ended after {self.max_iterations} iterations"
        )
        
        return False
    
    def get_task_history(self) -> List[Dict]:
        """Get task processing history"""
        return self.task_history
    
    def print_summary(self):
        """Print processing summary"""
        print("\n" + "="*60)
        print("RALPH WIGGUM LOOP SUMMARY")
        print("="*60)
        print(f"Iterations Run: {self.iteration_count}")
        print(f"Tasks Processed: {len(self.task_history)}")
        
        # Count by stage
        stages = {}
        for task in self.task_history:
            stage = task.get('stage', 'unknown')
            stages[stage] = stages.get(stage, 0) + 1
        
        print("\nTasks by Stage:")
        for stage, count in sorted(stages.items()):
            print(f"  {stage}: {count}")
        
        # Count by result
        results = {}
        for task in self.task_history:
            result = task.get('result', 'unknown')
            results[result] = results.get(result, 0) + 1
        
        print("\nTasks by Result:")
        for result, count in sorted(results.items()):
            print(f"  {result}: {count}")
        
        print("="*60)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Ralph Wiggum Reasoning Loop (Gold Tier)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./ralph-loop "Process multi-step task in Needs_Action" --max-iterations 20
  ./ralph-loop "Process sales leads" --max-iterations 15
  ./ralph-loop --max-iterations 20 --no-audit
        """
    )
    parser.add_argument('prompt', nargs='?', 
                       default="Process multi-step task in Needs_Action",
                       help='Prompt for the reasoning loop')
    parser.add_argument('--max-iterations', type=int, default=20,
                       help='Maximum number of iterations (default: 20 for Gold Tier)')
    parser.add_argument('--no-audit', action='store_true',
                       help='Disable audit logging')

    args = parser.parse_args()

    print(f"\nRunning Ralph Wiggum Loop (Gold Tier)")
    print(f"Prompt: '{args.prompt}'")
    print(f"Max Iterations: {args.max_iterations}")

    loop = RalphWiggumLoop(
        max_iterations=args.max_iterations,
        audit_enabled=not args.no_audit
    )
    
    success = loop.run(prompt=args.prompt)
    loop.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

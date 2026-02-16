#!/usr/bin/env python3
"""
Ralph Wiggum Reasoning Loop for Silver Tier
Implements Claude reasoning loop with TASK_COMPLETE promise
Processes files in /Needs_Action, analyzes with Task Analyzer, creates plan
"""

import os
import shutil
import glob
import time
from pathlib import Path
from typing import List, Dict, Any

class RalphWiggumLoop:
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.iteration_count = 0
        self.processed_files = []
        
    def scan_needs_action(self) -> List[str]:
        """Scan /Needs_Action for files to process"""
        needs_action_dir = Path("Needs_Action")
        if not needs_action_dir.exists():
            print("Needs_Action directory does not exist")
            return []
        
        # Get all files in Needs_Action
        files = list(needs_action_dir.glob("*"))
        return [str(f) for f in files if f.is_file()]
    
    def task_analyzer(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a file and determine what task needs to be performed
        This is a simplified version - in a real implementation, 
        this would connect to an AI model or complex analyzer
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Determine task type based on content
        if any(keyword in content for keyword in ['sales', 'client', 'project']):
            task_type = 'linkedin_post'
            description = 'Create LinkedIn post for business lead'
        elif any(keyword in content for keyword in ['urgent', 'invoice', 'payment']):
            task_type = 'financial_task'
            description = 'Handle financial matter'
        elif any(keyword in content for keyword in ['meeting', 'schedule', 'calendar']):
            task_type = 'schedule_task'
            description = 'Schedule meeting or appointment'
        else:
            task_type = 'general_task'
            description = 'General task to be handled'
        
        return {
            'file_path': file_path,
            'task_type': task_type,
            'description': description,
            'content': content
        }
    
    def execute_task(self, task: Dict[str, Any]) -> bool:
        """
        Execute the analyzed task
        Returns True if task is complete, False if it requires further steps
        """
        print(f"Executing task: {task['description']} for {task['file_path']}")
        
        # Handle different task types
        if task['task_type'] == 'linkedin_post':
            return self.handle_linkedin_post(task)
        elif task['task_type'] == 'financial_task':
            return self.handle_financial_task(task)
        elif task['task_type'] == 'schedule_task':
            return self.handle_schedule_task(task)
        else:
            return self.handle_general_task(task)
    
    def handle_linkedin_post(self, task: Dict[str, Any]) -> bool:
        """Handle LinkedIn post creation task"""
        # This would typically trigger the Auto LinkedIn Poster skill
        print(f"  Creating LinkedIn post for: {task['file_path']}")
        
        # Simulate checking if this requires HITL approval
        # For demo purposes, we'll say it requires approval (multi-step task)
        needs_approval = True
        
        if needs_approval:
            # Move to Pending_Approval for human approval
            pending_dir = Path("Pending_Approval")
            pending_dir.mkdir(exist_ok=True)
            
            dest_path = pending_dir / Path(task['file_path']).name
            shutil.move(task['file_path'], dest_path)
            print(f"  Moved to {dest_path} for approval")
            return False  # Task not complete, requires approval
        else:
            # If no approval needed, move to Done
            done_dir = Path("Done")
            done_dir.mkdir(exist_ok=True)
            
            dest_path = done_dir / Path(task['file_path']).name
            shutil.move(task['file_path'], dest_path)
            print(f"  Moved to {dest_path}")
            return True  # Task complete
    
    def handle_financial_task(self, task: Dict[str, Any]) -> bool:
        """Handle financial task"""
        print(f"  Handling financial task: {task['file_path']}")
        
        # Move to Done after processing
        done_dir = Path("Done")
        done_dir.mkdir(exist_ok=True)
        
        dest_path = done_dir / Path(task['file_path']).name
        shutil.move(task['file_path'], dest_path)
        print(f"  Moved to {dest_path}")
        return True  # Task complete
    
    def handle_schedule_task(self, task: Dict[str, Any]) -> bool:
        """Handle scheduling task"""
        print(f"  Handling scheduling task: {task['file_path']}")
        
        # Move to Done after processing
        done_dir = Path("Done")
        done_dir.mkdir(exist_ok=True)
        
        dest_path = done_dir / Path(task['file_path']).name
        shutil.move(task['file_path'], dest_path)
        print(f"  Moved to {dest_path}")
        return True  # Task complete
    
    def handle_general_task(self, task: Dict[str, Any]) -> bool:
        """Handle general task"""
        print(f"  Handling general task: {task['file_path']}")
        
        # Move to Done after processing
        done_dir = Path("Done")
        done_dir.mkdir(exist_ok=True)
        
        dest_path = done_dir / Path(task['file_path']).name
        shutil.move(task['file_path'], dest_path)
        print(f"  Moved to {dest_path}")
        return True  # Task complete
    
    def check_completion_promise(self) -> bool:
        """Check if all tasks are complete (TASK_COMPLETE promise)"""
        needs_action_files = self.scan_needs_action()
        return len(needs_action_files) == 0
    
    def run_iteration(self) -> bool:
        """Run a single iteration of the loop"""
        self.iteration_count += 1
        print(f"\n--- Iteration {self.iteration_count} ---")
        
        # Scan for files in Needs_Action
        files_to_process = self.scan_needs_action()
        
        if not files_to_process:
            print("No files to process in Needs_Action")
            return True  # Nothing to do, can exit
        
        print(f"Found {len(files_to_process)} files to process")
        
        # Process each file
        for file_path in files_to_process:
            print(f"Analyzing: {file_path}")
            
            # Analyze the task
            task = self.task_analyzer(file_path)
            
            # Execute the task
            task_complete = self.execute_task(task)
            
            if task_complete:
                print(f"Task completed: {file_path}")
            else:
                print(f"Task requires further steps: {file_path}")
        
        # Check if all tasks are complete
        all_complete = self.check_completion_promise()
        
        if all_complete:
            print("All tasks completed!")
            return True
        
        return False  # Continue loop
    
    def run(self):
        """Run the Ralph Wiggum reasoning loop"""
        print("Starting Ralph Wiggum Reasoning Loop...")
        print(f"Max iterations: {self.max_iterations}")
        
        for i in range(self.max_iterations):
            completed = self.run_iteration()
            
            if completed:
                print("\nTASK_COMPLETE: All tasks finished!")
                return True
        
        print(f"\nReached maximum iterations ({self.max_iterations}) without completing all tasks")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Ralph Wiggum Reasoning Loop')
    parser.add_argument('prompt', nargs='?', default="Process all files in /Needs_Action, analyze with Task Analyzer, create plan", 
                       help='Prompt for the reasoning loop')
    parser.add_argument('--max-iterations', type=int, default=10, 
                       help='Maximum number of iterations (default: 10)')
    
    args = parser.parse_args()
    
    print(f"Running Ralph Wiggum Loop with prompt: '{args.prompt}'")
    
    loop = RalphWiggumLoop(max_iterations=args.max_iterations)
    loop.run()

if __name__ == "__main__":
    main()
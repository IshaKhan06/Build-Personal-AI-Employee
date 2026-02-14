"""
File System Watcher for Bronze Tier AI Employee Project

Monitors the /Inbox folder and automatically processes new files by:
1. Copying them to /Needs_Action with a FILE_ prefix
2. Creating a .md metadata file with YAML frontmatter
3. Logging all actions to console

Installation:
    pip install watchdog

Usage:
    python watchers/filesystem_watcher.py

Testing:
    Drop any file in /Inbox folder to trigger the watcher
"""

import os
import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class InboxHandler(FileSystemEventHandler):
    """Handle file creation events in the Inbox folder."""
    
    def __init__(self, inbox_dir, needs_action_dir):
        self.inbox_dir = Path(inbox_dir)
        self.needs_action_dir = Path(needs_action_dir)
        
    def on_created(self, event):
        """Called when a file is created in the watched directory."""
        if not event.is_directory:
            self.process_new_file(event.src_path)
    
    def process_new_file(self, file_path):
        """Process a newly created file."""
        try:
            file_path = Path(file_path)
            
            # Skip temporary files that might be in the process of being written
            if file_path.name.startswith('.'):
                print(f"Skipping temporary file: {file_path.name}")
                return
                
            print(f"New file detected: {file_path.name}")
            
            # Copy file to Needs_Action with FILE_ prefix
            new_filename = f"FILE_{file_path.name}"
            destination_path = self.needs_action_dir / new_filename
            
            # Copy the file
            shutil.copy2(file_path, destination_path)
            print(f"Copied file to: {destination_path}")
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Create metadata .md file with YAML frontmatter
            metadata_filename = f"{file_path.stem}_metadata.md"
            metadata_path = self.needs_action_dir / metadata_filename
            
            metadata_content = f"""---
type: file_drop
original_name: {file_path.name}
size: {file_size}
status: pending
---
# Metadata for {file_path.name}

Original file: {file_path.name}
Size: {file_size} bytes
Status: pending
"""
            
            with open(metadata_path, 'w', encoding='utf-8') as meta_file:
                meta_file.write(metadata_content)
                
            print(f"Created metadata file: {metadata_path}")
            print(f"File processing complete for: {file_path.name}")
            
        except PermissionError:
            print(f"Permission denied when processing: {file_path}")
        except FileNotFoundError:
            print(f"File not found (may have been deleted): {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")


def main():
    """Main function to start the file system watcher."""
    # Define directory paths relative to the project root
    project_root = Path(__file__).parent.parent
    inbox_dir = project_root / "Inbox"
    needs_action_dir = project_root / "Needs_Action"
    
    # Verify directories exist
    if not inbox_dir.exists():
        print(f"Error: Inbox directory does not exist: {inbox_dir}")
        return
        
    if not needs_action_dir.exists():
        print(f"Error: Needs_Action directory does not exist: {needs_action_dir}")
        return
    
    # Create the event handler
    event_handler = InboxHandler(inbox_dir, needs_action_dir)
    
    # Create the observer
    observer = Observer()
    observer.schedule(event_handler, str(inbox_dir), recursive=False)
    
    # Start the observer
    observer.start()
    print(f"File system watcher started!")
    print(f"Monitoring: {inbox_dir}")
    print(f"Copying to: {needs_action_dir}")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(5)  # Check every 5 seconds (though actual events are handled asynchronously)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping file system watcher...")
    
    observer.join()
    print("File system watcher stopped.")


if __name__ == "__main__":
    main()
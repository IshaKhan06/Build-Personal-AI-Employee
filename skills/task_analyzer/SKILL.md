# Task Analyzer

## Description
Analyzes files in /Needs_Action, identifies type (file drop, etc.), creates simple action plan in Plan.md, checks if approval needed (e.g., payments or sensitive info), writes to /Pending_Approval if sensitive, uses Ralph Wiggum loop if multi-step task.

## Configuration
```json
{
  "name": "Task Analyzer",
  "version": "1.0",
  "description": "Analyzes files in the Needs_Action folder and determines appropriate actions",
  "author": "AI Employee System",
  "parameters": {
    "file_path": {
      "type": "string",
      "description": "Path to the file to analyze"
    }
  }
}
```

## Instructions
1. Analyze files in /Needs_Action
2. Identify type (file drop, etc.)
3. Create simple action plan in Plan.md
4. Check if approval needed (e.g., payments or sensitive info)
5. Write to /Pending_Approval if sensitive
6. Use Ralph Wiggum loop if multi-step task
7. Output analysis results

## Example Usage
@Task Analyzer analyze file.md
# Basic File Handler

## Description
Reads any .md file from /Needs_Action and summarizes its content, writes Plan.md in /Plans with simple checkboxes for next steps, moves completed files to /Done folder, always references Company_Handbook.md rules before any action.

## Configuration
```json
{
  "name": "Basic File Handler",
  "version": "1.0",
  "description": "Handles files in the Needs_Action folder by summarizing content and creating action plans",
  "author": "AI Employee System",
  "parameters": {
    "file_path": {
      "type": "string",
      "description": "Path to the file to process"
    }
  }
}
```

## Instructions
1. Read the specified .md file from /Needs_Action
2. Summarize its content
3. Write Plan.md in /Plans with simple checkboxes for next steps
4. Move completed files to /Done folder
5. Always reference Company_Handbook.md rules before any action
6. Output success message with full file paths

## Example Usage
@Basic File Handler process file.md
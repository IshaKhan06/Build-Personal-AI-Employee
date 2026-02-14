#!/bin/bash
# Basic File Handler Skill Implementation

# Function to read and summarize content from a file
handle_file() {
    local file_path="$1"
    
    # Check if file exists in Needs_Action folder
    if [ ! -f "../Needs_Action/$file_path" ]; then
        echo "Error: File $file_path not found in Needs_Action folder"
        return 1
    fi
    
    # Reference Company_Handbook.md rules before any action
    echo "Referencing Company_Handbook.md rules..."
    if [ -f "../Company_Handbook.md" ]; then
        cat ../Company_Handbook.md
    else
        echo "Warning: Company_Handbook.md not found"
    fi
    
    # Read and summarize the content
    echo "Reading file: $file_path"
    content=$(cat "../Needs_Action/$file_path")
    echo "Content of $file_path:"
    echo "$content"
    
    # Create summary
    summary="Summary of $file_path: $(echo "$content" | head -n 5)"
    
    # Write Plan.md in Plans folder with simple checkboxes for next steps
    plan_file="../Plans/Plan.md"
    echo "# Action Plan for $file_path" > "$plan_file"
    echo "" >> "$plan_file"
    echo "- [ ] Review content: $summary" >> "$plan_file"
    echo "- [ ] Determine next steps" >> "$plan_file"
    echo "- [ ] Execute required actions" >> "$plan_file"
    echo "- [ ] Verify completion" >> "$plan_file"
    
    # Move completed file to Done folder
    mv "../Needs_Action/$file_path" "../Done/$file_path"
    
    # Output success message with full file paths
    echo "Success! Processed file: ../Needs_Action/$file_path"
    echo "Created plan: $plan_file"
    echo "Moved file to: ../Done/$file_path"
}

# Main execution
if [ $# -eq 0 ]; then
    echo "Usage: $0 <filename>"
    echo "Example: $0 example.md"
    exit 1
fi

handle_file "$1"
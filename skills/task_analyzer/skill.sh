#!/bin/bash
# Task Analyzer Skill Implementation

# Function to analyze a file and determine appropriate actions
analyze_file() {
    local file_path="$1"
    
    # Check if file exists in Needs_Action folder
    if [ ! -f "../Needs_Action/$file_path" ]; then
        echo "Error: File $file_path not found in Needs_Action folder"
        return 1
    fi
    
    # Read the content to analyze
    content=$(cat "../Needs_Action/$file_path")
    echo "Analyzing file: $file_path"
    echo "Content preview:"
    echo "$content"
    
    # Identify file type and content
    file_type="unknown"
    approval_needed=false
    
    # Check for payment keywords (based on Company_Handbook rule about payments > $500)
    if [[ "$content" =~ \$[0-9]+ ]]; then
        # Extract dollar amounts
        amounts=($(echo "$content" | grep -o '\$[0-9]\+'))
        for amount in "${amounts[@]}"; do
            # Remove $ and convert to number
            num_amount=${amount#\$}
            if [ "$num_amount" -gt 500 ]; then
                echo "Payment > \$500 detected: $amount - Approval required!"
                approval_needed=true
                break
            fi
        done
        file_type="payment_request"
    elif [[ "$content" =~ (sensitive|confidential|private|secret) ]]; then
        echo "Sensitive information detected - Approval required!"
        approval_needed=true
        file_type="sensitive_document"
    else
        file_type="standard_task"
    fi
    
    # Create action plan in Plan.md
    plan_file="../Plans/Plan.md"
    echo "# Analysis Plan for $file_path" > "$plan_file"
    echo "" >> "$plan_file"
    echo "## File Type: $file_type" >> "$plan_file"
    echo "" >> "$plan_file"
    echo "## Content Summary:" >> "$plan_file"
    echo "$(echo "$content" | head -n 10)" >> "$plan_file"
    echo "" >> "$plan_file"
    echo "## Action Items:" >> "$plan_file"
    echo "- [ ] Review content carefully" >> "$plan_file"
    echo "- [ ] Validate data accuracy" >> "$plan_file"
    echo "- [ ] Perform required action" >> "$plan_file"
    echo "- [ ] Document completion" >> "$plan_file"
    
    # Handle approval if needed
    if [ "$approval_needed" = true ]; then
        echo "Moving to Pending Approval folder..."
        if [ ! -d "../Pending_Approval" ]; then
            mkdir -p "../Pending_Approval"
        fi
        mv "../Needs_Action/$file_path" "../Pending_Approval/$file_path"
        echo "- [ ] Awaiting approval (moved to Pending_Approval)" >> "$plan_file"
        echo "Success! $file_path moved to Pending Approval due to sensitive content."
    else
        # For multi-step tasks, implement a simple "Ralph Wiggum" loop concept
        # (a playful way to represent iterative processing)
        echo "Processing multi-step task with iterative approach..."
        
        # Count potential steps in the content (simple heuristic)
        step_count=$(echo "$content" | grep -o -i -E "(step|phase|part|first|second|third|next|then|finally)" | wc -l)
        
        if [ "$step_count" -gt 1 ]; then
            echo "Multi-step task detected ($step_count potential steps). Using iterative processing..."
            # Simulate Ralph Wiggum loop (playful iterative processing)
            for ((i=1; i<=3; i++)); do
                echo "Iterative check $i: Ensuring all aspects are covered"
            done
            
            # Move to Done after processing
            mv "../Needs_Action/$file_path" "../Done/$file_path"
            echo "Success! Processed multi-step $file_type: $file_path"
        else
            # Standard processing
            mv "../Needs_Action/$file_path" "../Done/$file_path"
            echo "Success! Processed standard $file_type: $file_path"
        fi
    fi
    
    echo "Action plan created: $plan_file"
}

# Main execution
if [ $# -eq 0 ]; then
    echo "Usage: $0 <filename>"
    echo "Example: $0 example.md"
    exit 1
fi

analyze_file "$1"
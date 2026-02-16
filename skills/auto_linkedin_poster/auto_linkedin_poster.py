"""
Auto LinkedIn Poster Skill
Scans /Needs_Action for sales/business lead messages and drafts LinkedIn posts
"""

import os
import glob
import re
import yaml
from datetime import datetime
from pathlib import Path

def scan_needs_action_for_leads():
    """
    Scan /Needs_Action for sales/business lead messages with keywords: sales, client, project
    """
    leads = []
    needs_action_dir = Path("Needs_Action")
    
    # Look for markdown files in Needs_Action
    for file_path in needs_action_dir.glob("*.md"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check if the content contains any of the keywords
            content_lower = content.lower()
            if any(keyword in content_lower for keyword in ['sales', 'client', 'project']):
                leads.append({
                    'file_path': str(file_path),
                    'content': content,
                    'filename': file_path.name
                })
    
    return leads

def extract_company_info():
    """
    Reference Company_Handbook.md for company information to customize posts
    """
    handbook_path = Path("Company_Handbook.md")
    company_info = {
        'services': [],
        'values': [],
        'tone': 'professional'
    }
    
    if handbook_path.exists():
        with open(handbook_path, 'r', encoding='utf-8') as f:
            handbook_content = f.read()
            
            # Extract services mentioned in handbook
            service_matches = re.findall(r'service[:\-\s]+([^\n\r]+)', handbook_content, re.IGNORECASE)
            company_info['services'] = [s.strip().title() for s in service_matches if s.strip()]
            
            # Extract values mentioned in handbook
            value_matches = re.findall(r'value[:\-\s]+([^\n\r]+)', handbook_content, re.IGNORECASE)
            company_info['values'] = [v.strip().title() for v in value_matches if v.strip()]
    
    return company_info

def draft_linkedin_post(lead_content, company_info):
    """
    Draft a LinkedIn post based on the lead information
    """
    # Extract potential service and benefit from the lead content
    content_lower = lead_content.lower()
    
    # Default values
    service = "our services"
    benefit = "business growth"
    
    # Try to extract service from the lead content
    if 'sales' in content_lower:
        service = "sales solutions"
        benefit = "increased revenue"
    elif 'client' in content_lower:
        service = "client management solutions"
        benefit = "better client relationships"
    elif 'project' in content_lower:
        service = "project management services"
        benefit = "successful project delivery"
    
    # If company info has specific services, use the first one
    if company_info['services']:
        service = company_info['services'][0]
    
    # Create the post
    post_text = f"Excited to offer {service} for {benefit}! DM for more."
    
    return post_text

def save_draft(post_content):
    """
    Save draft to /Plans/linkedin_post_[date].md with YAML frontmatter
    """
    plans_dir = Path("Plans")
    plans_dir.mkdir(exist_ok=True)
    
    # Create filename with current date
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"linkedin_post_{date_str}.md"
    filepath = plans_dir / filename
    
    # Create YAML frontmatter
    yaml_frontmatter = {
        'type': 'linkedin_post',
        'content': post_content,
        'status': 'draft',
        'created': datetime.now().isoformat(),
        'source': 'auto_linkedin_poster'
    }
    
    # Write the file with YAML frontmatter
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("---\n")
        yaml.dump(yaml_frontmatter, f, default_flow_style=False)
        f.write("---\n\n")
        f.write(post_content)
    
    return str(filepath)

def move_to_approval(filepath):
    """
    Move the draft to /Pending_Approval for human approval
    """
    pending_dir = Path("Pending_Approval")
    pending_dir.mkdir(exist_ok=True)
    
    # Move the file to Pending_Approval
    new_filepath = pending_dir / Path(filepath).name
    os.rename(filepath, new_filepath)
    
    return str(new_filepath)

def main():
    """
    Main function to process sales leads and create LinkedIn post drafts
    """
    print("Auto LinkedIn Poster: Starting scan for sales leads...")
    
    # Scan for leads
    leads = scan_needs_action_for_leads()
    
    if not leads:
        print("No sales/business leads found in Needs_Action folder.")
        return
    
    print(f"Found {len(leads)} potential leads in Needs_Action folder.")
    
    # Extract company information
    company_info = extract_company_info()
    
    # Process each lead
    for i, lead in enumerate(leads):
        print(f"Processing lead {i+1}/{len(leads)}: {lead['filename']}")
        
        # Draft LinkedIn post
        post_content = draft_linkedin_post(lead['content'], company_info)
        
        # Save draft to Plans folder
        draft_path = save_draft(post_content)
        print(f"Draft saved to: {draft_path}")
        
        # Move to Pending_Approval for human approval
        approval_path = move_to_approval(draft_path)
        print(f"Moved to approval: {approval_path}")
        
        print(f"LinkedIn post draft created and moved to approval: {approval_path}")
    
    print("Auto LinkedIn Poster: Processing complete.")

if __name__ == "__main__":
    main()
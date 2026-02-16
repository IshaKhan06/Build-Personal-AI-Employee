import os
import time
from datetime import datetime
import json
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import re


class GmailWatcher:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.creds = None
        self.service = None
        self.setup_credentials()
        
    def setup_credentials(self):
        """Setup Gmail API credentials"""
        # Load credentials from credentials.json in root directory
        credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
        token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.json')

        # Load existing token if available
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        else:
            # Always use OAuth flow to get proper credentials
            client_secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                              'client_secret_854414858878-vdnp38fgnp123sunh5acg39evvkgoasb.apps.googleusercontent.com.json')
            
            if os.path.exists(client_secrets_path):
                from google_auth_oauthlib.flow import InstalledAppFlow
                
                print("=" * 60)
                print("Gmail Authentication Required")
                print("=" * 60)
                print("Opening browser for authentication...")
                print("Please sign in with your Google account.")
                print("")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_path, self.SCOPES
                )
                
                self.creds = flow.run_local_server(port=0, open_browser=True)
                
                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())
                
                print("")
                print("Authentication successful! Token saved.")
                print("=" * 60)
            else:
                print(f"Client secrets file not found at {client_secrets_path}")
                print("Please download your client_secret from Google Cloud Console")
                print("and place it in the root directory.")
                self.creds = None
                return
            
        # Refresh token if needed
        if self.creds and self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
            
        # Build the service
        if self.creds:
            self.service = build('gmail', 'v1', credentials=self.creds)
    
    def search_emails(self, query):
        """Search for emails based on query"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10  # Limit to last 10 emails
            ).execute()
            
            messages = results.get('messages', [])
            return messages
        except Exception as e:
            print(f"Error searching emails: {e}")
            return []
    
    def get_email_details(self, msg_id):
        """Get detailed information about an email"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id
            ).execute()
            
            # Extract headers
            headers = {header['name']: header['value'] for header in message['payload']['headers']}
            
            # Get email body
            body = ""
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        import base64
                        body_data = part['body']['data']
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        break
            else:
                import base64
                body_data = message['payload']['body']['data']
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                
            return {
                'id': msg_id,
                'from': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
                'received': headers.get('Date', ''),
                'body': body
            }
        except Exception as e:
            print(f"Error getting email details: {e}")
            return None
    
    def save_email_to_markdown(self, email_data):
        """Save email data to markdown file with YAML frontmatter"""
        # Determine priority based on keywords
        keywords = ['urgent', 'invoice', 'payment', 'sales']
        body_lower = email_data['body'].lower()
        subject_lower = email_data['subject'].lower()
        
        priority = 'low'
        for keyword in keywords:
            if keyword in body_lower or keyword in subject_lower:
                priority = 'high'
                break
        
        # Create YAML frontmatter
        yaml_frontmatter = f"""---
type: gmail
from: "{email_data['from']}"
subject: "{email_data['subject']}"
received: "{email_data['received']}"
priority: {priority}
status: pending
---
"""
        
        # Create markdown content
        content = f"{yaml_frontmatter}\n## Email Content\n\n{email_data['body'][:500]}...\n\n"
        
        # Generate filename based on timestamp and subject
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subject_clean = re.sub(r'[^\w\s-]', '', email_data['subject'])[:50]
        filename = f"gmail_{timestamp}_{subject_clean}.md"
        
        # Save to Needs_Action directory
        needs_action_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Needs_Action')
        filepath = os.path.join(needs_action_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Saved email to {filepath}")
    
    def run(self):
        """Main loop to monitor Gmail"""
        print("Starting Gmail Watcher...")

        try:
            while True:
                try:
                    # Search for unread important emails with keywords
                    query = 'is:unread label:important (urgent OR invoice OR payment OR sales)'
                    messages = self.search_emails(query)

                    for msg in messages:
                        email_data = self.get_email_details(msg['id'])
                        if email_data:
                            self.save_email_to_markdown(email_data)
                            
                            # Mark as read after processing
                            self.service.users().messages().modify(
                                userId='me',
                                id=msg['id'],
                                body={'removeLabelIds': ['UNREAD']}
                            ).execute()
                    
                    print(f"Checked Gmail, found {len(messages)} matching emails")
                    
                    # Wait 120 seconds before next check
                    time.sleep(120)
                    
                except Exception as e:
                    print(f"Error in Gmail Watcher: {e}")
                    time.sleep(120)  # Wait before retrying
        except KeyboardInterrupt:
            print("Gmail Watcher stopped by user")


if __name__ == "__main__":
    """
    HOW TO RUN:
    1. Install dependencies: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
    2. Ensure credentials.json is in the root directory
    3. Run with PM2: pm2 start gmail_watcher.py --name gmail-watcher
    
    HOW TO TEST:
    1. Send a test email to your Gmail account with subject or body containing one of the keywords: urgent, invoice, payment, sales
    2. Mark the email as important
    3. Wait for the script to detect and save the email to the Needs_Action folder
    """
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\nGmail Watcher stopped by user")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        watcher = GmailWatcher()
        if watcher.service:
            watcher.run()
        else:
            print("Gmail Watcher could not start. Please check credentials.")
    except KeyboardInterrupt:
        print("\nGmail Watcher stopped by user")
    except Exception as e:
        print(f"Error: {e}")
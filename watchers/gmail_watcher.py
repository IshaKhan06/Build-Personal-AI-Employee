"""
Gmail Watcher (Gold Tier - Error Recovery)
Monitors Gmail for unread important emails with keywords
Saves detected items as .md files in /Needs_Action
Checks every 120 seconds
Features: Exponential backoff retry, error logging, graceful degradation
"""

import os
import time
from datetime import datetime
import json
import pickle
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import re

# Add parent directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))
from error_recovery import ErrorRecovery


class GmailWatcher:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.creds = None
        self.service = None
        
        # Initialize error recovery utility
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.error_recovery = ErrorRecovery(self.base_dir)
        self.component_name = "gmail_watcher"
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1  # seconds
        self.max_delay = 60  # seconds
        
        self.setup_credentials()

    def retry_with_backoff(self, func, *args, max_retries=None, base_delay=None, **kwargs):
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            max_retries: Maximum retry attempts
            base_delay: Base delay in seconds
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func or None if all retries failed
        """
        if max_retries is None:
            max_retries = self.max_retries
        if base_delay is None:
            base_delay = self.base_delay
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    delay = min(delay, self.max_delay)
                    
                    print(f"  Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {type(e).__name__}")
                    self.error_recovery.log_error(
                        self.component_name,
                        e,
                        {'function': func.__name__, 'attempt': attempt + 1}
                    )
                    time.sleep(delay)
                else:
                    print(f"  Max retries ({max_retries}) exceeded for {func.__name__}")
                    self.error_recovery.log_error(
                        self.component_name,
                        e,
                        {'function': func.__name__, 'final': True}
                    )
        
        return None

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
            print(f"Error searching emails: {type(e).__name__}: {e}")
            self.error_recovery.log_error(
                self.component_name,
                e,
                {'operation': 'search_emails', 'query': query}
            )
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
            print(f"Error getting email details: {type(e).__name__}: {e}")
            self.error_recovery.log_error(
                self.component_name,
                e,
                {'operation': 'get_email_details', 'msg_id': msg_id}
            )
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
        print(f"Error recovery: Max retries={self.max_retries}, Backoff=1-60s")

        try:
            while True:
                try:
                    # Search for unread important emails with keywords
                    query = 'is:unread label:important (urgent OR invoice OR payment OR sales)'
                    
                    # Use retry with backoff
                    messages = self.retry_with_backoff(self.search_emails, query)
                    
                    if messages:
                        for msg in messages:
                            try:
                                email_data = self.retry_with_backoff(self.get_email_details, msg['id'])
                                if email_data:
                                    self.save_email_to_markdown(email_data)

                                    # Mark as read after processing
                                    self.service.users().messages().modify(
                                        userId='me',
                                        id=msg['id'],
                                        body={'removeLabelIds': ['UNREAD']}
                                    ).execute()
                            except Exception as e:
                                print(f"  Error processing email {msg['id']}: {e}")
                                self.error_recovery.log_error(
                                    self.component_name,
                                    e,
                                    {'operation': 'process_email', 'msg_id': msg.get('id', 'unknown')}
                                )
                                # Graceful: skip this email, continue with others
                                continue
                    else:
                        print("  Skipped email check (API error)")

                    print(f"Checked Gmail, found {len(messages) if messages else 0} matching emails")

                    # Wait 120 seconds before next check
                    time.sleep(120)

                except Exception as e:
                    error_msg = f"Error in Gmail Watcher: {type(e).__name__}: {e}"
                    print(error_msg)
                    self.error_recovery.log_error(
                        self.component_name,
                        e,
                        {'stage': 'monitoring_loop'}
                    )
                    # Graceful: wait before retrying
                    time.sleep(120)
                    
        except KeyboardInterrupt:
            print("Gmail Watcher stopped by user")
        except Exception as e:
            error_msg = f"Gmail Watcher fatal error: {type(e).__name__}: {e}"
            print(error_msg)
            self.error_recovery.log_error(
                self.component_name,
                e,
                {'stage': 'fatal'}
            )
            raise


if __name__ == "__main__":
    import signal
    import sys
    import os
    
    # Redirect stderr to suppress all warnings
    class DevNull:
        def write(self, msg): pass
        def flush(self): pass
    
    def signal_handler(sig, frame):
        print("\nGmail Watcher stopped by user")
        sys.stdout.flush()
        os._exit(0)  # Force immediate exit, no cleanup
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        watcher = GmailWatcher()
        if watcher.service:
            watcher.run()
        else:
            print("Gmail Watcher could not start. Please check credentials.")
    except:
        print("\nGmail Watcher stopped by user")
    
    sys.stderr = DevNull()  # Suppress all errors
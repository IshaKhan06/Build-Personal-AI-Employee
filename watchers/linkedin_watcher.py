"""
LinkedIn Watcher (Gold Tier - Error Recovery)
Monitors LinkedIn for notifications and messages
Saves detected items as .md files in /Needs_Action
Checks every 60 seconds
Features: Exponential backoff retry, error logging, graceful degradation
"""

import os
import time
import asyncio
from datetime import datetime
import re
import sys
from playwright.async_api import async_playwright

# Add parent directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))
from error_recovery import ErrorRecovery


class LinkedInWatcher:
    def __init__(self):
        self.session_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'session', 'linkedin')
        os.makedirs(self.session_path, exist_ok=True)
        
        # Initialize error recovery utility
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.error_recovery = ErrorRecovery(self.base_dir)
        self.component_name = "linkedin_watcher"
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1  # seconds
        self.max_delay = 60  # seconds
        
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except:
            pass
        
    async def setup_browser(self):
        """Setup browser with persistent context"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.session_path,
            headless=False,  # Set to True if you want to run in background
            viewport={'width': 1280, 'height': 800}
        )
        self.page = await self.browser.new_page()
        
    async def login_linkedin(self):
        """Navigate to LinkedIn and wait for login"""
        await self.page.goto('https://www.linkedin.com/uas/login')
        
        # Wait for user to manually login
        print("Please login to LinkedIn in the browser window.")
        print("After logging in, navigate to your LinkedIn homepage.")
        
        # Wait for navigation to homepage (after login)
        login_success = False
        timeout = 120000  # 120 seconds timeout
        start_time = time.time()
        
        while not login_success and (time.time() - start_time) * 1000 < timeout:
            try:
                # Check if we're on the feed/homepage
                current_url = await self.page.evaluate("window.location.href")
                if 'linkedin.com/feed' in current_url or 'linkedin.com/news' in current_url:
                    print("LinkedIn logged in successfully")
                    login_success = True
                    break
                else:
                    print("Waiting for LinkedIn login...")
                    await self.page.wait_for_timeout(5000)  # Wait 5 seconds before checking again
            except:
                # Silently ignore errors during login check
                await self.page.wait_for_timeout(5000)
        
        if not login_success:
            print("Timeout waiting for LinkedIn login. Please ensure you logged in and navigated to your homepage.")
            raise Exception("LinkedIn login timeout")
        
    async def check_messages_and_notifications(self):
        """Check for new messages and notifications with business keywords"""
        # Keywords to look for
        keywords = ['sales', 'client', 'project']
        
        matching_items = []
        
        # Check messages
        try:
            # Navigate to messages
            await self.page.goto('https://www.linkedin.com/messaging/')
            await self.page.wait_for_timeout(3000)  # Wait for page to load
            
            # Look for unread messages
            # Using a more general selector for unread messages
            unread_messages = await self.page.query_selector_all('[data-test-is-unread]')
            
            for message in unread_messages:
                try:
                    # Get sender name
                    sender_element = await message.query_selector('img[alt], span[aria-hidden="true"]')
                    sender = await sender_element.text_content() if sender_element else "Unknown"
                    
                    # Get message preview
                    preview_element = await message.query_selector('p, span, div')
                    preview = await preview_element.text_content() if preview_element else ""
                    
                    # Check if message contains keywords
                    preview_lower = preview.lower()
                    for keyword in keywords:
                        if keyword in preview_lower:
                            matching_items.append({
                                'type': 'message',
                                'sender': sender.strip(),
                                'preview': preview.strip(),
                                'keyword_found': keyword
                            })
                            break  # Found a keyword, no need to check others
                            
                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue
        except Exception as e:
            print(f"Error checking messages: {e}")
        
        # Check notifications
        try:
            # Navigate to notifications
            await self.page.goto('https://www.linkedin.com/notifications/')
            await self.page.wait_for_timeout(3000)  # Wait for page to load
            
            # Look for unread notifications
            notification_elements = await self.page.query_selector_all('[data-test-notification]')
            
            for notification in notification_elements:
                try:
                    # Get notification text
                    text_element = await notification.query_selector('span, p, div')
                    notification_text = await text_element.text_content() if text_element else ""
                    
                    # Check if notification contains keywords
                    text_lower = notification_text.lower()
                    for keyword in keywords:
                        if keyword in text_lower:
                            matching_items.append({
                                'type': 'notification',
                                'sender': 'LinkedIn Notification',
                                'preview': notification_text.strip(),
                                'keyword_found': keyword
                            })
                            break  # Found a keyword, no need to check others
                            
                except Exception as e:
                    print(f"Error processing notification: {e}")
                    continue
        except Exception as e:
            print(f"Error checking notifications: {e}")
        
        return matching_items
    
    def save_item_to_markdown(self, item_data):
        """Save item data to markdown file with YAML frontmatter"""
        # Determine priority based on keyword
        priority_map = {'sales': 'high', 'client': 'medium', 'project': 'medium'}
        priority = priority_map.get(item_data['keyword_found'], 'low')
        
        # Create YAML frontmatter
        yaml_frontmatter = f"""---
type: linkedin_{item_data['type']}
from: "{item_data['sender']}"
subject: "LinkedIn {item_data['type']} - {item_data['keyword_found']} keyword found"
received: "{datetime.now().isoformat()}"
priority: {priority}
status: pending
---
"""
        
        # Create markdown content
        content = f"{yaml_frontmatter}\n## LinkedIn {item_data['type'].title()} Details\n\nPreview: {item_data['preview']}\nKeyword found: {item_data['keyword_found']}\n\n"
        
        # Generate filename based on timestamp and sender
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sender_clean = re.sub(r'[^\w\s-]', '', item_data['sender'])[:50]
        filename = f"linkedin_{item_data['type']}_{timestamp}_{sender_clean}_{item_data['keyword_found']}.md"
        
        # Save to Needs_Action directory
        needs_action_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Needs_Action')
        filepath = os.path.join(needs_action_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Saved LinkedIn {item_data['type']} to {filepath}")

    async def retry_with_backoff(self, func, *args, max_retries=None, base_delay=None, **kwargs):
        """Execute function with exponential backoff retry."""
        if max_retries is None:
            max_retries = self.max_retries
        if base_delay is None:
            base_delay = self.base_delay
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    delay = min(delay, self.max_delay)
                    print(f"  Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {type(e).__name__}")
                    self.error_recovery.log_error(self.component_name, e, {'function': func.__name__, 'attempt': attempt + 1})
                    await asyncio.sleep(delay)
                else:
                    print(f"  Max retries ({max_retries}) exceeded for {func.__name__}")
                    self.error_recovery.log_error(self.component_name, e, {'function': func.__name__, 'final': True})
        
        return None

    async def run(self):
        """Main loop to monitor LinkedIn"""
        print("Starting LinkedIn Watcher...")
        print(f"Error recovery: Max retries={self.max_retries}, Backoff=1-60s")

        try:
            await self.setup_browser()
            await self.login_linkedin()

            while True:
                try:
                    # Use retry with backoff
                    matching_items = await self.retry_with_backoff(self.check_messages_and_notifications)

                    if matching_items:
                        for item in matching_items:
                            try:
                                self.save_item_to_markdown(item)
                            except Exception as e:
                                print(f"  Error saving item: {e}")
                                self.error_recovery.log_error(
                                    self.component_name, e,
                                    {'operation': 'save_item_to_markdown', 'type': item.get('type', 'unknown')}
                                )
                                continue
                    else:
                        print("  Skipped check (API error)")

                    print(f"Checked LinkedIn, found {len(matching_items) if matching_items else 0} matching items")

                    # Wait 60 seconds before next check
                    await self.page.wait_for_timeout(60000)

                except Exception as e:
                    error_msg = f"Error in LinkedIn Watcher: {type(e).__name__}: {e}"
                    print(error_msg)
                    self.error_recovery.log_error(self.component_name, e, {'stage': 'monitoring_loop'})
                    # Graceful: wait before retrying
                    await self.page.wait_for_timeout(60000)
                    
        except Exception as e:
            error_msg = f"LinkedIn Watcher fatal error: {type(e).__name__}: {e}"
            print(error_msg)
            self.error_recovery.log_error(self.component_name, e, {'stage': 'fatal'})
            raise
        finally:
            await self.cleanup()


if __name__ == "__main__":
    import signal
    import sys
    import os
    
    # Redirect stderr to suppress all warnings
    class DevNull:
        def write(self, msg): pass
        def flush(self): pass
    
    def signal_handler(sig, frame):
        print("\nLinkedIn Watcher stopped by user")
        sys.stdout.flush()
        os._exit(0)  # Force immediate exit, no cleanup
    
    signal.signal(signal.SIGINT, signal_handler)
    
    async def main():
        watcher = LinkedInWatcher()
        await watcher.run()
    
    sys.stderr = DevNull()  # Suppress all errors
    asyncio.run(main())
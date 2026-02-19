"""
Twitter (X) Watcher (Gold Tier - Error Recovery)
Monitors DMs, tweets, and notifications on Twitter (X) for keywords: sales, client, project
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
import subprocess
from playwright.async_api import async_playwright

# Add parent directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))
from error_recovery import ErrorRecovery


class TwitterWatcher:
    def __init__(self):
        """Initialize the Twitter Watcher."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.session_path = os.path.join(base_dir, 'session', 'twitter')

        # Ensure session directory exists
        os.makedirs(self.session_path, exist_ok=True)

        self.needs_action_dir = os.path.join(base_dir, 'Needs_Action')
        os.makedirs(self.needs_action_dir, exist_ok=True)

        # Initialize error recovery utility
        self.error_recovery = ErrorRecovery(base_dir)
        self.component_name = "twitter_watcher"

        self.playwright = None
        self.browser = None
        self.page = None

        # Keywords to detect
        self.keywords = ['sales', 'client', 'project']

        # Check interval in seconds
        self.check_interval = 60

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1  # seconds
        self.max_delay = 60  # seconds

    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Cleanup error: {e}")

    async def setup_browser(self, user_data_dir):
        """Setup browser with persistent context using system Chrome"""
        self.playwright = await async_playwright().start()
        
        # Use system Chrome on Windows
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
        print(f"Using Chrome: {chrome_path}")
        print("INFO: Close the browser window to stop the watcher")
        print("INFO: Or press Ctrl+C to stop")
        
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={'width': 1366, 'height': 768},
            executable_path=chrome_path
        )
        self.page = await self.browser.new_page()
        return self.page

    async def check_window_closed_manually(self):
        """Manually check if browser window was closed by trying to access it"""
        try:
            if not self.page:
                return True
            # Try to get page title - this will fail if page/window is closed
            await self.page.title()
            # Also try a simple evaluation
            await self.page.evaluate('1')
            return False
        except Exception as e:
            # Page is closed or disconnected
            error_msg = str(e).lower()
            if 'closed' in error_msg or 'target' in error_msg or 'context' in error_msg:
                return True
            return False

    async def login_twitter(self):
        """Navigate to Twitter (X) and wait for login"""
        print("\n" + "="*50)
        print("TWITTER (X) MONITORING")
        print("="*50)
        print("Opening Twitter (X). Please log in if not already logged in.")
        print("Once logged in, the watcher will monitor for DMs/tweets/notifications.")
        
        await self.page.goto('https://twitter.com/')
        
        # Wait for page to load and check if logged in
        login_success = False
        timeout = 180000  # 3 minutes timeout
        start_time = time.time()
        
        while not login_success and (time.time() - start_time) * 1000 < timeout:
            try:
                # Check if logged in by looking for the main feed or profile elements
                feed_element = await self.page.query_selector('[data-testid="primaryColumn"], [role="main"]')
                if feed_element:
                    # Also check for login button (not logged in)
                    login_button = await self.page.query_selector('text=Sign in')
                    if not login_button:
                        print("Twitter logged in successfully!")
                        login_success = True
                        break
                print("Waiting for Twitter login...")
                await self.page.wait_for_timeout(5000)
            except Exception as e:
                await self.page.wait_for_timeout(5000)
        
        if not login_success:
            print("Timeout waiting for Twitter login. Please ensure you are logged in.")
            raise Exception("Twitter login timeout")

    async def check_twitter_dms(self):
        """Check Twitter Direct Messages for messages with keywords"""
        matching_items = []
        
        try:
            # Navigate to Messages
            await self.page.goto('https://twitter.com/messages')
            await self.page.wait_for_timeout(3000)
            
            # Look for conversation elements
            conversation_elements = await self.page.query_selector_all(
                '[role="group"] article, div[role="button"][aria-label*="message"]'
            )
            
            for elem in conversation_elements[:10]:  # Check up to 10 conversations
                try:
                    # Get conversation text
                    text_content = await elem.inner_text()
                    
                    # Check for keywords
                    text_lower = text_content.lower()
                    for keyword in self.keywords:
                        if keyword in text_lower:
                            # Try to extract username
                            username_elem = await elem.query_selector('[dir="auto"], span:not([class*="icon"])')
                            username = await username_elem.text_content() if username_elem else "Unknown"
                            
                            matching_items.append({
                                'platform': 'twitter',
                                'type': 'dm',
                                'from': username,
                                'content': text_content[:300],  # Limit content length
                                'keyword_found': keyword
                            })
                            break
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error checking Twitter DMs: {e}")
        
        return matching_items

    async def check_twitter_notifications(self):
        """Check Twitter notifications for mentions/tweets with keywords"""
        matching_items = []
        
        try:
            # Navigate to Notifications
            await self.page.goto('https://twitter.com/notifications')
            await self.page.wait_for_timeout(3000)
            
            # Look for notification elements
            notification_elements = await self.page.query_selector_all(
                'article[data-testid="notification"], [role="article"]'
            )
            
            for elem in notification_elements[:10]:
                try:
                    # Get notification text
                    text_content = await elem.inner_text()
                    
                    # Check for keywords
                    text_lower = text_content.lower()
                    for keyword in self.keywords:
                        if keyword in text_lower:
                            # Try to extract username
                            username_elem = await elem.query_selector('[dir="auto"]')
                            username = await username_elem.text_content() if username_elem else "Unknown"
                            
                            matching_items.append({
                                'platform': 'twitter',
                                'type': 'notification',
                                'from': username,
                                'content': text_content[:300],
                                'keyword_found': keyword
                            })
                            break
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error checking Twitter notifications: {e}")
        
        return matching_items

    async def check_twitter_mentions(self):
        """Check Twitter mentions for tweets with keywords"""
        matching_items = []
        
        try:
            # Navigate to Mentions via notifications tab
            await self.page.goto('https://twitter.com/notifications/mentions')
            await self.page.wait_for_timeout(3000)
            
            # Look for tweet elements
            tweet_elements = await self.page.query_selector_all(
                'article[data-testid="tweet"]'
            )
            
            for elem in tweet_elements[:10]:
                try:
                    # Get tweet text
                    text_content = await elem.inner_text()
                    
                    # Check for keywords
                    text_lower = text_content.lower()
                    for keyword in self.keywords:
                        if keyword in text_lower:
                            # Try to extract username
                            username_elem = await elem.query_selector('[data-testid="User-Name"]')
                            username = await username_elem.text_content() if username_elem else "Unknown"
                            
                            matching_items.append({
                                'platform': 'twitter',
                                'type': 'mention',
                                'from': username,
                                'content': text_content[:300],
                                'keyword_found': keyword
                            })
                            break
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error checking Twitter mentions: {e}")
        
        return matching_items

    def save_to_markdown(self, item_data):
        """
        Save item data to markdown file with YAML frontmatter in /Needs_Action
        
        Args:
            item_data: Dictionary with platform, type, from, content, keyword_found
        """
        # Determine priority based on keyword
        priority_map = {'sales': 'high', 'client': 'medium', 'project': 'medium'}
        priority = priority_map.get(item_data['keyword_found'], 'low')
        
        # Generate summary
        summary = self.generate_summary(item_data)
        
        # Create YAML frontmatter
        yaml_frontmatter = f"""---
type: twitter_{item_data['type']}
platform: twitter
from: "{item_data['from'].replace('"', "'")}"
subject: "Twitter {item_data['type'].title()} - {item_data['keyword_found']} keyword found"
received: "{datetime.now().isoformat()}"
priority: {priority}
status: pending
keyword: {item_data['keyword_found']}
---
"""
        # Create markdown content
        content = f"""{yaml_frontmatter}
# Twitter {item_data['type'].title()} Alert

## Summary
{summary}

## Original Content
{item_data['content']}

## Detection Details
- **Keyword Found:** {item_data['keyword_found']}
- **Platform:** twitter
- **Type:** {item_data['type']}
- **Detected At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*Generated by Twitter (X) Watcher*
"""
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_clean = re.sub(r'[^\w\s-]', '', item_data['from'])[:30]
        filename = f"twitter_{item_data['type']}_{timestamp}_{name_clean}_{item_data['keyword_found']}.md"
        
        # Save to Needs_Action directory
        filepath = os.path.join(self.needs_action_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Saved: {filename}")
        return filepath

    def generate_summary(self, item_data):
        """
        Generate a summary of the tweet/DM.
        
        Args:
            item_data: Dictionary with platform, type, from, content, keyword_found
            
        Returns:
            str: Generated summary
        """
        platform = item_data['platform'].title()
        item_type = item_data['type']
        sender = item_data['from']
        keyword = item_data['keyword_found']
        content = item_data['content']
        
        # Generate context-aware summary
        if item_type == 'dm':
            summary = f"New {keyword}-related direct message received from {sender} on {platform}. "
        elif item_type == 'mention':
            summary = f"New {keyword}-related mention from {sender} on {platform}. "
        else:
            summary = f"New {keyword}-related notification from {sender} on {platform}. "
        
        # Add content preview
        if len(content) > 100:
            summary += f"Message preview: '{content[:100]}...'"
        else:
            summary += f"Message: '{content}'"
        
        # Add action suggestion
        if keyword == 'sales':
            summary += " This appears to be a sales inquiry - consider prompt response."
        elif keyword == 'client':
            summary += " Client-related communication - may require attention."
        elif keyword == 'project':
            summary += " Project-related content - review for potential opportunities."
        
        return summary

    def _check_chrome_windows_windows(self):
        """Check if Chrome windows are visible on Windows"""
        try:
            # Use tasklist to check for chrome processes
            result = subprocess.run(
                'powershell -Command "(Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowHandle -ne 0}).Count"',
                shell=True, capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                try:
                    count = int(result.stdout.strip())
                    if count == 0:
                        return True  # No Chrome windows found
                except ValueError:
                    pass
            return False
        except Exception:
            return False  # If we can't check, assume window is still open

    async def is_browser_closed(self):
        """Check if the browser has been closed by the user"""
        try:
            if self.browser is None:
                return True
            # Check if browser context is still connected
            if not self.browser.is_connected():
                return True
            # Check if all pages are closed
            pages = self.browser.pages
            if not pages:
                return True
            # Try to evaluate something on the first page to check if it's alive
            try:
                await pages[0].evaluate('1')
                # Check if page is closed
                if pages[0].is_closed():
                    return True
                return False  # Browser and page are alive
            except Exception:
                # Page is closed or browser is disconnected
                return True
        except Exception:
            # Browser is closed or disconnected
            return True

    async def check_browser_closed(self):
        """Check if browser is closed and exit if so"""
        if not self.browser:
            return True
            
        try:
            # Method 1: Check if all pages are closed
            pages = self.browser.pages
            if not pages:
                # No pages left - user closed the window
                print("\n✓ Browser window closed by user.")
                print("Stopping watcher gracefully...")
                await self.cleanup()
                # Exit with code 0 so PM2 won't restart
                import sys
                sys.exit(0)
                return True
            
            # Method 2: Check if our main page is closed
            if self.page and self.page.is_closed():
                print("\n✓ Browser window closed by user.")
                print("Stopping watcher gracefully...")
                await self.cleanup()
                # Exit with code 0 so PM2 won't restart
                import sys
                sys.exit(0)
                return True
            
            # Method 3: Try to interact with page - will fail if window closed
            try:
                await self.page.evaluate('document.title')
            except Exception as page_error:
                # Page interaction failed - window likely closed
                print("\n✓ Browser window closed by user.")
                print("Stopping watcher gracefully...")
                await self.cleanup()
                import sys
                sys.exit(0)
                return True
            
            # Method 4: Windows-specific - check for Chrome window using tasklist
            if sys.platform == 'win32':
                chrome_windows_closed = self._check_chrome_windows_windows()
                if chrome_windows_closed:
                    print("\n✓ Browser window closed by user.")
                    print("Stopping watcher gracefully...")
                    await self.cleanup()
                    import sys
                    sys.exit(0)
                    return True
            
            return False
        except Exception as e:
            # Browser is disconnected
            print("\n✓ Browser window closed by user.")
            print("Stopping watcher gracefully...")
            await self.cleanup()
            import sys
            sys.exit(0)
            return True

    async def retry_with_backoff(self, func, *args, max_retries=None, base_delay=None, **kwargs):
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Async function to execute
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
                return await func(*args, **kwargs)
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
                    await asyncio.sleep(delay)
                else:
                    print(f"  Max retries ({max_retries}) exceeded for {func.__name__}")
                    self.error_recovery.log_error(
                        self.component_name,
                        e,
                        {'function': func.__name__, 'final': True}
                    )
        
        return None

    async def run(self):
        """Main run method - Twitter monitoring loop"""
        print("\nStarting Twitter (X) Watcher...")
        print("Close the browser window to stop the watcher.")
        print(f"Error recovery: Max retries={self.max_retries}, Backoff=1-60s")

        try:
            await self.setup_browser(self.session_path)
            await self.login_twitter()

            while True:
                try:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking Twitter...")

                    # Check DMs with retry
                    dms = await self.retry_with_backoff(self.check_twitter_dms)
                    if dms:
                        for dm in dms:
                            try:
                                self.save_to_markdown(dm)
                            except Exception as e:
                                print(f"  Error saving DM: {e}")
                                self.error_recovery.log_error(
                                    self.component_name,
                                    e,
                                    {'operation': 'save_to_markdown', 'type': 'dm'}
                                )
                                continue
                    else:
                        print("  Skipped DM check (network error)")

                    # Check notifications with retry
                    notifications = await self.retry_with_backoff(self.check_twitter_notifications)
                    if notifications:
                        for notif in notifications:
                            try:
                                self.save_to_markdown(notif)
                            except Exception as e:
                                print(f"  Error saving notification: {e}")
                                self.error_recovery.log_error(
                                    self.component_name,
                                    e,
                                    {'operation': 'save_to_markdown', 'type': 'notification'}
                                )
                                continue
                    else:
                        print("  Skipped notification check (network error)")

                    # Check mentions with retry
                    mentions = await self.retry_with_backoff(self.check_twitter_mentions)
                    if mentions:
                        for mention in mentions:
                            try:
                                self.save_to_markdown(mention)
                            except Exception as e:
                                print(f"  Error saving mention: {e}")
                                self.error_recovery.log_error(
                                    self.component_name,
                                    e,
                                    {'operation': 'save_to_markdown', 'type': 'mention'}
                                )
                                continue
                    else:
                        print("  Skipped mention check (network error)")

                    total_found = (len(dms) if dms else 0) + (len(notifications) if notifications else 0) + (len(mentions) if mentions else 0)
                    print(f"  Found {total_found} matching items")

                    # Wait 60 seconds before next check, checking browser status every 2 seconds
                    for _ in range(30):  # 30 x 2 seconds = 60 seconds
                        await self.check_browser_closed()
                        await self.page.wait_for_timeout(2000)

                except Exception as e:
                    error_msg = f"Error during monitoring: {type(e).__name__}: {e}"
                    print(error_msg)
                    self.error_recovery.log_error(
                        self.component_name,
                        e,
                        {'stage': 'monitoring_loop'}
                    )
                    # Graceful: wait and continue loop
                    await self.check_browser_closed()
                    await self.page.wait_for_timeout(self.check_interval * 1000)

        except Exception as e:
            error_msg = f"Twitter Watcher error: {type(e).__name__}: {e}"
            print(error_msg)
            self.error_recovery.log_error(
                self.component_name,
                e,
                {'stage': 'fatal'}
            )
            raise


async def main():
    """Main entry point"""
    watcher = TwitterWatcher()
    
    try:
        await watcher.run()
    except KeyboardInterrupt:
        print("\n\nWatcher interrupted by user")
        return 0
    except SystemExit as e:
        # Clean exit when browser is closed - preserve exit code
        return e.code if e.code is not None else 0
    except Exception as e:
        print(f"\nWatcher error: {e}")
        return 1
    finally:
        await watcher.cleanup()
    
    return 0


if __name__ == "__main__":
    import signal
    
    # Set UTF-8 encoding for stdout to handle Unicode characters
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    def signal_handler(sig, frame):
        print("\n\nTwitter Watcher stopped by user (Ctrl+C)")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nWatcher interrupted by user")
        sys.exit(0)
    except SystemExit as e:
        # Clean exit - preserve exit code
        sys.exit(e.code if e.code is not None else 0)
    except Exception as e:
        print(f"\nWatcher error: {e}")
        sys.exit(1)

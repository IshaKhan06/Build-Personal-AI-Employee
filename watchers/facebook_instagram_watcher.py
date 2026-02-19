"""
Facebook/Instagram Watcher (Gold Tier - Error Recovery)
Monitors messages and posts on Facebook and Instagram for keywords: sales, client, project
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


class FacebookInstagramWatcher:
    def __init__(self, platform='facebook'):
        """
        Initialize the watcher.

        Args:
            platform: 'facebook' or 'instagram' or 'both'
        """
        self.platform = platform
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.session_path_facebook = os.path.join(base_dir, 'session', 'facebook')
        self.session_path_instagram = os.path.join(base_dir, 'session', 'instagram')

        # Ensure session directories exist
        os.makedirs(self.session_path_facebook, exist_ok=True)
        os.makedirs(self.session_path_instagram, exist_ok=True)

        self.needs_action_dir = os.path.join(base_dir, 'Needs_Action')
        os.makedirs(self.needs_action_dir, exist_ok=True)

        # Initialize error recovery utility
        self.error_recovery = ErrorRecovery(base_dir)
        self.component_name = f"facebook_instagram_watcher_{platform}"

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
            if 'closed' in error_msg or 'target' in error_msg or 'closed' in error_msg or 'context' in error_msg:
                return True
            return False

    async def login_facebook(self):
        """Navigate to Facebook and wait for login"""
        print("\n" + "="*50)
        print("FACEBOOK MONITORING")
        print("="*50)
        print("Opening Facebook. Please log in if not already logged in.")
        print("Once logged in, the watcher will monitor for messages/posts.")
        
        await self.page.goto('https://www.facebook.com/')
        
        # Wait for page to load and check if logged in
        login_success = False
        timeout = 180000  # 3 minutes timeout
        start_time = time.time()

        while not login_success and (time.time() - start_time) * 1000 < timeout:
            try:
                # Check if logged in by looking for the main feed or profile elements
                feed_element = await self.page.query_selector('[role="main"], #ssrb_feed_start, div[aria-label="Stories"]')
                if feed_element:
                    print("Facebook logged in successfully!")
                    login_success = True
                    break
                else:
                    print("Waiting for Facebook login...")
                    await self.page.wait_for_timeout(5000)
            except Exception as e:
                await self.page.wait_for_timeout(5000)

        if not login_success:
            print("Timeout waiting for Facebook login. Please ensure you are logged in.")
            raise Exception("Facebook login timeout")

    async def login_instagram(self):
        """Navigate to Instagram and wait for login"""
        print("\n" + "="*50)
        print("INSTAGRAM MONITORING")
        print("="*50)
        print("Opening Instagram. Please log in if not already logged in.")
        
        await self.page.goto('https://www.instagram.com/')
        
        # Wait for page to load and check if logged in
        login_success = False
        timeout = 180000  # 3 minutes timeout
        start_time = time.time()

        while not login_success and (time.time() - start_time) * 1000 < timeout:
            try:
                # Check if logged in by looking for the main feed or profile elements
                feed_element = await self.page.query_selector('main, article, [role="main"]')
                if feed_element:
                    print("Instagram logged in successfully!")
                    login_success = True
                    break
                else:
                    print("Waiting for Instagram login...")
                    await self.page.wait_for_timeout(5000)
            except Exception as e:
                await self.page.wait_for_timeout(5000)

        if not login_success:
            print("Timeout waiting for Instagram login. Please ensure you are logged in.")
            raise Exception("Instagram login timeout")

    async def check_facebook_messages(self):
        """Check Facebook Messenger for messages with keywords"""
        matching_items = []
        
        try:
            # Navigate to Messenger
            await self.page.goto('https://www.facebook.com/messages/')
            await self.page.wait_for_timeout(3000)
            
            # Look for unread conversations
            unread_elements = await self.page.query_selector_all(
                '[aria-label*="unread"], [class*="unread"], div[role="row"][aria-selected="false"]'
            )
            
            for elem in unread_elements[:10]:  # Check up to 10 unread
                try:
                    # Get sender name
                    sender_elem = await elem.query_selector('span[dir="auto"], strong, h3')
                    sender_name = await sender_elem.text_content() if sender_elem else "Unknown"
                    
                    # Get message preview
                    message_elem = await elem.query_selector('span:not([aria-label]), div[dir="auto"]')
                    message_text = await message_elem.text_content() if message_elem else ""
                    
                    # Check for keywords
                    message_lower = message_text.lower()
                    for keyword in self.keywords:
                        if keyword in message_lower:
                            matching_items.append({
                                'platform': 'facebook',
                                'type': 'message',
                                'from': sender_name,
                                'content': message_text,
                                'keyword_found': keyword
                            })
                            break
                    
                    # Click to mark as read (optional)
                    # await elem.click()
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error checking Facebook messages: {e}")
        
        return matching_items

    async def check_facebook_posts(self):
        """Check Facebook posts/notifications for keywords"""
        matching_items = []
        
        try:
            # Navigate to notifications
            await self.page.goto('https://www.facebook.com/notifications/')
            await self.page.wait_for_timeout(3000)
            
            # Look for notification elements
            notification_elements = await self.page.query_selector_all(
                '[role="article"], div[role="article"], [data-visualcompletion="css-img"]'
            )
            
            for elem in notification_elements[:10]:
                try:
                    # Get notification text
                    text_content = await elem.inner_text()
                    
                    # Check for keywords
                    text_lower = text_content.lower()
                    for keyword in self.keywords:
                        if keyword in text_lower:
                            # Try to extract who posted
                            poster_elem = await elem.query_selector('strong, span[dir="auto"]')
                            poster = await poster_elem.text_content() if poster_elem else "Unknown"
                            
                            matching_items.append({
                                'platform': 'facebook',
                                'type': 'post',
                                'from': poster,
                                'content': text_content[:500],  # Limit content length
                                'keyword_found': keyword
                            })
                            break
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error checking Facebook posts: {e}")
        
        return matching_items

    async def check_instagram_messages(self):
        """Check Instagram Direct Messages for messages with keywords"""
        matching_items = []
        
        try:
            # Navigate to Instagram DMs
            await self.page.goto('https://www.instagram.com/direct/inbox/')
            await self.page.wait_for_timeout(3000)
            
            # Look for unread conversations
            unread_elements = await self.page.query_selector_all(
                'div[role="button"], article, div[tabindex]'
            )
            
            for elem in unread_elements[:10]:
                try:
                    # Get conversation text
                    text_content = await elem.inner_text()
                    
                    # Check for keywords
                    text_lower = text_content.lower()
                    for keyword in self.keywords:
                        if keyword in text_lower:
                            # Try to extract username
                            username_elem = await elem.query_selector('span, strong')
                            username = await username_elem.text_content() if username_elem else "Unknown"
                            
                            matching_items.append({
                                'platform': 'instagram',
                                'type': 'message',
                                'from': username,
                                'content': text_content[:300],
                                'keyword_found': keyword
                            })
                            break
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error checking Instagram messages: {e}")
        
        return matching_items

    async def check_instagram_posts(self):
        """Check Instagram posts/notifications for keywords"""
        matching_items = []
        
        try:
            # Navigate to Instagram activity/notifications
            await self.page.goto('https://www.instagram.com/accounts/activity/')
            await self.page.wait_for_timeout(3000)
            
            # Look for activity elements
            activity_elements = await self.page.query_selector_all(
                'article, div[role="button"], li'
            )
            
            for elem in activity_elements[:10]:
                try:
                    # Get activity text
                    text_content = await elem.inner_text()
                    
                    # Check for keywords
                    text_lower = text_content.lower()
                    for keyword in self.keywords:
                        if keyword in text_lower:
                            # Try to extract username
                            username_elem = await elem.query_selector('span, strong')
                            username = await username_elem.text_content() if username_elem else "Unknown"
                            
                            matching_items.append({
                                'platform': 'instagram',
                                'type': 'post',
                                'from': username,
                                'content': text_content[:300],
                                'keyword_found': keyword
                            })
                            break
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error checking Instagram posts: {e}")
        
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
type: {item_data['platform']}_{item_data['type']}
platform: {item_data['platform']}
from: "{item_data['from'].replace('"', "'")}"
subject: "{item_data['platform'].title()} {item_data['type'].title()} - {item_data['keyword_found']} keyword found"
received: "{datetime.now().isoformat()}"
priority: {priority}
status: pending
keyword: {item_data['keyword_found']}
---
"""
        # Create markdown content
        content = f"""{yaml_frontmatter}
# {item_data['platform'].title()} {item_data['type'].title()} Alert

## Summary
{summary}

## Original Content
{item_data['content']}

## Detection Details
- **Keyword Found:** {item_data['keyword_found']}
- **Platform:** {item_data['platform']}
- **Type:** {item_data['type']}
- **Detected At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*Generated by Facebook/Instagram Watcher*
"""
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_clean = re.sub(r'[^\w\s-]', '', item_data['from'])[:30]
        filename = f"{item_data['platform']}_{item_data['type']}_{timestamp}_{name_clean}_{item_data['keyword_found']}.md"
        
        # Save to Needs_Action directory
        filepath = os.path.join(self.needs_action_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Saved: {filename}")
        return filepath

    def generate_summary(self, item_data):
        """
        Generate a summary of the message/post.
        
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
        if item_type == 'message':
            summary = f"New {keyword}-related {item_type} received from {sender} on {platform}. "
        else:
            summary = f"New {keyword}-related {item_type} detected from {sender} on {platform}. "
        
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

    async def is_browser_closed(self):
        """Check if the browser has been closed by the user"""
        try:
            if self.browser is None:
                return True
            # Check our close event flag first
            if getattr(self, 'browser_closed', False):
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
        
        # All retries failed - graceful degradation: skip this operation
        return None

    async def run_facebook(self):
        """Run Facebook monitoring loop"""
        print("\nStarting Facebook Watcher...")
        print("Close the browser window to stop the watcher.")
        print(f"Error recovery: Max retries={self.max_retries}, Backoff=1-60s")

        try:
            await self.setup_browser(self.session_path_facebook)
            await self.login_facebook()

            while True:
                try:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking Facebook...")

                    # Check messages with retry
                    messages = await self.retry_with_backoff(self.check_facebook_messages)
                    if messages:
                        for msg in messages:
                            try:
                                self.save_to_markdown(msg)
                            except Exception as e:
                                print(f"  Error saving message: {e}")
                                self.error_recovery.log_error(
                                    self.component_name,
                                    e,
                                    {'operation': 'save_to_markdown', 'type': 'message'}
                                )
                                # Graceful: skip this message, continue with others
                                continue
                    else:
                        print("  Skipped message check (network error)")

                    # Check posts/notifications with retry
                    posts = await self.retry_with_backoff(self.check_facebook_posts)
                    if posts:
                        for post in posts:
                            try:
                                self.save_to_markdown(post)
                            except Exception as e:
                                print(f"  Error saving post: {e}")
                                self.error_recovery.log_error(
                                    self.component_name,
                                    e,
                                    {'operation': 'save_to_markdown', 'type': 'post'}
                                )
                                # Graceful: skip this post, continue with others
                                continue
                    else:
                        print("  Skipped post check (network error)")

                    total_found = (len(messages) if messages else 0) + (len(posts) if posts else 0)
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
            error_msg = f"Facebook Watcher error: {type(e).__name__}: {e}"
            print(error_msg)
            self.error_recovery.log_error(
                self.component_name,
                e,
                {'stage': 'fatal'}
            )
            raise

    async def run_instagram(self):
        """Run Instagram monitoring loop"""
        print("\nStarting Instagram Watcher...")
        print("Close the browser window to stop the watcher.")
        print(f"Error recovery: Max retries={self.max_retries}, Backoff=1-60s")

        try:
            await self.setup_browser(self.session_path_instagram)
            await self.login_instagram()

            while True:
                try:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking Instagram...")

                    # Check messages with retry
                    messages = await self.retry_with_backoff(self.check_instagram_messages)
                    if messages:
                        for msg in messages:
                            try:
                                self.save_to_markdown(msg)
                            except Exception as e:
                                print(f"  Error saving message: {e}")
                                self.error_recovery.log_error(
                                    self.component_name,
                                    e,
                                    {'operation': 'save_to_markdown', 'type': 'message'}
                                )
                                continue
                    else:
                        print("  Skipped message check (network error)")

                    # Check posts/notifications with retry
                    posts = await self.retry_with_backoff(self.check_instagram_posts)
                    if posts:
                        for post in posts:
                            try:
                                self.save_to_markdown(post)
                            except Exception as e:
                                print(f"  Error saving post: {e}")
                                self.error_recovery.log_error(
                                    self.component_name,
                                    e,
                                    {'operation': 'save_to_markdown', 'type': 'post'}
                                )
                                continue
                    else:
                        print("  Skipped post check (network error)")

                    total_found = (len(messages) if messages else 0) + (len(posts) if posts else 0)
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
            error_msg = f"Instagram Watcher error: {type(e).__name__}: {e}"
            print(error_msg)
            self.error_recovery.log_error(
                self.component_name,
                e,
                {'stage': 'fatal'}
            )
            raise

    async def run(self):
        """Main run method - runs both platforms or selected one"""
        if self.platform == 'both':
            print("="*60)
            print("FACEBOOK & INSTAGRAM WATCHER")
            print("="*60)
            print("Monitoring both platforms for keywords: sales, client, project")
            print("Check interval: 60 seconds")
            print("Session paths:")
            print(f"  Facebook: {self.session_path_facebook}")
            print(f"  Instagram: {self.session_path_instagram}")
            
            # Run Facebook first, then Instagram (sequential for simplicity)
            # For true parallel monitoring, you'd need separate browser instances
            await self.run_facebook()
            # After Facebook stops, run Instagram
            await self.run_instagram()
        elif self.platform == 'facebook':
            await self.run_facebook()
        elif self.platform == 'instagram':
            await self.run_instagram()


async def main(platform='facebook'):
    """Main entry point"""
    watcher = FacebookInstagramWatcher(platform=platform)

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
    import sys

    # Set UTF-8 encoding for stdout to handle Unicode characters
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    running = True

    def signal_handler(sig, frame):
        global running
        print("\n\nFacebook/Instagram Watcher stopped by user (Ctrl+C)")
        running = False
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Default to facebook, can be changed via command line argument
    platform = sys.argv[1] if len(sys.argv) > 1 else 'facebook'

    try:
        exit_code = asyncio.run(main(platform))
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

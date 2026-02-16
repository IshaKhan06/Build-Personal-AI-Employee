import os
import time
import asyncio
from datetime import datetime
import re
from playwright.async_api import async_playwright


class LinkedInWatcher:
    def __init__(self):
        self.session_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'session', 'linkedin')
        os.makedirs(self.session_path, exist_ok=True)
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
            except Exception as e:
                print(f"Error during LinkedIn login check: {e}")
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
    
    async def run(self):
        """Main loop to monitor LinkedIn"""
        print("Starting LinkedIn Watcher...")
        
        try:
            await self.setup_browser()
            await self.login_linkedin()
            
            while True:
                try:
                    matching_items = await self.check_messages_and_notifications()
                    
                    for item in matching_items:
                        self.save_item_to_markdown(item)
                    
                    print(f"Checked LinkedIn, found {len(matching_items)} matching items")
                    
                    # Wait 60 seconds before next check
                    await self.page.wait_for_timeout(60000)
                    
                except Exception as e:
                    print(f"Error in LinkedIn Watcher: {e}")
                    await self.page.wait_for_timeout(60000)  # Wait before retrying
        except KeyboardInterrupt:
            pass  # Handled by signal handler
        finally:
            # Cleanup
            await self.cleanup()


if __name__ == "__main__":
    """
    HOW TO RUN:
    1. Install dependencies: pip install playwright
    2. Install browser: playwright install chromium
    3. Run with PM2: pm2 start linkedin_watcher.py --name linkedin-watcher

    HOW TO TEST:
    1. Send a test message to your LinkedIn account containing one of the keywords: sales, client, project
    2. Or create a notification that includes one of these keywords
    3. Wait for the script to detect and save the item to the Needs_Action folder
    """
    import signal
    import sys
    
    watcher = None
    
    def signal_handler(sig, frame):
        print("\nLinkedIn Watcher stopped by user")
        if watcher:
            asyncio.run(watcher.cleanup())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    async def main():
        global watcher
        watcher = LinkedInWatcher()
        await watcher.run()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLinkedIn Watcher stopped by user")
    except Exception as e:
        print(f"Error: {e}")
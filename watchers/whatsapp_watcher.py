"""
WhatsApp Watcher (Gold Tier - Error Recovery)
Monitors WhatsApp Web for messages with keywords
Saves detected items as .md files in /Needs_Action
Checks every 30 seconds
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


class WhatsAppWatcher:
    def __init__(self):
        self.session_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'session', 'whatsapp')
        os.makedirs(self.session_path, exist_ok=True)
        
        # Initialize error recovery utility
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.error_recovery = ErrorRecovery(self.base_dir)
        self.component_name = "whatsapp_watcher"
        
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
        
    async def login_whatsapp_web(self):
        """Navigate to WhatsApp Web and wait for login"""
        print("Opening WhatsApp Web. Please scan the QR code with your phone.")
        await self.page.goto('https://web.whatsapp.com/')
        
        # Wait for QR code to disappear (indicating login)
        login_success = False
        timeout = 120000  # 120 seconds timeout (2 minutes)
        start_time = time.time()
        
        while not login_success and (time.time() - start_time) * 1000 < timeout:
            try:
                # Check if we're logged in by looking for the chat list or main app container
                chat_list_element = await self.page.query_selector('div[data-testid="chat-list"], div[data-testid="side"], #pane-side')
                if chat_list_element:
                    print("WhatsApp Web logged in successfully")
                    login_success = True
                    break
                else:
                    print("Waiting for QR code scan...")
                    await self.page.wait_for_timeout(5000)  # Wait 5 seconds before checking again
            except:
                # Silently ignore errors during login check
                await self.page.wait_for_timeout(5000)
        
        if not login_success:
            print("Timeout waiting for WhatsApp login. Please ensure you scanned the QR code.")
            raise Exception("WhatsApp login timeout")
    
    async def get_unread_chats_with_keywords(self):
        """Find chats with unread messages containing keywords"""
        # Keywords to look for
        keywords = ['urgent', 'invoice', 'payment', 'sales']
        
        # Get all unread chat elements (using more general selectors)
        unread_chats = await self.page.query_selector_all('div[data-testid="chat-list"] div[aria-label][data-unread="true"], [data-icon="chatUnreadDiv"], .unread-count')
        
        matching_chats = []
        
        for chat in unread_chats:
            try:
                # Get chat name using multiple possible selectors
                chat_name_element = await chat.query_selector('span[title], span[dir="auto"], div[tabindex] span')
                if chat_name_element:
                    chat_name = await chat_name_element.text_content()
                else:
                    # Try to get the chat name from the parent or nearby elements
                    chat_name = await chat.inner_text()
                
                # Click on the chat to view messages
                await chat.click()
                await self.page.wait_for_timeout(2000)  # Wait for messages to load
                
                # Get last few messages (using more general selectors)
                message_elements = await self.page.query_selector_all('span.selectable-text, .copyable-text span, [dir="ltr"] span')
                messages = []
                for msg_elem in message_elements[-5:]:  # Check last 5 messages
                    msg_text = await msg_elem.text_content()
                    messages.append(msg_text.lower())
                
                # Check if any message contains keywords
                full_text = ' '.join(messages)
                for keyword in keywords:
                    if keyword in full_text:
                        matching_chats.append({
                            'name': chat_name,
                            'last_message': messages[-1] if messages else '',
                            'keyword_found': keyword
                        })
                        break  # Found a keyword, no need to check others
                        
            except Exception as e:
                print(f"Error processing chat: {e}")
                continue
                
        return matching_chats
    
    def save_chat_to_markdown(self, chat_data):
        """Save chat data to markdown file with YAML frontmatter"""
        # Determine priority based on keyword
        priority_map = {'urgent': 'high', 'invoice': 'medium', 'payment': 'high', 'sales': 'medium'}
        priority = priority_map.get(chat_data['keyword_found'], 'low')
        
        # Create YAML frontmatter
        yaml_frontmatter = f"""---
type: whatsapp
from: "{chat_data['name']}"
subject: "WhatsApp Message - {chat_data['keyword_found']} keyword found"
received: "{datetime.now().isoformat()}"
priority: {priority}
status: pending
---
"""
        
        # Create markdown content
        content = f"{yaml_frontmatter}\n## Chat Details\n\nLast message: {chat_data['last_message']}\nKeyword found: {chat_data['keyword_found']}\n\n"
        
        # Generate filename based on timestamp and chat name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_clean = re.sub(r'[^\w\s-]', '', chat_data['name'])[:50]
        filename = f"whatsapp_{timestamp}_{name_clean}_{chat_data['keyword_found']}.md"
        
        # Save to Needs_Action directory
        needs_action_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Needs_Action')
        filepath = os.path.join(needs_action_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Saved WhatsApp message to {filepath}")

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
        """Main loop to monitor WhatsApp"""
        print("Starting WhatsApp Watcher...")
        print(f"Error recovery: Max retries={self.max_retries}, Backoff=1-60s")

        try:
            await self.setup_browser()
            await self.login_whatsapp_web()

            while True:
                try:
                    # Use retry with backoff
                    matching_chats = await self.retry_with_backoff(self.get_unread_chats_with_keywords)

                    if matching_chats:
                        for chat in matching_chats:
                            try:
                                self.save_chat_to_markdown(chat)
                            except Exception as e:
                                print(f"  Error saving chat: {e}")
                                self.error_recovery.log_error(
                                    self.component_name, e,
                                    {'operation': 'save_chat_to_markdown', 'name': chat.get('name', 'unknown')}
                                )
                                continue
                    else:
                        print("  Skipped check (API error)")

                    print(f"Checked WhatsApp, found {len(matching_chats) if matching_chats else 0} matching chats")

                    # Wait 30 seconds before next check
                    await self.page.wait_for_timeout(30000)

                except Exception as e:
                    error_msg = f"Error in WhatsApp Watcher: {type(e).__name__}: {e}"
                    print(error_msg)
                    self.error_recovery.log_error(self.component_name, e, {'stage': 'monitoring_loop'})
                    # Graceful: wait before retrying
                    await self.page.wait_for_timeout(30000)
                    
        except Exception as e:
            error_msg = f"WhatsApp Watcher fatal error: {type(e).__name__}: {e}"
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
        print("\nWhatsApp Watcher stopped by user")
        sys.stdout.flush()
        os._exit(0)  # Force immediate exit, no cleanup
    
    signal.signal(signal.SIGINT, signal_handler)
    
    async def main():
        watcher = WhatsAppWatcher()
        await watcher.run()
    
    sys.stderr = DevNull()  # Suppress all errors
    asyncio.run(main())
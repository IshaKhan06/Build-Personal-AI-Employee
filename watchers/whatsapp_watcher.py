import os
import time
import asyncio
from datetime import datetime
import re
from playwright.async_api import async_playwright


class WhatsAppWatcher:
    def __init__(self):
        self.session_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'session', 'whatsapp')
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
            except Exception as e:
                print(f"Error during login check: {e}")
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
    
    async def run(self):
        """Main loop to monitor WhatsApp"""
        print("Starting WhatsApp Watcher...")
        
        try:
            await self.setup_browser()
            await self.login_whatsapp_web()
            
            while True:
                try:
                    matching_chats = await self.get_unread_chats_with_keywords()
                    
                    for chat in matching_chats:
                        self.save_chat_to_markdown(chat)
                    
                    print(f"Checked WhatsApp, found {len(matching_chats)} matching chats")
                    
                    # Wait 30 seconds before next check
                    await self.page.wait_for_timeout(30000)
                    
                except Exception as e:
                    print(f"Error in WhatsApp Watcher: {e}")
                    await self.page.wait_for_timeout(30000)  # Wait before retrying
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
    3. Run with PM2: pm2 start whatsapp_watcher.py --name whatsapp-watcher
    
    HOW TO TEST:
    1. Send a test message to your WhatsApp account containing one of the keywords: urgent, invoice, payment, sales
    2. Ensure the message appears as unread in WhatsApp Web
    3. Wait for the script to detect and save the message to the Needs_Action folder
    """
    import signal
    import sys
    
    watcher = None
    
    def signal_handler(sig, frame):
        print("\nWhatsApp Watcher stopped by user")
        if watcher:
            asyncio.run(watcher.cleanup())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    async def main():
        global watcher
        watcher = WhatsAppWatcher()
        await watcher.run()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWhatsApp Watcher stopped by user")
    except Exception as e:
        print(f"Error: {e}")
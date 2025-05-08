import time
import random
import urllib.parse
from playwright.sync_api import sync_playwright
from typing import List
import os

WHATSAPP_SESSION_PATH = "whatsapp_session.json"

class WhatsAppSender:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        print(f"INFO: WhatsAppSender initialized. Session will be stored at: {os.path.abspath(WHATSAPP_SESSION_PATH)}")
        
    def __enter__(self):
        print("INFO: Entering WhatsAppSender context...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            timeout=60000
        )
        
        storage_state_to_load = None
        if os.path.exists(WHATSAPP_SESSION_PATH):
            print(f"INFO: Session file FOUND at {WHATSAPP_SESSION_PATH}. Attempting to load it.")
            storage_state_to_load = WHATSAPP_SESSION_PATH
        else:
            print(f"INFO: Session file NOT found at {WHATSAPP_SESSION_PATH}. A new session will require QR scan.")
            
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            storage_state=storage_state_to_load
        )
        
        self.page = self.context.new_page()
        print("INFO: New page created.")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("INFO: Exiting WhatsAppSender context...")
        if self.context:
            try:
                print(f"INFO: Attempting to save session state to {WHATSAPP_SESSION_PATH}...")
                self.context.storage_state(path=WHATSAPP_SESSION_PATH)
                print(f"✓ Session state successfully saved to {WHATSAPP_SESSION_PATH}")
            except Exception as e:
                print(f"✖ Error saving session state: {str(e)}")
                if self.page and not self.page.is_closed():
                    try: 
                        self.page.screenshot(path="error_saving_session.png")
                        print("INFO: Screenshot 'error_saving_session.png' taken.")
                    except Exception as se:
                        print(f"CRITICAL: Failed to take screenshot during session save error: {se}")

        if self.page and not self.page.is_closed():
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("INFO: Resources closed.")

    def _handle_fresh_look_popup(self):
        """Specifically handles the 'A fresh look for WhatsApp Web' popup"""
        print("INFO: Checking for 'Fresh Look' popup...")
        
        # Try multiple selectors for the Continue button
        selectors = [
            "div[role='dialog'] button >> text=Continue",  # Most specific
            "button:has-text('Continue')",                # More general
            "button >> text=Continue",                     # Most general
            "div[role='button'] >> text=Continue"          # Alternative
        ]
        
        for selector in selectors:
            try:
                print(f"INFO: Trying selector: {selector}")
                if self.page.is_visible(selector, timeout=5000):
                    print(f"INFO: Found 'Continue' button with selector: {selector}")
                    # Click with multiple methods for reliability
                    try:
                        self.page.click(selector, timeout=5000)
                        print("✓ Clicked 'Continue' button (method 1)")
                        return True
                    except:
                        self.page.locator(selector).click(timeout=5000)
                        print("✓ Clicked 'Continue' button (method 2)")
                        return True
            except Exception as e:
                print(f"DEBUG: Continue button not found with selector {selector}: {str(e)}")
                continue
                
        print("INFO: 'Fresh Look' popup not found or not clickable")
        return False

    def login_to_whatsapp(self):
        print("\nINFO: Starting login_to_whatsapp process...")
        try:
            self.page.goto("https://web.whatsapp.com", timeout=120000, wait_until="domcontentloaded")
            print("INFO: Navigated to WhatsApp Web. Waiting for page to settle...")
            
            # Initial wait for page to load
            self.page.wait_for_timeout(10000)

            # Check for existing session first
            try:
                self.page.wait_for_selector('div[data-testid="chat-list"]', timeout=10000)
                print("✓ Login successful: Chat list found (existing session).")
                return True
            except:
                print("INFO: No existing session found, proceeding to QR scan flow")

            # QR Code Scan Flow
            qr_selector = 'canvas[aria-label="Scan me!"]'
            try:
                print("INFO: Waiting for QR code to appear...")
                self.page.wait_for_selector(qr_selector, timeout=60000)
                print("INFO: QR code visible. Please scan with your phone...")
                
                # Wait for QR code to disappear (scan completed)
                self.page.wait_for_selector(qr_selector, state="hidden", timeout=120000)
                print("INFO: QR scan detected (QR code disappeared).")
                
                # Explicit wait for the fresh look popup
                print("INFO: Waiting for 'Fresh Look' popup...")
                self.page.wait_for_timeout(5000)  # Give it time to appear
                
                # Handle the popup with retries
                for attempt in range(3):
                    if self._handle_fresh_look_popup():
                        print("✓ 'Fresh Look' popup handled successfully")
                        break
                    print(f"INFO: Popup not found, attempt {attempt + 1}/3")
                    self.page.wait_for_timeout(3000)
                
                # Final verification
                self.page.wait_for_selector('div[data-testid="chat-list"]', timeout=15000)
                print("✓ Login verified with chat list")
                return True
                
            except Exception as e:
                print(f"✖ Error during QR scan process: {str(e)}")
                self.page.screenshot(path="error_qr_scan.png")
                raise

        except Exception as e:
            print(f"✖ Login failed: {str(e)}")
            if not self.page.is_closed():
                self.page.screenshot(path="error_login_failed.png")
            return False

    def send_message(self, phone_number: str, message: str):
        """Sends message with multiple fallback methods"""
        try:
            print(f"\nPreparing to send to {phone_number}...")
            chat_url = f"https://web.whatsapp.com/send?phone={phone_number}&text={urllib.parse.quote(message)}"
            self.page.goto(chat_url, timeout=60000)
            
            # Wait for chat to load
            self.page.wait_for_selector('div[contenteditable="true"]', timeout=15000)
            
            # Try multiple sending methods
            for attempt in range(3):
                try:
                    # Method 1: Click send button
                    try:
                        send_button = self.page.wait_for_selector(
                            'button[data-testid="compose-btn-send"]',
                            timeout=5000
                        )
                        send_button.click()
                        print("✓ Sent via send button")
                        time.sleep(2)
                        return True
                    except:
                        pass
                    
                    # Method 2: Keyboard Enter
                    input_box = self.page.query_selector('div[contenteditable="true"]')
                    input_box.click()
                    self.page.keyboard.press("Enter")
                    time.sleep(1)
                    self.page.keyboard.press("Enter")
                    
                    # Verify message sent
                    if self.page.query_selector('span[data-testid="msg-time"]'):
                        print("✓ Sent via keyboard")
                        return True
                        
                except Exception as e:
                    print(f"Attempt {attempt+1} failed: {str(e)}")
                    time.sleep(2)
                    self.page.reload()
            
            raise Exception("All sending methods failed")
            
        except Exception as e:
            print(f"✖ Failed to send to {phone_number}: {str(e)}")
            if not self.page.is_closed():
                self.page.screenshot(path=f"send_error_{phone_number}.png")
            return False


def send_whatsapp_messages(phone_numbers: List[str], message: str, min_delay=180, max_delay=300):
    """Main automation function"""
    print("\nStarting WhatsApp Automation")
    print("="*50)
    
    with WhatsAppSender(headless=False) as sender:
        if not sender.login_to_whatsapp():
            return
        
        for i, number in enumerate(phone_numbers, 1):
            print(f"\nProcessing {i}/{len(phone_numbers)}: {number}")
            clean_num = ''.join(c for c in number if c == '+' or c.isdigit())
            if not clean_num.startswith('+') or len(clean_num) < 10:
                print(f"✖ Invalid format: {number}")
                continue
            
            if not sender.send_message(clean_num, message):
                print("⚠ Retrying failed message...")
                sender.send_message(clean_num, message)
            
            if i < len(phone_numbers):
                delay = random.randint(min_delay, max_delay)
                print(f"\nWaiting {delay//60}m {delay%60}s before next...")
                time.sleep(delay)
    
    print("\nMessage sending completed!")
    print("="*50)


# Configuration
numbers = ["+12343807198"]  # Replace with your numbers
message = "This message sends automatically"

if __name__ == "__main__":
    send_whatsapp_messages(
        phone_numbers=numbers,
        message=message,
        min_delay=180,
        max_delay=300
    )
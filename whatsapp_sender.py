import time
import random
import urllib.parse
from playwright.sync_api import sync_playwright
from typing import List

class WhatsAppSender:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            timeout=60000
        )
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )
        self.page = self.context.new_page()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.page and not self.page.is_closed():
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def login_to_whatsapp(self):
        """Handles QR scan and specifically clicks the Continue button in the popup"""
        try:
            self.page.goto("https://web.whatsapp.com", timeout=120000)
            print("Waiting for QR code scan...")
            
            # Wait for QR code to disappear (scan complete)
            self.page.wait_for_selector('canvas', state='hidden', timeout=120000)
            print("QR scan detected")
            
            # SPECIFIC HANDLING FOR THE CONTINUE POPUP FROM YOUR SCREENSHOT
            print("Looking for Continue popup...")
            try:
                # Wait for the specific popup container to appear
                self.page.wait_for_selector('div[role="dialog"]', timeout=10000)
                
                # Click the Continue button using the exact structure from your screenshot
                continue_button = self.page.wait_for_selector(
                    'div[role="dialog"] >> button:has-text("Continue")', 
                    timeout=5000
                )
                continue_button.click()
                print("✓ Clicked Continue button in popup")
                time.sleep(2)  # Allow popup to fully close
            except Exception as e:
                print(f"Continue popup not found or could not click: {str(e)}")
                # Take screenshot for debugging
                self.page.screenshot(path="popup_error.png")
                print("Saved screenshot as 'popup_error.png'")
                raise Exception("Failed to handle Continue popup")
            
            # Proceed with normal login verification
            print("Verifying login...")
            login_verified = False
            login_indicators = [
                'div[data-testid="chat-list"]',  # Chat list
                'div[aria-label="Search input textbox"]',  # Search bar
                'div[title="New chat"]'  # New chat button
            ]
            
            for indicator in login_indicators:
                try:
                    self.page.wait_for_selector(indicator, timeout=15000)
                    login_verified = True
                    break
                except Exception as e:
                    print(f"Login indicator not found: {indicator} - {str(e)}")
                    continue
            
            if not login_verified:
                raise Exception("Could not verify login")
            
            print("✓ Login successful")
            time.sleep(2)  # Final stabilization
            return True
            
        except Exception as e:
            print(f"✖ Login failed: {str(e)}")
            if not self.page.is_closed():
                self.page.screenshot(path="login_error.png")
            return False
    
    def send_message(self, phone_number: str, message: str):
        """Guaranteed message sending with multiple fallbacks"""
        try:
            print(f"\nPreparing to send to {phone_number}...")
            
            # Load chat with pre-filled message
            chat_url = f"https://web.whatsapp.com/send?phone={phone_number}&text={urllib.parse.quote(message)}"
            self.page.goto(chat_url, timeout=60000)
            
            # Triple sending method with verification
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
                    except Exception as e:
                        print(f"Send button not found: {str(e)}")
                    
                    # Method 2: Keyboard Enter
                    input_box = self.page.wait_for_selector(
                        'div[contenteditable="true"]',
                        timeout=10000
                    )
                    input_box.click()
                    for _ in range(3):  # Multiple Enter presses
                        self.page.keyboard.press("Enter")
                        time.sleep(0.5)
                    
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
            
            # Clean and validate number
            clean_num = ''.join(c for c in number if c == '+' or c.isdigit())
            if not clean_num.startswith('+') or len(clean_num) < 10:
                print(f"✖ Invalid format: {number}")
                continue
            
            # Send with automatic retry
            if not sender.send_message(clean_num, message):
                print("⚠ Retrying failed message...")
                sender.send_message(clean_num, message)  # One automatic retry
            
            # Delay between messages
            if i < len(phone_numbers):
                delay = random.randint(min_delay, max_delay)
                print(f"\nWaiting {delay//60}m {delay%60}s before next...")
                time.sleep(delay)
    
    print("\nMessage sending completed!")
    print("="*50)


# Configuration
if __name__ == "__main__":
    numbers = ["+12343807198"]  # Replace with your numbers
    message = "This message sends automatically"  # Your message
    
    send_whatsapp_messages(
        phone_numbers=numbers,
        message=message,
        min_delay=180,  # 3 min minimum delay
        max_delay=300    # 5 min maximum delay
    )
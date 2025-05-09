from typing import List, Dict, Any
from whatsapp_sender import send_whatsapp_messages, Student
import time
import random

def run_automation():
    """Main function to run the automation tasks"""
    print("=== WhatsApp Automation Started ===")
    
    # Student and message data are now managed within whatsapp_sender.py
    # We no longer define them here or fetch them using get_message_templates()

    # We can still retrieve student count or message count if needed for logging,
    # but it would require new functions in whatsapp_sender.py to expose that, 
    # or by send_whatsapp_messages returning that info. For now, we remove the direct logging.
    # print(f"\nFound {len(students)} students to message.") 
    # print(f"Number of message templates: {len(message_templates)}")
    
    # Confirm before sending
    input("Press Enter to start sending messages (make sure WhatsApp Web is logged out)...")
    
    try:
        # Call the updated function. It will use its internal student and message lists.
        # We can still pass min_delay and max_delay if we want to override defaults from whatsapp_sender.py
        send_whatsapp_messages(
            # min_delay=200, # Example: override default min_delay
            # max_delay=400  # Example: override default max_delay
        )
    except Exception as e:
        print(f"\nError during automation: {str(e)}")
    finally:
        print("\n=== Automation Completed ===")

if __name__ == "__main__":
    run_automation()
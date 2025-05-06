from typing import List, Dict, Any
from whatsapp_sender import send_whatsapp_messages
import time
import random

def get_phone_numbers() -> List[str]:
    """Get the list of phone numbers to message"""
    # REPLACE THESE WITH YOUR ACTUAL PHONE NUMBERS
    # Format: +[country code][number], e.g., +1234567890
    return [
        "+12343807198",
    ]

def get_message_templates() -> Dict[str, Any]:
    """Get different message templates and configuration"""
    return {
        "first_admission": {
            "message": "Hello! This is an automated first admission message.",  # EDIT THIS MESSAGE
            "min_delay": 180,  # 3 minutes (minimum delay between messages)
            "max_delay": 300   # 5 minutes (maximum delay between messages)
        }
    }

def validate_phone_numbers(numbers: List[str]) -> List[str]:
    """Basic phone number validation"""
    valid_numbers = []
    for num in numbers:
        cleaned = ''.join([c for c in num if c == '+' or c.isdigit()])
        if cleaned.startswith('+') and len(cleaned) > 10:
            valid_numbers.append(cleaned)
        else:
            print(f"Invalid number format: {num}")
    return valid_numbers

def run_automation():
    """Main function to run the automation tasks"""
    print("=== WhatsApp Automation Started ===")
    
    # Get configuration
    templates = get_message_templates()
    message_config = templates["first_admission"]
    
    # Get and validate phone numbers
    phone_numbers = get_phone_numbers()
    valid_numbers = validate_phone_numbers(phone_numbers)
    
    if not valid_numbers:
        print("Error: No valid phone numbers found.")
        return
    
    print(f"\nFound {len(valid_numbers)} valid phone numbers to message.")
    print(f"Message to send: '{message_config['message']}'")
    print(f"Delay between messages: {message_config['min_delay']//60}-{message_config['max_delay']//60} minutes\n")
    
    # Confirm before sending
    input("Press Enter to start sending messages (make sure WhatsApp Web is logged out)...")
    
    try:
        send_whatsapp_messages(
            phone_numbers=valid_numbers,
            message=message_config["message"],
            min_delay=message_config["min_delay"],
            max_delay=message_config["max_delay"]
        )
    except Exception as e:
        print(f"\nError during automation: {str(e)}")
    finally:
        print("\n=== Automation Completed ===")

if __name__ == "__main__":
    run_automation()
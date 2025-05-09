from typing import List, Dict, Any
from whatsapp_sender import send_whatsapp_messages, Student, DEFAULT_STUDENTS
import time
import random

def get_message_templates() -> Dict[str, Any]:
    """Get different message templates and configuration"""
    return {
        "first_admission": {
            "message_options": [
                "Hello {name}! Welcome to the team. We are excited to have you!",
                "Hi {name}, great to have you join us! Looking forward to working together.",
                "{name}, a warm welcome from all of us! Let us know if you need anything to get started."
            ],
            "min_delay": 180,  # 3 minutes (minimum delay between messages)
            "max_delay": 300   # 5 minutes (maximum delay between messages)
        }
        # You can add other categories of messages here if needed
    }

def validate_students(students: List[Student]) -> List[Student]:
    """Validates student phone numbers and returns a list of students with valid numbers."""
    valid_students = []
    for student in students:
        cleaned_num = ''.join([c for c in student.phone_number if c == '+' or c.isdigit()])
        if cleaned_num.startswith('+') and len(cleaned_num) > 10:
            # Optionally, update student.phone_number to cleaned_num if desired
            # student.phone_number = cleaned_num 
            valid_students.append(student)
        else:
            print(f"Invalid number format for student {student.name}: {student.phone_number}")
    return valid_students

def run_automation(students_to_process: List[Student]):
    """Main function to run the automation tasks"""
    print("=== WhatsApp Automation Started ===")
    
    # Get configuration
    templates_config = get_message_templates()
    message_config = templates_config["first_admission"]
    
    # Validate students
    valid_students = validate_students(students_to_process)
    
    if not valid_students:
        print("Error: No valid students found for messaging.")
        return
    
    # Randomly select a message template from the options
    chosen_message_template = random.choice(message_config["message_options"])

    print(f"\nFound {len(valid_students)} valid students to message.")
    for student in valid_students:
        print(f"  - {student.name} ({student.phone_number})")
    print(f"Message to send (chosen template): '{chosen_message_template}'")
    print(f"Delay between messages: {message_config['min_delay']//60}-{message_config['max_delay']//60} minutes\n")
    
    input("Press Enter to start sending messages (make sure WhatsApp Web is logged out)...")
    
    try:
        send_whatsapp_messages(
            students=valid_students,
            message_template=chosen_message_template, # Pass the chosen template
            min_delay=message_config["min_delay"],
            max_delay=message_config["max_delay"]
        )
    except Exception as e:
        print(f"\nError during automation: {str(e)}")
    finally:
        print("\n=== Automation Completed ===")

if __name__ == "__main__":
    # DEFAULT_STUDENTS is now imported from whatsapp_sender
    run_automation(DEFAULT_STUDENTS)
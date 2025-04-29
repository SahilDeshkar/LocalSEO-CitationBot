# This file is intentionally left blank.
"""Utilities for text processing."""
import re

def clean_string(text):
    """
    Clean a string by removing extra whitespace and special characters.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
        
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def format_phone_number(phone):
    """
    Format a phone number consistently.
    
    Args:
        phone (str): Phone number to format
        
    Returns:
        str: Formatted phone number
    """
    if not phone:
        return ""
        
    # Extract digits only
    digits = re.sub(r'\D', '', phone)
    
    # Format US phone number
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if not standard format

def truncate_text(text, max_length=150):
    """
    Truncate text to a maximum length while preserving whole words.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
        
    # Truncate to the last space before max_length
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + "..."
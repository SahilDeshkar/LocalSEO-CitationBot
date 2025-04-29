# This file is intentionally left blank.
"""Utilities for file handling."""
import os
import json
import datetime

def ensure_directory_exists(directory):
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory (str): Path to the directory
    """
    os.makedirs(directory, exist_ok=True)  # Changed to use makedirs with exist_ok=True

def save_text_file(content, filename, directory):
    """
    Save content to a text file.
    
    Args:
        content (str): Content to save
        filename (str): Name of the file
        directory (str): Directory to save the file in
        
    Returns:
        str: Path to the saved file
    """
    ensure_directory_exists(directory)
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def save_json_file(data, filename, directory):
    """
    Save data to a JSON file.
    
    Args:
        data (dict): Data to save
        filename (str): Name of the file
        directory (str): Directory to save the file in
        
    Returns:
        str: Path to the saved file
    """
    ensure_directory_exists(directory)
    filepath = os.path.join(directory, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    return filepath

def generate_output_filename(business_name, extension='txt'):
    """
    Generate a filename for output based on business name and timestamp.
    
    Args:
        business_name (str): Name of the business
        extension (str): File extension
        
    Returns:
        str: Generated filename
    """
    # Clean business name for filename
    clean_name = "".join(c if c.isalnum() else "_" for c in business_name)
    clean_name = clean_name[:30]  # Limit length
    
    # Add timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{clean_name}_{timestamp}.{extension}"

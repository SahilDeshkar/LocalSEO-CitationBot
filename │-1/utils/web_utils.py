# This file is intentionally left blank.

# utils/web_utils.py
"""Utilities for web scraping and interaction."""
import random
import time
import requests
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import PAGE_LOAD_TIMEOUT

def get_random_user_agent():
    """Get a random user agent string."""
    ua = UserAgent()
    return ua.random

def get_chrome_driver(headless=True):
    """
    Initialize a Chrome webdriver with appropriate options.
    
    Args:
        headless (bool): Whether to run Chrome in headless mode
        
    Returns:
        WebDriver: Configured Chrome webdriver
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={get_random_user_agent()}")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
    return driver

def make_request(url, method="GET", params=None, headers=None, data=None, use_random_ua=True):
    """
    Make an HTTP request with appropriate headers and error handling.
    
    Args:
        url (str): URL to request
        method (str): HTTP method (GET, POST, etc.)
        params (dict): URL parameters
        headers (dict): HTTP headers
        data (dict): Request body for POST requests
        use_random_ua (bool): Whether to use a random user agent
        
    Returns:
        Response: HTTP response object
    """
    if headers is None:
        headers = {}
        
    if use_random_ua and "User-Agent" not in headers:
        headers["User-Agent"] = get_random_user_agent()
    
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            data=data,
            timeout=15
        )
        
        # Add a small delay to be respectful
        time.sleep(random.uniform(1, 3))
        
        return response
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {str(e)}")
# This file is intentionally left blank.
# agents/extractor_agent.py
"""Agent for extracting NAP information from Google Maps."""
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

from agents.base_agent import BaseAgent
from config import PAGE_LOAD_TIMEOUT, ELEMENT_WAIT_TIMEOUT

class ExtractorAgent(BaseAgent):
    def __init__(self):
        super().__init__("ExtractorAgent")
        
    async def run(self, google_maps_url):
        """
        Extract Name, Address, and Phone number from a Google Maps business link.
        
        Args:
            google_maps_url (str): URL to the Google Maps business
            
        Returns:
            dict: Contains the NAP information and success status
        """
        self.log_start(f"Processing URL: {google_maps_url}")
        
        try:
            # Initialize Chrome webdriver with options
            ua = UserAgent()
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")  # Suppress console logs
            options.add_argument(f"user-agent={ua.random}")
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            
            # Load the Google Maps page
            driver.get(google_maps_url)
            time.sleep(7)  # Increased delay to ensure page loads
            
            # Wait for page to load
            try:
                WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except Exception as e:
                self.logger.warning(f"Page load wait timed out: {str(e)}")
            
            # Extract business name
            name = None
            try:
                name_selectors = [
                    "h1.DUwDvf", 
                    "h1.fontHeadlineLarge", 
                    "h1", 
                    "div.fontHeadlineLarge",
                    "div[role='main'] div.lMbq3e",
                    "div[role='main'] div.qBF1Pd",
                    "div.qBF1Pd"
                ]
                for selector in name_selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].text.strip():
                        name = elements[0].text.strip()
                        break
                if not name:
                    title = driver.title
                    if " - " in title:
                        name = title.split(" - ")[0].strip()
                if not name:
                    self.logger.warning("Could not find business name with standard selectors")
            except Exception as e:
                self.logger.warning(f"Error extracting business name: {str(e)}")
            
            # Expand information if available
            try:
                possible_buttons = [
                    "//button[contains(., 'About')]",
                    "//button[contains(., 'Information')]",
                    "//button[contains(., 'Overview')]",
                    "//button[contains(@aria-label, 'Information')]",
                    "//div[contains(@role, 'tab') and contains(., 'About')]"
                ]
                for xpath in possible_buttons:
                    buttons = driver.find_elements(By.XPATH, xpath)
                    if buttons:
                        try:
                            buttons[0].click()
                            time.sleep(2)
                            break
                        except Exception as e:
                            self.logger.warning(f"Error clicking button: {str(e)}")
            except Exception as e:
                self.logger.warning(f"Error expanding information: {str(e)}")
            
            # Extract address
            address = None
            try:
                address_methods = [
                    lambda: driver.find_elements(By.CSS_SELECTOR, "button[data-item-id='address']"),
                    lambda: driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Address')]"),
                    lambda: driver.find_elements(By.XPATH, "//div[contains(text(), 'Address')]/following-sibling::div"),
                    lambda: driver.find_elements(By.XPATH, "//div[contains(@class, 'Io6YTe')]"),
                    lambda: driver.find_elements(By.XPATH, "//img[contains(@src, 'address')]/../../following-sibling::div"),
                ]
                for method in address_methods:
                    elements = method()
                    if elements and elements[0].text.strip():
                        address = elements[0].text.strip()
                        if address.lower().startswith("address:"):
                            address = address[8:].strip()
                        break
                if not address:
                    page_text = driver.page_source
                    address_pattern = r'(\d+\s+[A-Za-z\s]+(?:Road|Street|Avenue|Lane|Drive|Blvd|Boulevard|Ave|St|Rd|Dr|Ln|Way|Place|Pl|Court|Ct),\s+[A-Za-z\s]+,\s+[A-Za-z\s]+\s+[\d-]+)'
                    matches = re.findall(address_pattern, page_text)
                    if matches:
                        address = matches[0]
                if not address:
                    self.logger.warning("Could not find address with any method")
            except Exception as e:
                self.logger.warning(f"Error extracting address: {str(e)}")
                
            # Extract phone number
            phone = None
            try:
                phone_methods = [
                    lambda: driver.find_elements(By.CSS_SELECTOR, "button[data-item-id^='phone:']"),
                    lambda: driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Phone')]"),
                    lambda: driver.find_elements(By.XPATH, "//div[contains(text(), 'Phone')]/following-sibling::div"),
                    lambda: driver.find_elements(By.XPATH, "//img[contains(@src, 'phone')]/../../following-sibling::div"),
                ]
                for method in phone_methods:
                    elements = method()
                    if elements and elements[0].text.strip():
                        phone = elements[0].text.strip()
                        if phone.lower().startswith("phone:"):
                            phone = phone[6:].strip()
                        break
                if not phone:
                    page_text = driver.page_source
                    phone_pattern = r'(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4}|\+\d{1,2}\s*\d{3}\s*\d{3}\s*\d{4})'
                    matches = re.findall(phone_pattern, page_text)
                    if matches:
                        phone = matches[0]
                if not phone:
                    self.logger.warning("Could not find phone with any method")
            except Exception as e:
                self.logger.warning(f"Error extracting phone: {str(e)}")
            
            driver.quit()
            
            # Log missing information
            missing = []
            if not name:
                missing.append("name")
            if not address:
                missing.append("address")
            if not phone:
                missing.append("phone")
            
            if missing:
                self.logger.warning(f"Incomplete NAP data. Missing: {', '.join(missing)}")
            
            result = {
                "success": bool(name and address and phone),
                "partial_success": bool(name or address or phone),
                "name": name,
                "address": address,
                "phone": phone,
                "source_url": google_maps_url
            }
            
            self.log_completion("Extracted NAP information")
            return result
            
        except Exception as e:
            return self.handle_error(e)
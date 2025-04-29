# This file is intentionally left blank.
# agents/researcher_agent.py
"""Agent for researching business directory presence."""
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from fake_useragent import UserAgent

from agents.base_agent import BaseAgent
from config import BUSINESS_DIRECTORIES, DELAY_BETWEEN_REQUESTS

class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResearcherAgent")
        self.ua = UserAgent()
        
    async def run(self, business_data):
        """
        Search for the business across multiple directories and identify
        where it's missing.
        
        Args:
            business_data (dict): Contains name, address, phone info
            
        Returns:
            dict: Results of the directory search and missing directories
        """
        self.log_start(f"Researching directory presence for: {business_data.get('name', 'Unknown business')}")
        
        results = {
            "success": False,
            "directories_checked": {},
            "missing_directories": [],
            "selected_directories": []
        }
        
        try:
            # Validate we have at least a name
            if not business_data.get("name"):
                raise ValueError("No business name provided")
            
            business_name = business_data["name"]
            business_address = business_data.get("address", "")
            
            # Prepare a search query with just the name if address is unavailable
            if business_address and business_address != "Address unavailable":
                address_parts = business_address.split(",")[0] if business_address else ""
                search_query = f"{business_name} {address_parts}".strip()
            else:
                search_query = business_name.strip()
            
            # Check each directory
            for directory_url in BUSINESS_DIRECTORIES:
                domain = directory_url.split("//")[1].split("/")[0].replace("www.", "")
                
                try:
                    # Determine if business exists in this directory
                    exists = await self._check_directory(directory_url, search_query, business_data)
                    results["directories_checked"][domain] = {
                        "url": directory_url,
                        "exists": exists
                    }
                    
                    if not exists:
                        results["missing_directories"].append(domain)
                    
                    # Add random delay between requests to avoid getting blocked
                    time.sleep(DELAY_BETWEEN_REQUESTS + random.uniform(1, 3))
                    
                except Exception as e:
                    self.logger.warning(f"Error checking {domain}: {str(e)}")
                    # Consider it as missing if we can't check it
                    results["missing_directories"].append(domain)
                    results["directories_checked"][domain] = {
                        "url": directory_url,
                        "exists": False,
                        "error": str(e)
                    }
            
            # Select 2 directories where the business is missing
            if len(results["missing_directories"]) >= 2:
                results["selected_directories"] = random.sample(results["missing_directories"], 2)
            else:
                results["selected_directories"] = results["missing_directories"]
            
            results["success"] = True
            self.log_completion(f"Found {len(results['missing_directories'])} missing directories")
            
            return results
            
        except Exception as e:
            return self.handle_error(e)
    
    async def _check_directory(self, directory_url, search_query, business_data):
        """
        Check if the business exists in a specific directory.
        
        Args:
            directory_url (str): Base URL of the directory
            search_query (str): Search query to use
            business_data (dict): Business NAP data
            
        Returns:
            bool: True if business exists in directory, False otherwise
        """
        domain = directory_url.split("//")[1].split("/")[0]
        
        # Construct search URL based on the directory
        if "yelp.com" in domain:
            search_url = f"{directory_url}/search?find_desc={quote_plus(search_query)}"
        elif "yellowpages.com" in domain:
            search_url = f"{directory_url}/search?search_terms={quote_plus(search_query)}"
        elif "bbb.org" in domain:
            search_url = f"{directory_url}/search?find_text={quote_plus(search_query)}"
        elif "foursquare.com" in domain:
            search_url = f"{directory_url}/search?query={quote_plus(search_query)}"
        else:
            # Generic search URL pattern for other directories
            search_url = f"{directory_url}/search?q={quote_plus(search_query)}"
        
        # Get the search results page
        headers = {"User-Agent": self.ua.random}
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract business name for comparison
        business_name = business_data["name"].lower()
        
        # Different selectors for different directories
        selectors = [
            "h3.business-name", "a.business-name", ".listing-title", 
            ".business-title", "h2.title", ".business-link", 
            ".listing-title a", ".biz-name", ".result-title"
        ]
        
        # Look for business listings
        for selector in selectors:
            try:
                listings = soup.select(selector)
                for listing in listings:
                    if business_name in listing.text.strip().lower():
                        return True
            except:
                continue
                
        # Additional check for business address in the page content
        if business_data.get("address") and business_data["address"] != "Address unavailable":
            # Get first part of address (street address)
            street_address = business_data["address"].split(",")[0].lower()
            if len(street_address) > 10 and street_address in response.text.lower():
                return True
                
        # Check for phone number in the page
        if business_data.get("phone") and business_data["phone"] != "Phone unavailable":
            # Clean phone number for comparison
            clean_phone = ''.join(filter(str.isdigit, business_data["phone"]))
            if clean_phone and clean_phone in response.text:
                return True
                
        return False
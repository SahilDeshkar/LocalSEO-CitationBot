# config.py
"""Configuration settings for the NAP citation agent."""

# URLs for business directories to check
BUSINESS_DIRECTORIES = [
    "https://www.yelp.com",
    "https://www.yellowpages.com",
    "https://www.bbb.org",
    "https://www.foursquare.com",
    "https://www.manta.com",
    "https://www.superpages.com",
    "https://www.chamberofcommerce.com",
    "https://www.mapquest.com",
    "https://www.citysearch.com",
    "https://www.tripadvisor.com"
    "https://www.hotfrog.in",
    "https://www.provenexpert.com",
    "https://www.businessseek.biz/",
    "https://tupalo.com/"
]

# Wait times (in seconds)
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 10
DELAY_BETWEEN_REQUESTS = 3

# Output settings
OUTPUT_DIRECTORY = "data/output"
SUMMARY_WORD_COUNT = (100, 150)  # Min and max words

# Web scraping settings
USER_AGENT_ROTATION = True
USE_PROXIES = False
PROXY_LIST = []  # Add proxies here if USE_PROXIES is True

# Debug settings
DEBUG_MODE = True  # Set to False in production

# agents/base_agent.py
"""Base class for all agents in the system."""
from abc import ABC, abstractmethod
import logging

class BaseAgent(ABC):
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def run(self, *args, **kwargs):
        """Main method to execute the agent's task."""
        pass
    
    def log_start(self, message=None):
        """Log the start of an agent's execution."""
        self.logger.info(f"Starting {self.name}" + (f": {message}" if message else ""))
    
    def log_completion(self, message=None):
        """Log the completion of an agent's execution."""
        self.logger.info(f"Completed {self.name}" + (f": {message}" if message else ""))
    
    def log_error(self, error):
        """Log an error that occurred during execution."""
        self.logger.error(f"Error in {self.name}: {str(error)}")
        
    def handle_error(self, error):
        """Handle errors that occur during execution."""
        self.log_error(error)
        return {"success": False, "error": str(error)}

# This file is intentionally left blank.

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
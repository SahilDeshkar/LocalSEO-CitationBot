# This file is intentionally left blank.
# agents/citation_builder_agent.py
"""Agent for building NAP citations."""
from agents.base_agent import BaseAgent
from utils.text_utils import format_phone_number

class CitationBuilderAgent(BaseAgent):
    def __init__(self):
        super().__init__("CitationBuilderAgent")
        
    async def run(self, business_data, selected_directories):
        """
        Format clean NAP citations for the selected directories.
        
        Args:
            business_data (dict): NAP information
            selected_directories (list): Directories to create citations for
            
        Returns:
            dict: Formatted citations
        """
        self.log_start("Building citations")
        
        try:
            # Validate inputs - ensure we have at least a business name
            if not business_data.get("name"):
                raise ValueError("Missing business name")
                
            if not selected_directories:
                self.logger.warning("No directories selected for citation building")
                return {"success": True, "citations": {}}
            
            # Format business data with placeholders for missing info
            name = business_data["name"]
            address = business_data.get("address", "Address pending verification")
            phone = business_data.get("phone", "Phone pending verification")
            if phone != "Phone pending verification":
                phone = format_phone_number(phone)
            
            citations = {}
            
            # Generate citations for each selected directory
            for directory in selected_directories:
                # Create citation based on directory
                if directory == "yelp":
                    citation = self._format_yelp_citation(name, address, phone)
                elif directory == "yellowpages":
                    citation = self._format_yellowpages_citation(name, address, phone)
                elif directory == "bbb":
                    citation = self._format_bbb_citation(name, address, phone)
                elif directory == "foursquare":
                    citation = self._format_foursquare_citation(name, address, phone)
                elif directory == "manta":
                    citation = self._format_manta_citation(name, address, phone)
                elif directory == "superpages":
                    citation = self._format_superpages_citation(name, address, phone)
                elif directory == "chamberofcommerce":
                    citation = self._format_chamber_citation(name, address, phone)
                else:
                    # Generic citation format for other directories
                    citation = self._format_generic_citation(name, address, phone, directory)
                    
                citations[directory] = citation
            
            result = {
                "success": True,
                "citations": citations
            }
            
            self.log_completion(f"Created {len(citations)} citations")
            return result
            
        except Exception as e:
            return self.handle_error(e)
    
    def _format_generic_citation(self, name, address, phone, directory):
        """Format a generic citation for any directory."""
        return f"{name}\n{address}\n{phone}\n\nDirectory: {directory.capitalize()}"
    
    def _format_yelp_citation(self, name, address, phone):
        """Format a citation specifically for Yelp."""
        return f"{name}\n{address}\n{phone}\n\nSubmission for Yelp Business Directory"
    
    def _format_yellowpages_citation(self, name, address, phone):
        """Format a citation specifically for Yellow Pages."""
        return f"Business Name: {name}\nFull Address: {address}\nPhone: {phone}\n\nYellow Pages Listing Information"
    
    def _format_bbb_citation(self, name, address, phone):
        """Format a citation specifically for BBB."""
        return f"Company: {name}\nLocation: {address}\nContact: {phone}\n\nBetter Business Bureau Registration Information"
    
    def _format_foursquare_citation(self, name, address, phone):
        """Format a citation specifically for Foursquare."""
        return f"{name}\nLocated at: {address}\nCall: {phone}\n\nFoursquare Venue Information"
    
    def _format_manta_citation(self, name, address, phone):
        """Format a citation specifically for Manta."""
        return f"Business: {name}\nAddress: {address}\nPhone Number: {phone}\n\nManta Business Listing"
    
    def _format_superpages_citation(self, name, address, phone):
        """Format a citation specifically for Superpages."""
        return f"{name}\n{address}\n{phone}\n\nSuperpages Directory Information"
    
    def _format_chamber_citation(self, name, address, phone):
        """Format a citation specifically for Chamber of Commerce."""
        return f"Member Business: {name}\nBusiness Address: {address}\nContact Number: {phone}\n\nChamber of Commerce Directory Listing"

# agents/summary_agen
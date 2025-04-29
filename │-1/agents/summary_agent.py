# This file is intentionally left blank.
"""Agent for generating research process summary."""
from agents.base_agent import BaseAgent
from config import SUMMARY_WORD_COUNT

class SummaryAgent(BaseAgent):
    def __init__(self):
        super().__init__("SummaryAgent")
        
    async def run(self, business_data, research_results, citation_results):
        """
        Generate a summary of the research process.
        
        Args:
            business_data (dict): NAP information
            research_results (dict): Results from the researcher agent
            citation_results (dict): Results from the citation builder agent
            
        Returns:
            dict: Summary of the research process
        """
        self.log_start("Generating research summary")
        
        try:
            # Extract relevant information
            business_name = business_data.get("name", "Unknown business")
            directories_checked = len(research_results.get("directories_checked", {}))
            missing_directories = research_results.get("missing_directories", [])
            selected_directories = research_results.get("selected_directories", [])
            
            # Generate summary
            summary = self._generate_summary(
                business_name,
                directories_checked,
                missing_directories,
                selected_directories
            )
            
            result = {
                "success": True,
                "summary": summary,
                "word_count": len(summary.split())
            }
            
            self.log_completion(f"Generated summary with {result['word_count']} words")
            return result
            
        except Exception as e:
            return self.handle_error(e)
    
    def _generate_summary(self, business_name, directories_checked, missing_directories, selected_directories):
        """
        Generate a summary of the research process.
        
        Args:
            business_name (str): Name of the business
            directories_checked (int): Number of directories checked
            missing_directories (list): List of directories where business is missing
            selected_directories (list): Directories selected for citation
            
        Returns:
            str: Research summary
        """
        min_words, max_words = SUMMARY_WORD_COUNT
        
        summary = f"Research Summary for {business_name}\n\n"
        summary += f"The research process began by extracting the business's Name, Address, and Phone (NAP) information from Google Maps. "
        summary += f"This data was then used to search across {directories_checked} business directories to determine where the business already has listings. "
        
        if missing_directories:
            summary += f"The research found that {business_name} is missing from {len(missing_directories)} directories including {', '.join(missing_directories[:3])}"
            if len(missing_directories) > 3:
                summary += f" and {len(missing_directories) - 3} others"
            summary += ". "
        else:
            summary += f"Interestingly, {business_name} appears to be present in all checked directories. "
        
        if selected_directories:
            summary += f"Based on the findings, NAP citations were prepared for {', '.join(selected_directories)} "
            summary += f"as these directories would provide valuable additional visibility for {business_name}. "
        else:
            summary += "No directories were selected for citation building as the business appears to be well-represented across the checked platforms. "
        
        summary += "The final citations were formatted according to each directory's specific requirements to ensure accuracy and consistency of the business information across the web."
        
        # Check if within word count limits
        words = summary.split()
        if len(words) < min_words:
            summary += f" Maintaining consistent NAP information across business directories is crucial for local SEO and helps potential customers find accurate information about {business_name}."
        elif len(words) > max_words:
            # Trim to max words if too long
            summary = ' '.join(words[:max_words])
        
        return summary

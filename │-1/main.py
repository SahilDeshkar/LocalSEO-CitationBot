"""
NAP Citation Agent System with Modern Streamlit UI.
This application helps businesses manage their NAP (Name, Address, Phone) citations across
various business directories.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Handle import paths for both local and deployed environments
try:
    from agents.extractor_agent import ExtractorAgent
    from agents.researcher_agent import ResearcherAgent
    from agents.citation_builder_agent import CitationBuilderAgent
    from agents.summary_agent import SummaryAgent
    from utils.file_utils import save_text_file, generate_output_filename
    from config import OUTPUT_DIRECTORY, BUSINESS_DIRECTORIES
except ImportError:
    # When running in Streamlit Cloud, we need to add the current directory to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from agents.extractor_agent import ExtractorAgent
    from agents.researcher_agent import ResearcherAgent
    from agents.citation_builder_agent import CitationBuilderAgent
    from agents.summary_agent import SummaryAgent
    from utils.file_utils import save_text_file, generate_output_filename
    from config import OUTPUT_DIRECTORY, BUSINESS_DIRECTORIES

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("nap_citation_agent")

# Ensure output directory exists based on environment
def get_output_directory():
    """Get the appropriate output directory based on environment"""
    # For Streamlit Cloud, use a directory within the app's state
    if "STREAMLIT_RUNTIME" in os.environ:
        return "temp_output"
    # For Vercel or other serverless environments
    elif "VERCEL" in os.environ:
        return "/tmp/output"
    # Default to configured directory for local development
    else:
        return OUTPUT_DIRECTORY

# Create the output directory
def ensure_output_directory():
    """Ensure the output directory exists"""
    output_dir = get_output_directory()
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

# Modified to handle async in Streamlit environment
async def run_workflow(maps_url, progress_bar=None, status_text=None):
    """
    Execute the complete NAP citation workflow.
    
    Args:
        maps_url (str): Google Maps business URL
        progress_bar: Streamlit progress bar object
        status_text: Streamlit text element for status updates
        
    Returns:
        dict: Results of the workflow
    """
    logger.info(f"Starting workflow for URL: {maps_url}")
    output_dir = ensure_output_directory()
    
    # Validate the URL is not empty
    if not maps_url or not maps_url.strip():
        error_msg = "Google Maps URL cannot be empty"
        logger.error(error_msg)
        if status_text:
            status_text.text(f"❌ Error: {error_msg}")
        return {"success": False, "stage": "validation", "error": error_msg}
        
    # Update UI
    if status_text:
        status_text.text("Starting workflow...")
    if progress_bar:
        progress_bar.progress(5)
    
    # Initialize agents
    extractor = ExtractorAgent()
    researcher = ResearcherAgent()
    citation_builder = CitationBuilderAgent()
    summary_agent = SummaryAgent()
    
    # Step 1: Extract NAP from Google Maps
    if status_text:
        status_text.text("Extracting business information from Google Maps...")
    
    extraction_results = await extractor.run(maps_url)
    
    if progress_bar:
        progress_bar.progress(20)
    
    # Handle extraction failure
    if not extraction_results.get("success") and not extraction_results.get("partial_success"):
        error_msg = extraction_results.get('error', 'Failed to extract required information')
        logger.error(f"Extraction failed: {error_msg}")
        if status_text:
            status_text.text(f"❌ Extraction failed: {error_msg}")
        return {
            "success": False,
            "stage": "extraction",
            "error": error_msg
        }
    
    # Validate name is present
    if not extraction_results.get("name"):
        error_msg = "Failed to extract business name, which is required"
        logger.error(error_msg)
        if status_text:
            status_text.text(f"❌ {error_msg}")
        return {
            "success": False,
            "stage": "extraction",
            "error": error_msg
        }
    
    logger.info(f"Extracted business: {extraction_results['name']}")
    
    # Ensure all fields are at least empty strings, not None
    extraction_results["name"] = extraction_results.get("name", "")
    extraction_results["address"] = extraction_results.get("address", "Address unavailable")
    extraction_results["phone"] = extraction_results.get("phone", "Phone unavailable")
    
    # Step 2: Research directory presence
    if status_text:
        status_text.text(f"Researching {extraction_results['name']} across business directories...")
    
    research_results = await researcher.run(extraction_results)
    
    if progress_bar:
        progress_bar.progress(50)
    
    if not research_results.get("success"):
        error_msg = research_results.get('error', 'Research failed')
        logger.error(f"Research failed: {error_msg}")
        if status_text:
            status_text.text(f"❌ Research failed: {error_msg}")
        return {"success": False, "stage": "research", "error": error_msg}
    
    # Ensure we have missing_directories and selected_directories
    research_results["missing_directories"] = research_results.get("missing_directories", [])
    research_results["selected_directories"] = research_results.get("selected_directories", [])
    
    logger.info(f"Found {len(research_results['missing_directories'])} missing directories")
    
    # Step 3: Build citations
    if status_text:
        status_text.text("Building citations for missing directories...")
    
    citation_results = await citation_builder.run(
        extraction_results, 
        research_results["selected_directories"]
    )
    
    if progress_bar:
        progress_bar.progress(75)
    
    if not citation_results.get("success"):
        error_msg = citation_results.get('error', 'Citation building failed')
        logger.error(f"Citation building failed: {error_msg}")
        if status_text:
            status_text.text(f"❌ Citation building failed: {error_msg}")
        return {"success": False, "stage": "citation_building", "error": error_msg}
    
    # Ensure citations dictionary exists
    citation_results["citations"] = citation_results.get("citations", {})
    
    # Step 4: Generate summary
    if status_text:
        status_text.text("Generating summary report...")
    
    summary_results = await summary_agent.run(
        extraction_results,
        research_results,
        citation_results
    )
    
    if progress_bar:
        progress_bar.progress(90)
    
    if not summary_results.get("success"):
        error_msg = summary_results.get('error', 'Summary generation failed')
        logger.error(f"Summary generation failed: {error_msg}")
        if status_text:
            status_text.text(f"❌ Summary generation failed: {error_msg}")
        return {"success": False, "stage": "summary", "error": error_msg}
    
    # Ensure summary exists
    summary_results["summary"] = summary_results.get("summary", "Summary unavailable")
    
    # Step 5: Create output file
    try:
        if status_text:
            status_text.text("Creating final report...")
        
        filename = generate_output_filename(extraction_results["name"])
        
        # Compile content for output file
        content = f"NAP CITATION REPORT FOR {extraction_results['name']}\n"
        content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += f"BUSINESS INFORMATION:\n"
        content += f"Name: {extraction_results['name']}\n"
        content += f"Address: {extraction_results['address']}\n"
        content += f"Phone: {extraction_results['phone']}\n"
        content += f"Source URL: {extraction_results['source_url']}\n\n"
        
        content += f"RESEARCH SUMMARY:\n"
        content += f"{summary_results['summary']}\n\n"
        
        content += f"CITATIONS:\n"
        for directory, citation in citation_results["citations"].items():
            content += f"\n--- {directory.upper()} CITATION ---\n"
            content += f"{citation}\n"
            content += f"-------------------------\n"
        
        filepath = save_text_file(content, filename, output_dir)
        logger.info(f"Saved output to {filepath}")
        
        if progress_bar:
            progress_bar.progress(100)
        if status_text:
            status_text.text("✅ Process completed successfully!")
        
        return {
            "success": True,
            "business_name": extraction_results["name"],
            "output_file": filepath,
            "business_info": extraction_results,
            "directories_checked": len(research_results["directories_checked"]),
            "directories_missing": len(research_results["missing_directories"]),
            "missing_directories": research_results["missing_directories"],
            "citations_created": len(citation_results["citations"]),
            "citations": citation_results["citations"],
            "summary": summary_results["summary"],
            "content": content  # Include the full content for download in stateless environments
        }
        
    except Exception as e:
        logger.error(f"Output generation failed: {str(e)}")
        if status_text:
            status_text.text(f"❌ Output generation failed: {str(e)}")
        return {"success": False, "stage": "output", "error": str(e)}

def display_success_view(result):
    """Display successful result data in a clean UI format."""
    st.success(f"Successfully processed {result['business_name']}")
    
    # Business info card
    with st.expander("Business Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {result['business_info']['name']}")
            st.markdown(f"**Address:** {result['business_info']['address']}")
        with col2:
            st.markdown(f"**Phone:** {result['business_info']['phone']}")
            st.markdown(f"**Source:** [Google Maps]({result['business_info']['source_url']})")
    
    # Statistics
    st.subheader("Citation Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Directories Checked", result['directories_checked'])
    col2.metric("Missing Citations", result['directories_missing'])
    col3.metric("Citations Created", result['citations_created'])
    
    # Create visualization data
    directory_data = []
    for dir in BUSINESS_DIRECTORIES:
        directory_name = dir.replace("https://www.", "").split(".")[0]
        status = "Missing" if directory_name in result['missing_directories'] else "Present"
        directory_data.append({"Directory": directory_name, "Status": status})
    
    df = pd.DataFrame(directory_data)
    
    # Create visualization
    fig = px.pie(df, names='Status', title='Directory Citation Status',
                color='Status', color_discrete_map={'Present': '#66BB6A', 'Missing': '#EF5350'})
    st.plotly_chart(fig)
    
    # Citations
    st.subheader("Generated Citations")
    for directory, citation in result['citations'].items():
        with st.expander(f"{directory} Citation"):
            st.text_area("", citation, height=150, key=directory)
    
    # Summary
    st.subheader("Research Summary")
    st.write(result['summary'])
    
    # Report file
    st.subheader("Generated Report")
    
    # For stateless environments or Streamlit Cloud, use the content directly 
    report_content = result.get('content', '')
    if not report_content and os.path.exists(result['output_file']):
        with open(result['output_file'], 'r') as f:
            report_content = f.read()
    
    # Display the report content
    st.text_area("Report Content", report_content, height=300)
    
    # Button to download report
    filename = os.path.basename(result['output_file'])
    st.download_button(
        label="Download Report",
        data=report_content,
        file_name=filename,
        mime="text/plain",
        key="download_report"
    )

def display_history():
    """Display history of previously processed businesses."""
    st.subheader("Processing History")
    
    output_dir = get_output_directory()
    
    # Check if directory exists first to prevent errors
    if not os.path.exists(output_dir):
        st.info("No previous reports found.")
        return
    
    reports = []
    for file in os.listdir(output_dir):
        if file.endswith(".txt"):
            path = os.path.join(output_dir, file)
            modified_time = os.path.getmtime(path)
            reports.append({
                "filename": file,
                "path": path,
                "modified": datetime.fromtimestamp(modified_time)
            })
    
    if not reports:
        st.info("No previous reports found.")
        return
    
    # Sort by most recent
    reports.sort(key=lambda x: x["modified"], reverse=True)
    
    # Display as a table
    df = pd.DataFrame([
        {"Business": r["filename"].replace("_nap_citation_report.txt", "").replace("_", " "),
         "Date": r["modified"].strftime("%Y-%m-%d %H:%M")}
        for r in reports
    ])
    
    st.dataframe(df, use_container_width=True)
    
    # Allow viewing old reports
    selected_report = st.selectbox("Select a report to view", 
                                  options=[r["filename"] for r in reports],
                                  format_func=lambda x: x.replace("_nap_citation_report.txt", "").replace("_", " "))
    
    if selected_report:
        report_path = next(r["path"] for r in reports if r["filename"] == selected_report)
        try:
            with open(report_path, 'r') as f:
                report_content = f.read()
            
            st.text_area("Report Content", report_content, height=300)
            
            st.download_button(
                label="Download Report",
                data=report_content,
                file_name=selected_report,
                mime="text/plain",
                key="download_history_report"
            )
        except Exception as e:
            st.error(f"Could not read report: {str(e)}")

def display_settings():
    """Display and allow editing of settings."""
    st.subheader("Settings")
    
    st.write("These settings can be modified in config.py.")
    
    # Display directories with checkboxes
    st.write("Business Directories to Check:")
    for directory in BUSINESS_DIRECTORIES:
        st.checkbox(directory.replace("https://www.", ""), value=True, disabled=True)
    
    # Other settings
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Page Load Timeout (seconds)", value=30, disabled=True)
        st.number_input("Element Wait Timeout (seconds)", value=10, disabled=True)
        st.checkbox("Debug Mode", value=True, disabled=True)
    
    with col2:
        st.number_input("Delay Between Requests (seconds)", value=3, disabled=True)
        st.checkbox("User Agent Rotation", value=True, disabled=True)
        st.checkbox("Use Proxies", value=False, disabled=True)

# Streamlit event handlers
def handle_run_workflow(maps_url):
    """Run the workflow with proper Streamlit async handling"""
    # Create progress elements
    prog_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Starting processing...")
    
    # Run the async workflow using asyncio.run
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_workflow(maps_url, prog_bar, status_text))
        loop.close()
        
        # Store result in session state for persistence
        st.session_state.last_result = result
        
        return result
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}")
        status_text.text(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    """Main Streamlit UI function."""
    # Set page config
    st.set_page_config(
        page_title="NAP Citation Agent",
        page_icon="📍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'last_result' not in st.session_state:
        st.session_state.last_result = None
    
    # Sidebar
    with st.sidebar:
        st.title("📍 NAP Citation Agent")
        st.write("Manage your business citations across the web")
        
        # Navigation
        page = st.radio("Navigation", ["Process New Business", "History", "Settings"])
        
        st.divider()
        st.write("About")
        st.write("""
        This tool helps businesses ensure consistent NAP 
        (Name, Address, Phone) information across various 
        business directories.
        """)
    
    # Main content area
    if page == "Process New Business":
        st.header("Process New Business")
        
        # Input form
        with st.form("url_form"):
            maps_url = st.text_input(
                "Enter Google Maps Business URL",
                placeholder="https://www.google.com/maps/place/your-business-name"
            )
            
            submitted = st.form_submit_button("Start Processing")
        
        # Process the URL
        if submitted and maps_url:
            result = handle_run_workflow(maps_url)
            
            if result and result.get("success"):
                display_success_view(result)
            elif result:
                st.error(f"Workflow failed at stage: {result.get('stage')}")
                st.error(f"Error: {result.get('error')}")
        elif submitted:
            st.warning("Please enter a Google Maps URL.")
        
        # Display last result if available
        elif st.session_state.last_result and st.session_state.last_result.get("success"):
            st.info("Showing results from previous processing")
            display_success_view(st.session_state.last_result)
    
    elif page == "History":
        display_history()
    
    elif page == "Settings":
        display_settings()

# Run the Streamlit app
if __name__ == "__main__":
    main()
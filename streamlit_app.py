import streamlit as st
import sys
import os
import time
from datetime import datetime
import io
from contextlib import redirect_stdout
import glob
import re

# Add parent directory to path
sys.path.append(os.path.dirname(__file__))

from FCI_NewsAgents.workflows.workflow_builder import workflow_execution
from FCI_NewsAgents.services.scrapers.run_article_scrapers import scrape_articles
from FCI_NewsAgents.services.scrapers.csai_scraper import scrape_papers
from FCI_NewsAgents.utils.utils import convert_article_to_document, convert_paper_to_document
from FCI_NewsAgents.core.config import GuardrailsConfig

def filter_logs(logs: str) -> str:
    """Filter out unwanted logs like DevTools and ERROR messages from Selenium"""
    lines = logs.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Skip DevTools listening messages
        if 'DevTools listening on' in line:
            continue
        # Skip ERROR messages from GPU/command buffer
        if 'ERROR:gpu' in line or 'ERROR:' in line and 'gles2_cmd_decoder' in line:
            continue
        # Skip other Chrome/Selenium internal errors
        if 'GroupMarkerNotSet' in line:
            continue
        
        # Skip verbose scraping intermediate logs
        if 'Starting article scraping' in line:
            continue
        if 'Running' in line and 'scrapers in parallel' in line:
            continue
        if '[Scraper_' in line and 'Starting' in line and 'scraper...' in line:
            continue
        if 'Scraping articles from https://' in line:
            continue
        if 'Scraping article:' in line:
            continue
        if 'Error parsing date' in line:
            continue
        if 'Successfully scraped:' in line:
            continue
        
        # Keep the line if it doesn't match unwanted patterns
        if line.strip():  # Only add non-empty lines
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines).strip()

# Page configuration
st.set_page_config(
    page_title="FCI NewsAgents - AI News Report Generator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    .report-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-header">FCI NewsAgents</h1>', unsafe_allow_html=True)
st.markdown("""
    <p style='text-align: center; font-size: 1.2rem; color: #666;'>
    AI-Powered Vietnamese Tech Report Generator for FPT Smart Cloud
    </p>
""", unsafe_allow_html=True)

# Sidebar configuration
st.sidebar.header("Configuration")
st.sidebar.markdown("---")

# Scraping Configuration
st.sidebar.subheader("Data Collection Settings")

max_papers = st.sidebar.number_input(
    "Papers to Scrape from arXiv",
    min_value=10,
    max_value=100,
    value=30,
    step=5,
    help="Total number of academic papers to fetch from arXiv cs.AI category. More papers = longer scraping time but more selection choices."
)

parallel_scraping = st.sidebar.checkbox(
    "Enable Parallel Scraping",
    value=True,
    help="Run multiple article scrapers simultaneously for faster performance. Recommended to keep enabled."
)

max_workers = st.sidebar.slider(
    "Number of Parallel Workers",
    min_value=2,
    max_value=8,
    value=4,
    help="How many scrapers run at the same time. Higher = faster but uses more resources. Only applies if parallel scraping is enabled."
)

# Workflow Configuration
st.sidebar.subheader("Processing Limits")

max_papers_read = st.sidebar.number_input(
    "Papers to Analyze (MAX_PAPERS_READ)",
    min_value=1,
    max_value=20,
    value=10,
    help="Maximum number of papers that will go through the guardrails filter. This limits how many papers are evaluated by the LLM."
)

max_articles_read = st.sidebar.number_input(
    "Articles to Analyze (MAX_ARTICLES_READ)",
    min_value=1,
    max_value=20,
    value=10,
    help="Maximum number of articles that will go through the guardrails filter. This limits how many articles are evaluated by the LLM."
)

max_documents_to_llm = st.sidebar.number_input(
    "Documents in Final Report (MAX_DOCUMENTS_TO_LLM)",
    min_value=1,
    max_value=20,
    value=10,
    help="Maximum number of documents (papers + articles) to include in the generated Vietnamese report. The LLM will select the most relevant ones."
)

st.sidebar.markdown("---")
st.sidebar.caption("Note: Higher values increase processing time and API costs")

# Output folder
output_folder = os.path.join("FCI_NewsAgents", "workflow_output")
os.makedirs(output_folder, exist_ok=True)

# Initialize session state
if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False
if 'report_content' not in st.session_state:
    st.session_state.report_content = ""
if 'report_path' not in st.session_state:
    st.session_state.report_path = ""
if 'execution_logs' not in st.session_state:
    st.session_state.execution_logs = []

# Main content area
tab1, tab2, tab3 = st.tabs(["Generate Report", "View Reports", "About"])

with tab1:
    st.header("Generate New AI News Report")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Papers to Scrape", max_papers)
    with col2:
        st.metric("Max Papers Processed", max_papers_read)
    with col3:
        st.metric("Max Articles Processed", max_articles_read)
    
    st.markdown("---")
    
    # Generate button
    if st.button("Generate Report", type="primary", use_container_width=True):
        st.session_state.report_generated = False
        st.session_state.execution_logs = []
        
        # Create a custom config
        config = GuardrailsConfig()
        config.MAX_PAPERS_READ = max_papers_read
        config.MAX_ARTICLES_READ = max_articles_read
        config.MAX_DOCUMENTS_TO_LLM = max_documents_to_llm
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.expander("Execution Logs", expanded=True)
        log_placeholder = log_container.empty()
        
        try:
            overall_start = time.time()
            
            # Step 1: Scrape articles
            status_text.text("Step 1/3: Scraping articles from news sources...")
            progress_bar.progress(10)
            
            f = io.StringIO()
            with redirect_stdout(f):
                article_dicts = scrape_articles(parallel=parallel_scraping, max_workers=max_workers)
            
            logs = filter_logs(f.getvalue())
            if logs:
                st.session_state.execution_logs.append(f"**SCRAPING ARTICLES**\n```\n{logs}\n```")
            log_placeholder.markdown("\n\n".join(st.session_state.execution_logs))
            
            articles = [convert_article_to_document(a) for a in article_dicts]
            progress_bar.progress(30)
            
            # Step 2: Scrape papers
            status_text.text("Step 2/3: Scraping papers from arXiv...")
            
            f = io.StringIO()
            with redirect_stdout(f):
                paper_dicts = scrape_papers(max_results=max_papers)
            
            logs = filter_logs(f.getvalue())
            if logs:
                st.session_state.execution_logs.append(f"**SCRAPING PAPERS**\n```\n{logs}\n```")
            log_placeholder.markdown("\n\n".join(st.session_state.execution_logs))
            
            papers = [convert_paper_to_document(p) for p in paper_dicts]
            progress_bar.progress(50)
            
            # Step 3: Run workflow
            status_text.text("Step 3/3: Running workflow (Guardrails + Generation)...")
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Temporarily update the config
                import FCI_NewsAgents.core.config as config_module
                original_config = config_module.GuardrailsConfig()
                config_module.GuardrailsConfig.MAX_PAPERS_READ = max_papers_read
                config_module.GuardrailsConfig.MAX_ARTICLES_READ = max_articles_read
                config_module.GuardrailsConfig.MAX_DOCUMENTS_TO_LLM = max_documents_to_llm
                
                final_state = workflow_execution(papers=papers, articles=articles, output_folder=output_folder)
            
            logs = filter_logs(f.getvalue())
            if logs:
                st.session_state.execution_logs.append(f"**RUNNING WORKFLOW**\n```\n{logs}\n```")
            log_placeholder.markdown("\n\n".join(st.session_state.execution_logs))
            
            progress_bar.progress(100)
            
            total_time = time.time() - overall_start
            
            # Get the report
            report_content = final_state.get('final_report', 'No report generated')
            
            # Find the most recent report file
            report_files = glob.glob(os.path.join(output_folder, "ai_news_report_*.md"))
            if report_files:
                latest_report = max(report_files, key=os.path.getctime)
                st.session_state.report_path = latest_report
                with open(latest_report, 'r', encoding='utf-8') as f:
                    st.session_state.report_content = f.read()
            else:
                st.session_state.report_content = report_content
                st.session_state.report_path = "Generated in memory"
            
            st.session_state.report_generated = True
            
            status_text.success(f"Report generated successfully in {total_time:.2f} seconds!")
            
            # Show success metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Papers Scraped", len(papers))
            with col2:
                st.metric("Total Articles Scraped", len(articles))
            with col3:
                st.metric("Execution Time", f"{total_time:.2f}s")
            
        except Exception as e:
            status_text.error(f"Error: {str(e)}")
            st.exception(e)
    
    # Display generated report
    if st.session_state.report_generated and st.session_state.report_content:
        st.markdown("---")
        st.subheader("Generated Report")
        
        # Download button
        st.download_button(
            label="Download Report",
            data=st.session_state.report_content,
            file_name=f"ai_news_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
        
        # Display report
        with st.container():
            st.markdown('<div class="report-container">', unsafe_allow_html=True)
            st.markdown(st.session_state.report_content)
            st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("Previously Generated Reports")
    
    # List all reports
    report_files = glob.glob(os.path.join(output_folder, "ai_news_report_*.md"))
    report_files.sort(key=os.path.getctime, reverse=True)
    
    if report_files:
        st.info(f"Total reports: {len(report_files)}")
        
        for report_file in report_files:
            file_name = os.path.basename(report_file)
            file_time = datetime.fromtimestamp(os.path.getctime(report_file))
            
            with st.expander(f"{file_name} - {file_time.strftime('%Y-%m-%d %H:%M:%S')}"):
                with open(report_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(content)
                with col2:
                    st.download_button(
                        label="Download",
                        data=content,
                        file_name=file_name,
                        mime="text/markdown",
                        key=file_name
                    )
    else:
        st.warning("No reports found. Generate your first report in the 'Generate Report' tab!")

with tab3:
    st.header("About FCI NewsAgents")
    
    st.markdown("""
    ### Purpose
    This system is designed for **FPT Smart Cloud's internal tech newsletter**, helping the team stay updated on:
    - Latest AI research relevant to cloud services
    - Emerging cloud computing technologies
    - Practical applications in data engineering
    - Security developments in AI/cloud
    
    ### How It Works
    
    1. **Article Scraping**: Scrapes AI news from:
       - The Neuron Daily
       - TechRepublic
       - Google Research Blog
    
    2. **Paper Scraping**: Fetches papers from arXiv's Computer Science - Artificial Intelligence category
    
    3. **Guardrails**: LLM-based filtering to select relevant content based on FCI's interests
    
    4. **Report Generation**: Creates a comprehensive Vietnamese tech report with:
       - Catchy Vietnamese title
       - Executive summary
       - Detailed sections per article/paper
       - Reference table with links
       - Conclusion with insights for FPT Smart Cloud
    
    ### Technologies Used
    - **LangGraph**: Workflow orchestration
    - **Google Gemini**: Primary LLM for filtering and generation
    - **BeautifulSoup4 & Selenium**: Web scraping
    - **Feedparser**: RSS feed parsing
    - **arXiv API**: Academic paper retrieval
    - **Streamlit**: User interface
    
    ### Internal Tool
    Built for FPT Smart Cloud (FCI) - Internship 2025 Summer
    """)
    
    # Environment check
    st.markdown("---")
    st.subheader("Environment Check")
    
    import dotenv
    dotenv.load_dotenv()
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    col1, col2 = st.columns(2)
    with col1:
        if gemini_key:
            st.success("Gemini API Key: Configured")
        else:
            st.error("Gemini API Key: Not Found")
    
    with col2:
        if openai_key:
            st.success("OpenAI API Key: Configured")
        else:
            st.warning("OpenAI API Key: Not Found (Optional)")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>FCI NewsAgents v1.0</p>
        <p>FPT Smart Cloud</p>
    </div>
""", unsafe_allow_html=True)

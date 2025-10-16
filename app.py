import streamlit as st
import os
from dotenv import load_dotenv
from src.dexter.agent import Agent
from src.dexter.utils.discord import DiscordWebhook
from src.dexter.database import Database
import traceback
import uuid

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Dexter - Financial Research Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🤖 Dexter - Autonomous Financial Research Agent")
    st.markdown("*An autonomous agent for deep financial research that thinks, plans, and learns as it works.*")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # API Key status
        openai_key = os.getenv("OPENAI_API_KEY", "")
        financial_key = os.getenv("FINANCIAL_DATASETS_API_KEY", "")
        
        if openai_key and financial_key:
            st.success("✅ API Keys configured")
        else:
            st.error("❌ Missing API Keys")
            st.markdown("Please ensure you have set:")
            if not openai_key:
                st.markdown("- `OPENAI_API_KEY`")
            if not financial_key:
                st.markdown("- `FINANCIAL_DATASETS_API_KEY`")
        
        # Discord Webhook Configuration
        st.subheader("Discord Webhook")
        discord_webhook_url = st.text_input(
            "Discord Webhook URL (optional)",
            type="password",
            help="Paste your Discord webhook URL to receive research results in Discord"
        )
        if discord_webhook_url:
            st.session_state.discord_webhook = discord_webhook_url
            st.success("✅ Discord webhook configured")
            
            if st.button("🧪 Test Webhook"):
                try:
                    test_discord = DiscordWebhook(discord_webhook_url)
                    if test_discord.test_webhook():
                        st.success("✅ Test message sent successfully!")
                    else:
                        st.error("❌ Failed to send test message. Check your webhook URL.")
                except Exception as e:
                    st.error(f"❌ Webhook test failed: {str(e)}")
        else:
            st.session_state.discord_webhook = None
        
        with st.expander("How to get Discord Webhook URL"):
            st.markdown("""
            1. Go to your Discord server
            2. Right-click on a channel → Edit Channel
            3. Go to Integrations → Webhooks
            4. Click "New Webhook" or "Copy Webhook URL"
            5. Paste the URL above
            """)
        
        # Agent configuration
        st.subheader("Safety Limits")
        max_steps = st.slider("Max Total Steps", min_value=5, max_value=50, value=20)
        max_steps_per_task = st.slider("Max Steps Per Task", min_value=2, max_value=10, value=5)
        
        st.subheader("Example Queries")
        st.markdown("""
        - "What was Apple's revenue growth over the last 4 quarters?"
        - "Compare Microsoft and Google's operating margins for 2023"
        - "Analyze Tesla's cash flow trends over the past year"
        - "What is Amazon's debt-to-equity ratio based on recent financials?"
        """)
    
    # Main interface
    if not (openai_key and financial_key):
        st.warning("⚠️ Please configure your API keys in the environment variables to use Dexter.")
        st.code("""
# Add to your .env file:
OPENAI_API_KEY=your-openai-api-key
FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key
        """)
        return
    
    # Query input
    query = st.text_area(
        "Enter your financial research question:",
        placeholder="e.g., Compare Apple and Microsoft's revenue growth over the last 4 quarters",
        height=100
    )
    
    # Initialize session state
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'execution_log' not in st.session_state:
        st.session_state.execution_log = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'db' not in st.session_state:
        try:
            st.session_state.db = Database()
        except Exception as e:
            st.session_state.db = None
            st.warning(f"Database connection unavailable: {str(e)}")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🔍 Research", type="primary", disabled=not query.strip()):
            # Initialize agent with current configuration
            st.session_state.agent = Agent(
                max_steps=max_steps,
                max_steps_per_task=max_steps_per_task
            )
            st.session_state.results = None
            st.session_state.execution_log = []
            
            # Create placeholders for real-time updates
            with st.container():
                status_placeholder = st.empty()
                progress_placeholder = st.empty()
                log_placeholder = st.empty()
                
                try:
                    # Execute research with progress updates
                    status_placeholder.info("🤖 Dexter is analyzing your query...")
                    
                    def update_callback(step_info):
                        st.session_state.execution_log.append(step_info)
                        
                        # Update progress
                        progress = min(len(st.session_state.execution_log) / max_steps, 1.0)
                        progress_placeholder.progress(progress)
                        
                        # Update status
                        if step_info.get('type') == 'planning':
                            status_placeholder.info(f"📋 Planning: {step_info.get('message', '')}")
                        elif step_info.get('type') == 'action':
                            status_placeholder.info(f"⚡ Executing: {step_info.get('message', '')}")
                        elif step_info.get('type') == 'validation':
                            status_placeholder.info(f"✅ Validating: {step_info.get('message', '')}")
                        elif step_info.get('type') == 'answer':
                            status_placeholder.info(f"📝 Synthesizing: {step_info.get('message', '')}")
                        
                        # Update log display
                        with log_placeholder.expander("📊 Execution Log", expanded=False):
                            for i, log_entry in enumerate(st.session_state.execution_log):
                                st.text(f"Step {i+1}: [{log_entry.get('type', 'unknown')}] {log_entry.get('message', '')}")
                    
                    # Execute the research
                    results = st.session_state.agent.research(query, callback=update_callback)
                    st.session_state.results = results
                    
                    status_placeholder.success("✅ Research completed!")
                    progress_placeholder.progress(1.0)
                    
                    # Save to database
                    if st.session_state.db:
                        try:
                            result_id = st.session_state.db.save_research_result(
                                query=query,
                                answer=results.get('answer', ''),
                                tasks_completed=results.get('tasks_completed', []),
                                stats=results.get('stats', {}),
                                session_id=st.session_state.session_id
                            )
                            st.session_state.last_saved_id = result_id
                        except Exception as db_error:
                            st.warning(f"⚠️ Could not save to database: {str(db_error)}")
                    
                    # Send to Discord if webhook is configured
                    discord_webhook_url = st.session_state.get('discord_webhook')
                    if discord_webhook_url:
                        try:
                            discord = DiscordWebhook(discord_webhook_url)
                            webhook_success = discord.send_research_results(
                                query=query,
                                answer=results.get('answer', ''),
                                stats=results.get('stats', {}),
                                tasks=results.get('tasks_completed', [])
                            )
                            if webhook_success:
                                st.success("📤 Results sent to Discord!")
                            else:
                                st.warning("⚠️ Failed to send to Discord webhook")
                        except Exception as discord_error:
                            st.warning(f"⚠️ Discord webhook error: {str(discord_error)}")
                    
                except Exception as e:
                    status_placeholder.error(f"❌ Error during research: {str(e)}")
                    st.error("Full error details:")
                    st.code(traceback.format_exc())
                    
                    # Send error to Discord if webhook is configured
                    discord_webhook_url = st.session_state.get('discord_webhook')
                    if discord_webhook_url:
                        try:
                            discord = DiscordWebhook(discord_webhook_url)
                            discord.send_error_notification(query, str(e))
                        except Exception:
                            pass
    
    with col2:
        if st.button("🗑️ Clear Results"):
            st.session_state.results = None
            st.session_state.execution_log = []
            st.rerun()
    
    # Display results
    if st.session_state.results:
        st.markdown("---")
        st.header("📊 Research Results")
        
        # Main answer
        if 'answer' in st.session_state.results:
            st.subheader("Summary")
            st.markdown(st.session_state.results['answer'])
        
        # Detailed findings
        if 'tasks_completed' in st.session_state.results:
            st.subheader("Research Breakdown")
            
            for i, task in enumerate(st.session_state.results['tasks_completed'], 1):
                with st.expander(f"Task {i}: {task.get('description', 'Unknown task')}", expanded=False):
                    if 'result' in task:
                        st.markdown("**Result:**")
                        st.markdown(task['result'])
                    
                    if 'data' in task:
                        st.markdown("**Data Retrieved:**")
                        st.json(task['data'])
                    
                    if 'calculations' in task:
                        st.markdown("**Calculations:**")
                        st.code(task['calculations'])
        
        # Execution statistics
        if 'stats' in st.session_state.results:
            st.subheader("Execution Statistics")
            stats = st.session_state.results['stats']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Steps", stats.get('total_steps', 0))
            with col2:
                st.metric("Tasks Completed", stats.get('tasks_completed', 0))
            with col3:
                st.metric("API Calls", stats.get('api_calls', 0))
            with col4:
                st.metric("Execution Time", f"{stats.get('execution_time', 0):.2f}s")
    
    # Execution log
    if st.session_state.execution_log:
        with st.expander("📋 Detailed Execution Log", expanded=False):
            for i, log_entry in enumerate(st.session_state.execution_log):
                st.text(f"Step {i+1} [{log_entry.get('timestamp', '')}]: [{log_entry.get('type', 'unknown')}] {log_entry.get('message', '')}")

if __name__ == "__main__":
    main()

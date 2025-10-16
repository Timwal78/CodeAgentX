import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from src.dexter.agent import Agent
from src.dexter.utils.discord import DiscordWebhook
from src.dexter.database import Database
from src.dexter.utils.charts import FinancialCharts
from src.dexter.utils.export import ExportManager
from src.dexter.scheduler import MOASSScheduler
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
    
    # Initialize session state early
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'execution_log' not in st.session_state:
        st.session_state.execution_log = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'query_text' not in st.session_state:
        st.session_state.query_text = ""
    if 'db' not in st.session_state:
        try:
            st.session_state.db = Database()
        except Exception as e:
            st.session_state.db = None
            st.warning(f"Database connection unavailable: {str(e)}")
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = None
    if 'scheduler_running' not in st.session_state:
        st.session_state.scheduler_running = False
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # API Key status
        openai_key = os.getenv("OPENAI_API_KEY", "")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        financial_key = os.getenv("FINANCIAL_DATASETS_API_KEY", "")
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        fmp_key = os.getenv("FMP_API_KEY", "")
        
        # Show LLM Provider status
        st.subheader("🤖 AI Provider")
        if gemini_key:
            st.success("✅ Using Google Gemini (FREE)")
        elif openai_key:
            st.info("Using OpenAI (Requires credits)")
        else:
            st.error("❌ No AI provider configured")
            st.markdown("""
            **Get a FREE API key:**
            1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
            2. Click "Create API Key"
            3. Copy the key and add it as `GEMINI_API_KEY` secret
            
            *OR use OpenAI (requires credits):*
            - Add `OPENAI_API_KEY` from [OpenAI Platform](https://platform.openai.com/api-keys)
            """)
        
        # Financial data API status
        st.subheader("📊 Financial Data")
        if financial_key:
            st.success("✅ Financial Datasets API configured")
        else:
            st.error("❌ Missing FINANCIAL_DATASETS_API_KEY")
            st.markdown("Get it from [financialdatasets.ai](https://financialdatasets.ai/)")
        
        # Optional API Keys for fallback data sources
        fallback_sources = []
        if alpha_vantage_key:
            fallback_sources.append("Alpha Vantage")
        if fmp_key:
            fallback_sources.append("Financial Modeling Prep")
        
        if fallback_sources:
            st.info(f"📊 Fallback sources active: {', '.join(fallback_sources)}")
        else:
            with st.expander("ℹ️ Optional: Fallback Data Sources"):
                st.markdown("""
                For increased reliability, you can add optional API keys:
                - `ALPHA_VANTAGE_API_KEY` - Free tier: 25 calls/day
                - `FMP_API_KEY` - Financial Modeling Prep API
                
                These will be used if the primary API fails.
                """)
        
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
        
        # Scheduled Scanning
        st.markdown("---")
        st.subheader("⏰ Scheduled Scanning")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🦅 Start Scheduler" if not st.session_state.scheduler_running else "⏸️ Stop Scheduler"):
                try:
                    if not st.session_state.scheduler_running:
                        # Start scheduler
                        webhook_url = st.session_state.get('discord_webhook')
                        st.session_state.scheduler = MOASSScheduler(discord_webhook_url=webhook_url)
                        st.session_state.scheduler.start()
                        st.session_state.scheduler_running = True
                        st.success("🦅 Scheduler started!")
                    else:
                        # Stop scheduler
                        if st.session_state.scheduler:
                            st.session_state.scheduler.stop()
                        st.session_state.scheduler_running = False
                        st.info("Scheduler stopped")
                    st.rerun()
                except Exception as e:
                    st.error(f"Scheduler error: {str(e)}")
        
        with col2:
            if st.button("🔍 Manual Scan"):
                try:
                    webhook_url = st.session_state.get('discord_webhook')
                    if not st.session_state.scheduler:
                        st.session_state.scheduler = MOASSScheduler(discord_webhook_url=webhook_url)
                    
                    with st.spinner("Running eagle eyes scan..."):
                        results = st.session_state.scheduler.manual_scan("eagle_eyes")
                        if results:
                            st.success("✅ Scan complete!")
                            st.session_state.last_scan_results = results
                        else:
                            st.warning("Scan completed with errors")
                except Exception as e:
                    st.error(f"Scan error: {str(e)}")
        
        # Show schedule status
        if st.session_state.scheduler_running:
            st.success("🟢 Scheduler Active")
            with st.expander("📅 Schedule Details"):
                st.markdown("""
                **Eagle Eyes Scans** (comprehensive):
                - 🦅 **7:00 AM EST** - Market Open Prep
                - 🦅 **3:05 PM EST** - Power Hour Hunter
                
                **Regular Scans** (every 2 hours):
                - 📊 9:00 AM EST
                - 📊 11:00 AM EST
                - 📊 1:00 PM EST
                
                **What's scanned:**
                - MOASS candidates
                - TTM Squeeze setups
                - Bullish/bearish patterns
                - Penny stock opportunities
                - Double bottom + put wall
                """)
        
        # Show recent scans
        if st.session_state.scheduler and hasattr(st.session_state.scheduler, 'scan_history'):
            history = st.session_state.scheduler.get_scan_history(limit=5)
            if history:
                with st.expander("📊 Recent Scans"):
                    for i, scan in enumerate(reversed(history)):
                        scan_time = datetime.fromisoformat(scan['timestamp']).strftime('%I:%M %p')
                        scan_type = "🦅 Eagle Eyes" if scan['scan_type'] == 'eagle_eyes' else "📊 Regular"
                        findings_count = sum(len(v) for v in scan.get('findings', {}).values())
                        
                        with st.expander(f"{scan_type} - {scan_time} - {findings_count} findings"):
                            findings = scan.get('findings', {})
                            
                            # MOASS Candidates
                            if findings.get('moass'):
                                st.markdown("**🚀 MOASS Candidates:**")
                                for stock in findings['moass'][:3]:
                                    st.markdown(f"**{stock['symbol']}** @ ${stock['price']} - Score: {stock['moass_score']}/100")
                                    if 'buy_at' in stock:
                                        st.markdown(f"  📈 BUY @ ${stock['buy_at']} | 🎯 SELL @ ${stock['sell_at']} | 🛑 STOP @ ${stock['stop_loss']} | R:R {stock.get('risk_reward', 'N/A')}:1")
                            
                            # TTM Squeeze
                            if findings.get('squeeze'):
                                st.markdown("**💥 TTM Squeeze:**")
                                for stock in findings['squeeze'][:3]:
                                    status = "🔥 FIRING" if stock['squeeze_firing'] else "⏳ ACTIVE"
                                    st.markdown(f"**{stock['symbol']}** @ ${stock['price']} - {status}")
                                    if 'buy_at' in stock:
                                        st.markdown(f"  📈 BUY @ ${stock['buy_at']} | 🎯 SELL @ ${stock['sell_at']} | 🛑 STOP @ ${stock['stop_loss']}")
                            
                            # Penny Stocks
                            if findings.get('penny_stocks'):
                                st.markdown("**💰 Penny Stocks:**")
                                for stock in findings['penny_stocks'][:3]:
                                    st.markdown(f"**{stock['symbol']}** @ ${stock['price']} - Score: {stock['squeeze_score']}")
                                    if 'buy_at' in stock:
                                        st.markdown(f"  📈 BUY @ ${stock['buy_at']} | 🎯 SELL @ ${stock['sell_at']} | 🛑 STOP @ ${stock['stop_loss']}")
        
        st.markdown("---")
        
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
        
        # Conversation History
        if st.session_state.db:
            st.markdown("---")
            st.subheader("📜 Conversation History")
            
            search_term = st.text_input("Search history", placeholder="Search queries...")
            
            try:
                if search_term:
                    history = st.session_state.db.search_conversation_history(search_term, limit=10)
                else:
                    history = st.session_state.db.get_conversation_history(limit=10)
                
                if history:
                    for item in history:
                        query_preview = item['query'][:60] + "..." if len(item['query']) > 60 else item['query']
                        timestamp = item['created_at'].strftime("%b %d, %H:%M") if hasattr(item['created_at'], 'strftime') else str(item['created_at'])[:16]
                        
                        if st.button(f"📝 {query_preview}", key=f"hist_{item['id']}", help=f"{timestamp}"):
                            st.session_state.selected_history_id = item['id']
                            st.session_state.results = {
                                'query': item['query'],
                                'answer': item['answer'],
                                'tasks_completed': item['tasks_completed'],
                                'stats': item['stats']
                            }
                            st.rerun()
                else:
                    st.info("No research history yet")
            except Exception as e:
                st.error(f"Error loading history: {str(e)}")
            
            # Query Templates
            st.markdown("---")
            st.subheader("📑 Query Templates")
            
            tab1, tab2 = st.tabs(["Browse", "Create"])
            
            with tab1:
                try:
                    categories = st.session_state.db.get_template_categories()
                    category_filter = st.selectbox(
                        "Category",
                        options=["All"] + categories,
                        key="template_category_filter"
                    )
                    
                    if category_filter == "All":
                        templates = st.session_state.db.get_templates()
                    else:
                        templates = st.session_state.db.get_templates(category=category_filter)
                    
                    if templates:
                        for template in templates:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                if st.button(
                                    f"📄 {template['name']}", 
                                    key=f"template_{template['id']}",
                                    help=template.get('description', template['query_text'][:100])
                                ):
                                    st.session_state.query_text = template['query_text']
                                    st.rerun()
                            with col2:
                                if st.button("🗑️", key=f"del_template_{template['id']}", help="Delete"):
                                    st.session_state.db.delete_template(template['id'])
                                    st.rerun()
                    else:
                        st.info("No templates yet. Create one in the 'Create' tab!")
                except Exception as e:
                    st.error(f"Error loading templates: {str(e)}")
            
            with tab2:
                with st.form("create_template_form"):
                    template_name = st.text_input("Template Name", placeholder="e.g., Revenue Growth Analysis")
                    template_query = st.text_area(
                        "Query Template", 
                        placeholder="e.g., Compare {company1} and {company2}'s revenue growth over the last {quarters} quarters",
                        height=100
                    )
                    template_category = st.text_input("Category", placeholder="e.g., Revenue Analysis")
                    template_description = st.text_input("Description (optional)", placeholder="Brief description of this template")
                    
                    if st.form_submit_button("💾 Save Template"):
                        if template_name and template_query:
                            try:
                                st.session_state.db.save_template(
                                    name=template_name,
                                    query_text=template_query,
                                    category=template_category or None,
                                    description=template_description or None
                                )
                                st.success("✅ Template saved!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving template: {str(e)}")
                        else:
                            st.warning("Please provide a name and query text")
    
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
        value=st.session_state.query_text,
        placeholder="e.g., Compare Apple and Microsoft's revenue growth over the last 4 quarters",
        height=100,
        key="query_input"
    )
    
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
        
        col_header1, col_header2, col_header3, col_header4 = st.columns([2, 1, 1, 1])
        with col_header1:
            st.header("📊 Research Results")
        with col_header2:
            if st.button("💬 Follow-up", type="secondary"):
                previous_query = st.session_state.results.get('query', '')
                previous_answer = st.session_state.results.get('answer', '')[:500]
                st.session_state.query_text = f"Follow-up to: '{previous_query}'\n\nPrevious findings: {previous_answer}...\n\nMy follow-up question: "
                st.rerun()
        with col_header3:
            try:
                pdf_bytes = ExportManager.generate_pdf(
                    query=st.session_state.results.get('query', ''),
                    answer=st.session_state.results.get('answer', ''),
                    tasks=st.session_state.results.get('tasks_completed', []),
                    stats=st.session_state.results.get('stats', {})
                )
                st.download_button(
                    label="📄 PDF",
                    data=pdf_bytes,
                    file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    type="secondary"
                )
            except Exception as e:
                st.button("📄 PDF", disabled=True, help=str(e), type="secondary")
        with col_header4:
            try:
                excel_bytes = ExportManager.generate_excel(
                    query=st.session_state.results.get('query', ''),
                    answer=st.session_state.results.get('answer', ''),
                    tasks=st.session_state.results.get('tasks_completed', []),
                    stats=st.session_state.results.get('stats', {})
                )
                st.download_button(
                    label="📊 Excel",
                    data=excel_bytes,
                    file_name=f"research_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="secondary"
                )
            except Exception as e:
                st.button("📊 Excel", disabled=True, help=str(e), type="secondary")
        
        # Main answer
        if 'answer' in st.session_state.results:
            st.subheader("Summary")
            st.markdown(st.session_state.results['answer'])
        
        # Data Visualizations
        if 'tasks_completed' in st.session_state.results and st.session_state.results['tasks_completed']:
            try:
                charts = FinancialCharts.analyze_and_create_charts(st.session_state.results['tasks_completed'])
                if charts:
                    st.subheader("📈 Visual Analysis")
                    for chart in charts:
                        st.plotly_chart(chart, use_container_width=True)
            except Exception as chart_error:
                pass
        
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

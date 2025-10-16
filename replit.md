# Dexter - Autonomous Financial Research Agent 🤖

An autonomous agent for deep financial research that thinks, plans, and learns as it works.

## Overview

Dexter is a Streamlit-based financial research agent that uses a multi-agent architecture to perform comprehensive financial analysis. It takes complex financial questions, breaks them into structured research tasks, executes them with real-time market data, validates results, and synthesizes comprehensive answers.

## Recent Changes

### Latest Enhancements (October 16, 2025)
- **PostgreSQL Database Integration** - Added conversation history persistence with full search capability
- **Data Visualization** - Integrated Plotly charts for revenue trends, margin comparisons, and financial metrics
- **Export Functionality** - Built PDF and Excel export for research reports with formatted tables and statistics
- **Query Templates System** - Created template library for saving, browsing, and executing reusable analysis queries
- **Alternative Data Sources** - Added fallback support for Alpha Vantage and Financial Modeling Prep APIs
- **Follow-up Questions** - Implemented context-aware follow-up question functionality
- **Discord Webhooks** - Rich embed notifications for research results and errors sent to Discord channels
- **Options Trading Data** - Free options analysis using yfinance with strike prices, OI, volume, IV, and calculated Greeks
- **Unusual Flow Detection** - Identify unusual options activity based on volume/OI ratios
- **Options Visualization** - Volume/OI bar charts and implied volatility skew plots

## Architecture

### Multi-Agent System

1. **Planning Agent** - Analyzes queries and creates structured task plans
2. **Action Agent** - Executes individual tasks using appropriate financial data tools
3. **Validation Agent** - Checks task completion quality and data sufficiency
4. **Answer Agent** - Synthesizes findings into comprehensive responses

### Key Components

- `app.py` - Streamlit web interface with all features
- `src/dexter/agent.py` - Main agent orchestration logic
- `src/dexter/model.py` - LLM interface (OpenAI GPT-5)
- `src/dexter/tools.py` - Financial data retrieval with multi-source fallback
- `src/dexter/prompts.py` - System prompts for each agent
- `src/dexter/schemas.py` - Pydantic data models
- `src/dexter/database.py` - PostgreSQL integration for history and templates
- `src/dexter/utils/safety.py` - Safety manager for preventing runaway execution
- `src/dexter/utils/validation.py` - Validation manager for quality checks
- `src/dexter/utils/discord.py` - Discord webhook integration
- `src/dexter/utils/charts.py` - Plotly visualization for financial data
- `src/dexter/utils/export.py` - PDF and Excel export functionality

## Features

### Core Capabilities
- Intelligent task decomposition of complex financial queries
- Multi-source financial data retrieval with automatic fallback (Financial Datasets, Alpha Vantage, FMP)
- Self-validation and iterative refinement of results
- Safety features (loop detection, step limits)
- Comprehensive execution logging and statistics
- PostgreSQL-based conversation history with full-text search

### Data Visualization
- Automatic chart generation from financial data
- Revenue trend line charts
- Margin and ratio comparison bar charts
- Interactive Plotly visualizations

### Export & Sharing
- PDF report generation with formatted tables and statistics
- Excel workbook export with multiple sheets (summary, stats, tasks)
- Discord webhook integration with rich embeds
- Automatic error notifications and task breakdowns

### Query Templates
- Save reusable query templates with categories
- Browse and execute template library
- Template management (create, delete, organize)
- Parameter substitution support

### Safety Features
- Global step limit (configurable, default: 20)
- Per-task step limit (configurable, default: 5)
- Loop detection to prevent infinite execution
- Multi-provider API rate limiting
- Execution timeouts

## Configuration

### Required API Keys
- `OPENAI_API_KEY` - For AI agent reasoning and analysis (GPT-5)
- `FINANCIAL_DATASETS_API_KEY` - For real-time financial data (get from https://financialdatasets.ai/)

### Optional Configuration
- Discord webhook URL (configured in the Streamlit sidebar)
- Max steps (5-50, default: 20)
- Max steps per task (2-10, default: 5)

### Optional API Keys (Fallback Data Sources)
- `ALPHA_VANTAGE_API_KEY` - Free tier: 25 calls/day (https://www.alphavantage.co/)
- `FMP_API_KEY` - Financial Modeling Prep API (https://financialmodelingprep.com/)

## Example Queries

- "What was Apple's revenue growth over the last 4 quarters?"
- "Compare Microsoft and Google's operating margins for 2023"
- "Analyze Tesla's cash flow trends over the past year"
- "What is Amazon's debt-to-equity ratio based on recent financials?"

## How to Use

1. **Configure API Keys** - Add your OpenAI and Financial Datasets API keys as secrets
2. **Optional: Set up Discord Webhook** - Add your Discord webhook URL in the sidebar
3. **Enter Your Query** - Type your financial research question
4. **Click Research** - Dexter will autonomously plan, execute, and validate research
5. **View Results** - Get comprehensive analysis with data-backed insights
6. **Optional: Check Discord** - Results automatically sent to your Discord channel

## Technical Stack

- **Frontend**: Streamlit
- **AI/LLM**: OpenAI GPT-5
- **Data Validation**: Pydantic
- **Financial Data**: Financial Datasets API
- **Notifications**: Discord Webhooks
- **HTTP Requests**: Requests library

## Project Structure

```
dexter/
├── app.py                  # Main Streamlit application
├── src/
│   └── dexter/
│       ├── agent.py        # Agent orchestration
│       ├── model.py        # LLM interface
│       ├── tools.py        # Financial data tools
│       ├── prompts.py      # System prompts
│       ├── schemas.py      # Data models
│       └── utils/
│           ├── safety.py       # Safety manager
│           ├── validation.py   # Validation manager
│           └── discord.py      # Discord integration
├── .streamlit/
│   └── config.toml        # Streamlit configuration
└── replit.md              # This file
```

## Deployment

The application runs on Streamlit server on port 5000:
```bash
streamlit run app.py --server.port 5000
```

## Future Enhancements

Potential improvements include:
- Enhanced Discord features (interactive buttons, charts)
- Real-time streaming responses
- Multi-currency support
- Advanced financial modeling capabilities
- AI-powered insights and recommendations
- Integration with more data providers

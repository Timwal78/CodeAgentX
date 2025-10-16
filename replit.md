# Dexter - Autonomous Financial Research Agent 🤖

An autonomous agent for deep financial research that thinks, plans, and learns as it works.

## Overview

Dexter is a Streamlit-based financial research agent that uses a multi-agent architecture to perform comprehensive financial analysis. It takes complex financial questions, breaks them into structured research tasks, executes them with real-time market data, validates results, and synthesizes comprehensive answers.

## Recent Changes

### Discord Webhook Integration (October 16, 2025)
- Added Discord webhook functionality to send research results to Discord channels
- Created Discord utility module (`src/dexter/utils/discord.py`) with rich embed formatting
- Added webhook configuration UI in Streamlit sidebar
- Implemented test webhook button for quick validation
- Added automatic notifications for both successful research and errors

## Architecture

### Multi-Agent System

1. **Planning Agent** - Analyzes queries and creates structured task plans
2. **Action Agent** - Executes individual tasks using appropriate financial data tools
3. **Validation Agent** - Checks task completion quality and data sufficiency
4. **Answer Agent** - Synthesizes findings into comprehensive responses

### Key Components

- `app.py` - Streamlit web interface with Discord webhook integration
- `src/dexter/agent.py` - Main agent orchestration logic
- `src/dexter/model.py` - LLM interface (OpenAI GPT-5)
- `src/dexter/tools.py` - Financial data retrieval tools
- `src/dexter/prompts.py` - System prompts for each agent
- `src/dexter/schemas.py` - Pydantic data models
- `src/dexter/utils/safety.py` - Safety manager for preventing runaway execution
- `src/dexter/utils/validation.py` - Validation manager for quality checks
- `src/dexter/utils/discord.py` - Discord webhook integration

## Features

### Core Capabilities
- Intelligent task decomposition of complex financial queries
- Real-time financial data retrieval (income statements, balance sheets, cash flow)
- Self-validation and iterative refinement of results
- Safety features (loop detection, step limits)
- Comprehensive execution logging and statistics

### Discord Integration
- Send research results as rich Discord embeds
- Automatic error notifications
- Task breakdown visibility
- Execution statistics in Discord
- Test webhook functionality

### Safety Features
- Global step limit (configurable, default: 20)
- Per-task step limit (configurable, default: 5)
- Loop detection to prevent infinite execution
- API rate limiting
- Execution timeouts

## Configuration

### Required API Keys
- `OPENAI_API_KEY` - For AI agent reasoning and analysis (GPT-5)
- `FINANCIAL_DATASETS_API_KEY` - For real-time financial data (get from https://financialdatasets.ai/)

### Optional Configuration
- Discord webhook URL (configured in the Streamlit sidebar)
- Max steps (5-50, default: 20)
- Max steps per task (2-10, default: 5)

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
- Conversation history and follow-up questions
- Data visualization charts for financial metrics
- Export functionality (PDF/Excel)
- Multiple data source support
- Saved query templates
- Enhanced Discord features (interactive buttons, charts)

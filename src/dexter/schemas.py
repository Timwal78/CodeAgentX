from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class Task(BaseModel):
    """Schema for individual research tasks."""
    id: str
    description: str
    tool_needed: str
    dependencies: List[str] = Field(default_factory=list)
    priority: int = Field(default=1, ge=1, le=5)
    estimated_time: Optional[int] = None  # in seconds


class TaskResult(BaseModel):
    """Schema for completed task results."""
    task_id: str
    description: str
    result: str
    data: Optional[Dict[str, Any]] = None
    calculations: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: str
    execution_time: Optional[float] = None


class ResearchResult(BaseModel):
    """Schema for complete research session results."""
    query: str
    answer: str
    tasks_completed: List[Dict[str, Any]]
    stats: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None


class CompanyProfile(BaseModel):
    """Schema for company profile information."""
    symbol: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    description: Optional[str] = None
    website: Optional[str] = None
    headquarters: Optional[str] = None
    employees: Optional[int] = None


class FinancialStatement(BaseModel):
    """Base schema for financial statements."""
    symbol: str
    period: str  # e.g., "2023-Q4", "2023"
    period_type: str  # "annual" or "quarterly"
    currency: str = "USD"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class IncomeStatement(FinancialStatement):
    """Schema for income statement data."""
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    earnings_per_share: Optional[float] = None
    shares_outstanding: Optional[float] = None


class BalanceSheet(FinancialStatement):
    """Schema for balance sheet data."""
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    total_debt: Optional[float] = None
    shareholders_equity: Optional[float] = None
    retained_earnings: Optional[float] = None


class CashFlowStatement(FinancialStatement):
    """Schema for cash flow statement data."""
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    net_change_in_cash: Optional[float] = None


class FinancialRatios(BaseModel):
    """Schema for calculated financial ratios."""
    symbol: str
    period: str
    
    # Profitability ratios
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    
    # Liquidity ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None
    
    # Leverage ratios
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None
    
    # Efficiency ratios
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ExecutionLog(BaseModel):
    """Schema for execution step logging."""
    step_number: int
    step_type: str  # "planning", "action", "validation", "answer"
    message: str
    timestamp: str
    duration: Optional[float] = None
    success: bool = True
    error_details: Optional[str] = None


class AgentConfiguration(BaseModel):
    """Schema for agent configuration settings."""
    max_steps: int = 20
    max_steps_per_task: int = 5
    timeout_seconds: int = 300
    retry_attempts: int = 3
    enable_validation: bool = True
    enable_safety_checks: bool = True
    log_level: str = "INFO"
    
    # Model configuration
    model_name: str = "gpt-5"
    max_tokens: int = 4096
    
    # API configuration
    api_timeout: int = 30
    rate_limit_per_minute: int = 60

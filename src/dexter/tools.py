import os
import requests
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta


class FinancialDataTools:
    """
    Tools for retrieving real-time financial data from Financial Datasets API with fallback support.
    Supports multiple data providers: Financial Datasets, Alpha Vantage, and Financial Modeling Prep.
    """
    
    def __init__(self):
        # Primary API - Financial Datasets
        self.api_key = os.getenv("FINANCIAL_DATASETS_API_KEY")
        if not self.api_key:
            raise ValueError("FINANCIAL_DATASETS_API_KEY environment variable is required")
        
        self.base_url = "https://api.financialdatasets.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Alternative APIs (optional)
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.fmp_key = os.getenv("FMP_API_KEY")
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """
        Return descriptions of available tools for the planning agent.
        """
        return {
            "financial_data": "Retrieve income statements, balance sheets, and cash flow statements for public companies",
            "company_info": "Get basic company information and profile data",
            "financial_ratios": "Calculate and retrieve financial ratios and metrics",
            "historical_data": "Access historical financial performance data"
        }
    
    def get_financial_data(self, symbol: str, statement_type: str = "all") -> Optional[Dict[str, Any]]:
        """
        Retrieve financial statements for a given company symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            statement_type: 'income', 'balance', 'cash_flow', or 'all'
        """
        try:
            results = {}
            
            # Get different types of financial statements
            if statement_type in ["income", "all"]:
                income_data = self._get_income_statement(symbol)
                if income_data:
                    results["income_statement"] = income_data
            
            if statement_type in ["balance", "all"]:
                balance_data = self._get_balance_sheet(symbol)
                if balance_data:
                    results["balance_sheet"] = balance_data
            
            if statement_type in ["cash_flow", "all"]:
                cash_flow_data = self._get_cash_flow(symbol)
                if cash_flow_data:
                    results["cash_flow"] = cash_flow_data
            
            # Get company profile
            profile_data = self._get_company_profile(symbol)
            if profile_data:
                results["company_profile"] = profile_data
            
            return results if results else None
            
        except Exception as e:
            print(f"Error retrieving financial data for {symbol}: {str(e)}")
            return None
    
    def _get_income_statement(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get income statement data."""
        try:
            url = f"{self.base_url}/financials/income-statement/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Income statement API error {response.status_code}: {response.text}")
                return self._get_fallback_income_data(symbol)
                
        except Exception as e:
            print(f"Income statement request error: {str(e)}")
            return self._get_fallback_income_data(symbol)
    
    def _get_balance_sheet(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get balance sheet data."""
        try:
            url = f"{self.base_url}/financials/balance-sheet/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Balance sheet API error {response.status_code}: {response.text}")
                return self._get_fallback_balance_data(symbol)
                
        except Exception as e:
            print(f"Balance sheet request error: {str(e)}")
            return self._get_fallback_balance_data(symbol)
    
    def _get_cash_flow(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cash flow statement data."""
        try:
            url = f"{self.base_url}/financials/cash-flow/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Cash flow API error {response.status_code}: {response.text}")
                return self._get_fallback_cash_flow_data(symbol)
                
        except Exception as e:
            print(f"Cash flow request error: {str(e)}")
            return self._get_fallback_cash_flow_data(symbol)
    
    def _get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company profile and basic information."""
        try:
            url = f"{self.base_url}/company/profile/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Company profile API error {response.status_code}: {response.text}")
                return self._get_fallback_profile_data(symbol)
                
        except Exception as e:
            print(f"Company profile request error: {str(e)}")
            return self._get_fallback_profile_data(symbol)
    
    def calculate_financial_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate common financial ratios from financial statement data.
        """
        ratios = {}
        
        try:
            # Extract data from financial statements
            income = financial_data.get("income_statement", {})
            balance = financial_data.get("balance_sheet", {})
            
            if income and balance:
                # Get latest period data (assuming it's in the first element)
                latest_income = income[0] if isinstance(income, list) and income else income
                latest_balance = balance[0] if isinstance(balance, list) and balance else balance
                
                # Revenue and profitability ratios
                revenue = latest_income.get("revenue", 0)
                net_income = latest_income.get("netIncome", 0)
                total_assets = latest_balance.get("totalAssets", 0)
                total_equity = latest_balance.get("totalEquity", 0)
                total_debt = latest_balance.get("totalDebt", 0)
                
                if revenue > 0:
                    ratios["profit_margin"] = (net_income / revenue) * 100
                
                if total_assets > 0:
                    ratios["roa"] = (net_income / total_assets) * 100  # Return on Assets
                
                if total_equity > 0:
                    ratios["roe"] = (net_income / total_equity) * 100  # Return on Equity
                    ratios["debt_to_equity"] = total_debt / total_equity
                
        except Exception as e:
            print(f"Error calculating ratios: {str(e)}")
        
        return ratios
    
    def _get_fallback_income_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback method using alternative data providers."""
        # Try Alpha Vantage first
        if self.alpha_vantage_key:
            try:
                url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={self.alpha_vantage_key}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if "annualReports" in data and data["annualReports"]:
                        return {
                            "source": "Alpha Vantage",
                            "data": data["annualReports"][:4],
                            "symbol": symbol
                        }
            except Exception as e:
                print(f"Alpha Vantage fallback failed: {str(e)}")
        
        # Try FMP as second fallback
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?apikey={self.fmp_key}&limit=4"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return {
                            "source": "Financial Modeling Prep",
                            "data": data,
                            "symbol": symbol
                        }
            except Exception as e:
                print(f"FMP fallback failed: {str(e)}")
        
        # If all fallbacks fail, return error
        return {
            "symbol": symbol,
            "statement_type": "income_statement",
            "error": "Unable to retrieve income statement data from any source",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_fallback_balance_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback method using alternative data providers."""
        # Try Alpha Vantage first
        if self.alpha_vantage_key:
            try:
                url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={self.alpha_vantage_key}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if "annualReports" in data and data["annualReports"]:
                        return {
                            "source": "Alpha Vantage",
                            "data": data["annualReports"][:4],
                            "symbol": symbol
                        }
            except Exception as e:
                print(f"Alpha Vantage balance sheet fallback failed: {str(e)}")
        
        # Try FMP as second fallback
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{symbol}?apikey={self.fmp_key}&limit=4"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return {
                            "source": "Financial Modeling Prep",
                            "data": data,
                            "symbol": symbol
                        }
            except Exception as e:
                print(f"FMP balance sheet fallback failed: {str(e)}")
        
        return {
            "symbol": symbol,
            "statement_type": "balance_sheet",
            "error": "Unable to retrieve balance sheet data from any source",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_fallback_cash_flow_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback method using alternative data providers."""
        # Try Alpha Vantage first
        if self.alpha_vantage_key:
            try:
                url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey={self.alpha_vantage_key}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if "annualReports" in data and data["annualReports"]:
                        return {
                            "source": "Alpha Vantage",
                            "data": data["annualReports"][:4],
                            "symbol": symbol
                        }
            except Exception as e:
                print(f"Alpha Vantage cash flow fallback failed: {str(e)}")
        
        # Try FMP as second fallback
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{symbol}?apikey={self.fmp_key}&limit=4"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return {
                            "source": "Financial Modeling Prep",
                            "data": data,
                            "symbol": symbol
                        }
            except Exception as e:
                print(f"FMP cash flow fallback failed: {str(e)}")
        
        return {
            "symbol": symbol,
            "statement_type": "cash_flow",
            "error": "Unable to retrieve cash flow data from any source",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_fallback_profile_data(self, symbol: str) -> Dict[str, Any]:
        """Fallback method using alternative data providers."""
        # Try Alpha Vantage first
        if self.alpha_vantage_key:
            try:
                url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.alpha_vantage_key}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if "Symbol" in data:
                        return {
                            "source": "Alpha Vantage",
                            "symbol": data.get("Symbol"),
                            "name": data.get("Name"),
                            "exchange": data.get("Exchange"),
                            "sector": data.get("Sector"),
                            "industry": data.get("Industry"),
                            "description": data.get("Description")
                        }
            except Exception as e:
                print(f"Alpha Vantage profile fallback failed: {str(e)}")
        
        # Try FMP as second fallback
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={self.fmp_key}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        profile = data[0]
                        return {
                            "source": "Financial Modeling Prep",
                            "symbol": profile.get("symbol"),
                            "name": profile.get("companyName"),
                            "exchange": profile.get("exchangeShortName"),
                            "sector": profile.get("sector"),
                            "industry": profile.get("industry"),
                            "description": profile.get("description"),
                            "website": profile.get("website")
                        }
            except Exception as e:
                print(f"FMP profile fallback failed: {str(e)}")
        
        return {
            "symbol": symbol,
            "company_name": f"Company with symbol {symbol}",
            "error": "Unable to retrieve company profile data from any source",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_multiple_companies_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve financial data for multiple companies for comparison.
        """
        results = {}
        
        for symbol in symbols:
            company_data = self.get_financial_data(symbol)
            if company_data:
                results[symbol] = company_data
        
        return results

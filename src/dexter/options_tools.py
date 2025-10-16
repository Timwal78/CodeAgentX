import yfinance as yf
import numpy as np
from scipy.stats import norm
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd


class OptionsDataTools:
    """
    Tools for retrieving options data using yfinance (free).
    Includes Greeks calculation using Black-Scholes model.
    """
    
    def __init__(self):
        self.risk_free_rate = 0.045  # Default 4.5% risk-free rate (can be updated)
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Return descriptions of available options tools."""
        return {
            "options_chain": "Get full options chain with strike prices, expiration dates, open interest, volume, and implied volatility",
            "options_greeks": "Calculate option Greeks (delta, gamma, theta, vega, rho) for any option",
            "unusual_options": "Identify unusual options activity based on volume/OI ratios",
            "put_call_ratio": "Calculate put/call ratio for volume and open interest analysis"
        }
    
    def get_options_chain(
        self, 
        symbol: str, 
        expiration: Optional[str] = None,
        option_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get options chain data for a symbol.
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            expiration: Specific expiration date (YYYY-MM-DD) or None for all
            option_type: 'calls', 'puts', or None for both
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get available expiration dates
            expiration_dates = ticker.options
            
            if not expiration_dates:
                return {
                    "error": f"No options data available for {symbol}",
                    "symbol": symbol
                }
            
            # If specific expiration requested
            if expiration:
                if expiration not in expiration_dates:
                    return {
                        "error": f"Expiration {expiration} not available",
                        "available_expirations": list(expiration_dates),
                        "symbol": symbol
                    }
                chains_to_fetch = [expiration]
            else:
                # Get next 3 expirations
                chains_to_fetch = expiration_dates[:3]
            
            # Fetch option chains
            all_data = {
                "symbol": symbol,
                "current_price": self._get_current_price(ticker),
                "expirations": []
            }
            
            for exp_date in chains_to_fetch:
                chain = ticker.option_chain(exp_date)
                
                exp_data = {
                    "expiration": exp_date,
                    "days_to_expiration": self._days_to_expiration(exp_date)
                }
                
                if option_type != 'puts':
                    calls_df = chain.calls
                    exp_data["calls"] = self._process_options_data(calls_df, "call")
                
                if option_type != 'calls':
                    puts_df = chain.puts
                    exp_data["puts"] = self._process_options_data(puts_df, "put")
                
                all_data["expirations"].append(exp_data)
            
            return all_data
            
        except Exception as e:
            return {
                "error": f"Failed to retrieve options data: {str(e)}",
                "symbol": symbol
            }
    
    def calculate_greeks(
        self,
        symbol: str,
        strike: float,
        expiration: str,
        option_type: str = "call"
    ) -> Dict[str, Any]:
        """
        Calculate Greeks for a specific option.
        
        Args:
            symbol: Stock ticker
            strike: Strike price
            expiration: Expiration date (YYYY-MM-DD)
            option_type: 'call' or 'put'
        """
        try:
            ticker = yf.Ticker(symbol)
            current_price = self._get_current_price(ticker)
            
            # Get option data
            chain = ticker.option_chain(expiration)
            options_df = chain.calls if option_type.lower() == "call" else chain.puts
            
            # Find the specific option
            option_row = options_df[options_df['strike'] == strike]
            
            if option_row.empty:
                return {
                    "error": f"Option with strike {strike} not found",
                    "symbol": symbol
                }
            
            option_data = option_row.iloc[0]
            
            # Calculate time to expiration
            T = self._days_to_expiration(expiration) / 365.0
            
            # Get implied volatility
            iv = option_data.get('impliedVolatility', 0.3)
            
            # Calculate Greeks
            greeks = self._black_scholes_greeks(
                S=current_price,
                K=strike,
                T=T,
                r=self.risk_free_rate,
                sigma=iv,
                option_type=option_type.lower()
            )
            
            return {
                "symbol": symbol,
                "strike": strike,
                "expiration": expiration,
                "option_type": option_type,
                "current_price": current_price,
                "last_price": float(option_data.get('lastPrice', 0)),
                "bid": float(option_data.get('bid', 0)),
                "ask": float(option_data.get('ask', 0)),
                "volume": int(option_data.get('volume', 0)),
                "open_interest": int(option_data.get('openInterest', 0)),
                "implied_volatility": float(iv),
                "greeks": greeks
            }
            
        except Exception as e:
            return {
                "error": f"Failed to calculate Greeks: {str(e)}",
                "symbol": symbol
            }
    
    def identify_unusual_activity(
        self,
        symbol: str,
        min_volume_oi_ratio: float = 2.0,
        min_volume: int = 500
    ) -> Dict[str, Any]:
        """
        Identify unusual options activity based on volume/OI ratios.
        
        Args:
            symbol: Stock ticker
            min_volume_oi_ratio: Minimum volume/OI ratio to flag as unusual
            min_volume: Minimum volume threshold
        """
        try:
            ticker = yf.Ticker(symbol)
            expiration_dates = ticker.options[:3]  # Check next 3 expirations
            
            unusual_calls = []
            unusual_puts = []
            
            for exp_date in expiration_dates:
                chain = ticker.option_chain(exp_date)
                
                # Check calls
                calls = chain.calls
                unusual_call_rows = calls[
                    (calls['volume'] >= min_volume) & 
                    (calls['openInterest'] > 0) &
                    ((calls['volume'] / calls['openInterest']) >= min_volume_oi_ratio)
                ]
                
                for _, row in unusual_call_rows.iterrows():
                    unusual_calls.append({
                        "strike": float(row['strike']),
                        "expiration": exp_date,
                        "volume": int(row['volume']),
                        "open_interest": int(row['openInterest']),
                        "volume_oi_ratio": float(row['volume'] / row['openInterest']),
                        "last_price": float(row['lastPrice']),
                        "implied_volatility": float(row.get('impliedVolatility', 0))
                    })
                
                # Check puts
                puts = chain.puts
                unusual_put_rows = puts[
                    (puts['volume'] >= min_volume) & 
                    (puts['openInterest'] > 0) &
                    ((puts['volume'] / puts['openInterest']) >= min_volume_oi_ratio)
                ]
                
                for _, row in unusual_put_rows.iterrows():
                    unusual_puts.append({
                        "strike": float(row['strike']),
                        "expiration": exp_date,
                        "volume": int(row['volume']),
                        "open_interest": int(row['openInterest']),
                        "volume_oi_ratio": float(row['volume'] / row['openInterest']),
                        "last_price": float(row['lastPrice']),
                        "implied_volatility": float(row.get('impliedVolatility', 0))
                    })
            
            return {
                "symbol": symbol,
                "unusual_calls": sorted(unusual_calls, key=lambda x: x['volume_oi_ratio'], reverse=True),
                "unusual_puts": sorted(unusual_puts, key=lambda x: x['volume_oi_ratio'], reverse=True),
                "total_unusual": len(unusual_calls) + len(unusual_puts)
            }
            
        except Exception as e:
            return {
                "error": f"Failed to identify unusual activity: {str(e)}",
                "symbol": symbol
            }
    
    def calculate_put_call_ratio(self, symbol: str) -> Dict[str, Any]:
        """Calculate put/call ratio for volume and open interest."""
        try:
            ticker = yf.Ticker(symbol)
            expiration_dates = ticker.options[:3]
            
            total_call_volume = 0
            total_put_volume = 0
            total_call_oi = 0
            total_put_oi = 0
            
            for exp_date in expiration_dates:
                chain = ticker.option_chain(exp_date)
                
                total_call_volume += chain.calls['volume'].sum()
                total_put_volume += chain.puts['volume'].sum()
                total_call_oi += chain.calls['openInterest'].sum()
                total_put_oi += chain.puts['openInterest'].sum()
            
            volume_pcr = total_put_volume / total_call_volume if total_call_volume > 0 else 0
            oi_pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            return {
                "symbol": symbol,
                "put_call_volume_ratio": float(volume_pcr),
                "put_call_oi_ratio": float(oi_pcr),
                "total_call_volume": int(total_call_volume),
                "total_put_volume": int(total_put_volume),
                "total_call_oi": int(total_call_oi),
                "total_put_oi": int(total_put_oi),
                "interpretation": self._interpret_pcr(volume_pcr, oi_pcr)
            }
            
        except Exception as e:
            return {
                "error": f"Failed to calculate P/C ratio: {str(e)}",
                "symbol": symbol
            }
    
    def _get_current_price(self, ticker) -> float:
        """Get current stock price."""
        try:
            hist = ticker.history(period='1d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            return 0.0
        except:
            return 0.0
    
    def _days_to_expiration(self, expiration: str) -> int:
        """Calculate days to expiration."""
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        return (exp_date - datetime.now()).days
    
    def _process_options_data(self, df: pd.DataFrame, option_type: str) -> List[Dict]:
        """Process options DataFrame into list of dicts."""
        result = []
        for _, row in df.iterrows():
            result.append({
                "strike": float(row['strike']),
                "last_price": float(row.get('lastPrice', 0)),
                "bid": float(row.get('bid', 0)),
                "ask": float(row.get('ask', 0)),
                "volume": int(row.get('volume', 0)),
                "open_interest": int(row.get('openInterest', 0)),
                "implied_volatility": float(row.get('impliedVolatility', 0))
            })
        return result
    
    def _black_scholes_greeks(
        self, 
        S: float, 
        K: float, 
        T: float, 
        r: float, 
        sigma: float, 
        option_type: str = 'call'
    ) -> Dict[str, float]:
        """Calculate option Greeks using Black-Scholes model."""
        
        if T <= 0 or sigma <= 0:
            return {
                "delta": 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0
            }
        
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Delta
        if option_type == 'call':
            delta = norm.cdf(d1)
        else:
            delta = -norm.cdf(-d1)
        
        # Gamma (same for calls and puts)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Theta
        if option_type == 'call':
            theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                    - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        else:
            theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) 
                    + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
        
        # Vega (same for calls and puts)
        vega = (S * norm.pdf(d1) * np.sqrt(T)) / 100
        
        # Rho
        if option_type == 'call':
            rho = (K * T * np.exp(-r * T) * norm.cdf(d2)) / 100
        else:
            rho = (-K * T * np.exp(-r * T) * norm.cdf(-d2)) / 100
        
        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "theta": float(theta),
            "vega": float(vega),
            "rho": float(rho)
        }
    
    def _interpret_pcr(self, volume_pcr: float, oi_pcr: float) -> str:
        """Interpret put/call ratio values."""
        if volume_pcr > 1.5:
            return "Bearish sentiment (high put volume relative to calls)"
        elif volume_pcr < 0.7:
            return "Bullish sentiment (high call volume relative to puts)"
        else:
            return "Neutral sentiment (balanced put/call activity)"

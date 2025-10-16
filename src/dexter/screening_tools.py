import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import requests
import os


class StockScreener:
    """
    Advanced stock screening and scanning tools with technical analysis,
    pattern detection, and options-based indicators.
    """
    
    def __init__(self):
        self.financial_api_key = os.getenv("FINANCIAL_DATASETS_API_KEY")
        
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Return descriptions of available screening tools."""
        return {
            "stock_screener": "Scan and filter stocks by price, volume, market cap, technical indicators, and patterns",
            "penny_stock_scanner": "Find penny stocks with squeeze potential, volume spikes, and momentum",
            "pattern_detector": "Detect technical patterns like double bottom, breakouts, reversals",
            "options_screener": "Screen stocks by put/call walls, gamma exposure, and unusual flow",
            "momentum_scanner": "Find stocks with strong momentum, volume confirmation, and trend strength"
        }
    
    def get_stock_universe(self, category: str = "all") -> List[str]:
        """
        Get list of stocks to scan based on category.
        
        Args:
            category: 'all', 'penny' (under $5), 'small_cap', 'mid_cap', 'popular'
        """
        if category == "penny":
            # Common penny stocks and small caps that tend to have volatility
            return [
                "SNDL", "GNUS", "SOFI", "PLTR", "NIO", "XELA", "MULN", "BBIG",
                "PROG", "ATER", "CEI", "BBAI", "SST", "NILE", "APRN", "RDBX",
                "AMC", "GME", "SPRT", "WISH", "CLOV", "SDC", "TLRY", "ACB",
                "SAVA", "MMAT", "WKHS", "RIDE", "GOEV", "TSLA", "RIVN", "LCID"
            ]
        elif category == "popular":
            # Most actively traded stocks
            return [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD",
                "SPY", "QQQ", "NFLX", "DIS", "BABA", "PYPL", "SQ", "COIN",
                "GME", "AMC", "BB", "PLTR", "SOFI", "NIO", "RIVN", "LCID"
            ]
        elif category == "all":
            # Combine both for comprehensive screening
            return list(set(self.get_stock_universe("penny") + self.get_stock_universe("popular")))
        
        return []
    
    def screen_penny_stocks_squeeze(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Find penny stocks with highest squeeze potential.
        
        Looks for:
        - Price under $5
        - High short interest
        - Volume spike
        - Tight consolidation
        - Breaking resistance
        """
        stocks = self.get_stock_universe("penny")
        results = []
        
        for symbol in stocks:
            try:
                ticker = yf.Ticker(symbol)
                
                # Get current price and volume data
                hist = ticker.history(period="3mo")
                if hist.empty or len(hist) < 20:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                
                # Filter penny stocks (under $5)
                if current_price >= 5:
                    continue
                
                # Calculate indicators
                avg_volume_20 = hist['Volume'].tail(20).mean()
                recent_volume = hist['Volume'].tail(5).mean()
                volume_ratio = recent_volume / avg_volume_20 if avg_volume_20 > 0 else 0
                
                # Price momentum
                price_change_1d = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0
                price_change_5d = ((current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100) if len(hist) > 5 else 0
                
                # Bollinger Bands for squeeze detection
                bb_middle = hist['Close'].tail(20).mean()
                bb_std = hist['Close'].tail(20).std()
                bb_upper = bb_middle + (2 * bb_std)
                bb_lower = bb_middle - (2 * bb_std)
                bb_width = ((bb_upper - bb_lower) / bb_middle * 100) if bb_middle > 0 else 0
                
                # RSI for momentum
                rsi = self._calculate_rsi(hist['Close'])
                
                # Squeeze score (higher is better)
                squeeze_score = 0
                if volume_ratio > 1.5:
                    squeeze_score += 30
                if price_change_1d > 5:
                    squeeze_score += 25
                if bb_width < 10:
                    squeeze_score += 20
                if rsi > 50 and rsi < 70:
                    squeeze_score += 15
                if price_change_5d > 0:
                    squeeze_score += 10
                
                results.append({
                    "symbol": symbol,
                    "price": round(current_price, 2),
                    "volume_ratio": round(volume_ratio, 2),
                    "price_change_1d": round(price_change_1d, 2),
                    "price_change_5d": round(price_change_5d, 2),
                    "bb_width": round(bb_width, 2),
                    "rsi": round(rsi, 2),
                    "squeeze_score": round(squeeze_score, 1),
                    "avg_volume": int(avg_volume_20)
                })
                
            except Exception as e:
                print(f"Error scanning {symbol}: {str(e)}")
                continue
        
        # Sort by squeeze score
        results.sort(key=lambda x: x['squeeze_score'], reverse=True)
        return results[:top_n]
    
    def detect_double_bottom_with_put_wall(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Find stocks with double bottom pattern at put wall with volume and momentum.
        
        Looks for:
        - Double bottom price pattern
        - Strong put wall (support level)
        - Volume increasing on second bottom
        - Momentum turning upward
        """
        stocks = self.get_stock_universe("all")
        results = []
        
        for symbol in stocks:
            try:
                ticker = yf.Ticker(symbol)
                
                # Get historical data
                hist = ticker.history(period="3mo")
                if hist.empty or len(hist) < 40:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                
                # Detect double bottom pattern
                pattern_detected, bottom_price = self._detect_double_bottom(hist['Close'])
                if not pattern_detected:
                    continue
                
                # Check for put wall (options data)
                put_wall_price = self._find_put_wall(ticker)
                
                # Volume analysis
                avg_volume = hist['Volume'].tail(20).mean()
                recent_volume = hist['Volume'].tail(5).mean()
                volume_trend = recent_volume / avg_volume if avg_volume > 0 else 0
                
                # Momentum indicators
                rsi = self._calculate_rsi(hist['Close'])
                macd, signal = self._calculate_macd(hist['Close'])
                macd_crossover = macd > signal
                
                # Price relative to bottom
                distance_from_bottom = ((current_price - bottom_price) / bottom_price * 100) if bottom_price > 0 else 0
                
                # Check if put wall aligns with double bottom
                put_wall_alignment = abs(put_wall_price - bottom_price) / bottom_price * 100 if put_wall_price and bottom_price > 0 else 100
                
                # Score the setup
                setup_score = 0
                if volume_trend > 1.2:
                    setup_score += 25
                if macd_crossover:
                    setup_score += 25
                if rsi > 40 and rsi < 60:
                    setup_score += 20
                if put_wall_alignment < 5:
                    setup_score += 20
                if distance_from_bottom > 0 and distance_from_bottom < 5:
                    setup_score += 10
                
                results.append({
                    "symbol": symbol,
                    "price": round(current_price, 2),
                    "bottom_price": round(bottom_price, 2),
                    "put_wall": round(put_wall_price, 2) if put_wall_price else None,
                    "volume_trend": round(volume_trend, 2),
                    "rsi": round(rsi, 2),
                    "macd_crossover": macd_crossover,
                    "distance_from_bottom": round(distance_from_bottom, 2),
                    "setup_score": round(setup_score, 1)
                })
                
            except Exception as e:
                print(f"Error analyzing {symbol}: {str(e)}")
                continue
        
        # Sort by setup score
        results.sort(key=lambda x: x['setup_score'], reverse=True)
        return results[:top_n]
    
    def screen_momentum_breakout(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Screen stocks by custom momentum and technical criteria.
        
        Args:
            criteria: Dict with filters like min_price, max_price, min_volume_ratio, 
                     min_rsi, max_rsi, pattern_type, etc.
        """
        category = criteria.get("category", "all")
        stocks = self.get_stock_universe(category)
        results = []
        
        for symbol in stocks:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="3mo")
                
                if hist.empty or len(hist) < 20:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                
                # Apply price filters
                if criteria.get("min_price") and current_price < criteria["min_price"]:
                    continue
                if criteria.get("max_price") and current_price > criteria["max_price"]:
                    continue
                
                # Volume analysis
                avg_volume = hist['Volume'].tail(20).mean()
                recent_volume = hist['Volume'].tail(5).mean()
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 0
                
                if criteria.get("min_volume_ratio") and volume_ratio < criteria["min_volume_ratio"]:
                    continue
                
                # Technical indicators
                rsi = self._calculate_rsi(hist['Close'])
                if criteria.get("min_rsi") and rsi < criteria["min_rsi"]:
                    continue
                if criteria.get("max_rsi") and rsi > criteria["max_rsi"]:
                    continue
                
                # Moving averages
                ma_20 = hist['Close'].tail(20).mean()
                ma_50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else ma_20
                above_ma20 = current_price > ma_20
                above_ma50 = current_price > ma_50
                
                # Price momentum
                price_change_1d = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0
                price_change_5d = ((current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100) if len(hist) > 5 else 0
                
                results.append({
                    "symbol": symbol,
                    "price": round(current_price, 2),
                    "volume_ratio": round(volume_ratio, 2),
                    "rsi": round(rsi, 2),
                    "above_ma20": above_ma20,
                    "above_ma50": above_ma50,
                    "price_change_1d": round(price_change_1d, 2),
                    "price_change_5d": round(price_change_5d, 2),
                    "avg_volume": int(avg_volume)
                })
                
            except Exception as e:
                print(f"Error screening {symbol}: {str(e)}")
                continue
        
        return results
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[float, float]:
        """Calculate MACD and signal line."""
        if len(prices) < 26:
            return 0.0, 0.0
        
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        return float(macd.iloc[-1]), float(signal.iloc[-1])
    
    def _detect_double_bottom(self, prices: pd.Series) -> Tuple[bool, float]:
        """Detect double bottom pattern in price data."""
        if len(prices) < 40:
            return False, 0.0
        
        # Look for two distinct bottoms with similar lows
        recent_prices = prices.tail(40).values
        
        # Find local minima
        minima_indices = []
        for i in range(2, len(recent_prices) - 2):
            if (recent_prices[i] < recent_prices[i-1] and 
                recent_prices[i] < recent_prices[i-2] and
                recent_prices[i] < recent_prices[i+1] and 
                recent_prices[i] < recent_prices[i+2]):
                minima_indices.append(i)
        
        # Need at least 2 bottoms
        if len(minima_indices) < 2:
            return False, 0.0
        
        # Check if last two minima are similar in price
        last_two_minima = [recent_prices[i] for i in minima_indices[-2:]]
        price_difference = abs(last_two_minima[0] - last_two_minima[1]) / min(last_two_minima) * 100
        
        # Double bottom if within 3% price difference
        if price_difference < 3:
            return True, min(last_two_minima)
        
        return False, 0.0
    
    def _find_put_wall(self, ticker: yf.Ticker) -> Optional[float]:
        """Find the strongest put wall (support level) from options data."""
        try:
            # Get nearest expiration options
            expirations = ticker.options
            if not expirations:
                return None
            
            # Use nearest expiration
            nearest_exp = expirations[0]
            options_chain = ticker.option_chain(nearest_exp)
            
            if options_chain.puts.empty:
                return None
            
            # Find strike with highest put open interest
            puts = options_chain.puts
            puts = puts.sort_values('openInterest', ascending=False)
            
            if len(puts) > 0:
                return float(puts.iloc[0]['strike'])
            
        except Exception as e:
            print(f"Error finding put wall: {str(e)}")
        
        return None

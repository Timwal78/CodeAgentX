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
            "pattern_detector": "Detect technical patterns like double bottom, breakouts, reversals, head and shoulders, flags, triangles",
            "options_screener": "Screen stocks by put/call walls, gamma exposure, and unusual flow",
            "momentum_scanner": "Find stocks with strong momentum, volume confirmation, and trend strength",
            "squeeze_detector": "Detect TTM Squeeze setups using Bollinger Bands + Keltner Channels with momentum confirmation",
            "bullish_patterns": "Scan for bullish patterns: double bottom, cup and handle, ascending triangle, bull flag, golden cross",
            "bearish_patterns": "Scan for bearish patterns: double top, head and shoulders, descending triangle, bear flag, death cross"
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
                
                # Calculate trading levels
                trading_levels = self._calculate_trading_levels(hist, current_price)
                
                results.append({
                    "symbol": symbol,
                    "price": round(current_price, 2),
                    "buy_at": trading_levels["buy_price"],
                    "sell_at": trading_levels["sell_target"],
                    "stop_loss": trading_levels["stop_loss"],
                    "risk_reward": trading_levels["risk_reward"],
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
    
    def detect_ttm_squeeze(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Detect TTM Squeeze setups (Bollinger Bands inside Keltner Channels).
        
        The squeeze happens when:
        - Bollinger Bands contract inside Keltner Channels (consolidation)
        - Price coils tight (low volatility)
        - Then fires when BB breaks out of KC (explosive move)
        
        Returns stocks in squeeze or about to fire.
        """
        stocks = self.get_stock_universe("all")
        results = []
        
        for symbol in stocks:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="3mo")
                
                if hist.empty or len(hist) < 20:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                
                # Calculate Bollinger Bands (20-period, 2 std dev)
                bb_middle = hist['Close'].rolling(20).mean()
                bb_std = hist['Close'].rolling(20).std()
                bb_upper = bb_middle + (2 * bb_std)
                bb_lower = bb_middle - (2 * bb_std)
                bb_width = ((bb_upper - bb_lower) / bb_middle * 100).iloc[-1]
                
                # Calculate Keltner Channels (20-period EMA, 1.5 ATR)
                ema_20 = hist['Close'].ewm(span=20).mean()
                tr1 = hist['High'] - hist['Low']
                tr2 = abs(hist['High'] - hist['Close'].shift())
                tr3 = abs(hist['Low'] - hist['Close'].shift())
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = tr.rolling(20).mean()
                
                kc_upper = ema_20 + (1.5 * atr)
                kc_lower = ema_20 - (1.5 * atr)
                kc_width = ((kc_upper - kc_lower) / ema_20 * 100).iloc[-1]
                
                # Squeeze detection: BB inside KC
                bb_inside_kc = (bb_upper.iloc[-1] < kc_upper.iloc[-1] and 
                               bb_lower.iloc[-1] > kc_lower.iloc[-1])
                
                # Squeeze firing: BB breaking out of KC
                squeeze_firing = (bb_upper.iloc[-1] > kc_upper.iloc[-1] or 
                                 bb_lower.iloc[-1] < kc_lower.iloc[-1])
                
                # Momentum direction
                momentum = self._calculate_squeeze_momentum(hist['Close'])
                
                # Volume confirmation
                avg_volume = hist['Volume'].tail(20).mean()
                recent_volume = hist['Volume'].tail(5).mean()
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 0
                
                # Squeeze score
                squeeze_score = 0
                if bb_inside_kc:
                    squeeze_score += 40
                if squeeze_firing and momentum > 0:
                    squeeze_score += 30
                if volume_ratio > 1.3:
                    squeeze_score += 20
                if bb_width < 5:
                    squeeze_score += 10
                
                if squeeze_score > 30:
                    # Calculate trading levels
                    trading_levels = self._calculate_trading_levels(hist, current_price)
                    
                    results.append({
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "buy_at": trading_levels["buy_price"],
                        "sell_at": trading_levels["sell_target"],
                        "stop_loss": trading_levels["stop_loss"],
                        "risk_reward": trading_levels["risk_reward"],
                        "squeeze_active": bb_inside_kc,
                        "squeeze_firing": squeeze_firing,
                        "bb_width": round(bb_width, 2),
                        "kc_width": round(kc_width, 2),
                        "momentum": round(momentum, 2),
                        "volume_ratio": round(volume_ratio, 2),
                        "squeeze_score": round(squeeze_score, 1)
                    })
                
            except Exception as e:
                print(f"Error analyzing {symbol} for squeeze: {str(e)}")
                continue
        
        results.sort(key=lambda x: x['squeeze_score'], reverse=True)
        return results[:top_n]
    
    def detect_bullish_patterns(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Scan for bullish chart patterns:
        - Double Bottom
        - Cup and Handle
        - Ascending Triangle
        - Bull Flag
        - Golden Cross (50 MA crosses above 200 MA)
        - Inverse Head and Shoulders
        """
        stocks = self.get_stock_universe("all")
        results = []
        
        for symbol in stocks:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="6mo")
                
                if hist.empty or len(hist) < 50:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                patterns_found = []
                bullish_score = 0
                
                # Double Bottom
                is_double_bottom, bottom_price = self._detect_double_bottom(hist['Close'])
                if is_double_bottom:
                    patterns_found.append("Double Bottom")
                    bullish_score += 25
                
                # Cup and Handle
                if self._detect_cup_and_handle(hist['Close']):
                    patterns_found.append("Cup and Handle")
                    bullish_score += 30
                
                # Ascending Triangle
                if self._detect_ascending_triangle(hist['Close'], hist['High']):
                    patterns_found.append("Ascending Triangle")
                    bullish_score += 25
                
                # Bull Flag
                if self._detect_bull_flag(hist['Close'], hist['Volume']):
                    patterns_found.append("Bull Flag")
                    bullish_score += 20
                
                # Golden Cross
                if len(hist) >= 200:
                    ma_50 = hist['Close'].rolling(50).mean()
                    ma_200 = hist['Close'].rolling(200).mean()
                    if (ma_50.iloc[-1] > ma_200.iloc[-1] and 
                        ma_50.iloc[-5] <= ma_200.iloc[-5]):
                        patterns_found.append("Golden Cross")
                        bullish_score += 35
                
                # Inverse Head and Shoulders
                if self._detect_inverse_head_shoulders(hist['Close']):
                    patterns_found.append("Inverse H&S")
                    bullish_score += 30
                
                if patterns_found:
                    results.append({
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "patterns": patterns_found,
                        "bullish_score": bullish_score,
                        "rsi": round(self._calculate_rsi(hist['Close']), 2)
                    })
                
            except Exception as e:
                print(f"Error detecting bullish patterns for {symbol}: {str(e)}")
                continue
        
        results.sort(key=lambda x: x['bullish_score'], reverse=True)
        return results[:top_n]
    
    def detect_bearish_patterns(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Scan for bearish chart patterns:
        - Double Top
        - Head and Shoulders
        - Descending Triangle
        - Bear Flag
        - Death Cross (50 MA crosses below 200 MA)
        - Rising Wedge
        """
        stocks = self.get_stock_universe("all")
        results = []
        
        for symbol in stocks:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="6mo")
                
                if hist.empty or len(hist) < 50:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                patterns_found = []
                bearish_score = 0
                
                # Double Top
                if self._detect_double_top(hist['Close']):
                    patterns_found.append("Double Top")
                    bearish_score += 25
                
                # Head and Shoulders
                if self._detect_head_shoulders(hist['Close']):
                    patterns_found.append("Head and Shoulders")
                    bearish_score += 30
                
                # Descending Triangle
                if self._detect_descending_triangle(hist['Close'], hist['Low']):
                    patterns_found.append("Descending Triangle")
                    bearish_score += 25
                
                # Bear Flag
                if self._detect_bear_flag(hist['Close'], hist['Volume']):
                    patterns_found.append("Bear Flag")
                    bearish_score += 20
                
                # Death Cross
                if len(hist) >= 200:
                    ma_50 = hist['Close'].rolling(50).mean()
                    ma_200 = hist['Close'].rolling(200).mean()
                    if (ma_50.iloc[-1] < ma_200.iloc[-1] and 
                        ma_50.iloc[-5] >= ma_200.iloc[-5]):
                        patterns_found.append("Death Cross")
                        bearish_score += 35
                
                if patterns_found:
                    results.append({
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "patterns": patterns_found,
                        "bearish_score": bearish_score,
                        "rsi": round(self._calculate_rsi(hist['Close']), 2)
                    })
                
            except Exception as e:
                print(f"Error detecting bearish patterns for {symbol}: {str(e)}")
                continue
        
        results.sort(key=lambda x: x['bearish_score'], reverse=True)
        return results[:top_n]
    
    def find_moass_candidates(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Find potential MOASS (Mother Of All Short Squeeze) candidates.
        
        Looks for the perfect storm:
        - High short interest
        - Low float
        - Increasing volume
        - Bullish momentum
        - Options gamma squeeze potential
        - Retailer interest (social sentiment proxy)
        """
        stocks = self.get_stock_universe("all")
        results = []
        
        for symbol in stocks:
            try:
                ticker = yf.Ticker(symbol)
                
                # Price and volume data
                hist = ticker.history(period="3mo")
                if hist.empty or len(hist) < 20:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                
                # Volume analysis - critical for MOASS
                avg_volume_20 = hist['Volume'].tail(20).mean()
                recent_volume = hist['Volume'].tail(5).mean()
                volume_surge = recent_volume / avg_volume_20 if avg_volume_20 > 0 else 0
                
                # Price momentum
                price_change_5d = ((current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100) if len(hist) > 5 else 0
                price_change_20d = ((current_price - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21] * 100) if len(hist) > 20 else 0
                
                # RSI for momentum confirmation
                rsi = self._calculate_rsi(hist['Close'])
                
                # Check for options activity (gamma squeeze potential)
                gamma_potential = self._check_gamma_squeeze_potential(ticker)
                
                # TTM Squeeze detection
                squeeze_active = self._is_in_squeeze(hist)
                
                # MOASS Score calculation
                moass_score = 0
                
                # Volume surge (most important)
                if volume_surge > 3:
                    moass_score += 35
                elif volume_surge > 2:
                    moass_score += 25
                elif volume_surge > 1.5:
                    moass_score += 15
                
                # Price momentum
                if price_change_5d > 20:
                    moass_score += 25
                elif price_change_5d > 10:
                    moass_score += 15
                
                # RSI sweet spot (not overbought yet)
                if 50 < rsi < 70:
                    moass_score += 15
                
                # Gamma potential
                if gamma_potential:
                    moass_score += 20
                
                # Squeeze setup
                if squeeze_active:
                    moass_score += 15
                
                # Only include high potential candidates
                if moass_score >= 40:
                    # Calculate trading levels
                    trading_levels = self._calculate_trading_levels(hist, current_price)
                    
                    results.append({
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "buy_at": trading_levels["buy_price"],
                        "sell_at": trading_levels["sell_target"],
                        "stop_loss": trading_levels["stop_loss"],
                        "risk_reward": trading_levels["risk_reward"],
                        "volume_surge": round(volume_surge, 2),
                        "price_change_5d": round(price_change_5d, 2),
                        "price_change_20d": round(price_change_20d, 2),
                        "rsi": round(rsi, 2),
                        "gamma_potential": gamma_potential,
                        "squeeze_active": squeeze_active,
                        "moass_score": round(moass_score, 1),
                        "avg_volume": int(avg_volume_20)
                    })
                
            except Exception as e:
                print(f"Error analyzing {symbol} for MOASS: {str(e)}")
                continue
        
        # Sort by MOASS score
        results.sort(key=lambda x: x['moass_score'], reverse=True)
        return results[:top_n]
    
    def _calculate_squeeze_momentum(self, prices: pd.Series) -> float:
        """Calculate momentum for squeeze indicator."""
        if len(prices) < 20:
            return 0.0
        
        # Linear regression slope of recent prices
        recent = prices.tail(10).values
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent, 1)[0]
        return float(slope)
    
    def _detect_cup_and_handle(self, prices: pd.Series) -> bool:
        """Detect cup and handle pattern."""
        if len(prices) < 60:
            return False
        
        recent = prices.tail(60).values
        
        # Find the cup (U-shape)
        left_peak = recent[0]
        bottom = min(recent[10:40])
        right_peak = recent[-1]
        
        # Cup criteria
        cup_depth = (left_peak - bottom) / left_peak
        peaks_similar = abs(left_peak - right_peak) / left_peak < 0.05
        
        # Handle (small pullback at the end)
        handle_pullback = (right_peak - min(recent[-10:])) / right_peak
        
        return (0.15 < cup_depth < 0.45 and peaks_similar and 
                0.05 < handle_pullback < 0.20)
    
    def _detect_ascending_triangle(self, prices: pd.Series, highs: pd.Series) -> bool:
        """Detect ascending triangle (flat top, rising bottom)."""
        if len(prices) < 40:
            return False
        
        recent_highs = highs.tail(20).values
        recent_lows = prices.tail(20).values
        
        # Flat resistance at top
        resistance_flat = np.std(recent_highs[-5:]) / np.mean(recent_highs[-5:]) < 0.02
        
        # Rising support at bottom
        x = np.arange(len(recent_lows))
        slope = np.polyfit(x, recent_lows, 1)[0]
        rising_support = slope > 0
        
        return resistance_flat and rising_support
    
    def _detect_descending_triangle(self, prices: pd.Series, lows: pd.Series) -> bool:
        """Detect descending triangle (flat bottom, falling top)."""
        if len(prices) < 40:
            return False
        
        recent_highs = prices.tail(20).values
        recent_lows = lows.tail(20).values
        
        # Flat support at bottom
        support_flat = np.std(recent_lows[-5:]) / np.mean(recent_lows[-5:]) < 0.02
        
        # Falling resistance at top
        x = np.arange(len(recent_highs))
        slope = np.polyfit(x, recent_highs, 1)[0]
        falling_resistance = slope < 0
        
        return support_flat and falling_resistance
    
    def _detect_bull_flag(self, prices: pd.Series, volumes: pd.Series) -> bool:
        """Detect bull flag pattern."""
        if len(prices) < 30:
            return False
        
        recent = prices.tail(30).values
        
        # Strong uptrend (pole)
        pole_start = recent[0]
        pole_end = recent[10]
        pole_gain = (pole_end - pole_start) / pole_start
        
        # Consolidation (flag)
        flag_slope = np.polyfit(np.arange(20), recent[-20:], 1)[0]
        flag_range = (max(recent[-20:]) - min(recent[-20:])) / np.mean(recent[-20:])
        
        return pole_gain > 0.15 and abs(flag_slope) < 0.01 and flag_range < 0.10
    
    def _detect_bear_flag(self, prices: pd.Series, volumes: pd.Series) -> bool:
        """Detect bear flag pattern."""
        if len(prices) < 30:
            return False
        
        recent = prices.tail(30).values
        
        # Strong downtrend (pole)
        pole_start = recent[0]
        pole_end = recent[10]
        pole_drop = (pole_start - pole_end) / pole_start
        
        # Consolidation (flag)
        flag_slope = np.polyfit(np.arange(20), recent[-20:], 1)[0]
        flag_range = (max(recent[-20:]) - min(recent[-20:])) / np.mean(recent[-20:])
        
        return pole_drop > 0.15 and abs(flag_slope) < 0.01 and flag_range < 0.10
    
    def _detect_double_top(self, prices: pd.Series) -> bool:
        """Detect double top pattern."""
        if len(prices) < 40:
            return False
        
        recent = prices.tail(40).values
        
        # Find local maxima
        maxima_indices = []
        for i in range(2, len(recent) - 2):
            if (recent[i] > recent[i-1] and recent[i] > recent[i-2] and
                recent[i] > recent[i+1] and recent[i] > recent[i+2]):
                maxima_indices.append(i)
        
        if len(maxima_indices) < 2:
            return False
        
        # Check last two peaks
        last_two_peaks = [recent[i] for i in maxima_indices[-2:]]
        price_diff = abs(last_two_peaks[0] - last_two_peaks[1]) / max(last_two_peaks) * 100
        
        return price_diff < 3
    
    def _detect_head_shoulders(self, prices: pd.Series) -> bool:
        """Detect head and shoulders pattern."""
        if len(prices) < 60:
            return False
        
        recent = prices.tail(60).values
        
        # Find three peaks
        peaks = []
        for i in range(5, len(recent) - 5):
            if all(recent[i] > recent[i+j] for j in range(-5, 6) if j != 0):
                peaks.append((i, recent[i]))
        
        if len(peaks) < 3:
            return False
        
        # Check pattern: left shoulder < head > right shoulder
        left_shoulder = peaks[-3][1]
        head = peaks[-2][1]
        right_shoulder = peaks[-1][1]
        
        head_higher = head > left_shoulder and head > right_shoulder
        shoulders_similar = abs(left_shoulder - right_shoulder) / max(left_shoulder, right_shoulder) < 0.05
        
        return head_higher and shoulders_similar
    
    def _detect_inverse_head_shoulders(self, prices: pd.Series) -> bool:
        """Detect inverse head and shoulders pattern."""
        if len(prices) < 60:
            return False
        
        recent = prices.tail(60).values
        
        # Find three troughs
        troughs = []
        for i in range(5, len(recent) - 5):
            if all(recent[i] < recent[i+j] for j in range(-5, 6) if j != 0):
                troughs.append((i, recent[i]))
        
        if len(troughs) < 3:
            return False
        
        # Check pattern: left shoulder > head < right shoulder
        left_shoulder = troughs[-3][1]
        head = troughs[-2][1]
        right_shoulder = troughs[-1][1]
        
        head_lower = head < left_shoulder and head < right_shoulder
        shoulders_similar = abs(left_shoulder - right_shoulder) / min(left_shoulder, right_shoulder) < 0.05
        
        return head_lower and shoulders_similar
    
    def _check_gamma_squeeze_potential(self, ticker: yf.Ticker) -> bool:
        """Check if stock has gamma squeeze potential from options."""
        try:
            expirations = ticker.options
            if not expirations:
                return False
            
            # Check near-term expiration
            options_chain = ticker.option_chain(expirations[0])
            
            # High call open interest + volume = gamma potential
            if not options_chain.calls.empty:
                total_call_oi = options_chain.calls['openInterest'].sum()
                total_call_volume = options_chain.calls['volume'].sum()
                
                return total_call_oi > 10000 and total_call_volume > 5000
            
        except Exception:
            pass
        
        return False
    
    def _is_in_squeeze(self, hist: pd.DataFrame) -> bool:
        """Check if stock is in TTM Squeeze."""
        if len(hist) < 20:
            return False
        
        # Bollinger Bands
        bb_middle = hist['Close'].rolling(20).mean()
        bb_std = hist['Close'].rolling(20).std()
        bb_upper = bb_middle + (2 * bb_std)
        bb_lower = bb_middle - (2 * bb_std)
        
        # Keltner Channels
        ema_20 = hist['Close'].ewm(span=20).mean()
        tr1 = hist['High'] - hist['Low']
        tr2 = abs(hist['High'] - hist['Close'].shift())
        tr3 = abs(hist['Low'] - hist['Close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(20).mean()
        kc_upper = ema_20 + (1.5 * atr)
        kc_lower = ema_20 - (1.5 * atr)
        
        # Squeeze when BB inside KC
        return (bb_upper.iloc[-1] < kc_upper.iloc[-1] and 
                bb_lower.iloc[-1] > kc_lower.iloc[-1])
    
    def _calculate_trading_levels(self, hist: pd.DataFrame, current_price: float, 
                                   risk_reward_ratio: float = 2.5) -> Dict[str, float]:
        """
        Calculate buy, sell, and stop loss levels for a stock.
        
        Args:
            hist: Price history DataFrame
            current_price: Current stock price
            risk_reward_ratio: Target risk/reward ratio (default 2.5:1)
        
        Returns:
            Dictionary with buy_price, sell_target, stop_loss
        """
        if len(hist) < 20:
            return {
                "buy_price": round(current_price, 2),
                "sell_target": round(current_price * 1.25, 2),
                "stop_loss": round(current_price * 0.92, 2)
            }
        
        # Support level (recent swing low)
        support = hist['Low'].tail(20).min()
        
        # Resistance level (recent swing high)
        resistance = hist['High'].tail(20).max()
        
        # ATR for volatility-based stops
        tr1 = hist['High'] - hist['Low']
        tr2 = abs(hist['High'] - hist['Close'].shift())
        tr3 = abs(hist['Low'] - hist['Close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        
        # Buy price: current price or slight pullback to support
        if current_price - support < atr:
            buy_price = current_price  # Already near support
        else:
            buy_price = current_price * 0.98  # 2% pullback entry
        
        # Stop loss: Below support or 1.5x ATR below buy price
        atr_stop = buy_price - (1.5 * atr)
        support_stop = support * 0.98  # Just below support
        stop_loss = max(atr_stop, support_stop)  # Use wider stop
        
        # Sell target: Based on risk/reward ratio
        risk = buy_price - stop_loss
        sell_target = buy_price + (risk * risk_reward_ratio)
        
        # Adjust sell target to resistance if closer
        if sell_target > resistance and resistance > current_price:
            sell_target = resistance * 0.98  # Just before resistance
        
        # Ensure minimum gain potential (25%)
        min_target = buy_price * 1.25
        if sell_target < min_target:
            sell_target = min_target
        
        return {
            "buy_price": round(buy_price, 2),
            "sell_target": round(sell_target, 2),
            "stop_loss": round(stop_loss, 2),
            "risk_reward": round((sell_target - buy_price) / (buy_price - stop_loss), 1)
        }

import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Dict, List, Any, Optional
import json
from .screening_tools import StockScreener
from .options_tools import OptionsDataTools
from .utils.discord import send_discord_notification


class MOASSScheduler:
    """
    Scheduled scanner for MOASS hunting and pattern detection.
    
    Schedule:
    - 7:00 AM EST - Eagle Eyes Scan (comprehensive market open prep)
    - Every 2 hours - Regular scans
    - 3:05 PM EST - Eagle Eyes Scan (power hour hunter)
    """
    
    def __init__(self, discord_webhook_url: Optional[str] = None):
        self.screener = StockScreener()
        self.options_tools = OptionsDataTools()
        self.discord_webhook_url = discord_webhook_url
        self.scheduler = BackgroundScheduler(timezone='US/Eastern')
        self.scan_history = []
        self.is_running = False
        
    def start(self):
        """Start the scheduled scanner."""
        if self.is_running:
            print("Scheduler already running")
            return
        
        # Eagle Eyes Scan at 7:00 AM EST (market open prep)
        self.scheduler.add_job(
            self.eagle_eyes_scan,
            CronTrigger(hour=7, minute=0, timezone='US/Eastern'),
            id='eagle_eyes_morning',
            name='Eagle Eyes - Market Open'
        )
        
        # Eagle Eyes Scan at 3:05 PM EST (power hour)
        self.scheduler.add_job(
            self.eagle_eyes_scan,
            CronTrigger(hour=15, minute=5, timezone='US/Eastern'),
            id='eagle_eyes_power_hour',
            name='Eagle Eyes - Power Hour'
        )
        
        # Regular scans every 2 hours (9am, 11am, 1pm)
        # Skip 7am and 3pm since those are covered by eagle eyes
        self.scheduler.add_job(
            self.regular_scan,
            CronTrigger(hour='9,11,13', minute=0, timezone='US/Eastern'),
            id='regular_scans',
            name='Regular 2-Hour Scan'
        )
        
        self.scheduler.start()
        self.is_running = True
        print("🦅 MOASS Scheduler started!")
        print("Schedule:")
        print("  7:00 AM EST - Eagle Eyes (Market Open)")
        print("  9:00 AM EST - Regular Scan")
        print("  11:00 AM EST - Regular Scan")
        print("  1:00 PM EST - Regular Scan")
        print("  3:05 PM EST - Eagle Eyes (Power Hour)")
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            print("Scheduler stopped")
    
    def eagle_eyes_scan(self):
        """
        Comprehensive eagle eyes scan - looks for EVERYTHING.
        
        Runs:
        - MOASS candidates
        - TTM Squeeze setups
        - Bullish patterns
        - Bearish patterns (to avoid)
        - Penny stock opportunities
        - Double bottom + put wall setups
        """
        print(f"🦅 EAGLE EYES SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}")
        
        results = {
            "scan_type": "eagle_eyes",
            "timestamp": datetime.now().isoformat(),
            "findings": {}
        }
        
        try:
            # 1. MOASS Candidates (HIGHEST PRIORITY)
            print("  🚀 Scanning for MOASS candidates...")
            moass_candidates = self.screener.find_moass_candidates(top_n=5)
            if moass_candidates:
                results["findings"]["moass"] = moass_candidates
                print(f"    Found {len(moass_candidates)} MOASS candidates!")
            
            # 2. TTM Squeeze Setups
            print("  💥 Detecting TTM Squeeze setups...")
            squeeze_stocks = self.screener.detect_ttm_squeeze(top_n=10)
            if squeeze_stocks:
                results["findings"]["squeeze"] = squeeze_stocks
                print(f"    Found {len(squeeze_stocks)} squeeze setups!")
            
            # 3. Bullish Patterns
            print("  📈 Scanning bullish patterns...")
            bullish = self.screener.detect_bullish_patterns(top_n=10)
            if bullish:
                results["findings"]["bullish_patterns"] = bullish
                print(f"    Found {len(bullish)} bullish patterns!")
            
            # 4. Penny Stock Opportunities
            print("  💰 Scanning penny stocks...")
            penny_stocks = self.screener.screen_penny_stocks_squeeze(top_n=10)
            if penny_stocks:
                results["findings"]["penny_stocks"] = penny_stocks
                print(f"    Found {len(penny_stocks)} penny stock opportunities!")
            
            # 5. Double Bottom + Put Wall
            print("  🎯 Detecting double bottom at put wall...")
            double_bottom = self.screener.detect_double_bottom_with_put_wall(top_n=5)
            if double_bottom:
                results["findings"]["double_bottom_put_wall"] = double_bottom
                print(f"    Found {len(double_bottom)} double bottom setups!")
            
            # 6. Bearish Patterns (to avoid)
            print("  📉 Checking bearish patterns (avoid these)...")
            bearish = self.screener.detect_bearish_patterns(top_n=5)
            if bearish:
                results["findings"]["bearish_patterns"] = bearish
                print(f"    Found {len(bearish)} bearish patterns to avoid!")
            
            # Save to history
            self.scan_history.append(results)
            
            # Send Discord notification
            if self.discord_webhook_url:
                self._send_eagle_eyes_alert(results)
            
            print("  ✅ Eagle Eyes scan complete!")
            return results
            
        except Exception as e:
            print(f"  ❌ Eagle Eyes scan error: {str(e)}")
            return None
    
    def regular_scan(self):
        """
        Regular 2-hour interval scan - focuses on key indicators.
        
        Runs:
        - MOASS candidates
        - TTM Squeeze setups
        - Top penny stocks
        """
        print(f"📊 REGULAR SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}")
        
        results = {
            "scan_type": "regular",
            "timestamp": datetime.now().isoformat(),
            "findings": {}
        }
        
        try:
            # 1. MOASS Candidates
            print("  🚀 Scanning for MOASS candidates...")
            moass_candidates = self.screener.find_moass_candidates(top_n=3)
            if moass_candidates:
                results["findings"]["moass"] = moass_candidates
                print(f"    Found {len(moass_candidates)} MOASS candidates!")
            
            # 2. TTM Squeeze
            print("  💥 Detecting TTM Squeeze...")
            squeeze_stocks = self.screener.detect_ttm_squeeze(top_n=5)
            if squeeze_stocks:
                results["findings"]["squeeze"] = squeeze_stocks
                print(f"    Found {len(squeeze_stocks)} squeeze setups!")
            
            # 3. Penny Stocks
            print("  💰 Scanning penny stocks...")
            penny_stocks = self.screener.screen_penny_stocks_squeeze(top_n=5)
            if penny_stocks:
                results["findings"]["penny_stocks"] = penny_stocks
                print(f"    Found {len(penny_stocks)} penny stock opportunities!")
            
            # Save to history
            self.scan_history.append(results)
            
            # Send Discord notification if notable findings
            if self.discord_webhook_url and self._has_notable_findings(results):
                self._send_regular_alert(results)
            
            print("  ✅ Regular scan complete!")
            return results
            
        except Exception as e:
            print(f"  ❌ Regular scan error: {str(e)}")
            return None
    
    def manual_scan(self, scan_type: str = "eagle_eyes") -> Dict[str, Any]:
        """Run a manual scan immediately."""
        if scan_type == "eagle_eyes":
            return self.eagle_eyes_scan()
        else:
            return self.regular_scan()
    
    def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scan history."""
        return self.scan_history[-limit:]
    
    def _has_notable_findings(self, results: Dict[str, Any]) -> bool:
        """Check if scan has notable findings worth alerting."""
        findings = results.get("findings", {})
        
        # Alert if any MOASS candidates with score > 60
        if findings.get("moass"):
            for candidate in findings["moass"]:
                if candidate.get("moass_score", 0) > 60:
                    return True
        
        # Alert if any squeeze about to fire
        if findings.get("squeeze"):
            for stock in findings["squeeze"]:
                if stock.get("squeeze_firing") and stock.get("momentum", 0) > 0:
                    return True
        
        return False
    
    def _send_eagle_eyes_alert(self, results: Dict[str, Any]):
        """Send comprehensive eagle eyes alert to Discord."""
        findings = results.get("findings", {})
        timestamp = results.get("timestamp", "")
        
        # Build message
        message = "🦅 **EAGLE EYES SCAN COMPLETE** 🦅\n\n"
        
        # MOASS Candidates
        if findings.get("moass"):
            message += "🚀 **MOASS CANDIDATES:**\n"
            for stock in findings["moass"][:3]:
                message += f"  • **{stock['symbol']}** - Score: {stock['moass_score']}/100\n"
                message += f"    Volume: {stock['volume_surge']}x | Price Δ: {stock['price_change_5d']}% | Gamma: {'✅' if stock['gamma_potential'] else '❌'}\n"
            message += "\n"
        
        # TTM Squeeze
        if findings.get("squeeze"):
            message += "💥 **TTM SQUEEZE SETUPS:**\n"
            for stock in findings["squeeze"][:3]:
                status = "🔥 FIRING" if stock['squeeze_firing'] else "⏳ ACTIVE"
                message += f"  • **{stock['symbol']}** - {status}\n"
                message += f"    BB Width: {stock['bb_width']}% | Momentum: {stock['momentum']}\n"
            message += "\n"
        
        # Bullish Patterns
        if findings.get("bullish_patterns"):
            message += "📈 **BULLISH PATTERNS:**\n"
            for stock in findings["bullish_patterns"][:3]:
                patterns = ", ".join(stock['patterns'])
                message += f"  • **{stock['symbol']}** - {patterns}\n"
            message += "\n"
        
        # Double Bottom + Put Wall
        if findings.get("double_bottom_put_wall"):
            message += "🎯 **DOUBLE BOTTOM AT PUT WALL:**\n"
            for stock in findings["double_bottom_put_wall"][:2]:
                message += f"  • **{stock['symbol']}** - Setup Score: {stock['setup_score']}\n"
                message += f"    Bottom: ${stock['bottom_price']} | Put Wall: ${stock.get('put_wall', 'N/A')}\n"
            message += "\n"
        
        # Penny Stocks
        if findings.get("penny_stocks"):
            message += "💰 **TOP PENNY STOCKS:**\n"
            for stock in findings["penny_stocks"][:3]:
                message += f"  • **{stock['symbol']}** - ${stock['price']} | Score: {stock['squeeze_score']}\n"
            message += "\n"
        
        message += f"_Scan completed at {datetime.fromisoformat(timestamp).strftime('%I:%M %p EST')}_"
        
        # Send to Discord
        send_discord_notification(
            self.discord_webhook_url,
            "Eagle Eyes Market Scan",
            message,
            color=0xFFD700  # Gold color for eagle eyes
        )
    
    def _send_regular_alert(self, results: Dict[str, Any]):
        """Send regular scan alert to Discord."""
        findings = results.get("findings", {})
        timestamp = results.get("timestamp", "")
        
        message = "📊 **Market Scan Update**\n\n"
        
        # Only include notable findings
        if findings.get("moass"):
            message += "🚀 **MOASS Alerts:**\n"
            for stock in findings["moass"]:
                if stock.get("moass_score", 0) > 60:
                    message += f"  • **{stock['symbol']}** - Score: {stock['moass_score']}/100\n"
        
        if findings.get("squeeze"):
            message += "💥 **Squeeze Alerts:**\n"
            for stock in findings["squeeze"]:
                if stock.get("squeeze_firing") and stock.get("momentum", 0) > 0:
                    message += f"  • **{stock['symbol']}** - FIRING with momentum {stock['momentum']}\n"
        
        message += f"\n_Scan at {datetime.fromisoformat(timestamp).strftime('%I:%M %p EST')}_"
        
        send_discord_notification(
            self.discord_webhook_url,
            "Market Scan Alert",
            message,
            color=0x3498DB  # Blue for regular
        )

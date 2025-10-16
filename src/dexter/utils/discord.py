import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class DiscordWebhook:
    """
    Discord webhook integration for sending research results to Discord channels.
    """
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_research_results(self, query: str, answer: str, stats: Dict[str, Any], tasks: List[Dict] = None) -> bool:
        """
        Send research results to Discord as a rich embed.
        
        Args:
            query: The original research query
            answer: The final answer/summary
            stats: Execution statistics
            tasks: List of completed tasks (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            embed = self._create_research_embed(query, answer, stats, tasks)
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return response.status_code == 204
            
        except Exception as e:
            print(f"Discord webhook error: {str(e)}")
            return False
    
    def _create_research_embed(self, query: str, answer: str, stats: Dict[str, Any], tasks: List[Dict] = None) -> Dict:
        """
        Create a Discord embed with research results.
        """
        # Truncate answer if too long (Discord has a 4096 char limit for embed descriptions)
        max_answer_length = 1800
        truncated_answer = answer[:max_answer_length] + "..." if len(answer) > max_answer_length else answer
        
        embed = {
            "title": "🤖 Financial Research Complete",
            "description": f"**Query:** {query}\n\n**Summary:**\n{truncated_answer}",
            "color": 3447003,  # Blue color
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Dexter Financial Research Agent"
            },
            "fields": []
        }
        
        # Add statistics
        if stats:
            stats_text = f"""
            📊 Total Steps: {stats.get('total_steps', 'N/A')}
            ✅ Tasks Completed: {stats.get('tasks_completed', 'N/A')}
            🔄 API Calls: {stats.get('api_calls', 'N/A')}
            ⏱️ Execution Time: {stats.get('execution_time', 0):.2f}s
            """
            embed["fields"].append({
                "name": "Execution Statistics",
                "value": stats_text.strip(),
                "inline": False
            })
        
        # Add task breakdown (if available and not too many)
        if tasks and len(tasks) <= 5:
            for i, task in enumerate(tasks, 1):
                task_desc = task.get('description', 'Unknown task')
                # Truncate task description if too long
                if len(task_desc) > 200:
                    task_desc = task_desc[:200] + "..."
                
                embed["fields"].append({
                    "name": f"Task {i}",
                    "value": task_desc,
                    "inline": False
                })
        elif tasks and len(tasks) > 5:
            embed["fields"].append({
                "name": "Tasks Completed",
                "value": f"{len(tasks)} tasks executed successfully",
                "inline": False
            })
        
        return embed
    
    def send_simple_message(self, message: str, title: Optional[str] = None) -> bool:
        """
        Send a simple text message to Discord.
        
        Args:
            message: The message content
            title: Optional title for the embed
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if title:
                payload = {
                    "embeds": [{
                        "title": title,
                        "description": message,
                        "color": 3447003,
                        "timestamp": datetime.utcnow().isoformat()
                    }]
                }
            else:
                payload = {
                    "content": message
                }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return response.status_code == 204
            
        except Exception as e:
            print(f"Discord webhook error: {str(e)}")
            return False
    
    def send_error_notification(self, query: str, error_message: str) -> bool:
        """
        Send an error notification to Discord.
        
        Args:
            query: The original research query
            error_message: The error message
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            embed = {
                "title": "❌ Research Error",
                "description": f"**Query:** {query}\n\n**Error:**\n```{error_message[:500]}```",
                "color": 15158332,  # Red color
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Dexter Financial Research Agent"
                }
            }
            
            payload = {"embeds": [embed]}
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return response.status_code == 204
            
        except Exception as e:
            print(f"Discord webhook error: {str(e)}")
            return False
    
    def test_webhook(self) -> bool:
        """
        Test if the webhook URL is valid and working.
        
        Returns:
            bool: True if webhook is working, False otherwise
        """
        return self.send_simple_message(
            "✅ Discord webhook successfully connected to Dexter!",
            "Webhook Test"
        )

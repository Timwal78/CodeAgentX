import time
from typing import Dict, Set, Optional
from datetime import datetime, timedelta


class SafetyManager:
    """
    Safety manager to prevent infinite loops and runaway execution.
    Implements various safety mechanisms for the autonomous agent.
    """
    
    def __init__(self, max_steps: int = 20, max_steps_per_task: int = 5):
        self.max_steps = max_steps
        self.max_steps_per_task = max_steps_per_task
        
        # Execution tracking
        self.start_time = None
        self.step_count = 0
        self.task_step_counts: Dict[str, int] = {}
        self.visited_states: Set[str] = set()
        self.execution_log = []
        
        # Safety thresholds
        self.max_execution_time = 600  # 10 minutes
        self.max_api_calls_per_minute = 60
        self.loop_detection_threshold = 3
        
        # API rate limiting
        self.api_call_times = []
        self.last_api_call_time = None
    
    def initialize_session(self):
        """Initialize a new safety session."""
        self.start_time = time.time()
        self.step_count = 0
        self.task_step_counts.clear()
        self.visited_states.clear()
        self.execution_log.clear()
        self.api_call_times.clear()
    
    def should_stop_execution(self, current_step: int) -> bool:
        """
        Determine if execution should be stopped based on safety criteria.
        """
        # Check global step limit
        if current_step >= self.max_steps:
            self.log_safety_event("STOP", f"Reached maximum steps limit: {self.max_steps}")
            return True
        
        # Check execution time limit
        if self.start_time and (time.time() - self.start_time) > self.max_execution_time:
            self.log_safety_event("STOP", f"Reached maximum execution time: {self.max_execution_time}s")
            return True
        
        # Check for potential infinite loops
        if self._detect_loop():
            self.log_safety_event("STOP", "Potential infinite loop detected")
            return True
        
        return False
    
    def should_stop_task(self, task_id: str) -> bool:
        """
        Determine if a specific task should be stopped.
        """
        task_steps = self.task_step_counts.get(task_id, 0)
        
        if task_steps >= self.max_steps_per_task:
            self.log_safety_event("TASK_STOP", f"Task {task_id} reached maximum steps: {self.max_steps_per_task}")
            return True
        
        return False
    
    def record_step(self, step_type: str, task_id: Optional[str] = None, state_signature: Optional[str] = None):
        """
        Record a step in the execution process.
        """
        self.step_count += 1
        
        # Track task-specific steps
        if task_id:
            self.task_step_counts[task_id] = self.task_step_counts.get(task_id, 0) + 1
        
        # Track state for loop detection
        if state_signature:
            self.visited_states.add(state_signature)
        
        # Log the step
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": self.step_count,
            "type": step_type,
            "task_id": task_id,
            "state_signature": state_signature
        }
        self.execution_log.append(log_entry)
    
    def record_api_call(self):
        """
        Record an API call for rate limiting purposes.
        """
        current_time = time.time()
        self.api_call_times.append(current_time)
        self.last_api_call_time = current_time
        
        # Clean old entries (older than 1 minute)
        one_minute_ago = current_time - 60
        self.api_call_times = [t for t in self.api_call_times if t > one_minute_ago]
    
    def should_rate_limit(self) -> bool:
        """
        Check if we should rate limit API calls.
        """
        if len(self.api_call_times) >= self.max_api_calls_per_minute:
            self.log_safety_event("RATE_LIMIT", f"API rate limit reached: {self.max_api_calls_per_minute}/minute")
            return True
        return False
    
    def get_rate_limit_delay(self) -> float:
        """
        Calculate how long to wait before next API call.
        """
        if not self.api_call_times:
            return 0.0
        
        # If we're at the rate limit, wait until the oldest call is > 1 minute old
        if len(self.api_call_times) >= self.max_api_calls_per_minute:
            oldest_call = min(self.api_call_times)
            wait_until = oldest_call + 60
            return max(0, wait_until - time.time())
        
        return 0.0
    
    def _detect_loop(self) -> bool:
        """
        Detect potential infinite loops by analyzing execution patterns.
        """
        if len(self.execution_log) < self.loop_detection_threshold:
            return False
        
        # Check for repeated state signatures
        recent_states = [log.get("state_signature") for log in self.execution_log[-self.loop_detection_threshold:]]
        recent_states = [s for s in recent_states if s is not None]
        
        if len(recent_states) >= self.loop_detection_threshold:
            # If all recent states are the same, we might be in a loop
            if len(set(recent_states)) == 1:
                return True
        
        # Check for repeating step patterns
        recent_steps = [log.get("type") for log in self.execution_log[-6:]]
        if len(recent_steps) >= 4:
            # Look for ABAB pattern
            if (recent_steps[-4] == recent_steps[-2] and 
                recent_steps[-3] == recent_steps[-1] and 
                recent_steps[-4] != recent_steps[-3]):
                return True
        
        return False
    
    def log_safety_event(self, event_type: str, message: str):
        """
        Log a safety-related event.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "SAFETY_EVENT",
            "event_type": event_type,
            "message": message,
            "step": self.step_count
        }
        self.execution_log.append(log_entry)
        print(f"[SAFETY] {event_type}: {message}")
    
    def get_execution_stats(self) -> Dict[str, any]:
        """
        Get current execution statistics.
        """
        current_time = time.time()
        execution_time = current_time - self.start_time if self.start_time else 0
        
        return {
            "total_steps": self.step_count,
            "execution_time": execution_time,
            "api_calls_last_minute": len(self.api_call_times),
            "tasks_in_progress": len(self.task_step_counts),
            "max_steps": self.max_steps,
            "max_steps_per_task": self.max_steps_per_task,
            "safety_events": [log for log in self.execution_log if log.get("type") == "SAFETY_EVENT"]
        }
    
    def create_state_signature(self, task_id: str, action: str, result_summary: str) -> str:
        """
        Create a signature for the current state to help with loop detection.
        """
        # Create a hash-like signature from key components
        import hashlib
        
        state_components = f"{task_id}:{action}:{result_summary[:100]}"
        signature = hashlib.md5(state_components.encode()).hexdigest()[:8]
        return signature
    
    def is_execution_healthy(self) -> bool:
        """
        Check if the current execution appears to be healthy.
        """
        stats = self.get_execution_stats()
        
        # Check if we're approaching limits
        if stats["total_steps"] > (self.max_steps * 0.8):
            return False
        
        if stats["execution_time"] > (self.max_execution_time * 0.8):
            return False
        
        if len(stats["safety_events"]) > 3:
            return False
        
        return True

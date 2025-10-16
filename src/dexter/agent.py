import time
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from .model import LLMInterface
from .tools import FinancialDataTools
from .options_tools import OptionsDataTools
from .prompts import SYSTEM_PROMPTS
from .schemas import Task, TaskResult, ResearchResult
from .utils.safety import SafetyManager
from .utils.validation import ValidationManager


class Agent:
    """
    Main orchestration agent that coordinates the multi-agent system
    for autonomous financial research.
    """
    
    def __init__(self, max_steps: int = 20, max_steps_per_task: int = 5):
        self.max_steps = max_steps
        self.max_steps_per_task = max_steps_per_task
        
        # Initialize components
        self.llm = LLMInterface()
        self.tools = FinancialDataTools()
        self.options_tools = OptionsDataTools()
        self.safety = SafetyManager(max_steps, max_steps_per_task)
        self.validator = ValidationManager()
        
        # Execution state
        self.current_step = 0
        self.execution_log = []
        self.start_time = None
        self.api_call_count = 0
    
    def research(self, query: str, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Main research method that orchestrates the entire process.
        """
        self.start_time = time.time()
        self.current_step = 0
        self.execution_log = []
        self.api_call_count = 0
        
        try:
            # Step 1: Planning Phase
            self._log_step("planning", "Analyzing query and creating research plan", callback)
            tasks = self._planning_agent(query)
            
            # Step 2: Execution Phase
            completed_tasks = []
            for task in tasks:
                if self.safety.should_stop_execution(self.current_step):
                    break
                
                self._log_step("action", f"Executing task: {task.description}", callback)
                task_result = self._action_agent(task)
                
                # Step 3: Validation Phase
                self._log_step("validation", f"Validating task completion", callback)
                if self._validation_agent(task, task_result):
                    completed_tasks.append(task_result)
                else:
                    # Retry task if validation fails and within limits
                    retry_count = 0
                    while retry_count < self.max_steps_per_task and not self.safety.should_stop_execution(self.current_step):
                        self._log_step("action", f"Retrying task: {task.description} (attempt {retry_count + 2})", callback)
                        task_result = self._action_agent(task)
                        
                        if self._validation_agent(task, task_result):
                            completed_tasks.append(task_result)
                            break
                        retry_count += 1
            
            # Step 4: Answer Synthesis Phase
            self._log_step("answer", "Synthesizing final answer from completed tasks", callback)
            final_answer = self._answer_agent(query, completed_tasks)
            
            # Compile results
            execution_time = time.time() - self.start_time
            return ResearchResult(
                query=query,
                answer=final_answer,
                tasks_completed=[task.dict() for task in completed_tasks],
                stats={
                    "total_steps": self.current_step,
                    "tasks_completed": len(completed_tasks),
                    "api_calls": self.api_call_count,
                    "execution_time": execution_time
                }
            ).dict()
            
        except Exception as e:
            self._log_step("error", f"Research failed: {str(e)}", callback)
            raise e
    
    def _planning_agent(self, query: str) -> List[Task]:
        """
        Planning agent that decomposes the query into structured tasks.
        """
        self.current_step += 1
        self.api_call_count += 1
        
        # Combine stock and options tool descriptions
        all_tools = {
            **self.tools.get_tool_descriptions(),
            **self.options_tools.get_tool_descriptions()
        }
        
        prompt = SYSTEM_PROMPTS["planning"].format(
            query=query,
            available_tools=all_tools
        )
        
        response = self.llm.generate_structured_response(
            prompt,
            "Please analyze the query and create a detailed task plan. Return a JSON object with 'tasks' array containing task objects with 'id', 'description', 'tool_needed', and 'dependencies' fields."
        )
        
        # Parse tasks from response
        tasks = []
        try:
            parsed_response = json.loads(response)
            for i, task_data in enumerate(parsed_response.get("tasks", [])):
                task = Task(
                    id=task_data.get("id", f"task_{i}"),
                    description=task_data.get("description", ""),
                    tool_needed=task_data.get("tool_needed", ""),
                    dependencies=task_data.get("dependencies", [])
                )
                tasks.append(task)
        except json.JSONDecodeError:
            # Fallback: create a single generic task
            tasks.append(Task(
                id="task_1",
                description=f"Research: {query}",
                tool_needed="financial_data",
                dependencies=[]
            ))
        
        return tasks
    
    def _action_agent(self, task: Task) -> TaskResult:
        """
        Action agent that executes individual tasks using appropriate tools.
        """
        self.current_step += 1
        self.api_call_count += 1
        
        # Execute the task using the specified tool
        tool_result = None
        if task.tool_needed == "financial_data":
            # Extract company/symbol from task description
            companies = self._extract_companies_from_text(task.description)
            if companies:
                tool_result = self.tools.get_financial_data(companies[0])
                self.api_call_count += 1
        
        elif task.tool_needed == "options_chain":
            companies = self._extract_companies_from_text(task.description)
            if companies:
                tool_result = self.options_tools.get_options_chain(companies[0])
                self.api_call_count += 1
        
        elif task.tool_needed == "options_greeks":
            companies = self._extract_companies_from_text(task.description)
            if companies:
                # For Greeks calculation, we need the options chain first
                # The LLM will analyze the chain data to identify key strikes
                tool_result = self.options_tools.get_options_chain(companies[0])
                self.api_call_count += 1
                
                # Note: Specific Greeks calculation requires strike/expiration
                # which the validation/answer agent can request if needed
        
        elif task.tool_needed == "unusual_options":
            companies = self._extract_companies_from_text(task.description)
            if companies:
                tool_result = self.options_tools.identify_unusual_activity(companies[0])
                self.api_call_count += 1
        
        elif task.tool_needed == "put_call_ratio":
            companies = self._extract_companies_from_text(task.description)
            if companies:
                tool_result = self.options_tools.calculate_put_call_ratio(companies[0])
                self.api_call_count += 1
        
        # Generate analysis based on tool result
        prompt = SYSTEM_PROMPTS["action"].format(
            task_description=task.description,
            tool_result=tool_result or "No data retrieved",
            query_context=""  # Could add broader context here
        )
        
        analysis = self.llm.generate_response(prompt)
        self.api_call_count += 1
        
        return TaskResult(
            task_id=task.id,
            description=task.description,
            result=analysis,
            data=tool_result,
            success=True,
            timestamp=datetime.now().isoformat()
        )
    
    def _validation_agent(self, task: Task, task_result: TaskResult) -> bool:
        """
        Validation agent that checks if a task was completed successfully.
        """
        self.current_step += 1
        self.api_call_count += 1
        
        prompt = SYSTEM_PROMPTS["validation"].format(
            task_description=task.description,
            task_result=task_result.result,
            success_criteria="Task provides specific, data-backed analysis relevant to the original request"
        )
        
        validation_response = self.llm.generate_structured_response(
            prompt,
            "Validate the task completion. Return JSON with 'is_valid' boolean and 'reason' string."
        )
        
        try:
            validation_data = json.loads(validation_response)
            return validation_data.get("is_valid", False)
        except json.JSONDecodeError:
            # Default to considering task complete if validation parsing fails
            return True
    
    def _answer_agent(self, original_query: str, completed_tasks: List[TaskResult]) -> str:
        """
        Answer agent that synthesizes findings into a comprehensive response.
        """
        self.current_step += 1
        self.api_call_count += 1
        
        task_summaries = []
        for task in completed_tasks:
            summary = f"Task: {task.description}\nResult: {task.result}"
            if task.data:
                summary += f"\nData: {json.dumps(task.data, indent=2)}"
            task_summaries.append(summary)
        
        prompt = SYSTEM_PROMPTS["answer"].format(
            original_query=original_query,
            completed_tasks="\n\n".join(task_summaries)
        )
        
        final_answer = self.llm.generate_response(prompt)
        self.api_call_count += 1
        
        return final_answer
    
    def _extract_companies_from_text(self, text: str) -> List[str]:
        """
        Extract company names/symbols from text description.
        """
        # Simple extraction - could be enhanced with NLP
        common_companies = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'meta': 'META',
            'facebook': 'META',
            'nvidia': 'NVDA',
            'netflix': 'NFLX'
        }
        
        text_lower = text.lower()
        found_companies = []
        
        for company, symbol in common_companies.items():
            if company in text_lower:
                found_companies.append(symbol)
        
        # Also look for stock symbols (3-5 uppercase letters)
        import re
        symbols = re.findall(r'\b[A-Z]{3,5}\b', text)
        found_companies.extend(symbols)
        
        return list(set(found_companies))  # Remove duplicates
    
    def _log_step(self, step_type: str, message: str, callback: Optional[Callable] = None):
        """
        Log execution step and call callback if provided.
        """
        log_entry = {
            "type": step_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "step_number": self.current_step
        }
        
        self.execution_log.append(log_entry)
        
        if callback:
            callback(log_entry)

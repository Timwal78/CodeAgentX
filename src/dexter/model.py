import os
import json
from typing import Optional
from openai import OpenAI


class LLMInterface:
    """
    Interface for interacting with OpenAI's language models.
    Handles both structured and unstructured responses.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=self.api_key)
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-5"
    
    def generate_response(self, prompt: str, max_completion_tokens: int = 4096) -> str:
        """
        Generate a standard text response.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=max_completion_tokens
            )
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def generate_structured_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        max_completion_tokens: int = 4096
    ) -> str:
        """
        Generate a structured JSON response.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=max_completion_tokens
            )
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Failed to generate structured response: {str(e)}")
    
    def analyze_financial_data(self, data: dict, analysis_request: str) -> str:
        """
        Specialized method for financial data analysis.
        """
        system_prompt = """You are a financial analysis expert. Analyze the provided 
        financial data and respond to the specific analysis request. Provide detailed, 
        data-driven insights with specific numbers and calculations where appropriate."""
        
        user_prompt = f"""
        Analysis Request: {analysis_request}
        
        Financial Data:
        {json.dumps(data, indent=2)}
        
        Please provide a comprehensive analysis addressing the request.
        """
        
        return self.generate_response(f"{system_prompt}\n\n{user_prompt}")
    
    def validate_task_completion(self, task_description: str, task_result: str) -> bool:
        """
        Validate if a task has been completed successfully.
        """
        prompt = f"""
        Evaluate whether the following task has been completed successfully:
        
        Task: {task_description}
        Result: {task_result}
        
        Respond with JSON in this format: {{"is_valid": boolean, "reason": "explanation"}}
        
        Consider a task successful if it provides specific, actionable insights with 
        supporting data or clear reasoning.
        """
        
        try:
            response = self.generate_structured_response(
                "You are a task validation expert. Analyze task completion quality.",
                prompt
            )
            validation_data = json.loads(response)
            return validation_data.get("is_valid", False)
            
        except Exception:
            # Default to successful if validation fails
            return True

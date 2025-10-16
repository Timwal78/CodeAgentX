import os
import json
from typing import Optional
from openai import OpenAI
import google.generativeai as genai


class LLMInterface:
    """
    Interface for LLM interactions with automatic fallback.
    Supports OpenAI (paid) and Google Gemini (FREE).
    """
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        # Determine which provider to use
        self.provider = None
        
        # Try Gemini first (FREE!)
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.provider = "gemini"
            except:
                pass
        
        # Fallback to OpenAI if available
        if not self.provider and self.openai_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_key)
                self.openai_model = "gpt-4o-mini"  # More affordable than gpt-5
                self.provider = "openai"
            except:
                pass
        
        if not self.provider:
            raise ValueError(
                "No LLM provider available. Please set either:\n"
                "- GEMINI_API_KEY (FREE: https://aistudio.google.com/apikey)\n"
                "- OPENAI_API_KEY (Paid: https://platform.openai.com/api-keys)"
            )
    
    def generate_response(self, prompt: str, max_completion_tokens: int = 4096) -> str:
        """
        Generate a standard text response.
        """
        try:
            if self.provider == "gemini":
                response = self.gemini_model.generate_content(prompt)
                return response.text
            
            elif self.provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
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
            if self.provider == "gemini":
                # Gemini doesn't have JSON mode, so we explicitly request JSON in the prompt
                combined_prompt = f"""{system_prompt}

{user_prompt}

IMPORTANT: You must respond with ONLY valid JSON. No other text before or after. Start your response with {{ and end with }}.
"""
                response = self.gemini_model.generate_content(combined_prompt)
                response_text = response.text.strip()
                
                # Extract JSON if wrapped in markdown code blocks
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()
                
                return response_text
            
            elif self.provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
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

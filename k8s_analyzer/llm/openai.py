import json
import time
from typing import Dict, Any
from openai import OpenAI, RateLimitError, APIError
from .base import BaseLLM
from ..core.config import (
    OPENAI_API_KEY,
    DEFAULT_OPENAI_MODEL,
    MAX_RETRIES,
    RETRY_DELAY
)
from ..core.exceptions import LLMConfigError, LLMAPIError

class OpenAILLM(BaseLLM):
    """OpenAI implementation of the LLM interface."""
    
    def _initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not OPENAI_API_KEY:
            raise LLMConfigError("OPENAI_API_KEY environment variable not set")
        
        self.model = self.model or DEFAULT_OPENAI_MODEL
        try:
            self.client = OpenAI()
            self.logger.info(f"Initialized OpenAI client with model: {self.model}")
        except Exception as e:
            raise LLMConfigError(f"Failed to initialize OpenAI client: {e}")
    
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Analyze using OpenAI's chat completion API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        retries = 0
        while retries < MAX_RETRIES:
            try:
                self.logger.debug(f"Sending request to OpenAI: {messages}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=3000,
                    temperature=0.5,
                )
                return self.validate_response(response)
                
            except RateLimitError:
                retries += 1
                self.logger.warning(
                    f"Rate limit exceeded. Retrying in {RETRY_DELAY}s... ({retries}/{MAX_RETRIES})"
                )
                if retries >= MAX_RETRIES:
                    raise LLMAPIError(
                        f"Rate limit exceeded after {MAX_RETRIES} retries. Please wait or reduce query scope."
                    )
                time.sleep(RETRY_DELAY)
                
            except APIError as e:
                raise LLMAPIError(f"OpenAI API error: {e}")
                
            except Exception as e:
                raise LLMAPIError(f"Unexpected error during OpenAI analysis: {e}")
    
    def validate_response(self, response: Any) -> Dict[str, Any]:
        """Validate and parse OpenAI response."""
        try:
            analysis = response.choices[0].message.content.strip()
            self.logger.debug(f"Received response from OpenAI: {analysis[:100]}...")
            
            # Clean up potential markdown formatting
            cleaned_analysis = analysis
            if cleaned_analysis.startswith("```json"):
                cleaned_analysis = cleaned_analysis[7:]
            if cleaned_analysis.startswith("```"):
                cleaned_analysis = cleaned_analysis[3:]
            if cleaned_analysis.endswith("```"):
                cleaned_analysis = cleaned_analysis[:-3]
            cleaned_analysis = cleaned_analysis.strip()
            
            try:
                parsed_analysis = json.loads(cleaned_analysis)
                return {"analysis": parsed_analysis, "success": True}
            except json.JSONDecodeError:
                self.logger.warning(f"OpenAI response was not valid JSON: {analysis}")
                return {
                    "analysis": {"raw_output": analysis},
                    "success": True,
                    "warning": "Non-JSON response"
                }
                
        except Exception as e:
            raise LLMAPIError(f"Failed to validate OpenAI response: {e}") 
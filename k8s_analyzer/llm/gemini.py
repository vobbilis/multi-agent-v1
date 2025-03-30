"""Google Gemini implementation of the LLM interface."""

import json
import time
from typing import Dict, Any
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
from .base import BaseLLM
from ..core.config import (
    GOOGLE_API_KEY,
    DEFAULT_GEMINI_MODEL,
    MAX_RETRIES,
    RETRY_DELAY,
    MAX_TOKENS,
    TEMPERATURE
)
from ..core.exceptions import LLMConfigError, LLMAPIError

class GeminiLLM(BaseLLM):
    """Google Gemini implementation of the LLM interface."""
    
    def _initialize(self) -> None:
        """Initialize the Gemini client."""
        if not GOOGLE_API_KEY:
            raise LLMConfigError("GOOGLE_API_KEY environment variable not set")
            
        self.model = self.model or DEFAULT_GEMINI_MODEL
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model_client = genai.GenerativeModel(
                model_name=self.model,
                generation_config={
                    "max_output_tokens": MAX_TOKENS,
                    "temperature": TEMPERATURE
                }
            )
            self.logger.info(f"Initialized Gemini client with model: {self.model}")
        except Exception as e:
            raise LLMConfigError(f"Failed to initialize Gemini client: {e}")
    
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Analyze using Gemini's chat API."""
        # Combine prompts as Gemini doesn't have separate system/user roles
        combined_prompt = f"{system_prompt}\n\nUser Query: {user_prompt}"
        
        retries = 0
        while retries < MAX_RETRIES:
            try:
                self.logger.debug(f"Sending request to Gemini: {combined_prompt[:100]}...")
                response = self.model_client.generate_content(combined_prompt)
                return self.validate_response(response)
                
            except genai.types.BlockedPromptException as e:
                raise LLMAPIError(f"Gemini blocked prompt: {e}")
                
            except genai.types.GenerateContentResponseError as e:
                retries += 1
                self.logger.warning(
                    f"Gemini API error. Retrying in {RETRY_DELAY}s... ({retries}/{MAX_RETRIES})"
                )
                if retries >= MAX_RETRIES:
                    raise LLMAPIError(f"Gemini API error after {MAX_RETRIES} retries: {e}")
                time.sleep(RETRY_DELAY)
                
            except Exception as e:
                raise LLMAPIError(f"Unexpected error during Gemini analysis: {e}")
    
    def validate_response(self, response: GenerateContentResponse) -> Dict[str, Any]:
        """Validate and parse Gemini response."""
        try:
            analysis = response.text.strip()
            self.logger.debug(f"Received response from Gemini: {analysis[:100]}...")
            
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
                self.logger.warning(f"Gemini response was not valid JSON: {analysis}")
                return {
                    "analysis": {"raw_output": analysis},
                    "success": True,
                    "warning": "Non-JSON response"
                }
                
        except Exception as e:
            raise LLMAPIError(f"Failed to validate Gemini response: {e}") 
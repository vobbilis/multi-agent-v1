"""ReAct agent implementation for K8s Analyzer."""

import uuid
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Type
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm, Prompt
import os
import inspect
import re

from .base import BaseReActAgent, AgentState
from ..tools.result import ToolResult
from .config import (
    MAX_ITERATIONS,
    THOUGHT_PROCESS_TIMEOUT,
    ACTION_EXECUTION_TIMEOUT,
    HITL_ENABLED,
    HITL_TIMEOUT,
    HITL_AUTO_APPROVE_SAFE_ACTIONS,
    AUTO_APPROVE_ACTIONS,
    SAFE_ACTIONS,
    DANGEROUS_ACTIONS,
    DISPLAY_THOUGHT_PROCESS,
    DISPLAY_TOOL_OUTPUTS,
    MAX_OUTPUT_WIDTH,
    get_prompt_template
)
from .exceptions import (
    ReActError,
    ReActConfigError,
    ReActStateError,
    ReActToolError,
    ReActValidationError,
    ReActTimeoutError,
    ReActMaxIterationsError,
    ReActHITLError,
    ReActPromptError,
    ReActParsingError,
    ReActAbortError
)
from ..llm import get_llm, LLMError
from ..tools import get_tool_registry, ToolError, ToolRegistry
from ..llm.base import BaseLLM
from ..llm.exceptions import LLMResponseError
from ..tools.result import ToolResultEncoder

class ReActState:
    pass
    # ... existing code ...

class ReActAgent(BaseReActAgent):
    """Implementation of the ReAct agent for Kubernetes analysis."""
    
    def __init__(self, llm: BaseLLM, tools: ToolRegistry):
        """Initialize the ReAct agent with pre-configured LLM and ToolRegistry."""
        self.logger = logging.getLogger("k8s_analyzer.react.agent")
        self.console = Console()
        
        # Assign the provided llm and tools instances
        self.llm = llm
        self.tools = tools
            
        # Initialize state
        self.state: Optional[AgentState] = None
        # Add placeholder for execution_logger if needed immediately
        self.execution_logger = None 
        
    def initialize_state(self, session_id: Optional[str] = None, **kwargs) -> None:
        """Initialize or reset the agent state."""
        self.state = AgentState(
            session_id=session_id or str(uuid.uuid4()),
            history=[],
            context={},
            max_iterations=kwargs.get("max_iterations", MAX_ITERATIONS),
            current_iteration=0,
            last_tool_result=None,
            start_time=datetime.now()
        )
        self.logger.info(f"Initialized agent state with session {self.state.session_id}")
        
    def analyze_question(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        log_dir: str = "logs",
        initial_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyzes a user question using the ReAct loop.

        Args:
            question: The user's question.
            context: Additional context for the analysis.
            log_dir: Directory to store execution logs.
            initial_feedback: Initial user feedback to guide the first step.

        Returns:
            A dictionary containing the final analysis result or an error.
        """
        if not self.state or not self.state.session_id:
             # Ensure state exists. Use ReActState if that's the correct class, else AgentState
             # Assuming AgentState based on previous diff:
            self.state = AgentState()
        self.logger.info(f"Initialized/Using agent state with session {self.state.session_id}")

        # --- Execution Logging Setup ---
        if not self.execution_logger:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            log_file = os.path.join(log_dir, f"react_execution_{self.state.session_id}.log")
            self.execution_logger = logging.getLogger(f"ReActExecution_{self.state.session_id}")
            self.execution_logger.setLevel(logging.INFO)
            # Prevent propagation to root logger if desired
            # self.execution_logger.propagate = False
            # Remove existing handlers to avoid duplicates if re-analyzing
            for handler in self.execution_logger.handlers[:]:
                handler.close()
                self.execution_logger.removeHandler(handler)
            file_handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.execution_logger.addHandler(file_handler)
            self.logger.info(f"Execution log will be saved to: {log_file}")
        # --- End Execution Logging Setup ---

        self.logger.info(f"Starting ReAct analysis for question: {question}")
        self.execution_logger.info(f"--- Starting ReAct Analysis (Session: {self.state.session_id}) ---")
        self.execution_logger.info(f"Question: {question}")
        self.execution_logger.info(f"Initial Context: {context}")

        initial_context = context if context else {}
        initial_context["question"] = question
        # We'll add tool descriptions later
        initial_context["tools"] = "Tool descriptions placeholder."

        feedback = initial_feedback

        for i in range(self.state.max_iterations):
            self.logger.info(f"Iteration {i+1}/{self.state.max_iterations}")
            self.execution_logger.info(f"\n--- Iteration {i+1}/{self.state.max_iterations} ---")

            try:
                # <<< REPLACE PLACEHOLDER WITH CORE LOGIC >>>
                # 1. Build Prompts
                self.execution_logger.info("Building prompts...")
                system_prompt = self._build_system_prompt()
                user_prompt = self._build_user_prompt(initial_context, feedback=feedback)
                feedback = None # Reset feedback after using it in the prompt
                self.execution_logger.debug(f"System Prompt:\n{system_prompt}")
                self.execution_logger.debug(f"User Prompt:\n{user_prompt}")

                if not user_prompt or not user_prompt.strip():
                    self.logger.error("User prompt content is empty or invalid. Cannot proceed.")
                    self.execution_logger.error("User prompt content is empty or invalid.")
                    raise ReActError("User prompt content is empty or invalid.")

                # 2. Generate LLM Response
                self.execution_logger.info("Querying LLM...")
                # Use the analyze method from the LLM wrapper
                # Ensure the LLM's analyze method is compatible (takes system_prompt, user_prompt)
                # Check signature if needed (code removed for clarity, assume compatible)
                llm_response_raw = self.llm.analyze(system_prompt=system_prompt, user_prompt=user_prompt)
                
                # Check if the response format indicates success or failure from the LLM wrapper itself
                if isinstance(llm_response_raw, dict) and not llm_response_raw.get('success', True):
                    error_msg = llm_response_raw.get('error', 'LLM analysis failed internally.')
                    self.logger.error(f"LLM analysis returned failure: {error_msg}")
                    self.execution_logger.error(f"LLM analysis returned failure: {error_msg}")
                    # Provide feedback for retry or raise error
                    feedback = f"The LLM analysis failed: {error_msg}. Please try again or adjust the approach."
                    continue # Retry the loop
                    
                # Extract the actual string content to parse
                # Assuming the successful response is a string or can be converted
                if isinstance(llm_response_raw, dict):
                     # Adapt based on actual LLM wrapper output structure
                     llm_content = llm_response_raw.get('analysis', {}).get('raw_output') 
                     if not llm_content: 
                          llm_content = llm_response_raw.get('raw_output') # Try another common key
                     if not llm_content:
                          llm_content = str(llm_response_raw) # Fallback
                else:
                     llm_content = str(llm_response_raw)
                     
                self.execution_logger.info(f"LLM Raw Response Content:\n{llm_content}")

                # 3. Extract Reasoning and Parse JSON Decision
                reasoning_text, json_block = self._extract_reasoning_and_json(llm_content)
                self.state.add_interaction("llm", reasoning_text if reasoning_text else llm_content) 
                if reasoning_text:
                    self.logger.info(f"LLM Reasoning: {reasoning_text}")
                    self.execution_logger.info(f"LLM Reasoning:\n{reasoning_text}")
                else:
                    self.logger.warning("Could not extract separate reasoning from LLM response.")
                    self.execution_logger.warning("Could not extract separate reasoning.")

                if not json_block:
                    self.logger.error("LLM response did not contain a valid JSON block.")
                    self.execution_logger.error("LLM response did not contain a valid JSON block.")
                    feedback = "Your response did not contain the required JSON block. Please provide the action or final answer in the specified JSON format." 
                    continue # Retry the loop with feedback

                proposed_decision = self._parse_llm_response(json_block)
                self.execution_logger.info(f"Parsed Decision: {proposed_decision}")

                # 4. Process Decision (Final Answer or Action)
                if proposed_decision["type"] == "final_answer":
                    self.logger.info(f"Final Answer Proposed: {proposed_decision.get('main_response', 'N/A')}")
                    self.execution_logger.info(f"--- Final Answer Proposed ---")
                    self.execution_logger.info(json.dumps(proposed_decision, indent=2))
                    # Optionally format before returning
                    # final_formatted = self._format_final_answer(proposed_decision)
                    return proposed_decision # End of loop

                elif proposed_decision["type"] == "action":
                    action = proposed_decision["action"]
                    self.logger.info(f"Action Proposed: Tool={action.get('tool')}, Params={action.get('parameters')}")
                    self.execution_logger.info("--- Action Proposed ---")
                    self.execution_logger.info(json.dumps(action, indent=2))

                    # 5. Get User Confirmation
                    confirmation = self._get_user_confirmation(action)
                    # If confirmation is False (i.e., user said 'no'), ReActAbortError is raised inside the method
                    self.logger.info(f"User approved action: {action}")
                    self.execution_logger.info("User approved action.")

                    # 6. Execute Action
                    tool_name = action.get("tool")
                    tool_params = action.get("parameters", {})
                    self.execution_logger.info(f"Executing action: {tool_name} with params: {tool_params}")
                    
                    try:
                        # Use ToolRegistry to execute
                        result = self.tools.execute_tool(tool_name, **tool_params)
                        
                        self.logger.info(f"Action Result: {result}") # Log raw result
                        self.execution_logger.info("--- Action Result ---")
                        # Use ToolResultEncoder for JSON serialization
                        self.execution_logger.info(json.dumps(result, indent=2, cls=ToolResultEncoder))
                        
                        # Add interaction with the result
                        self.state.add_interaction("tool", result, action=action)
                        
                        if isinstance(result, ToolResult) and not result.success:
                             self.logger.warning(f"Tool execution reported failure: {result.error}")
                             feedback = f"The tool '{tool_name}' reported an error: {result.error}. Please analyze and proceed."
                        elif isinstance(result, dict) and not result.get("success", True):
                             error_msg = result.get("error", "Unknown error")
                             self.logger.warning(f"Tool execution failed: {error_msg}")
                             feedback = f"The tool '{tool_name}' failed: {error_msg}. Please analyze and proceed."
                             
                    except Exception as tool_exec_err:
                        self.logger.error(f"Tool execution raised exception: {tool_exec_err}", exc_info=True)
                        self.execution_logger.error(f"Tool execution raised exception: {tool_exec_err}", exc_info=True)
                        error_result = {"success": False, "tool": tool_name, "error": str(tool_exec_err)}
                        self.state.add_interaction("tool", error_result, action=action)
                        self.execution_logger.info("--- Action Failed (Exception) ---")
                        self.execution_logger.info(json.dumps(error_result, indent=2))
                        feedback = f"Executing tool '{tool_name}' raised an error: {tool_exec_err}. Please analyze and proceed."

                else:
                    # Should not happen if parsing is correct
                    self.logger.error(f"Unknown decision type from LLM: {proposed_decision.get('type')}")
                    self.execution_logger.error(f"Unknown decision type from LLM: {proposed_decision.get('type')}")
                    raise LLMResponseError(f"Unknown decision type from LLM: {proposed_decision.get('type')}")
                # <<< END OF CORE LOGIC >>>

            except (LLMResponseError, ReActError, ReActAbortError) as e:
                self.logger.error(f"Error in ReAct iteration {i+1}: {e}", exc_info=True)
                self.execution_logger.error(f"--- Error in Iteration {i+1} ---")
                self.execution_logger.error(f"{type(e).__name__}: {e}", exc_info=True)
                if isinstance(e, ReActAbortError):
                     return {"type": "error", "error_type": "UserAbort", "message": str(e)}
                # Provide feedback for recoverable errors? Maybe retry?
                # For now, return generic error for others
                return {"type": "error", "error_type": type(e).__name__, "message": str(e)}
            except Exception as e:
                 self.logger.error(f"Unexpected error in ReAct iteration {i+1}: {e}", exc_info=True)
                 self.execution_logger.error(f"--- Unexpected Error in Iteration {i+1} ---")
                 self.execution_logger.error(f"Unexpected {type(e).__name__}: {e}", exc_info=True)
                 return {"type": "error", "error_type": "UnexpectedError", "message": str(e)}

        # --- Max Iterations Reached Handling --- 
        self.logger.warning(f"Reached maximum iterations ({self.state.max_iterations}) without a final answer.")
        # ... (Return MaxIterationsReached error as defined before) ...
        return {"type": "error", "error_type": "MaxIterationsReached", "message": "Max iterations reached."}
        
    def propose_actions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get next actions from the LLM."""
        try:
            # Build prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(context)
            
            # Get LLM response
            response = self.llm.analyze(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            # Parse and validate actions
            actions = self._parse_llm_response(response)
            return actions
            
        except LLMError as e:
            raise ReActPromptError(f"Failed to get actions from LLM: {e}")
            
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool action."""
        try:
            tool_name = action["action"]["tool"]
            parameters = action["action"]["parameters"]
            
            tool = self.tools.get_tool(tool_name)
            if not tool:
                raise ReActToolError(f"Unknown tool: {tool_name}")
                
            result = tool.execute(**parameters)
            
            # If result is a ToolResult object, convert it to a dict
            if hasattr(result, 'to_dict') and callable(getattr(result, 'to_dict')):
                result_dict = result.to_dict()
                return {
                    "success": result_dict.get("success", True),
                    "tool": tool_name,
                    "result": result_dict
                }
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
            
        except ToolError as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
            
    def validate_action(self, action: Dict[str, Any]) -> bool:
        """Validate an action and get HITL approval if needed."""
        try:
            # Basic validation
            if not isinstance(action, dict):
                raise ReActValidationError("Invalid action format")
                
            if "action" not in action or "tool" not in action["action"]:
                raise ReActValidationError("Missing required action fields")
                
            tool_name = action["action"]["tool"]
            
            # Auto-approve if configured
            if AUTO_APPROVE_ACTIONS:
                return True
                
            # Check if HITL is needed
            if not HITL_ENABLED:
                return True
                
            if HITL_AUTO_APPROVE_SAFE_ACTIONS and tool_name in SAFE_ACTIONS:
                return True
                
            if tool_name in DANGEROUS_ACTIONS:
                self.console.print(
                    Panel(
                        f"[red]WARNING: {tool_name} is a dangerous action![/red]\n"
                        "Please review carefully before approving.",
                        title="⚠️ Dangerous Action"
                    )
                )
                
            # Get human approval
            self.console.print("\nProposed action:")
            self.console.print(
                Syntax(
                    json.dumps(action, indent=2),
                    "json",
                    theme="monokai",
                    word_wrap=True
                )
            )
            
            return Confirm.ask("Approve this action?")
            
        except Exception as e:
            self.logger.error(f"Action validation failed: {e}")
            return False
            
    def format_history(self) -> List[Dict[str, Any]]:
        """Format the agent's action and result history, ensuring serializability."""
        formatted_history = []

        for entry in self.state.history:
            action = entry.get("action", {})
            result = entry.get("result", {}) # Get potentially non-serializable result

            serializable_result = self._make_serializable(result) # Make it serializable

            formatted_history.append({
                "action": action, # Assuming action is already serializable (usually dict)
                "result": serializable_result,
                "timestamp": entry.get("timestamp", datetime.now().isoformat())
            })

        return formatted_history
        
    def get_final_answer(self) -> Dict[str, Any]:
        """Get the final analysis answer."""
        if not self.state or not self.state.history:
            return {"error": "No analysis has been performed yet."}
            
        # Look for final answer in history
        for entry in reversed(self.state.history):
            if entry.get("final_answer"):
                return {
                    "success": True,
                    "answer": entry.get("final_answer"),
                    "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                    "metadata": {
                        "iterations": len(self.state.history),
                        "session_id": self.state.session_id
                    }
                }
        
        # If no final answer, return the last observation
        if self.state.history:
            last_entry = self.state.history[-1]
            return {
                "success": True,
                "answer": last_entry.get("observation", "Analysis complete, but no final answer was provided."),
                "timestamp": last_entry.get("timestamp", datetime.now().isoformat()),
                "metadata": {
                    "iterations": len(self.state.history),
                    "session_id": self.state.session_id,
                    "is_final": False
                }
            }
            
        return {
            "success": False,
            "error": "No analysis data available",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "session_id": self.state.session_id if self.state else None
            }
        }
        
    def _build_system_prompt(self) -> str:
        """Constructs the system prompt using templates."""
        base_template = get_prompt_template("base")
        tools_template = get_prompt_template("tools")
        format_template = get_prompt_template("format")

        tool_descriptions = self._get_tool_descriptions()
        if "Error retrieving" in tool_descriptions or "No tool descriptions available" in tool_descriptions:
             self.logger.warning("Could not get tool descriptions for system prompt.")
             tool_descriptions = "Tool descriptions are currently unavailable."

        # Combine templates
        system_prompt = f"{base_template}\n{tools_template.format(tool_descriptions=tool_descriptions)}\n{format_template}"
        return system_prompt

    def _build_user_prompt(self, initial_context: Dict[str, Any], feedback: Optional[str] = None) -> str:
        """Builds the user prompt including the question, context, and history."""
        history_items = []
        action_counter = 1

        # Use the serializable history method
        history = self._get_serializable_history()

        for interaction in history:
            # Only include tool interactions (action + result) in the prompt history
            if interaction["role"] == "tool" and "action" in interaction:
                action_str = json.dumps(interaction["action"], indent=2)
                result_str = json.dumps(interaction["content"], indent=2, cls=ToolResultEncoder)

                history_items.append(f"Action {action_counter}:\n```json\n{action_str}\n```")
                history_items.append(f"Result:\n```json\n{result_str}\n```")
                action_counter += 1

        history_str = "\n\n".join(history_items)
        # Sanitize context slightly for prompt display
        prompt_context = {k: v for k, v in initial_context.items() if k != 'tools'} # Exclude redundant tool list
        context_str = json.dumps(prompt_context, indent=2)

        # Construct the final prompt string
        prompt_parts = [
            f"Question: {initial_context.get('question', 'N/A')}",
            f"\nContext:\n{context_str}",
            f"\nAction History:\n{history_str}" if history_str else "\nAction History:\n(No actions taken yet)"
        ]

        # Add feedback if provided
        if feedback:
             prompt_parts.append(f"\n\nFeedback on last step: {feedback}")

        user_prompt = "\n\n".join(prompt_parts)

        # Ensure the prompt is not empty
        if not user_prompt.strip():
             self.logger.warning("Generated user prompt is empty.")
             return "Please analyze the initial question and context." # Fallback prompt

        return user_prompt

    def _parse_llm_response(self, llm_response_json_str: str) -> Dict[str, Any]:
        """Parses the JSON block from the LLM response into a dictionary."""
        try:
            # Clean the string: remove potential ```json ... ``` markers if present
            cleaned_str = re.sub(r"^```json\s*|\s*```$", "", llm_response_json_str.strip(), flags=re.MULTILINE)
            parsed = json.loads(cleaned_str)

            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON is not a dictionary.")

            if "type" not in parsed or parsed["type"] not in ["action", "final_answer"]:
                 raise ValueError("Missing or invalid 'type' field in LLM response.")

            if parsed["type"] == "action":
                if "action" not in parsed or not isinstance(parsed["action"], dict):
                     raise ValueError("Missing or invalid 'action' dictionary for type 'action'.")
                if "tool" not in parsed["action"]:
                     raise ValueError("Missing 'tool' field in 'action' dictionary.")
                if "parameters" not in parsed["action"]:
                     parsed["action"]["parameters"] = {} # Ensure parameters dict exists
                elif not isinstance(parsed["action"]["parameters"], dict):
                     raise ValueError("'parameters' field must be a dictionary.")

            elif parsed["type"] == "final_answer":
                 required_keys = ["main_response", "confidence", "reasoning"]
                 for key in required_keys:
                     if key not in parsed:
                         raise ValueError(f"Missing required key '{key}' for 'final_answer'.")
                 if "next_steps" not in parsed: parsed["next_steps"] = []
                 if "analyzed_components" not in parsed: parsed["analyzed_components"] = []

            self.logger.info(f"Successfully parsed LLM response type: {parsed['type']}")
            return parsed
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode LLM JSON response: {e}\nResponse: {llm_response_json_str}", exc_info=True)
            raise LLMResponseError(f"Invalid JSON format in LLM response: {e}") from e
        except ValueError as e:
            self.logger.error(f"Invalid structure in LLM JSON response: {e}\nResponse: {llm_response_json_str}", exc_info=True)
            raise LLMResponseError(f"Invalid JSON structure in LLM response: {e}") from e
        except Exception as e:
             self.logger.error(f"Unexpected error parsing LLM response: {e}\nResponse: {llm_response_json_str}", exc_info=True)
             raise LLMResponseError(f"Unexpected error parsing LLM response: {e}") from e

    def _extract_reasoning_and_json(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts reasoning text and the JSON block from LLM response."""
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_block = json_match.group(1).strip()
            reasoning_text = text[:json_match.start()].strip()
            return reasoning_text if reasoning_text else None, json_block
        else:
            self.logger.warning("Could not find JSON block in LLM response.")
            # Attempt to find *any* JSON object if ```json``` block is missing
            try:
                first_brace = text.find('{')
                last_brace = text.rfind('}')
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    potential_json = text[first_brace:last_brace+1]
                    # Quick validation
                    json.loads(potential_json) 
                    self.logger.info("Found JSON object without ```json``` markers.")
                    reasoning = text[:first_brace].strip()
                    return reasoning if reasoning else None, potential_json
            except (json.JSONDecodeError, Exception):
                pass # Ignore if parsing fails
            # Fallback: return whole text as reasoning
            return text.strip(), None

    def _get_user_confirmation(self, action: Dict[str, Any]) -> bool:
        """Asks the user for confirmation before executing an action."""
        # Check configuration first
        if AUTO_APPROVE_ACTIONS:
            self.logger.info("Auto-approving action based on configuration.")
            return True
        if not HITL_ENABLED:
             self.logger.info("HITL disabled, auto-approving action.")
             return True

        tool_name = action.get("tool", "Unknown Tool")
        is_dangerous = tool_name in DANGEROUS_ACTIONS
        is_safe = tool_name in SAFE_ACTIONS

        if HITL_AUTO_APPROVE_SAFE_ACTIONS and is_safe and not is_dangerous:
             self.logger.info(f"Auto-approving safe action: {tool_name}")
             return True

        # Display action details to the user
        self.console.print("\n" + "-" * 40)
        title = "[bold yellow]Proposed Action for Review[/bold yellow]"
        if is_dangerous:
             title = "[bold red]⚠️ DANGEROUS Action for Review ⚠️[/bold red]"
        elif is_safe:
             title = "[bold green]Safe Action Proposed[/bold green]"
             
        panel_content = (
            f"[bold]Tool:[/bold] {action.get('tool', 'N/A')}\n"
            f"[bold]Parameters:[/bold] {json.dumps(action.get('parameters', {}), indent=2)}\n"
            f"[bold]Reasoning:[/bold] {action.get('reasoning', 'N/A')}"
        )
        self.console.print(Panel(panel_content, title=title, border_style="yellow" if not is_safe and not is_dangerous else ("red" if is_dangerous else "green")))
        self.console.print("-" * 40)
        
        # Loop for user input
        while True:
            try:
                response = Prompt.ask(
                    "Approve execution?", 
                    choices=["yes", "no", "details", "abort"],
                    default="yes"
                ).lower()
                
                if response == "yes":
                    return True
                elif response == "no":
                    # User rejected, provide feedback to LLM in next iteration
                    self.logger.info(f"User rejected action: {tool_name}")
                    # The rejection feedback will be handled by the main loop sending 'feedback'
                    raise ReActAbortError(f"User rejected action: {tool_name}") # Raise specific error
                elif response == "abort":
                     self.logger.info("User chose to abort the analysis.")
                     raise ReActAbortError("User aborted execution.")
                elif response == "details":
                    # Show full JSON if requested
                    self.console.print("[bold]Full Action Details:[/bold]")
                    self.console.print(Syntax(json.dumps(action, indent=2), "json", theme="default", line_numbers=True))
                else:
                     # Should not happen with Prompt.ask choices
                     self.console.print("[red]Invalid input.[/red]") 
                     
            except KeyboardInterrupt:
                 self.logger.warning("User interrupted confirmation prompt. Aborting.")
                 raise ReActAbortError("User aborted execution via KeyboardInterrupt.")
            except EOFError:
                 self.logger.warning("EOFError encountered during user input. Aborting.")
                 raise ReActAbortError("Execution aborted due to closed input stream.")

    def _make_serializable(self, data: Any) -> Any:
        """Attempts to make various data types JSON serializable."""
        # Handle ToolResult first if it's directly passed
        if isinstance(data, ToolResult):
             try:
                  return data.to_dict() # Assuming ToolResult has a to_dict method
             except AttributeError:
                  self.logger.warning("ToolResult object does not have a to_dict method. Converting to string.")
                  return str(data)
             except Exception as e:
                  self.logger.error(f"Error converting ToolResult to dict: {e}", exc_info=True)
                  return f"Error serializing ToolResult: {e}"
        
        # Handle dictionaries, potentially containing ToolResult
        elif isinstance(data, dict):
            serializable_dict = {}
            for k, v in data.items():
                serializable_dict[k] = self._make_serializable(v)
            return serializable_dict
        
        # Handle lists
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        
        # Basic types that are already serializable
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        
        # Fallback: Convert unknown types to string after attempting direct serialization
        else:
            try:
                 json.dumps(data)
                 return data # If it works, return as is
            except (TypeError, OverflowError):
                 self.logger.warning(f"Data of type {type(data)} is not directly JSON serializable. Converting to string.")
                 return str(data)

    def _get_serializable_history(self) -> List[Dict[str, Any]]:
        """Returns the interaction history in a serializable format."""
        serializable_history = []
        # Adjust based on whether self.state is ReActState or AgentState
        history_list = self.state.history if hasattr(self.state, 'history') else []
        
        for interaction in history_list:
            # Ensure interaction is a dictionary before proceeding
            if not isinstance(interaction, dict):
                 self.logger.warning(f"Skipping non-dictionary item in history: {interaction}")
                 continue
                 
            role = interaction.get("role")
            content = interaction.get("content")
            action = interaction.get("action") # May be None
            
            serializable_content = self._make_serializable(content)
            entry = {"role": role, "content": serializable_content}
            
            if action:
                 serializable_action = self._make_serializable(action)
                 entry["action"] = serializable_action
                 
            serializable_history.append(entry)
        return serializable_history

    def _get_tool_descriptions(self) -> str:
        """Gets formatted descriptions of all registered tools."""
        try:
            # Assuming self.tools is the ToolRegistry instance
            descriptions = self.tools.get_tool_descriptions()
            if not descriptions:
                self.logger.warning("No tool descriptions found in ToolRegistry.")
                return "No tool descriptions available."
            
            formatted_desc = []
            for name, desc_data in descriptions.items():
                description = desc_data.get('description', 'No description')
                parameters = desc_data.get('parameters')
                formatted_desc.append(f"- `{name}`: {description}")
                if parameters:
                    # Simple parameter formatting
                    param_str = ", ".join([f"{k} ({v.get('type', 'any')})" for k, v in parameters.items()])
                    formatted_desc.append(f"  Parameters: {param_str}")
            
            return "\n".join(formatted_desc) if formatted_desc else "No tool descriptions available."
        except Exception as e:
            self.logger.error(f"Failed to get tool descriptions: {e}", exc_info=True)
            return "Error retrieving tool descriptions."

    def reset_state(self):
        """Resets the agent's internal state for a new analysis session."""
        # Log the previous session ID if it exists
        if self.state and self.state.session_id:
            self.logger.info(f"Resetting agent state from session {self.state.session_id}")

        new_session_id = str(uuid.uuid4())
        self.state = AgentState(
            session_id=new_session_id,
            history=[],
            context={},
            max_iterations=MAX_ITERATIONS,
            current_iteration=0,
            last_tool_result=None,
            start_time=datetime.now()
        )

        # Ensure execution logger is setup *after* state is reset
        # Assuming _setup_execution_logger uses self.state.session_id
        if hasattr(self, '_setup_execution_logger'):
             self.execution_logger = self._setup_execution_logger(self.state.session_id)
        else:
             # Placeholder if the method isn't defined yet or handled elsewhere
             self.execution_logger = logging.getLogger(f"execution_{new_session_id}")
             # Add basic configuration if needed, e.g., handler, formatter

        # Log the *new* session ID
        self.logger.info(f"Agent state reset. New session ID: {self.state.session_id}")
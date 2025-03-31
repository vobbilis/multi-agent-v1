# Proposal for Enhanced Kubernetes Analyzer Output and Interaction

## 1. Goal

This proposal outlines changes to the `k8s_analyzer` project to:

1.  **Standardize Output**: Align the final analysis result format with the detailed JSON structure defined in `tool_output.md`.
2.  **Enhance HITL Interaction**: Improve the Human-In-The-Loop (HITL) model to present the structured analysis (`actions`, `next_steps`) to the user for review and potential follow-up, inspired by the concepts likely present in `/home/opsramp/go/src/github.com/vobbilis/k8s-labeler/anthropic/v2/k8s_analyzer_client_v2.py`.

## 2. Current State Analysis

*   **Output Format**:
    *   The primary output object (`AnalysisResult`) currently holds basic `success`, `answer`, `error`, `metadata`, `context`, and `interactions`.
    *   The internal ReAct agent produces a `final_answer` JSON blob containing `type`, `main_response`, `confidence`, `reasoning`, `next_steps`, and `analyzed_components`.
    *   Neither of these fully matches the target structure in `tool_output.md`, lacking fields like `session_id`, prioritized `actions` with commands, detailed `metadata.cluster_stats`, and categorized `next_steps`.
*   **Interaction Model**:
    *   The current HITL mechanism (within `ReActAgent`'s `execute_action`) prompts the user *before executing intermediate tool calls* (like `check_node_status`) if run interactively.
    *   It does *not* currently present the final, structured analysis result (with prioritized actions and categorized next steps) for user review or action execution after the analysis is complete. The interaction is focused on approving the *process* rather than reviewing the *outcome*.

## 3. Proposed Changes

### 3.1. Result Structure Overhaul

*   **Modify/Replace `AnalysisResult`**: Update `k8s_analyzer.core.analyzer.AnalysisResult` (or create a dedicated class) to precisely mirror the `tool_output.md` JSON structure.
    *   **Add Fields**: Introduce `session_id`, `actions` (list of dictionaries with `priority`, `component`, `description`, `command`), and ensure `next_steps` (list of dictionaries with `id`, `category`, `description`, `rationale`) and `metadata` (with nested `cluster_stats`, `analysis_timestamp`, `analyzed_components`) match the specification.
    *   **Mapping**: Potentially map existing concepts like `critical_points` or `pressure_points` to the new `actions` list, implementing prioritization logic.

### 3.2. ReAct Agent Final Output Generation

*   **Adjust Final LLM Prompt**: Modify the final prompt used by `ReActAgent` when generating the `final_answer`. The prompt should explicitly request the LLM to structure its final analysis according to the `tool_output.md` JSON format.
*   **Enhance Aggregation & Analysis**: The agent must reliably:
    *   Aggregate data from all tool calls executed during the analysis.
    *   Analyze the aggregated data to identify specific issues, assign priorities (`HIGH`, `MEDIUM`, `LOW`) to create the `actions` list, and suggest relevant `kubectl` commands.
    *   Generate categorized `next_steps` (`INVESTIGATE`, `OPTIMIZE`, `MONITOR`) with clear rationale.
    *   Extract or calculate data for `metadata.cluster_stats`.
*   **Populate New Structure**: Ensure the agent correctly populates the new `AnalysisResult` structure based on the LLM's structured output.

### 3.3. Presentation & HITL Enhancement

*   **Update `__main__.py`**:
    *   Modify `display_analysis_result` to present the new structured data clearly (e.g., using `rich` Tables for `actions` and `next_steps`).
    *   Update the `--format json` output to serialize the new `AnalysisResult` structure correctly.
*   **Implement Final Review HITL (Option B - Local CLI Client)**: The `k8s_analyzer` core will focus on generating the structured `AnalysisResult` JSON. The local CLI (`__main__.py`) will act as the initial interactive client for the HITL process. After receiving the structured result, `__main__.py` will:
    *   Parse the `actions` and `next_steps`.
    *   Present these clearly to the user (e.g., using `rich` Tables).
    *   Prompt the user interactively if they want to execute any of the suggested `kubectl` commands listed in the `actions`. If approved, `__main__.py` will invoke the necessary `kubectl` execution logic (potentially reusing parts of the `kubectl` tool).
    *   This keeps the core analyzer focused on generation, while the CLI handles the final user interaction based on the structured output. A server/client architecture can be considered later.

### 3.4. Potential New Tools/Logic

*   **Cluster Stats Tool**: May need a new tool or logic within existing tools (e.g., `kubectl`) to efficiently gather statistics required for `metadata.cluster_stats` (node count, pod counts by status, namespace count).
*   **Prioritization/Categorization Logic**: Implement logic (either via LLM prompting or coded rules) to consistently assign priorities to `actions` and categories to `next_steps`.

## 4. Benefits

*   **Clarity**: Provides a much clearer, structured, and actionable overview of the cluster state.
*   **Actionability**: Directly links findings to suggested investigation commands (`actions`) and follow-up strategies (`next_steps`).
*   **User Control**: Enhances the HITL aspect by allowing users to review the final analysis and decide on immediate investigation steps based on suggested commands.
*   **Standardization**: Adopts a well-defined output schema suitable for programmatic consumption by other tools or dashboards.

## 5. Implementation Sketch

*   **`k8s_analyzer/core/analyzer.py`**: Modify `AnalysisResult` class definition. Update `EnhancedClusterAnalyzer.analyze_question` to return the new structure.
*   **`k8s_analyzer/react/agent.py`**: Modify `ReActAgent._build_final_prompt` (or similar) to request the new JSON format. Update logic that processes the LLM's final response to parse and populate the new `AnalysisResult` fields.
*   **`k8s_analyzer/__main__.py`**: Update `display_analysis_result` and JSON serialization logic. Potentially add interactive prompts for executing action commands (if Option 3.3.A is chosen).
*   **`k8s_analyzer/tools/`**: Potentially add a new tool for cluster stats or modify existing tools.

## 6. Open Questions

*   **HITL Implementation**: The decision is to implement **Option B (Client-Focused)**, with the local CLI (`__main__.py`) serving as the initial client responsible for parsing the structured output and managing the final interactive review and command execution phase.
*   **Prioritization/Categorization Source**: Determine whether the LLM should be responsible for assigning priorities/categories based on prompted instructions, or if this should be implemented with explicit rules in the Python code after receiving the LLM analysis. LLM might be more flexible but potentially less consistent. 
import os
from dotenv import load_dotenv

# --- Tool Class Imports ---
# Keep only KubectlTool import if needed elsewhere, or remove if only analyzer used it
# from ..tools.kubectl import KubectlTool 
# REMOVE ANALYZER IMPORTS
# from .analyzer import (
#     ClusterHealthAnalyzer,
#     ResourceAnalyzer,
#     WorkloadAnalyzer,
#     NetworkAnalyzer,
#     SecurityAnalyzer,
#     StorageAnalyzer,
#     MaintenanceAnalyzer
# )
# --- End Tool Class Imports ---

# Load environment variables
load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", ""))  # For backward compatibility
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))  # Default max tokens
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))  # Default temperature

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Default Models
DEFAULT_OPENAI_MODEL = "gpt-4-mini"
DEFAULT_GEMINI_MODEL = "gemini-1.5-pro-latest"

# Logging Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'k8s_analyzer_enhanced.log'

# Deprecated? Keep for reference or remove if unused
TOOL_NAMES = {
    "health_analyzer": "ClusterHealthAnalyzer",
    "resource_analyzer": "ResourceAnalyzer",
    "workload_analyzer": "WorkloadAnalyzer",
    "network_analyzer": "NetworkAnalyzer",
    "security_analyzer": "SecurityAnalyzer",
    "storage_analyzer": "StorageAnalyzer",
    "maintenance_analyzer": "MaintenanceAnalyzer"
}

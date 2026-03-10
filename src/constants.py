"""
Global Constants for SpamGuard

Centralized configuration for all hardcoded values, timeouts, and thresholds.
Makes the codebase easier to maintain and tune.
"""

# ============================================
# IMAP Connection Settings
# ============================================

IMAP_CONNECTION_TIMEOUT = 10  # seconds - timeout for IMAP connection
IMAP_PORT_DEFAULT = 993  # Standard IMAP SSL port

# ============================================
# LLM & Ollama Settings
# ============================================

# Timeout for LLM inference requests
LLM_INFERENCE_TIMEOUT = 120  # seconds

# Timeout for LLM model warmup/initialization
LLM_WARMUP_TIMEOUT = 60  # seconds

# Token generation parameters
LLM_NUM_PREDICT_FAST = 150  # Fast inference mode
LLM_NUM_PREDICT_THINKING = 2000  # Extended thinking mode

# Ollama availability check timeout
OLLAMA_CHECK_TIMEOUT = 3  # seconds

# ============================================
# HTTP & Network Settings
# ============================================

HTTP_STATUS_OK = 200  # Standard HTTP OK response code

# Timeout for downloading external blacklists
EXTERNAL_LIST_DOWNLOAD_TIMEOUT = 30  # seconds

# Number of retry attempts for failed downloads
EXTERNAL_LIST_DOWNLOAD_RETRIES = 3

# Exponential backoff delays between retries
EXTERNAL_LIST_RETRY_BACKOFF_SECONDS = [1, 5, 15]

# Maximum size of external blacklist files
MAX_EXTERNAL_LIST_SIZE_BYTES = 50_000_000  # 50MB

# ============================================
# List Management Settings
# ============================================

# Maximum length of an individual list entry (email or domain)
MAX_LIST_ENTRY_LENGTH = 255  # characters

# Update interval for external blacklists
EXTERNAL_LIST_UPDATE_INTERVAL_HOURS = 24

# ============================================
# Email Processing Settings
# ============================================

# Maximum length of email body preview for LLM analysis
EMAIL_PREVIEW_MAX_LENGTH = 1000  # characters

# Maximum display length for email subjects
MAX_EMAIL_SUBJECT_LENGTH = 60  # characters (for display truncation)

# Maximum display length for email subjects in summaries
MAX_SUMMARY_SUBJECT_LENGTH = 70  # characters

# Number of subjects to show per sender in summary
MAX_SUBJECTS_TO_SHOW = 3

# ============================================
# Spam Detection Sensitivity
# ============================================

# Temperature parameter for LLM (lower = more deterministic)
LLM_TEMPERATURE = 0.1  # Range: 0.0 (deterministic) to 1.0 (random)

# ============================================
# Logging & Output
# ============================================

# Log level for IMAP debug messages
IMAP_DEBUG_LEVEL = False  # Set to True for verbose debugging

# ============================================
# Feature Flags (for future use)
# ============================================

# Enable experimental features
ENABLE_EXPERIMENTAL_FEATURES = False

# Enable detailed profiling
ENABLE_PROFILING = False

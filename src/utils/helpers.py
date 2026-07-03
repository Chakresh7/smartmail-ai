"""
Helper utilities for SmartMail AI.

Includes text processing, token counting, logging setup,
error handling, and other utility functions.
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from functools import wraps
import hashlib

try:
    import tiktoken
except ImportError:
    tiktoken = None


# ============ Logging Setup ============
def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    format_style: str = "json"
) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None = console only)
        format_style: Log format (json or text)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("smartmail_ai")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Format
    if format_style == "json":
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s: %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# ============ Token Counting ============
def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Count tokens in text for a given model.
    
    Args:
        text: Text to count tokens for
        model: Model name (gpt-3.5-turbo, gpt-4, etc.)
    
    Returns:
        Number of tokens
    """
    if not tiktoken:
        # Fallback: rough estimate (1 token ≈ 4 chars)
        return len(text) // 4
    
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback for unknown models
        return len(text) // 4


def estimate_cost(
    tokens: int,
    model: str = "gpt-3.5-turbo",
    input_cost_per_1k: float = 0.0005,
    output_cost_per_1k: float = 0.0015
) -> float:
    """
    Estimate API cost for token usage.
    
    Args:
        tokens: Number of tokens
        model: Model name
        input_cost_per_1k: Cost per 1k input tokens
        output_cost_per_1k: Cost per 1k output tokens
    
    Returns:
        Estimated cost in dollars
    """
    # Rough estimate: assume 30% of tokens are output
    input_tokens = int(tokens * 0.7)
    output_tokens = int(tokens * 0.3)
    
    return (input_tokens / 1000) * input_cost_per_1k + \
           (output_tokens / 1000) * output_cost_per_1k


# ============ Text Processing ============
def clean_email_text(text: str) -> str:
    """
    Clean email text by removing quotes, signatures, etc.
    
    Args:
        text: Raw email text
    
    Returns:
        Cleaned text
    """
    lines = text.split("\n")
    cleaned_lines = []
    in_quote = False
    
    for line in lines:
        # Skip common signature patterns
        if any(pattern in line.lower() for pattern in [
            "-- ", "sent from", "regards,", "thanks,", "best regards",
            "sincerely,", "___", "---"
        ]):
            in_quote = True
        
        # Skip quoted text (lines starting with >)
        if line.strip().startswith(">"):
            in_quote = True
            continue
        
        if not in_quote and line.strip():
            cleaned_lines.append(line)
    
    cleaned_text = "\n".join(cleaned_lines).strip()
    
    # Remove extra whitespace
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    cleaned_text = re.sub(r" {2,}", " ", cleaned_text)
    
    return cleaned_text


def extract_email_addresses(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to search
    
    Returns:
        List of email addresses
    """
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return list(set(re.findall(pattern, text)))


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Text to search
    
    Returns:
        List of URLs
    """
    pattern = r"https?://[^\s]+"
    return re.findall(pattern, text)


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text with ellipsis
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


# ============ JSON Parsing ============
def safe_json_parse(text: str, default: Any = None) -> Any:
    """
    Safely parse JSON from text, returning default on error.
    
    Args:
        text: JSON text
        default: Default value if parsing fails
    
    Returns:
        Parsed JSON or default
    """
    try:
        # Try to find JSON in curly braces
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return default
    except json.JSONDecodeError:
        return default


def extract_json_objects(text: str) -> List[Dict[str, Any]]:
    """
    Extract all JSON objects from text.
    
    Args:
        text: Text containing JSON
    
    Returns:
        List of parsed JSON objects
    """
    objects = []
    # Find all JSON-like patterns
    pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    matches = re.finditer(pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            obj = json.loads(match.group())
            objects.append(obj)
        except json.JSONDecodeError:
            continue
    
    return objects


def extract_text_from_response(resp: Any) -> str:
    """Best-effort extractor to obtain textual content from various LLM SDK responses.

    Handles common shapes returned by different SDKs:
    - New OpenAI Responses objects with `.output` or `.output_text`
    - Legacy `choices` lists with `text` or `message` fields
    - Dict-shaped responses
    - Objects with `choices` attribute

    Falls back to `str(resp)` when shape is unknown.
    """
    try:
        # dict-like responses
        if isinstance(resp, dict):
            if "output_text" in resp:
                return resp["output_text"]
            if "output" in resp:
                out = resp["output"]
                if isinstance(out, list):
                    parts = []
                    for item in out:
                        if isinstance(item, dict) and "content" in item:
                            for c in item["content"]:
                                if isinstance(c, dict):
                                    parts.append(c.get("text", ""))
                                else:
                                    parts.append(str(c))
                        else:
                            parts.append(str(item))
                    return "\n".join(parts)
            if "choices" in resp:
                parts = []
                for c in resp.get("choices", []):
                    if isinstance(c, dict):
                        if "text" in c:
                            parts.append(c["text"])
                        elif "message" in c:
                            msg = c["message"]
                            if isinstance(msg, dict):
                                content = msg.get("content") or ""
                                if isinstance(content, list):
                                    for cc in content:
                                        if isinstance(cc, dict):
                                            parts.append(cc.get("text", ""))
                                        else:
                                            parts.append(str(cc))
                                else:
                                    parts.append(str(content))
                return "\n".join(parts)

        # object-like responses
        val = getattr(resp, "output_text", None)
        if isinstance(val, (str, bytes)):
            return val

        out = getattr(resp, "output", None)
        if isinstance(out, (list, dict)):
            if isinstance(out, list):
                parts = []
                for item in out:
                    if isinstance(item, dict) and "content" in item:
                        for c in item["content"]:
                            if isinstance(c, dict):
                                parts.append(c.get("text", ""))
                            else:
                                parts.append(str(c))
                    else:
                        parts.append(str(item))
                return "\n".join(parts)
            return str(out)

        choices_val = getattr(resp, "choices", None)
        if isinstance(choices_val, (list, tuple)):
            parts = []
            for ch in choices_val:
                if hasattr(ch, "text") and isinstance(getattr(ch, "text"), (str, bytes)):
                    parts.append(getattr(ch, "text"))
                elif isinstance(ch, dict) and "text" in ch:
                    parts.append(ch["text"])
            if parts:
                return "\n".join(parts)

        # Fallback
        return str(resp)
    except Exception:
        return str(resp)


# ============ Error Handling ============
class SmartMailException(Exception):
    """Base exception for SmartMail AI."""
    pass


class ConfigurationError(SmartMailException):
    """Raised when configuration is invalid."""
    pass


class APIError(SmartMailException):
    """Raised when API call fails."""
    pass


class ProcessingError(SmartMailException):
    """Raised during email processing."""
    pass


class RAGError(SmartMailException):
    """Raised during RAG operations."""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_multiplier: float = 2.0
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Initial delay in seconds
        backoff_multiplier: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    logging.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    import time
                    time.sleep(delay)
                    delay *= backoff_multiplier
        return wrapper
    return decorator


# ============ Data Hashing ============
def hash_email(email_id: str, sender: str, subject: str) -> str:
    """
    Create consistent hash for email.
    
    Args:
        email_id: Email ID
        sender: Sender address
        subject: Email subject
    
    Returns:
        Hash string
    """
    content = f"{email_id}:{sender}:{subject}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============ Time Utilities ============
def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


def parse_iso_datetime(date_string: str) -> Optional[datetime]:
    """
    Parse ISO format datetime string.
    
    Args:
        date_string: ISO format datetime
    
    Returns:
        Parsed datetime or None
    """
    try:
        return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


# ============ Formatting ============
def format_email_for_display(
    subject: str,
    sender: str,
    body: str,
    max_body_length: int = 500
) -> str:
    """
    Format email for dashboard display.
    
    Args:
        subject: Email subject
        sender: Sender email
        body: Email body
        max_body_length: Maximum body length to display
    
    Returns:
        Formatted email string
    """
    preview = truncate_text(body, max_body_length)
    return f"From: {sender}\nSubject: {subject}\n\n{preview}"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable form.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., "1m 23s")
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"

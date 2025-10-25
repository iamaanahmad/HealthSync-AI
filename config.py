"""
Configuration settings for HealthSync agents.
"""

import os
from typing import Dict, Any

# Agent configuration
AGENT_CONFIG = {
    "patient_consent": {
        "port": 8001,
        "name": "Patient Consent Agent",
        "description": "Manages patient data sharing permissions with granular control"
    },
    "data_custodian": {
        "port": 8002,
        "name": "Data Custodian Agent",
        "description": "Represents healthcare institutions and validates data access requests"
    },
    "research_query": {
        "port": 8003,
        "name": "Research Query Agent", 
        "description": "Processes research queries and orchestrates data retrieval"
    },
    "privacy": {
        "port": 8004,
        "name": "Privacy Agent",
        "description": "Performs data anonymization and ensures privacy compliance"
    },
    "metta_integration": {
        "port": 8005,
        "name": "MeTTa Integration Agent",
        "description": "Manages knowledge graph operations and reasoning"
    }
}

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# MeTTa configuration
METTA_CONFIG = {
    "host": os.getenv("METTA_HOST", "localhost"),
    "port": int(os.getenv("METTA_PORT", "8080")),
    "timeout": int(os.getenv("METTA_TIMEOUT", "30"))
}

# Chat Protocol configuration
CHAT_CONFIG = {
    "session_timeout": int(os.getenv("CHAT_SESSION_TIMEOUT", "3600")),  # 1 hour
    "max_message_size": int(os.getenv("CHAT_MAX_MESSAGE_SIZE", "10240"))  # 10KB
}

# Privacy configuration
PRIVACY_CONFIG = {
    "k_anonymity_threshold": int(os.getenv("K_ANONYMITY_THRESHOLD", "5")),
    "max_suppression_rate": float(os.getenv("MAX_SUPPRESSION_RATE", "0.1")),  # 10%
    "encryption_key_size": int(os.getenv("ENCRYPTION_KEY_SIZE", "256"))
}

# Error handling configuration
ERROR_CONFIG = {
    "circuit_breaker_threshold": int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")),
    "circuit_breaker_timeout": int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60")),
    "max_retry_attempts": int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
    "retry_base_delay": float(os.getenv("RETRY_BASE_DELAY", "1.0"))
}

# Agentverse configuration
AGENTVERSE_CONFIG = {
    "registration_endpoint": os.getenv("AGENTVERSE_ENDPOINT", "https://agentverse.ai"),
    "api_key": os.getenv("AGENTVERSE_API_KEY", ""),
    "project_id": os.getenv("AGENTVERSE_PROJECT_ID", "healthsync"),
    "badges": ["Innovation Lab", "ASI Alliance Hackathon"]
}

def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get configuration for specific agent."""
    return AGENT_CONFIG.get(agent_name, {})

def get_all_config() -> Dict[str, Any]:
    """Get all configuration settings."""
    return {
        "agents": AGENT_CONFIG,
        "logging": {
            "level": LOG_LEVEL,
            "directory": LOG_DIR
        },
        "metta": METTA_CONFIG,
        "chat": CHAT_CONFIG,
        "privacy": PRIVACY_CONFIG,
        "error_handling": ERROR_CONFIG,
        "agentverse": AGENTVERSE_CONFIG
    }
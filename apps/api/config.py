"""
Configuration management using Pydantic Settings.

All configuration loaded from environment variables or .env file.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    LOG_LEVEL: str = "INFO"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./clustercloud.db"
    
    # Authentication & Security
    JWT_SECRET: str = "your-secret-key-here-change-in-production"
    NODE_API_KEY: Optional[str] = None  # Master API key for node authentication
    ENABLE_NODE_AUTH: bool = False  # Enable in production
    
    # Resource Limits (MVP - soft limits)
    MAX_TASK_MEMORY_MB: int = 2048  # 2GB per task
    MAX_TASK_CPU_CORES: float = 2.0  # 2 CPU cores per task
    MAX_TASK_DISK_MB: int = 5120  # 5GB disk per task
    
    # Security Settings
    ENABLE_DOCKER_ISOLATION: bool = True
    DOCKER_SECURITY_OPT: str = "no-new-privileges:true"
    EPHEMERAL_FILE_RETENTION_HOURS: int = 24
    
    # AWS Bedrock Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Node Agent Configuration
    HEARTBEAT_INTERVAL_SECONDS: int = 5
    MAX_CONCURRENT_TASKS: int = 2
    
    # Workload Execution
    DOCKER_NETWORK: str = "clustercloud_network"
    WORKLOAD_TIMEOUT_SECONDS: int = 300
    TASK_TIMEOUT_SECONDS: int = 120
    
    # Tokenomics (CLSTR)
    INITIAL_CUSTOMER_BALANCE: int = 10000
    PROVIDER_RELIABILITY_STAKE: int = 100
    BROKER_FEE_PERCENTAGE: int = 5
    FAILURE_PENALTY_PERCENTAGE: int = 20
    RECOVERY_REWARD_PERCENTAGE: int = 10
    
    # Monitoring & Reliability
    HEARTBEAT_TIMEOUT_SECONDS: int = 15
    MAX_TASK_RETRIES: int = 3
    NODE_HEALTH_CHECK_INTERVAL_SECONDS: int = 10
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()

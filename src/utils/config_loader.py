"""
Configuration Loader
Loads and validates YAML configuration with environment-specific overrides
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from utils.logger import get_logger
from utils.exception import ConfigurationError

logger = get_logger(__name__)


class AppConfig(BaseModel):
    """Application configuration schema"""
    name: str
    version: str
    description: str
    max_upload_size_mb: int = 50


class LoggingConfig(BaseModel):
    """Logging configuration schema"""
    level: str = "INFO"
    format: str
    date_format: str
    file_rotation: Dict[str, int]


class DocumentConfig(BaseModel):
    """Document processing configuration"""
    extraction_strategy: str = "hi_res"
    extract_images: bool = True
    extract_tables: bool = True
    infer_table_structure: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 200
    enable_ocr: bool = True
    ocr_dpi: int = 100


class EmbeddingsConfig(BaseModel):
    """Embeddings configuration"""
    provider: str = "ollama"
    model: str = "nomic-embed-text"
    dimensions: int = 768
    base_url: str = "http://localhost:11434"


class VectorStoreConfig(BaseModel):
    """Vector store configuration"""
    provider: str = "qdrant"
    collection_name: str = "ipdf_multimodal"
    distance_metric: str = "COSINE"
    search_limit: int = 5
    vector_size: int = 768


class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: str = "ollama"
    model: str = "llama3.2"
    temperature: float = 0.1
    max_tokens: int = 2048
    base_url: str = "http://localhost:11434"


class UIConfig(BaseModel):
    """UI configuration"""
    page_title: str = "iPDF - Chat with PDFs"
    page_icon: str = "📄"
    layout: str = "wide"
    sidebar_state: str = "expanded"
    pdf_viewer_height: int = 800
    chat_height: int = 600
    theme: Dict[str, str] = {}


class Config(BaseModel):
    """Main configuration model"""
    app: AppConfig
    logging: LoggingConfig
    document: DocumentConfig
    embeddings: EmbeddingsConfig
    vectorstore: VectorStoreConfig
    llm: LLMConfig
    ui: UIConfig
    
    class Config:
        arbitrary_types_allowed = True


class ConfigLoader:
    """Load and manage application configuration"""
    
    def __init__(self, config_dir: str = "config", environment: Optional[str] = None):
        """
        Initialize configuration loader
        
        Args:
            config_dir: Directory containing config files
            environment: Environment name (development, production, etc.)
        """
        load_dotenv()  # Load environment variables
        
        self.config_dir = Path(config_dir)
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self._config: Optional[Config] = None
        
        logger.info(f"Loading configuration for environment: {self.environment}")
    
    def load(self) -> Config:
        """
        Load configuration from YAML files
        
        Returns:
            Validated configuration object
        """
        try:
            # Load base configuration
            base_config = self._load_yaml(self.config_dir / "config.yaml")
            
            # Validate and create config object
            self._config = Config(**base_config)
            
            logger.info("Configuration loaded successfully")
            return self._config
        
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}", sys)
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to load {file_path}: {str(e)}", sys)
    
    @property
    def config(self) -> Config:
        """Get loaded configuration"""
        if self._config is None:
            self._config = self.load()
        return self._config


# Global config instance
_config_loader: Optional[ConfigLoader] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader.config

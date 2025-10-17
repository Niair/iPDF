"""
Model Manager - Manage different LLM models
"""
from typing import List, Dict, Any
import yaml
from pathlib import Path

from utils.logger import get_logger
from core.llm_handler import LLMHandler

logger = get_logger(__name__)


class ModelManager:
    """Manage available models"""
    
    def __init__(self, config_path: str = "config/models.yaml"):
        """
        Initialize model manager
        
        Args:
            config_path: Path to models configuration
        """
        self.config_path = Path(config_path)
        self.models = self._load_models()
        logger.info(f"ModelManager initialized with {len(self.models)} models")
    
    def _load_models(self) -> List[Dict[str, Any]]:
        """Load available models from config"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('llm_models', [])
        except Exception as e:
            logger.error(f"Failed to load models config: {str(e)}")
            return []
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return [model['name'] for model in self.models]
    
    def get_model_id(self, model_name: str) -> str:
        """Get model ID from name"""
        for model in self.models:
            if model['name'] == model_name:
                return model['model_id']
        return "llama3.2"  # Default
    
    def create_llm_handler(self, model_name: str) -> LLMHandler:
        """
        Create LLM handler for specific model
        
        Args:
            model_name: Model name
            
        Returns:
            LLMHandler instance
        """
        model_id = self.get_model_id(model_name)
        return LLMHandler(model=model_id)

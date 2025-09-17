# Configuration manager
import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AIConfig:
    """AI configuration settings"""
    model_name: str = "gemini-pro"
    temperature: float = 0.7
    max_tokens: int = 1000

@dataclass
class MPOBStandard:
    """MPOB standard definition"""
    parameter: str
    min_value: float
    max_value: float
    unit: str

@dataclass
class MPOBStandards:
    """MPOB standards collection"""
    standards: Dict[str, MPOBStandard]

@dataclass
class EconomicConfig:
    """Economic configuration"""
    currency: str = "MYR"
    fertilizer_prices: Dict[str, float] = None

@dataclass
class OCRConfig:
    """OCR configuration"""
    confidence_threshold: float = 0.8
    language: str = "en"
    preprocessing: bool = True

@dataclass
class UIConfig:
    """UI configuration"""
    theme: str = "light"
    sidebar_expanded: bool = True
    show_advanced: bool = False

class ConfigManager:
    """Configuration manager for the application"""
    
    def __init__(self):
        self.config_dir = "config"
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Ensure config directory exists"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def get_ai_config(self) -> AIConfig:
        """Get AI configuration"""
        return AIConfig()
    
    def get_mpob_standards(self) -> MPOBStandards:
        """Get MPOB standards"""
        return MPOBStandards(standards={})
    
    def get_economic_config(self) -> EconomicConfig:
        """Get economic configuration"""
        return EconomicConfig()
    
    def get_ocr_config(self) -> OCRConfig:
        """Get OCR configuration"""
        return OCRConfig()
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration"""
        return UIConfig()
    
    def save_config(self, config_type: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration"""
        try:
            config_path = os.path.join(self.config_dir, f"{config_type}.json")
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            return True
        except Exception:
            return False
    
    def load_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """Load configuration"""
        try:
            config_path = os.path.join(self.config_dir, f"{config_type}.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception:
            return None
    
    def reset_to_defaults(self, config_type: str) -> bool:
        """Reset configuration to defaults"""
        try:
            config_path = os.path.join(self.config_dir, f"{config_type}.json")
            if os.path.exists(config_path):
                os.remove(config_path)
            return True
        except Exception:
            return False

# Global config manager instance
config_manager = ConfigManager()

def get_ui_config() -> UIConfig:
    """Get UI configuration"""
    return config_manager.get_ui_config()

def get_ai_config() -> AIConfig:
    """Get AI configuration"""
    return config_manager.get_ai_config()

def get_mpob_standards() -> MPOBStandards:
    """Get MPOB standards"""
    return config_manager.get_mpob_standards()

def get_economic_config() -> EconomicConfig:
    """Get economic configuration"""
    return config_manager.get_economic_config()
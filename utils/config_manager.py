import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from .firebase_config import get_firestore_client, COLLECTIONS
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AIConfig:
    """AI model configuration for Google Gemini"""
    model: str = "gemini-2.5-pro"  # Best Gemini model
    temperature: float = 0.0
    max_tokens: int = 65536
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    embedding_model: str = "text-embedding-004"
    enable_rag: bool = True
    enable_caching: bool = True
    retry_attempts: int = 3
    timeout_seconds: int = 30
    confidence_threshold: float = 0.7

@dataclass
class MPOBStandard:
    """Individual MPOB standard parameter"""
    min: float
    max: float
    optimal: float
    unit: str
    description: str = ""
    critical: bool = False

@dataclass
class MPOBStandards:
    """Complete MPOB standards configuration"""
    name: str = "MPOB Standards"
    version: str = "1.0"
    region: str = "Malaysia"
    soil_standards: Dict[str, MPOBStandard] = None
    leaf_standards: Dict[str, MPOBStandard] = None
    active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class EconomicConfig:
    """Economic calculation configuration"""
    currency: str = "RM"
    yield_price_per_ton: float = 2500.0
    fertilizer_costs: Dict[str, float] = None
    application_costs: Dict[str, float] = None
    labor_costs: Dict[str, float] = None
    equipment_costs: Dict[str, float] = None
    inflation_rate: float = 0.03
    discount_rate: float = 0.08
    region: str = "Malaysia"
    updated_at: datetime = None

@dataclass
class OCRConfig:
    """OCR processing configuration"""
    psm_modes: List[int] = None
    character_whitelist: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,%-/()[]{}:;"
    scale_factor_min: float = 1.0
    scale_factor_max: float = 3.0
    contrast_enhancement: float = 1.5
    sharpness_enhancement: float = 2.0
    bilateral_filter_d: int = 9
    bilateral_filter_sigma_color: float = 75.0
    bilateral_filter_sigma_space: float = 75.0
    adaptive_threshold_block_size: int = 11
    adaptive_threshold_c: int = 2
    confidence_threshold: float = 0.7
    report_type_patterns: Dict[str, List[str]] = None

@dataclass
class UIConfig:
    """UI/UX configuration"""
    theme: str = "light"
    primary_color: str = "#2E8B57"
    secondary_color: str = "#228B22"
    accent_color: str = "#4CAF50"
    language: str = "English"
    date_format: str = "%Y-%m-%d"
    number_format: str = "en_US"
    units: Dict[str, List[str]] = None
    display_preferences: Dict[str, Any] = None

class ConfigManager:
    """Centralized configuration management system"""
    
    def __init__(self):
        self.db = get_firestore_client()
        self._cache = {}
        self._cache_expiry = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Initialize default configurations
        self._initialize_default_configs()

    def _ensure_db(self) -> bool:
        """Ensure Firestore client is available; try to (re)acquire lazily."""
        if not self.db:
            self.db = get_firestore_client()
        return self.db is not None
    
    def _initialize_default_configs(self):
        """Initialize default configurations if they don't exist"""
        try:
            if not self._ensure_db():
                logger.warning("Database connection not available; skipping default config initialization")
                return
            # Check if configurations exist, if not create defaults
            if not self._config_exists('ai_config'):
                self._create_default_ai_config()
            
            if not self._config_exists('mpob_standards'):
                self._create_default_mpob_standards()
            
            if not self._config_exists('economic_config'):
                self._create_default_economic_config()
            
            if not self._config_exists('ocr_config'):
                self._create_default_ocr_config()
            
            if not self._config_exists('ui_config'):
                self._create_default_ui_config()
                
        except Exception as e:
            logger.error(f"Error initializing default configs: {str(e)}")
    
    def _config_exists(self, config_name: str) -> bool:
        """Check if configuration exists in Firestore"""
        try:
            if not self._ensure_db():
                return False
            doc_ref = self.db.collection('system_config').document(config_name)
            return doc_ref.get().exists
        except Exception:
            return False
    
    def _create_default_ai_config(self):
        """Create default AI configuration"""
        default_config = AIConfig()
        self.save_config('ai_config', asdict(default_config))
    
    def _create_default_mpob_standards(self):
        """Create default MPOB standards"""
        soil_standards = {
            'pH': MPOBStandard(min=4.5, max=5.5, optimal=5.0, unit='-', description='Soil acidity/alkalinity', critical=True),
            'Nitrogen': MPOBStandard(min=0.10, max=0.15, optimal=0.125, unit='%', description='Total nitrogen content'),
            'Organic Carbon': MPOBStandard(min=1.0, max=3.0, optimal=2.0, unit='%', description='Organic carbon content'),
            'Total P': MPOBStandard(min=20, max=40, optimal=30, unit='mg/kg', description='Total phosphorus'),
            'Available P': MPOBStandard(min=15, max=30, optimal=22, unit='mg/kg', description='Available phosphorus', critical=True),
            'Exch. K': MPOBStandard(min=0.15, max=0.25, optimal=0.20, unit='meq%', description='Exchangeable potassium'),
            'Exch. Ca': MPOBStandard(min=2.0, max=4.0, optimal=3.0, unit='meq%', description='Exchangeable calcium'),
            'Exch. Mg': MPOBStandard(min=0.8, max=1.5, optimal=1.15, unit='meq%', description='Exchangeable magnesium'),
            'C.E.C': MPOBStandard(min=8.0, max=15.0, optimal=12.0, unit='meq%', description='Cation exchange capacity')
        }
        
        leaf_standards = {
            'N': MPOBStandard(min=2.4, max=2.8, optimal=2.6, unit='%', description='Leaf nitrogen content'),
            'P': MPOBStandard(min=0.15, max=0.18, optimal=0.165, unit='%', description='Leaf phosphorus content', critical=True),
            'K': MPOBStandard(min=0.9, max=1.2, optimal=1.05, unit='%', description='Leaf potassium content'),
            'Mg': MPOBStandard(min=0.25, max=0.35, optimal=0.30, unit='%', description='Leaf magnesium content'),
            'Ca': MPOBStandard(min=0.5, max=0.7, optimal=0.60, unit='%', description='Leaf calcium content'),
            'B': MPOBStandard(min=15, max=25, optimal=20, unit='mg/kg', description='Leaf boron content'),
            'Cu': MPOBStandard(min=5, max=10, optimal=7.5, unit='mg/kg', description='Leaf copper content'),
            'Zn': MPOBStandard(min=15, max=25, optimal=20, unit='mg/kg', description='Leaf zinc content')
        }
        
        standards = MPOBStandards(
            soil_standards={k: asdict(v) for k, v in soil_standards.items()},
            leaf_standards={k: asdict(v) for k, v in leaf_standards.items()},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.save_config('mpob_standards', asdict(standards))
    
    def _create_default_economic_config(self):
        """Create default economic configuration"""
        economic_config = EconomicConfig(
            fertilizer_costs={
                'urea': 2.5,
                'dap': 3.0,
                'mop': 2.0,
                'kieserite': 2.5,
                'lime': 0.8,
                'npk_15_15_15': 2.8
            },
            application_costs={
                'manual': 50.0,
                'mechanical': 30.0,
                'aerial': 80.0
            },
            labor_costs={
                'skilled': 25.0,
                'unskilled': 15.0,
                'supervisor': 40.0
            },
            equipment_costs={
                'tractor': 200.0,
                'spreader': 150.0,
                'sprayer': 100.0
            },
            updated_at=datetime.now()
        )
        
        self.save_config('economic_config', asdict(economic_config))
    
    def _create_default_ocr_config(self):
        """Create default OCR configuration"""
        ocr_config = OCRConfig(
            psm_modes=[6, 4, 3],
            report_type_patterns={
                'soil': ['soil', 'ph', 'organic carbon', 'exchangeable', 'c.e.c', 'meq%'],
                'leaf': ['dry matter', 'leaf', 'mg/kg dry matter', 'frond']
            }
        )
        
        self.save_config('ocr_config', asdict(ocr_config))
    
    def _create_default_ui_config(self):
        """Create default UI configuration"""
        ui_config = UIConfig(
            units={
                'land_size': ['hectares', 'acres', 'square_meters'],
                'yield': ['tonnes/hectare', 'kg/hectare', 'tonnes/acre', 'kg/acre'],
                'weight': ['kg', 'tons', 'pounds'],
                'area': ['hectares', 'acres', 'square_meters', 'square_feet']
            },
            display_preferences={
                'show_icons': True,
                'show_colors': True,
                'compact_mode': False,
                'auto_refresh': True,
                'default_chart_type': 'line'
            }
        )
        
        self.save_config('ui_config', asdict(ui_config))
    
    def get_config(self, config_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get configuration from Firestore with caching"""
        try:
            # Check cache first
            if use_cache and config_name in self._cache:
                if datetime.now() < self._cache_expiry.get(config_name, datetime.min):
                    return self._cache[config_name]
            
            if not self._ensure_db():
                logger.error("Database connection not available")
                return None
            
            # Fetch from Firestore
            doc_ref = self.db.collection('system_config').document(config_name)
            doc = doc_ref.get()
            
            if doc.exists:
                config_data = doc.to_dict()
                
                # Update cache
                if use_cache:
                    self._cache[config_name] = config_data
                    self._cache_expiry[config_name] = datetime.now() + self.cache_duration
                
                return config_data
            else:
                logger.warning(f"Configuration '{config_name}' not found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting config '{config_name}': {str(e)}")
            return None
    
    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration to Firestore"""
        try:
            if not self._ensure_db():
                logger.error("Database connection not available")
                return False
            
            # Add metadata
            config_data['updated_at'] = datetime.now()
            config_data['updated_by'] = st.session_state.get('user_id', 'system')
            
            # Save to Firestore
            doc_ref = self.db.collection('system_config').document(config_name)
            doc_ref.set(config_data, merge=True)
            
            # Update cache
            self._cache[config_name] = config_data
            self._cache_expiry[config_name] = datetime.now() + self.cache_duration
            
            logger.info(f"Configuration '{config_name}' saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config '{config_name}': {str(e)}")
            return False
    
    def get_ai_config(self) -> AIConfig:
        """Get AI configuration"""
        config_data = self.get_config('ai_config')
        if config_data:
            # Filter out metadata fields that aren't part of AIConfig
            filtered_data = {k: v for k, v in config_data.items() 
                           if k not in ['updated_at', 'created_at', 'updated_by', 'created_by']}
            return AIConfig(**filtered_data)
        return AIConfig()  # Return default if not found
    
    def get_mpob_standards(self) -> MPOBStandards:
        """Get MPOB standards configuration"""
        config_data = self.get_config('mpob_standards')
        if config_data:
            # Filter out metadata fields that aren't part of MPOBStandards
            filtered_data = {k: v for k, v in config_data.items() 
                           if k not in ['updated_by', 'created_by']}
            
            # Convert nested dicts back to MPOBStandard objects
            if filtered_data.get('soil_standards'):
                soil_standards = {}
                for k, v in filtered_data['soil_standards'].items():
                    soil_standards[k] = MPOBStandard(**v)
                filtered_data['soil_standards'] = soil_standards
            
            if filtered_data.get('leaf_standards'):
                leaf_standards = {}
                for k, v in filtered_data['leaf_standards'].items():
                    leaf_standards[k] = MPOBStandard(**v)
                filtered_data['leaf_standards'] = leaf_standards
            
            config = MPOBStandards(**filtered_data)
        else:
            config = self._get_default_mpob_standards()
        
        # Ensure all dictionary fields have default values if None
        if config.soil_standards is None:
            config.soil_standards = {}
        
        if config.leaf_standards is None:
            config.leaf_standards = {}
        
        return config
    
    def get_economic_config(self) -> EconomicConfig:
        """Get economic configuration"""
        config_data = self.get_config('economic_config')
        if config_data:
            # Filter out metadata fields that aren't part of EconomicConfig
            filtered_data = {k: v for k, v in config_data.items() 
                           if k not in ['updated_at', 'created_at', 'updated_by', 'created_by']}
            config = EconomicConfig(**filtered_data)
        else:
            config = EconomicConfig()  # Return default if not found
        
        # Ensure all dictionary fields have default values if None
        if config.fertilizer_costs is None:
            config.fertilizer_costs = {
                'urea': 2.5,
                'dap': 3.0,
                'mop': 2.0,
                'kieserite': 2.5,
                'lime': 0.8,
                'npk_15_15_15': 2.8
            }
        
        if config.application_costs is None:
            config.application_costs = {
                'manual': 50.0,
                'mechanical': 30.0,
                'aerial': 80.0
            }
        
        if config.labor_costs is None:
            config.labor_costs = {
                'skilled': 25.0,
                'unskilled': 15.0,
                'supervisor': 40.0
            }
        
        if config.equipment_costs is None:
            config.equipment_costs = {
                'tractor': 200.0,
                'spreader': 150.0,
                'sprayer': 100.0
            }
        
        return config
    
    def get_ocr_config(self) -> OCRConfig:
        """Get OCR configuration"""
        config_data = self.get_config('ocr_config')
        if config_data:
            # Filter out metadata fields that aren't part of OCRConfig
            filtered_data = {k: v for k, v in config_data.items() 
                           if k not in ['updated_at', 'created_at', 'updated_by', 'created_by']}
            config = OCRConfig(**filtered_data)
        else:
            config = OCRConfig()  # Return default if not found
        
        # Ensure all list/dict fields have default values if None
        if config.psm_modes is None:
            config.psm_modes = [6, 4, 3]
        
        if config.report_type_patterns is None:
            config.report_type_patterns = {
                'soil': ['soil', 'ph', 'organic carbon', 'exchangeable', 'c.e.c', 'meq%'],
                'leaf': ['dry matter', 'leaf', 'mg/kg dry matter', 'frond']
            }
        
        return config
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration"""
        config_data = self.get_config('ui_config')
        if config_data:
            # Filter out metadata fields that aren't part of UIConfig
            filtered_data = {k: v for k, v in config_data.items() 
                           if k not in ['updated_at', 'created_at', 'updated_by', 'created_by']}
            config = UIConfig(**filtered_data)
        else:
            config = UIConfig()  # Return default if not found
        
        # Ensure all dictionary fields have default values if None
        if config.units is None:
            config.units = {
                'land_size': ['hectares', 'acres'],
                'yield': ['tonnes/hectare', 'kg/hectare']
            }
        
        if config.display_preferences is None:
            config.display_preferences = {
                'show_icons': True,
                'show_colors': True,
                'compact_mode': False,
                'auto_refresh': True,
                'default_chart_type': 'bar'
            }
        
        return config
    
    def _get_default_mpob_standards(self) -> MPOBStandards:
        """Get default MPOB standards"""
        return MPOBStandards(
            soil_standards={},
            leaf_standards={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def clear_cache(self, config_name: str = None):
        """Clear configuration cache"""
        if config_name:
            self._cache.pop(config_name, None)
            self._cache_expiry.pop(config_name, None)
        else:
            self._cache.clear()
            self._cache_expiry.clear()
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all configurations"""
        configs = {}
        config_names = ['ai_config', 'mpob_standards', 'economic_config', 'ocr_config', 'ui_config']
        
        for config_name in config_names:
            configs[config_name] = self.get_config(config_name)
        
        return configs
    
    def reset_to_defaults(self, config_name: str) -> bool:
        """Reset configuration to defaults"""
        try:
            if config_name == 'ai_config':
                self._create_default_ai_config()
            elif config_name == 'mpob_standards':
                self._create_default_mpob_standards()
            elif config_name == 'economic_config':
                self._create_default_economic_config()
            elif config_name == 'ocr_config':
                self._create_default_ocr_config()
            elif config_name == 'ui_config':
                self._create_default_ui_config()
            else:
                logger.error(f"Unknown configuration: {config_name}")
                return False
            
            # Clear cache
            self.clear_cache(config_name)
            return True
            
        except Exception as e:
            logger.error(f"Error resetting config '{config_name}': {str(e)}")
            return False

# Global config manager instance
config_manager = ConfigManager()

# Convenience functions
def get_ai_config() -> AIConfig:
    """Get AI configuration"""
    return config_manager.get_ai_config()

def get_mpob_standards() -> MPOBStandards:
    """Get MPOB standards"""
    return config_manager.get_mpob_standards()

def get_economic_config() -> EconomicConfig:
    """Get economic configuration"""
    return config_manager.get_economic_config()

def get_ocr_config() -> OCRConfig:
    """Get OCR configuration"""
    return config_manager.get_ocr_config()

def get_ui_config() -> UIConfig:
    """Get UI configuration"""
    return config_manager.get_ui_config()

def save_config(config_name: str, config_data: Dict[str, Any]) -> bool:
    """Save configuration"""
    return config_manager.save_config(config_name, config_data)

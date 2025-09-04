import os
import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import time
from dataclasses import dataclass
from datetime import datetime
from utils.reference_search import reference_search_engine
import pandas as pd

# Set environment variables to prevent metadata service usage
# This must be done before any Google Cloud libraries are imported
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''
os.environ['GOOGLE_CLOUD_PROJECT'] = 'agriai-cbd8b'
os.environ['GOOGLE_AUTH_DISABLE_METADATA'] = 'true'
os.environ['GCE_METADATA_HOST'] = ''
os.environ['GCE_METADATA_ROOT'] = ''
os.environ['GCE_METADATA_TIMEOUT'] = '0'
os.environ['GOOGLE_CLOUD_DISABLE_METADATA'] = 'true'

# Additional environment variables to completely disable metadata service
os.environ['GOOGLE_AUTH_DISABLE_METADATA'] = 'true'
os.environ['GOOGLE_CLOUD_DISABLE_METADATA'] = 'true'
os.environ['GCE_METADATA_HOST'] = ''
os.environ['GCE_METADATA_ROOT'] = ''
os.environ['GCE_METADATA_TIMEOUT'] = '0'

# Monkey patch the Google Auth library at module level to prevent metadata service usage
try:
    import google.auth
    import google.auth.compute_engine
    import google.auth.transport.requests
    
    # Override the default credential discovery to never use metadata service
    original_default = google.auth.default
    def patched_default(scopes=None, request=None):
        # Always return None to force explicit credential usage
        return None, None
    google.auth.default = patched_default
    
    # Disable compute engine credentials completely
    def disabled_compute_engine_credentials(*args, **kwargs):
        raise Exception("Compute Engine credentials disabled for Streamlit Cloud")
    google.auth.compute_engine.Credentials = disabled_compute_engine_credentials
    
except ImportError:
    pass

# LangChain imports for Google Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    try:
        from langchain_community.chat_models import ChatGoogleGenerativeAI
    except ImportError:
        # Fallback to direct Google Generative AI
        import google.generativeai as genai
        ChatGoogleGenerativeAI = None

# Firebase imports
from .firebase_config import get_firestore_client
from .config_manager import get_ai_config, get_mpob_standards, get_economic_config
from .feedback_system import FeedbackLearningSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    step_number: int
    step_title: str
    step_description: str
    results: Dict[str, Any]
    issues_identified: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    data_quality_score: float
    confidence_level: str


class DataProcessor:
    """Handles data extraction and validation from soil and leaf samples"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataProcessor")
    
    def extract_soil_parameters(self, soil_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate soil parameters from OCR data - ALL SAMPLES"""
        try:
            if not soil_data or 'data' not in soil_data:
                return {}
            
            samples = soil_data.get('data', {}).get('samples', [])
            if not samples:
                return {}
            
            # Extract parameters from ALL samples and calculate statistics
            all_samples_data = []
            
            for sample in samples:
                sample_data = {
                    'sample_no': sample.get('sample_no', 'N/A'),
                    'lab_no': sample.get('lab_no', 'N/A'),
                    'pH': self._safe_float_extract(sample, 'pH'),
                    'Nitrogen_%': self._safe_float_extract(sample, 'Nitrogen_%'),
                    'Organic_Carbon_%': self._safe_float_extract(sample, 'Organic_Carbon_%'),
                    'Total_P_mg_kg': self._safe_float_extract(sample, 'Total_P_mg_kg'),
                    'Available_P_mg_kg': self._safe_float_extract(sample, 'Available_P_mg_kg'),
                    'Exchangeable_K_meq%': self._safe_float_extract(sample, 'Exchangeable_K_meq%'),
                    'Exchangeable_Ca_meq%': self._safe_float_extract(sample, 'Exchangeable_Ca_meq%'),
                    'Exchangeable_Mg_meq%': self._safe_float_extract(sample, 'Exchangeable_Mg_meq%'),
                    'CEC_meq%': self._safe_float_extract(sample, 'CEC_meq%')
                }
                all_samples_data.append(sample_data)
            
            # Calculate statistics for each parameter across all samples
            parameter_stats = {}
            parameter_names = ['pH', 'Nitrogen_%', 'Organic_Carbon_%', 'Total_P_mg_kg', 'Available_P_mg_kg', 
                             'Exchangeable_K_meq%', 'Exchangeable_Ca_meq%', 'Exchangeable_Mg_meq%', 'CEC_meq%']
            
            for param in parameter_names:
                values = [sample[param] for sample in all_samples_data if sample[param] is not None]
                if values:
                    parameter_stats[param] = {
                        'values': values,
                        'average': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'count': len(values),
                        'samples': [{'sample_no': sample['sample_no'], 'lab_no': sample['lab_no'], 'value': sample[param]} 
                                  for sample in all_samples_data if sample[param] is not None]
                    }
            
            # Also include the raw samples data for LLM analysis
            extracted_params = {
                'parameter_statistics': parameter_stats,
                'all_samples': all_samples_data,
                'total_samples': len(samples),
                'extracted_parameters': len(parameter_stats)
            }
            
            self.logger.info(f"Extracted {len(parameter_stats)} soil parameters from {len(samples)} samples")
            return extracted_params
            
        except Exception as e:
            self.logger.error(f"Error extracting soil parameters: {str(e)}")
            return {}
    
    def extract_leaf_parameters(self, leaf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate leaf parameters from OCR data - ALL SAMPLES"""
        try:
            if not leaf_data or 'data' not in leaf_data:
                return {}
            
            samples = leaf_data.get('data', {}).get('samples', [])
            if not samples:
                return {}
            
            # Extract parameters from ALL samples and calculate statistics
            all_samples_data = []
            
            for sample in samples:
                sample_data = {
                    'sample_no': sample.get('sample_no', 'N/A'),
                    'lab_no': sample.get('lab_no', 'N/A'),
                    'N_%': self._safe_float_extract(sample, 'N_%'),
                    'P_%': self._safe_float_extract(sample, 'P_%'),
                    'K_%': self._safe_float_extract(sample, 'K_%'),
                    'Mg_%': self._safe_float_extract(sample, 'Mg_%'),
                    'Ca_%': self._safe_float_extract(sample, 'Ca_%'),
                    'B_mg_kg': self._safe_float_extract(sample, 'B_mg_kg'),
                    'Cu_mg_kg': self._safe_float_extract(sample, 'Cu_mg_kg'),
                    'Zn_mg_kg': self._safe_float_extract(sample, 'Zn_mg_kg')
                }
                all_samples_data.append(sample_data)
            
            # Calculate statistics for each parameter across all samples
            parameter_stats = {}
            parameter_names = ['N_%', 'P_%', 'K_%', 'Mg_%', 'Ca_%', 'B_mg_kg', 'Cu_mg_kg', 'Zn_mg_kg']
            
            for param in parameter_names:
                values = [sample[param] for sample in all_samples_data if sample[param] is not None]
                if values:
                    parameter_stats[param] = {
                        'values': values,
                        'average': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'count': len(values),
                        'samples': [{'sample_no': sample['sample_no'], 'lab_no': sample['lab_no'], 'value': sample[param]} 
                                  for sample in all_samples_data if sample[param] is not None]
                    }
            
            # Also include the raw samples data for LLM analysis
            extracted_params = {
                'parameter_statistics': parameter_stats,
                'all_samples': all_samples_data,
                'total_samples': len(samples),
                'extracted_parameters': len(parameter_stats)
            }
            
            self.logger.info(f"Extracted {len(parameter_stats)} leaf parameters from {len(samples)} samples")
            return extracted_params
            
        except Exception as e:
            self.logger.error(f"Error extracting leaf parameters: {str(e)}")
            return {}
    
    def _safe_float_extract(self, sample: Dict[str, Any], key: str) -> Optional[float]:
        """Safely extract float value from sample data"""
        try:
            value = sample.get(key)
            if value is None:
                return None
            
            # Handle string values
            if isinstance(value, str):
                # Remove any non-numeric characters except decimal point and minus
                cleaned = re.sub(r'[^\d.-]', '', value)
                if cleaned:
                    return float(cleaned)
                return None
            
            # Handle numeric values
            if isinstance(value, (int, float)):
                return float(value)
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    def validate_data_quality(self, soil_params: Dict[str, Any], leaf_params: Dict[str, Any]) -> Tuple[float, str]:
        """Validate data quality and return score and confidence level"""
        try:
            # Extract parameter counts from new data structure
            soil_param_count = soil_params.get('extracted_parameters', 0) if soil_params else 0
            leaf_param_count = leaf_params.get('extracted_parameters', 0) if leaf_params else 0
            total_params = soil_param_count + leaf_param_count
            
            if total_params == 0:
                return 0.0, "No Data"
            
            # Check for critical parameters in new structure
            critical_soil = ['pH', 'CEC_meq%', 'Exchangeable_K_meq%']
            critical_leaf = ['N_%', 'P_%', 'K_%']
            
            critical_found = 0
            
            # Check soil critical parameters
            if 'parameter_statistics' in soil_params:
                for param in critical_soil:
                    if param in soil_params['parameter_statistics']:
                        critical_found += 1
            
            # Check leaf critical parameters
            if 'parameter_statistics' in leaf_params:
                for param in critical_leaf:
                    if param in leaf_params['parameter_statistics']:
                        critical_found += 1
            
            # Calculate quality score based on parameter coverage and sample count
            soil_samples = soil_params.get('total_samples', 0) if soil_params else 0
            leaf_samples = leaf_params.get('total_samples', 0) if leaf_params else 0
            total_samples = soil_samples + leaf_samples
            
            # Quality score considers parameter coverage, critical parameters, and sample count
            param_score = min(1.0, total_params / 17.0)  # 9 soil + 8 leaf parameters
            critical_score = critical_found / 6.0  # 3 critical soil + 3 critical leaf
            sample_score = min(1.0, total_samples / 20.0)  # Expected 20 samples total
            
            quality_score = (param_score * 0.4) + (critical_score * 0.4) + (sample_score * 0.2)
            quality_score = min(1.0, quality_score)
            
            # Determine confidence level
            if quality_score >= 0.8:
                confidence = "High"
            elif quality_score >= 0.6:
                confidence = "Medium"
            elif quality_score >= 0.3:
                confidence = "Low"
            else:
                confidence = "Very Low"
            
            return quality_score, confidence
            
        except Exception as e:
            self.logger.error(f"Error validating data quality: {str(e)}")
            return 0.0, "Unknown"


class StandardsComparator:
    """Manages MPOB standards comparison and issue identification"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.StandardsComparator")
        self.mpob_standards = get_mpob_standards()
    
    def compare_soil_parameters(self, soil_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare soil parameters against MPOB standards - ALL SAMPLES"""
        issues = []
        
        try:
            # Define MPOB standards for soil parameters (updated to match OCR field names)
            soil_standards = {
                'pH': {'min': 4.5, 'max': 5.5, 'optimal': 5.0, 'critical': True},
                'Nitrogen_%': {'min': 0.10, 'max': 0.15, 'optimal': 0.125, 'critical': False},
                'Organic_Carbon_%': {'min': 1.0, 'max': 3.0, 'optimal': 2.0, 'critical': False},
                'Total_P_mg_kg': {'min': 20, 'max': 40, 'optimal': 30, 'critical': False},
                'Available_P_mg_kg': {'min': 15, 'max': 30, 'optimal': 22, 'critical': True},
                'Exchangeable_K_meq%': {'min': 0.15, 'max': 0.25, 'optimal': 0.20, 'critical': True},
                'Exchangeable_Ca_meq%': {'min': 2.0, 'max': 4.0, 'optimal': 3.0, 'critical': False},
                'Exchangeable_Mg_meq%': {'min': 0.8, 'max': 1.5, 'optimal': 1.15, 'critical': False},
                'CEC_meq%': {'min': 8.0, 'max': 15.0, 'optimal': 12.0, 'critical': True}
            }
            
            # Check if we have parameter statistics from the new data structure
            if 'parameter_statistics' not in soil_params:
                return issues
            
            for param, stats in soil_params['parameter_statistics'].items():
                if param not in soil_standards:
                    continue
                
                standard = soil_standards[param]
                min_val = standard['min']
                max_val = standard['max']
                optimal = standard['optimal']
                critical = standard['critical']
                
                # Check each individual sample for issues
                out_of_range_samples = []
                for sample in stats['samples']:
                    sample_value = sample['value']
                    sample_no = sample.get('sample_no', 'N/A')
                    lab_no = sample.get('lab_no', 'N/A')
                    sample_id = f"{sample_no} ({lab_no})" if lab_no != 'N/A' else f"Sample {sample_no}"
                    
                    # Check if this individual sample is outside optimal range
                    if sample_value < min_val or sample_value > max_val:
                        out_of_range_samples.append({
                            'sample_no': sample_no,
                            'lab_no': lab_no,
                            'sample_id': sample_id,
                            'value': sample_value,
                            'min_val': min_val,
                            'max_val': max_val
                        })
                
                # Only create an issue if there are samples outside the optimal range
                if out_of_range_samples:
                    # Use average value for overall assessment
                    avg_value = stats['average']
                    
                    # Determine overall issue status
                    if avg_value < min_val:
                        status = "Deficient"
                        severity = "High" if critical else "Medium"
                        impact = f"Below optimal range ({min_val}-{max_val})"
                    elif avg_value > max_val:
                        status = "Excessive"
                        severity = "High" if critical else "Medium"
                        impact = f"Above optimal range ({min_val}-{max_val})"
                    else:
                        # Average is in range but some samples are out of range
                        status = "Mixed"
                        severity = "Medium" if critical else "Low"
                        impact = f"Some samples outside optimal range ({min_val}-{max_val})"
                    
                    issue = {
                        'parameter': param,
                        'current_value': avg_value,
                        'optimal_range': f"{min_val}-{max_val}",
                        'optimal_value': optimal,
                        'status': status,
                        'severity': severity,
                        'impact': impact,
                        'critical': critical,
                        'source': 'Soil Analysis',
                        'sample_id': f"{len(out_of_range_samples)} out of {stats['count']} samples",
                        'out_of_range_samples': out_of_range_samples,
                        'total_samples': stats['count'],
                        'out_of_range_count': len(out_of_range_samples),
                        'type': 'soil'
                    }
                    
                    issues.append(issue)
            
            self.logger.info(f"Identified {len(issues)} soil issues from {soil_params.get('total_samples', 0)} samples")
            if len(issues) == 0:
                self.logger.warning(f"No soil issues detected. Parameter statistics: {list(soil_params.get('parameter_statistics', {}).keys())}")
                for param, stats in soil_params.get('parameter_statistics', {}).items():
                    self.logger.warning(f"  {param}: avg={stats.get('average', 'N/A')}, samples={stats.get('count', 0)}")
            return issues
            
        except Exception as e:
            self.logger.error(f"Error comparing soil parameters: {str(e)}")
            return []
    
    def compare_leaf_parameters(self, leaf_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare leaf parameters against MPOB standards - ALL SAMPLES"""
        issues = []
        
        try:
            # Define MPOB standards for leaf parameters (updated to match OCR field names)
            leaf_standards = {
                'N_%': {'min': 2.4, 'max': 2.8, 'optimal': 2.6, 'critical': True},
                'P_%': {'min': 0.15, 'max': 0.18, 'optimal': 0.165, 'critical': True},
                'K_%': {'min': 0.9, 'max': 1.2, 'optimal': 1.05, 'critical': True},
                'Mg_%': {'min': 0.25, 'max': 0.35, 'optimal': 0.30, 'critical': True},
                'Ca_%': {'min': 0.5, 'max': 0.7, 'optimal': 0.60, 'critical': True},
                'B_mg_kg': {'min': 15, 'max': 25, 'optimal': 20, 'critical': False},
                'Cu_mg_kg': {'min': 5, 'max': 10, 'optimal': 7.5, 'critical': False},
                'Zn_mg_kg': {'min': 15, 'max': 25, 'optimal': 20, 'critical': False}
            }
            
            # Check if we have parameter statistics from the new data structure
            if 'parameter_statistics' not in leaf_params:
                return issues
            
            for param, stats in leaf_params['parameter_statistics'].items():
                if param not in leaf_standards:
                    continue
                
                standard = leaf_standards[param]
                min_val = standard['min']
                max_val = standard['max']
                optimal = standard['optimal']
                critical = standard['critical']
                
                # Check each individual sample for issues
                out_of_range_samples = []
                for sample in stats['samples']:
                    sample_value = sample['value']
                    sample_no = sample.get('sample_no', 'N/A')
                    lab_no = sample.get('lab_no', 'N/A')
                    sample_id = f"{sample_no} ({lab_no})" if lab_no != 'N/A' else f"Sample {sample_no}"
                    
                    # Check if this individual sample is outside optimal range
                    if sample_value < min_val or sample_value > max_val:
                        out_of_range_samples.append({
                            'sample_no': sample_no,
                            'lab_no': lab_no,
                            'sample_id': sample_id,
                            'value': sample_value,
                            'min_val': min_val,
                            'max_val': max_val
                        })
                
                # Only create an issue if there are samples outside the optimal range
                if out_of_range_samples:
                    # Use average value for overall assessment
                    avg_value = stats['average']
                    
                    # Determine overall issue status
                    if avg_value < min_val:
                        status = "Deficient"
                        severity = "High" if critical else "Medium"
                        impact = f"Below optimal range ({min_val}-{max_val})"
                    elif avg_value > max_val:
                        status = "Excessive"
                        severity = "High" if critical else "Medium"
                        impact = f"Above optimal range ({min_val}-{max_val})"
                    else:
                        # Average is in range but some samples are out of range
                        status = "Mixed"
                        severity = "Medium" if critical else "Low"
                        impact = f"Some samples outside optimal range ({min_val}-{max_val})"
                    
                    issue = {
                        'parameter': param,
                        'current_value': avg_value,
                        'optimal_range': f"{min_val}-{max_val}",
                        'optimal_value': optimal,
                        'status': status,
                        'severity': severity,
                        'impact': impact,
                        'critical': critical,
                        'source': 'Leaf Analysis',
                        'sample_id': f"{len(out_of_range_samples)} out of {stats['count']} samples",
                        'out_of_range_samples': out_of_range_samples,
                        'total_samples': stats['count'],
                        'out_of_range_count': len(out_of_range_samples),
                        'type': 'leaf'
                    }
                    
                    issues.append(issue)
            
            self.logger.info(f"Identified {len(issues)} leaf issues from {leaf_params.get('total_samples', 0)} samples")
            return issues
            
        except Exception as e:
            self.logger.error(f"Error comparing leaf parameters: {str(e)}")
            return []


class PromptAnalyzer:
    """Processes dynamic prompts and generates step-by-step analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PromptAnalyzer")
        self.ai_config = get_ai_config()
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM with Google Gemini configuration"""
        try:
            # Get Google API key from Streamlit secrets or environment
            google_api_key = None
            
            # Try Streamlit secrets first
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'google_ai' in st.secrets:
                    google_api_key = st.secrets.google_ai.get('api_key') or st.secrets.google_ai.get('google_api_key') or st.secrets.google_ai.get('gemini_api_key')
            except:
                pass
            
            # Fallback to environment variables
            if not google_api_key:
                google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            
            if not google_api_key:
                self.logger.error("Google API key not found. Please set GOOGLE_API_KEY or GEMINI_API_KEY in Streamlit secrets or environment variables")
                self.llm = None
                return
            
            # Prefer widely available Gemini models and harden against invalid configs
            configured_model = getattr(self.ai_config, 'model', 'gemini-2.5-pro') if self.ai_config else 'gemini-2.5-pro'
            # Sanitize model: if any legacy OpenAI models configured, force Gemini
            try:
                if isinstance(configured_model, str) and ('gpt-' in configured_model or 'openai' in configured_model.lower()):
                    self.logger.warning(f"Non-Gemini model '{configured_model}' detected. Overriding to Gemini.")
                    configured_model = 'gemini-2.5-pro'
            except Exception:
                configured_model = 'gemini-2.5-pro'
            # Final model fallback list to avoid NotFound errors on older SDKs
            preferred_models = [
                configured_model,
                'gemini-2.5-pro',
                'gemini-1.5-pro',
                'gemini-1.5-pro-latest',
                'gemini-1.0-pro'
            ]
            temperature = getattr(self.ai_config, 'temperature', 0.0) if self.ai_config else 0.0
            # Gemini 2.5 Pro supports up to 65,536 output tokens
            cfg_max_tokens = getattr(self.ai_config, 'max_tokens', 65536) if self.ai_config else 65536
            try:
                cfg_max_tokens_int = int(cfg_max_tokens)
            except Exception:
                cfg_max_tokens_int = 65536
            max_tokens = min(cfg_max_tokens_int, 65536)
            
            # Try models in order until one initializes
            init_error = None
            for mdl in preferred_models:
                try:
                    if ChatGoogleGenerativeAI:
                        # Use LangChain integration (keep args minimal for compatibility)
                        self.llm = ChatGoogleGenerativeAI(
                            model=mdl,
                            temperature=temperature
                        )
                    else:
                        # Fallback to direct Google Generative AI
                        import google.generativeai as genai
                        genai.configure(api_key=google_api_key)
                        self.llm = genai.GenerativeModel(mdl)
                        self._use_direct_gemini = True
                        self._temperature = temperature
                        self._max_tokens = max_tokens
                    model = mdl
                    init_error = None
                    break
                except Exception as e:
                    init_error = e
                    self.llm = None
                    continue
            if init_error:
                raise init_error
            
            self.logger.info(f"LLM configured with max_tokens={max_tokens}, temperature={temperature}")
            self.logger.info(f"LLM initialized successfully with model: {model}")
            
        except Exception as e:
            self.logger.error(f"Error initializing LLM: {str(e)}")
            self.llm = None
    
    def ensure_llm_available(self):
        """Ensure LLM is available, reinitialize if necessary"""
        if not self.llm:
            self.logger.warning("LLM not available, attempting to reinitialize...")
            self._initialize_llm()
        return self.llm is not None
    
    def extract_steps_from_prompt(self, prompt_text: str) -> List[Dict[str, str]]:
        """Extract steps dynamically from prompt text"""
        try:
            steps = []
            
            # Use regex to find step patterns
            step_pattern = r'Step\s+(\d+):\s*([^\n]+)'
            matches = re.findall(step_pattern, prompt_text, re.IGNORECASE)
            
            # Debug: Log what we found
            self.logger.info(f"DEBUG: Found {len(matches)} step matches in prompt")
            for i, (step_num, step_title) in enumerate(matches):
                self.logger.info(f"DEBUG: Match {i+1}: Step {step_num}: {step_title[:100]}...")
            
            for step_num, step_title in matches:
                # Extract description (content after the title until next step or end)
                start_pos = prompt_text.find(f"Step {step_num}:")
                if start_pos == -1:
                    continue
                
                # Find next step or end of text
                next_step_pos = prompt_text.find(f"Step {int(step_num) + 1}:", start_pos)
                if next_step_pos == -1:
                    description = prompt_text[start_pos:].strip()
                else:
                    description = prompt_text[start_pos:next_step_pos].strip()
                
                steps.append({
                    'number': int(step_num),
                    'title': step_title.strip(),
                    'description': description
                })
            
            self.logger.info(f"Extracted {len(steps)} steps from prompt")
            return steps
            
        except Exception as e:
            self.logger.error(f"Error extracting steps from prompt: {str(e)}")
            return []
    
    def generate_step_analysis(self, step: Dict[str, str], soil_params: Dict[str, Any], 
                             leaf_params: Dict[str, Any], land_yield_data: Dict[str, Any],
                             previous_results: List[Dict[str, Any]] = None, total_steps: int = None) -> Dict[str, Any]:
        """Generate analysis for a specific step using LLM"""
        try:
            # Ensure LLM is available before proceeding
            if not self.ensure_llm_available():
                self.logger.error(f"LLM not available for Step {step['number']}, using default result")
                self.logger.error(f"LLM object: {self.llm}")
                self.logger.error(f"AI Config: {self.ai_config}")
                return self._get_default_step_result(step)
            
            # For Step 5 (Economic Impact Forecast), generate economic forecast using user data
            economic_forecast = None
            if step['number'] == 5 and land_yield_data:
                results_generator = ResultsGenerator()
                # Generate recommendations from previous steps if available
                recommendations = []
                for prev_result in (previous_results or []):
                    if 'specific_recommendations' in prev_result:
                        recommendations.extend(prev_result['specific_recommendations'])
                economic_forecast = results_generator.generate_economic_forecast(land_yield_data, recommendations)
            
            # Prepare context for the LLM
            _ = self._prepare_step_context(step, soil_params, leaf_params, land_yield_data, previous_results)
            
            # Search for relevant references with enhanced limits
            search_query = f"{step.get('title', '')} {step.get('description', '')} oil palm cultivation Malaysia"
            references = reference_search_engine.search_all_references(search_query, db_limit=6, web_limit=6)
            
            # Create enhanced prompt for this specific step based on the ACTUAL prompt structure
            total_step_count = total_steps if total_steps else (len(previous_results) + 1 if previous_results else 1)
            
            # Use the ACTUAL step content from the active prompt instead of hardcoded prompts
            # This ensures the LLM follows the exact steps configured by the user
            system_prompt = f"""You are an expert agronomist specializing in oil palm cultivation in Malaysia with 20+ years of experience. 
            You must analyze the provided data according to the SPECIFIC step instructions from the active prompt configuration and provide detailed, accurate results.
            
            ANALYSIS CONTEXT:
            - This is Step {step['number']} of a {total_step_count} step analysis process
            - Step Title: {step['title']}
            - Total Steps in Analysis: {total_step_count}
            
            STEP {step['number']} INSTRUCTIONS FROM ACTIVE PROMPT:
            {step['description']}
            
            FORECAST DETECTION:
            - If the step title or description contains words like "forecast", "projection", "5-year", "yield forecast", "graph", or "chart", you MUST include yield_forecast data
            - The yield_forecast should contain baseline_yield and 5-year projections for high/medium/low investment scenarios
                
                CRITICAL REQUIREMENTS:
            1. Follow the EXACT instructions provided in the step description above
            2. Analyze ALL available samples (soil, leaf, yield data) comprehensively
            3. Use MPOB standards for Malaysian oil palm cultivation
            4. Provide statistical analysis across all samples (mean, range, standard deviation)
            5. Generate accurate visualizations using REAL data from ALL samples
            6. Include specific, actionable recommendations based on the step requirements
            7. Ensure all analysis is based on the actual uploaded data, not generic examples
            8. For Step 6 (Forecast Graph): Generate realistic 5-year yield projections based on actual current yield data
            9. For visualizations: Use actual sample values, not placeholder data
            10. For yield forecast: Calculate realistic improvements based on investment levels and current yield
            11. IMPORTANT: For ANY step that involves yield forecasting or 5-year projections, you MUST include yield_forecast with baseline_yield and 5-year projections for high/medium/low investment
            12. Use the actual current yield from land_yield_data as baseline_yield, not generic values
            13. If the step description mentions "forecast", "projection", "5-year", or "yield forecast", include yield_forecast data
            14. MANDATORY: ALWAYS provide key_findings as a list of 4 specific, actionable insights with quantified data
            15. MANDATORY: ALWAYS provide detailed_analysis as comprehensive explanation in non-technical language
            16. MANDATORY: ALWAYS provide summary as clear, concise overview of the analysis results
            
            DATA ANALYSIS APPROACH:
            - Process each sample individually first
            - Calculate aggregate statistics across all samples
            - Identify patterns, variations, and outliers
            - Compare against MPOB standards for oil palm
            - Generate visualizations with actual sample data
            - Provide recommendations based on the specific step requirements
                
                You must provide a detailed analysis in JSON format with the following structure:
                {{
                "summary": "Comprehensive summary based on the specific step requirements and actual data analysis",
                "detailed_analysis": "Detailed analysis following the exact step instructions with statistical insights across all samples. This should be a comprehensive explanation of the analysis results in clear, non-technical language.",
                    "key_findings": [
                    "Key finding 1: Most critical insight based on step requirements with specific values and data points",
                    "Key finding 2: Important trend or pattern identified across samples with quantified results",
                    "Key finding 3: Significant finding with quantified impact and specific recommendations",
                    "Key finding 4: Additional insight based on step requirements with actionable information"
                ],
                "formatted_analysis": "Formatted analysis text following the step requirements with proper structure and formatting",
                "specific_recommendations": [
                    "Specific recommendation 1 based on step requirements",
                    "Specific recommendation 2 based on step requirements",
                    "Specific recommendation 3 based on step requirements"
                    ],
                    "visualizations": [
                        {{
                            "type": "bar_chart",
                        "title": "Relevant chart title based on step requirements",
                            "data": {{
                            "categories": ["Sample 1", "Sample 2", "Sample 3", "Sample 4", "Sample 5", "Sample 6", "Sample 7", "Sample 8", "Sample 9", "Sample 10"],
                            "values": [actual values from each sample]
                            }}
                        }},
                        {{
                            "type": "pie_chart",
                        "title": "Relevant pie chart title based on step requirements",
                            "data": {{
                            "labels": ["Category 1", "Category 2", "Category 3"],
                            "values": [calculated percentages based on actual sample analysis]
                            }}
                        }}
                    ],
                "yield_forecast": {{
                    "baseline_yield": "current yield from land_yield_data (use actual value provided)",
                    "high_investment": [baseline, baseline*1.15, baseline*1.25, baseline*1.35, baseline*1.40, baseline*1.45],
                    "medium_investment": [baseline, baseline*1.08, baseline*1.15, baseline*1.20, baseline*1.25, baseline*1.30],
                    "low_investment": [baseline, baseline*1.03, baseline*1.06, baseline*1.08, baseline*1.10, baseline*1.12]
                }},
                "statistical_analysis": {{
                    "sample_count": "number of samples analyzed",
                    "mean_values": "mean values for key parameters across all samples",
                    "standard_deviations": "variation measures across samples",
                    "outliers": "identification of unusual values across samples"
                }},
                "data_quality": "Assessment of data completeness, reliability, and representativeness across all samples",
                "confidence_level": "High/Medium/Low based on sample size and data quality"
                }}"""
            
            
            # Format references for inclusion in prompt
            reference_summary = reference_search_engine.get_reference_summary(references)
            
            human_prompt = f"""Please analyze the following data according to Step {step['number']} - {step['title']}:
            
            SOIL DATA:
            {self._format_soil_data_for_llm(soil_params)}
            
            LEAF DATA:
            {self._format_leaf_data_for_llm(leaf_params)}
            
            LAND & YIELD DATA:
            {self._format_land_yield_data_for_llm(land_yield_data)}
            
            PREVIOUS STEP RESULTS:
            {self._format_previous_results_for_llm(previous_results)}
            
            RESEARCH REFERENCES:
            {reference_summary}
            
            Please provide your analysis in the requested JSON format. Be specific and detailed in your findings and recommendations. Use the research references to support your analysis where relevant."""
            
            # Generate response using Google Gemini with retries
            self.logger.info(f"Generating LLM response for Step {step['number']}")
            last_err = None
            for attempt in range(1, (getattr(self.ai_config, 'retry_attempts', 3) or 3) + 1):
                try:
                    if hasattr(self, '_use_direct_gemini') and self._use_direct_gemini:
                        # Use direct Gemini API
                        import google.generativeai as genai
                        combined_prompt = f"{system_prompt}\n\n{human_prompt}"
                        generation_config = genai.types.GenerationConfig(
                            temperature=self._temperature,
                            max_output_tokens=self._max_tokens,
                        )
                        resp_obj = self.llm.generate_content(
                            combined_prompt,
                            generation_config=generation_config
                        )
                        class GeminiResponse:
                            def __init__(self, content):
                                self.content = content
                        response = GeminiResponse(resp_obj.text)
                    else:
                        # Use LangChain client
                        response = self.llm.invoke(system_prompt + "\n\n" + human_prompt)
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    # Backoff on rate/quota errors, otherwise fail fast
                    if any(k in err_str for k in ["429", "quota", "insufficient_quota", "quota_exceeded", "resource_exhausted"]):
                        sleep_s = min(2 ** attempt, 8)
                        self.logger.warning(f"LLM quota/rate error on attempt {attempt}, retrying in {sleep_s}s...")
                        time.sleep(sleep_s)
                        continue
                    else:
                        raise
            if last_err:
                raise last_err
            
            # Log the raw JSON response from LLM
            self.logger.info(f"=== STEP {step['number']} RAW JSON RESPONSE ===")
            self.logger.info(f"Raw LLM Response: {response.content}")
            self.logger.info(f"=== END STEP {step['number']} RAW JSON RESPONSE ===")
            
            result = self._parse_llm_response(response.content, step)
            
            # Log the parsed result
            self.logger.info(f"=== STEP {step['number']} PARSED RESULT ===")
            self.logger.info(f"Parsed Result: {json.dumps(result, indent=2, default=str)}")
            self.logger.info(f"=== END STEP {step['number']} PARSED RESULT ===")
            
            # Convert JSON to text format for UI display
            result = self._convert_json_to_text_format(result, step['number'])
            
            # Add economic forecast to Step 5 result
            if step['number'] == 5 and economic_forecast:
                result['economic_forecast'] = economic_forecast
                self.logger.info(f"Added economic forecast to Step 5 result: {economic_forecast}")
            elif step['number'] == 5 and not economic_forecast:
                # Generate fallback economic forecast if none was generated
                results_generator = ResultsGenerator()
                if land_yield_data:
                    fallback_forecast = results_generator.generate_economic_forecast(land_yield_data, [])
                    result['economic_forecast'] = fallback_forecast
                    self.logger.info(f"Generated fallback economic forecast for Step 5")
                else:
                    result['economic_forecast'] = results_generator._get_default_economic_forecast()
                    self.logger.info(f"Using default economic forecast for Step 5")
            
            # Add references to result
            result['references'] = references
            self.logger.info(f"Added {references.get('total_found', 0)} references to Step {step['number']} result")
            
            self.logger.info(f"Generated analysis for Step {step['number']}: {result.get('summary', 'No summary')}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error generating step analysis for Step {step['number']}: {error_msg}")
            
            # If it's an API quota error, fall back silently so users can proceed up to daily limit
            if ("429" in error_msg or "quota" in error_msg.lower() or 
                "insufficient_quota" in error_msg or "quota_exceeded" in error_msg.lower() or
                "resource_exhausted" in error_msg.lower()):
                self.logger.warning(f"API quota issue for Step {step['number']}. Using silent fallback analysis.")
                return self._get_default_step_result(step)
            else:
                return self._get_default_step_result(step)
    
    def _prepare_step_context(self, step: Dict[str, str], soil_params: Dict[str, Any],
                            leaf_params: Dict[str, Any], land_yield_data: Dict[str, Any],
                            previous_results: List[Dict[str, Any]] = None) -> str:
        """Prepare context for LLM analysis with enhanced all-samples data"""
        context_parts = []
        
        # Add soil data (enhanced format)
        if soil_params and 'parameter_statistics' in soil_params:
            context_parts.append("SOIL ANALYSIS DATA (All Samples):")
            for param, stats in soil_params['parameter_statistics'].items():
                context_parts.append(f"- {param}:")
                context_parts.append(f"  Average: {stats['average']:.3f}")
                context_parts.append(f"  Range: {stats['min']:.3f} - {stats['max']:.3f}")
                context_parts.append(f"  Samples: {stats['count']}")
                context_parts.append("")
        
        # Add leaf data (enhanced format)
        if leaf_params and 'parameter_statistics' in leaf_params:
            context_parts.append("LEAF ANALYSIS DATA (All Samples):")
            for param, stats in leaf_params['parameter_statistics'].items():
                context_parts.append(f"- {param}:")
                context_parts.append(f"  Average: {stats['average']:.3f}")
                context_parts.append(f"  Range: {stats['min']:.3f} - {stats['max']:.3f}")
                context_parts.append(f"  Samples: {stats['count']}")
                context_parts.append("")
        
        # Add land and yield data
        if land_yield_data:
            context_parts.append("LAND & YIELD DATA:")
            context_parts.append(f"- Land Size: {land_yield_data.get('land_size', 0)} {land_yield_data.get('land_unit', 'hectares')}")
            context_parts.append(f"- Current Yield: {land_yield_data.get('current_yield', 0)} {land_yield_data.get('yield_unit', 'tonnes/hectare')}")
            context_parts.append("")
        
        # Add previous results if available
        if previous_results:
            context_parts.append("PREVIOUS ANALYSIS RESULTS:")
            for i, prev_result in enumerate(previous_results[-2:], 1):  # Last 2 results
                context_parts.append(f"Step {prev_result.get('step_number', i)}: {prev_result.get('summary', 'No summary available')}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _parse_llm_response(self, response: str, step: Dict[str, str]) -> Dict[str, Any]:
        """Parse LLM response and extract structured data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                
                # Base result structure
                result = {
                    'step_number': step['number'],
                    'step_title': step['title'],
                    'summary': parsed_data.get('summary', 'Analysis completed'),
                    'detailed_analysis': parsed_data.get('detailed_analysis', 'Detailed analysis not available'),
                    'key_findings': parsed_data.get('key_findings', []),
                    'data_quality': parsed_data.get('data_quality', 'Unknown'),
                    'confidence_level': parsed_data.get('confidence_level', 'Medium'),
                    'analysis': parsed_data  # Store the full parsed data for display
                }
                
                # Add step-specific data based on step number
                if step['number'] == 1:  # Data Analysis
                    result.update({
                        'nutrient_comparisons': parsed_data.get('nutrient_comparisons', []),
                        'visualizations': parsed_data.get('visualizations', [])
                    })
                elif step['number'] == 2:  # Issue Diagnosis
                    result.update({
                        'identified_issues': parsed_data.get('identified_issues', []),
                        'visualizations': parsed_data.get('visualizations', [])
                    })
                elif step['number'] == 3:  # Solution Recommendations
                    result.update({
                        'solution_options': parsed_data.get('solution_options', [])
                    })
                elif step['number'] == 4:  # Regenerative Agriculture
                    result.update({
                        'regenerative_practices': parsed_data.get('regenerative_practices', [])
                    })
                elif step['number'] == 5:  # Economic Impact Forecast
                    result.update({
                        'economic_analysis': parsed_data.get('economic_analysis', {})
                    })
                elif step['number'] == 6:  # Forecast Graph
                    result.update({
                        'yield_forecast': parsed_data.get('yield_forecast', {}),
                        'assumptions': parsed_data.get('assumptions', []),
                        'visualizations': parsed_data.get('visualizations', [])
                    })
                
                # Always include yield_forecast and visualizations if they exist in the parsed data
                # This ensures any step with forecast data will have it available
                if 'yield_forecast' in parsed_data and parsed_data['yield_forecast']:
                    result['yield_forecast'] = parsed_data['yield_forecast']
                if 'visualizations' in parsed_data and parsed_data['visualizations']:
                    result['visualizations'] = parsed_data['visualizations']
                
                return result
            
            # Fallback: extract text content and try to structure it
            return {
                'step_number': step['number'],
                'step_title': step['title'],
                'summary': 'Analysis completed',
                'detailed_analysis': response[:500] + "..." if len(response) > 500 else response,
                'data_quality': 'Unknown',
                'confidence_level': 'Medium',
                'analysis': {'raw_response': response}
            }
                
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {str(e)}")
            return self._get_default_step_result(step)
    
    def _format_soil_data_for_llm(self, soil_params: Dict[str, Any]) -> str:
        """Format soil data for LLM consumption - ALL SAMPLES"""
        if not soil_params:
            return "No soil data available"
        
        formatted = []
        
        # Add summary statistics
        if 'parameter_statistics' in soil_params:
            formatted.append("SOIL PARAMETER STATISTICS (All Samples):")
            for param, stats in soil_params['parameter_statistics'].items():
                formatted.append(f"- {param}:")
                formatted.append(f"  Average: {stats['average']:.3f}")
                formatted.append(f"  Range: {stats['min']:.3f} - {stats['max']:.3f}")
                formatted.append(f"  Samples: {stats['count']}")
                formatted.append("")
        
        # Add individual sample data
        if 'all_samples' in soil_params:
            formatted.append("INDIVIDUAL SOIL SAMPLE DATA:")
            for sample in soil_params['all_samples']:
                formatted.append(f"Sample {sample['sample_no']} (Lab: {sample['lab_no']}):")
                for param, value in sample.items():
                    if param not in ['sample_no', 'lab_no'] and value is not None:
                        formatted.append(f"  {param}: {value}")
                formatted.append("")
        
        return "\n".join(formatted) if formatted else "No soil parameters available"
    
    def _format_leaf_data_for_llm(self, leaf_params: Dict[str, Any]) -> str:
        """Format leaf data for LLM consumption - ALL SAMPLES"""
        if not leaf_params:
            return "No leaf data available"
        
        formatted = []
        
        # Add summary statistics
        if 'parameter_statistics' in leaf_params:
            formatted.append("LEAF PARAMETER STATISTICS (All Samples):")
            for param, stats in leaf_params['parameter_statistics'].items():
                formatted.append(f"- {param}:")
                formatted.append(f"  Average: {stats['average']:.3f}")
                formatted.append(f"  Range: {stats['min']:.3f} - {stats['max']:.3f}")
                formatted.append(f"  Samples: {stats['count']}")
                formatted.append("")
        
        # Add individual sample data
        if 'all_samples' in leaf_params:
            formatted.append("INDIVIDUAL LEAF SAMPLE DATA:")
            for sample in leaf_params['all_samples']:
                formatted.append(f"Sample {sample['sample_no']} (Lab: {sample['lab_no']}):")
                for param, value in sample.items():
                    if param not in ['sample_no', 'lab_no'] and value is not None:
                        formatted.append(f"  {param}: {value}")
                formatted.append("")
        
        return "\n".join(formatted) if formatted else "No leaf parameters available"
    
    def _format_land_yield_data_for_llm(self, land_yield_data: Dict[str, Any]) -> str:
        """Format land and yield data for LLM consumption"""
        if not land_yield_data:
            return "No land and yield data available"
        
        formatted = []
        for param, value in land_yield_data.items():
            if value is not None and value != 0:
                formatted.append(f"- {param}: {value}")
        
        return "\n".join(formatted) if formatted else "No land and yield data available"
    
    def _format_previous_results_for_llm(self, previous_results: List[Dict[str, Any]]) -> str:
        """Format previous step results for LLM consumption"""
        if not previous_results:
            return "No previous step results available"
        
        formatted = []
        for i, result in enumerate(previous_results, 1):
            step_num = result.get('step_number', i)
            step_title = result.get('step_title', f'Step {step_num}')
            summary = result.get('summary', 'No summary available')
            formatted.append(f"Step {step_num} ({step_title}): {summary}")
        
        return "\n".join(formatted)

    def _get_default_step_result(self, step: Dict[str, str]) -> Dict[str, Any]:
        """Get default result when LLM is not available"""
        # Provide meaningful fallback content based on step type
        step_fallbacks = {
            1: {
                'summary': 'Data analysis completed using fallback processing',
                'detailed_analysis': 'Soil and leaf data has been processed and validated. Please check your Google API quota to get detailed AI analysis.',
                'key_findings': [
                    'Data has been successfully extracted and validated',
                    'Soil and leaf parameters are available for analysis',
                    'MPOB standards comparison completed',
                    'Ready for detailed AI analysis once API quota is restored'
                ]
            },
            2: {
                'summary': 'Issue diagnosis completed using standard analysis',
                'detailed_analysis': 'Standard agronomic issue detection has been performed. AI-powered diagnosis requires Google API access.',
                'key_findings': [
                    'Standard nutrient level analysis completed',
                    'Basic issue identification performed',
                    'MPOB standards comparison available',
                    'Detailed AI diagnosis pending API quota restoration'
                ]
            },
            3: {
                'summary': 'Solution recommendations prepared',
                'detailed_analysis': 'Basic solution framework has been established. Detailed AI recommendations require Google API access.',
                'key_findings': [
                    'Standard solution approaches identified',
                    'Basic investment options outlined',
                    'General application guidelines provided',
                    'AI-powered detailed recommendations pending'
                ]
            },
            4: {
                'summary': 'Regenerative agriculture strategies outlined',
                'detailed_analysis': 'Standard regenerative practices have been identified. AI integration requires Google API access.',
                'key_findings': [
                    'Standard regenerative practices identified',
                    'Basic soil health improvement strategies outlined',
                    'General sustainability approaches provided',
                    'AI-optimized integration pending'
                ]
            },
            5: {
                'summary': 'Economic impact assessment prepared',
                'detailed_analysis': 'Basic economic framework established. Detailed AI calculations require Google API access.',
                'key_findings': [
                    'Basic economic framework established',
                    'Standard ROI calculations available',
                    'General cost-benefit analysis provided',
                    'AI-powered detailed forecasts pending'
                ]
            },
            6: {
                'summary': 'Yield forecast framework prepared',
                'detailed_analysis': 'Basic yield projection structure established. Detailed AI forecasts require Google API access.',
                'key_findings': [
                    'Basic yield projection framework established',
                    'Standard forecasting approach outlined',
                    'General trend analysis available',
                    'AI-powered detailed projections pending'
                ]
            }
        }
        
        fallback = step_fallbacks.get(step['number'], {
            'summary': f"Step {step['number']} analysis completed",
            'detailed_analysis': f"Analysis for {step['title']} - LLM not available",
            'key_findings': ['Analysis pending Google API quota restoration']
        })
        
        result = {
            'step_number': step['number'],
            'step_title': step['title'],
            'summary': fallback['summary'],
            'detailed_analysis': fallback['detailed_analysis'],
            'key_findings': fallback['key_findings'],
            'data_quality': 'Standard',
            'confidence_level': 'Medium',
            'analysis': {'status': 'fallback_mode', 'api_error': 'Google API quota exceeded'}
        }
        
        # Add step-specific empty data based on step number
        if step['number'] == 1:  # Data Analysis
            result.update({
                'nutrient_comparisons': [],
                'visualizations': []
            })
        elif step['number'] == 2:  # Issue Diagnosis
            result.update({
                'identified_issues': [],
                'visualizations': []
            })
        elif step['number'] == 3:  # Solution Recommendations
            result.update({
                'solution_options': []
            })
        elif step['number'] == 4:  # Regenerative Agriculture
            result.update({
                'regenerative_practices': []
            })
        elif step['number'] == 5:  # Economic Impact Forecast
            result.update({
                'economic_analysis': {}
            })
        elif step['number'] == 6:  # Forecast Graph
            # Generate fallback yield forecast with normalized baseline (t/ha)
            try:
                current_yield_raw = land_yield_data.get('current_yield', 0) if land_yield_data else 0
                yield_unit = land_yield_data.get('yield_unit', 'tonnes/hectare') if land_yield_data else 'tonnes/hectare'
                if yield_unit == 'kg/hectare':
                    norm_current = current_yield_raw / 1000
                elif yield_unit == 'tonnes/acre':
                    norm_current = current_yield_raw * 2.47105
                elif yield_unit == 'kg/acre':
                    norm_current = (current_yield_raw / 1000) * 2.47105
                else:
                    norm_current = current_yield_raw
            except Exception:
                norm_current = 0
            fallback_forecast = self._generate_fallback_yield_forecast(norm_current)
            result.update({
                'yield_forecast': fallback_forecast,
                'assumptions': [
                    "Projections start from current yield baseline",
                    "Projections require yearly follow-up and adaptive adjustments",
                    "Yield improvements based on addressing identified nutrient issues"
                ]
            })
        
        return result
    
    def _convert_json_to_text_format(self, result: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """Convert JSON structured data to text format for UI display"""
        try:
            # Start with the base result
            text_result = result.copy()
            
            # Convert step-specific data to text format
            formatted_text = ""
            if step_number == 1:  # Data Analysis
                formatted_text = self._format_step1_text(result)
            elif step_number == 2:  # Issue Diagnosis
                formatted_text = self._format_step2_text(result)
            elif step_number == 3:  # Solution Recommendations
                formatted_text = self._format_step3_text(result)
            elif step_number == 4:  # Regenerative Agriculture
                formatted_text = self._format_step4_text(result)
            elif step_number == 5:  # Economic Impact Forecast
                formatted_text = self._format_step5_text(result)
            elif step_number == 6:  # Forecast Graph
                formatted_text = self._format_step6_text(result)
            
            # Ensure we always have some formatted content
            if not formatted_text or formatted_text.strip() == "":
                formatted_text = self._create_fallback_formatted_text(result, step_number)
            
            text_result['formatted_analysis'] = formatted_text
            self.logger.info(f"Generated formatted analysis for Step {step_number}: {len(formatted_text)} characters")
            
            return text_result
            
        except Exception as e:
            self.logger.error(f"Error converting JSON to text format: {str(e)}")
            # Create fallback formatted text
            text_result = result.copy()
            text_result['formatted_analysis'] = self._create_fallback_formatted_text(result, step_number)
            return text_result
    
    def _create_fallback_formatted_text(self, result: Dict[str, Any], step_number: int) -> str:
        """Create fallback formatted text when step-specific formatting fails"""
        text_parts = []
        
        # Add step title
        step_titles = {
            1: "Data Analysis & Interpretation",
            2: "Issue Diagnosis & Problem Identification", 
            3: "Solution Recommendations & Strategies",
            4: "Regenerative Agriculture Integration",
            5: "Economic Impact & ROI Analysis",
            6: "Yield Forecast & Projections"
        }
        
        text_parts.append(f"## {step_titles.get(step_number, f'Step {step_number} Analysis')}")
        text_parts.append("")
        
        # Add summary if available
        if result.get('summary'):
            text_parts.append(f"**Summary:** {result['summary']}")
            text_parts.append("")
        
        # Add key findings if available
        if result.get('key_findings'):
            text_parts.append("### 🔍 Key Findings")
            for i, finding in enumerate(result['key_findings'], 1):
                text_parts.append(f"**{i}.** {finding}")
            text_parts.append("")
        
        # Add detailed analysis if available
        if result.get('detailed_analysis'):
            text_parts.append("### 📋 Detailed Analysis")
            text_parts.append(str(result['detailed_analysis']))
            text_parts.append("")
        
        # Add any other available data
        for key, value in result.items():
            if key not in ['summary', 'key_findings', 'detailed_analysis', 'formatted_analysis'] and value:
                if isinstance(value, (list, dict)):
                    text_parts.append(f"### {key.replace('_', ' ').title()}")
                    text_parts.append(str(value))
                    text_parts.append("")
                elif isinstance(value, str) and len(value) > 10:
                    text_parts.append(f"**{key.replace('_', ' ').title()}:** {value}")
                    text_parts.append("")
        
        return "\n".join(text_parts)
    
    def _generate_fallback_yield_forecast(self, current_yield: float) -> Dict[str, Any]:
        """Generate realistic fallback yield forecast based on current yield baseline"""
        if current_yield <= 0:
            # Default baseline if no current yield data
            current_yield = 15.0  # Average oil palm yield in Malaysia
        
        # Calculate realistic improvements over 5 years
        # High investment: 25% total improvement
        # Medium investment: 18% total improvement  
        # Low investment: 12% total improvement
        
        high_improvement = 0.25
        medium_improvement = 0.18
        low_improvement = 0.12
        
        # Generate year-by-year progression (gradual improvement)
        years = [0, 1, 2, 3, 4, 5]
        
        high_yields = []
        medium_yields = []
        low_yields = []
        
        for year in years:
            if year == 0:
                # Year 0 = current baseline
                high_yields.append(current_yield)
                medium_yields.append(current_yield)
                low_yields.append(current_yield)
            else:
                # Gradual improvement each year
                year_progress = year / 5.0  # 0.2, 0.4, 0.6, 0.8, 1.0
                
                # High investment progression
                high_target = current_yield * (1 + high_improvement)
                high_yield = current_yield + (high_target - current_yield) * year_progress
                high_yields.append(round(high_yield, 1))
                
                # Medium investment progression
                medium_target = current_yield * (1 + medium_improvement)
                medium_yield = current_yield + (medium_target - current_yield) * year_progress
                medium_yields.append(round(medium_yield, 1))
                
                # Low investment progression
                low_target = current_yield * (1 + low_improvement)
                low_yield = current_yield + (low_target - current_yield) * year_progress
                low_yields.append(round(low_yield, 1))
        
        return {
            'baseline_yield': current_yield,
            'high_investment': high_yields,
            'medium_investment': medium_yields,
            'low_investment': low_yields
        }
    
    def _format_step1_text(self, result: Dict[str, Any]) -> str:
        """Format Step 1 (Data Analysis) to text"""
        text_parts = []
        
        # Summary
        if result.get('summary'):
            text_parts.append(f"## Summary\n{result['summary']}\n")
        
        # Key Findings
        if result.get('key_findings'):
            text_parts.append("## 🔍 Key Findings\n")
            for i, finding in enumerate(result['key_findings'], 1):
                text_parts.append(f"**{i}.** {finding}")
            text_parts.append("")
        
        # Detailed Analysis
        if result.get('detailed_analysis'):
            text_parts.append(f"## 📋 Detailed Analysis\n{result['detailed_analysis']}\n")
        
        # Nutrient Comparisons
        if result.get('nutrient_comparisons'):
            text_parts.append("## 📊 Nutrient Level Comparisons\n")
            for comp in result['nutrient_comparisons']:
                text_parts.append(f"**{comp.get('parameter', 'Unknown')}:**")
                text_parts.append(f"- Current Level: {comp.get('current', 'N/A')}")
                text_parts.append(f"- Optimal Range: {comp.get('optimal', 'N/A')}")
                text_parts.append(f"- Status: {comp.get('status', 'Unknown')}")
                if comp.get('ratio_analysis'):
                    text_parts.append(f"- Ratio Analysis: {comp['ratio_analysis']}")
                text_parts.append("")
        
        # Visualizations
        if result.get('visualizations'):
            text_parts.append("## 📈 Data Visualizations\n")
            for i, viz in enumerate(result['visualizations'], 1):
                text_parts.append(f"**Visualization {i}: {viz.get('title', 'Untitled')}**")
                text_parts.append(f"- Type: {viz.get('type', 'Unknown')}")
                text_parts.append("")
        
        return "\n".join(text_parts)
    
    def _format_step2_text(self, result: Dict[str, Any]) -> str:
        """Format Step 2 (Issue Diagnosis) to text"""
        text_parts = []
        
        # Summary
        if result.get('summary'):
            text_parts.append(f"## Summary\n{result['summary']}\n")
        
        # Key Findings
        if result.get('key_findings'):
            text_parts.append("## 🔍 Key Findings\n")
            for i, finding in enumerate(result['key_findings'], 1):
                text_parts.append(f"**{i}.** {finding}")
            text_parts.append("")
        
        # Detailed Analysis
        if result.get('detailed_analysis'):
            text_parts.append(f"## 📋 Detailed Analysis\n{result['detailed_analysis']}\n")
        
        # Identified Issues
        if result.get('identified_issues'):
            text_parts.append("## ⚠️ Identified Agronomic Issues\n")
            for issue in result['identified_issues']:
                text_parts.append(f"**{issue.get('parameter', 'Unknown Parameter')}:**")
                text_parts.append(f"- Issue Type: {issue.get('issue_type', 'Unknown')}")
                text_parts.append(f"- Severity: {issue.get('severity', 'Unknown')}")
                text_parts.append(f"- Likely Cause: {issue.get('cause', 'Unknown')}")
                text_parts.append(f"- Expected Impact: {issue.get('impact', 'Unknown')}")
                text_parts.append("")
        
        return "\n".join(text_parts)
    
    def _format_step3_text(self, result: Dict[str, Any]) -> str:
        """Format Step 3 (Solution Recommendations) to text"""
        text_parts = []
        
        # Summary
        if result.get('summary'):
            text_parts.append(f"## Summary\n{result['summary']}\n")
        
        # Key Findings
        if result.get('key_findings'):
            text_parts.append("## 🔍 Key Findings\n")
            for i, finding in enumerate(result['key_findings'], 1):
                text_parts.append(f"**{i}.** {finding}")
            text_parts.append("")
        
        # Detailed Analysis
        if result.get('detailed_analysis'):
            text_parts.append(f"## 📋 Detailed Analysis\n{result['detailed_analysis']}\n")
        
        # Solution Options
        if result.get('solution_options'):
            text_parts.append("## 💡 Recommended Solutions\n")
            for solution in result['solution_options']:
                text_parts.append(f"**{solution.get('parameter', 'Unknown Parameter')}:**")
                
                # High Investment
                if solution.get('high_investment'):
                    high = solution['high_investment']
                    text_parts.append("### 🔥 High Investment Approach")
                    text_parts.append(f"- Product: {high.get('product', 'N/A')}")
                    text_parts.append(f"- Application Rate: {high.get('rate', 'N/A')}")
                    text_parts.append(f"- Timing: {high.get('timing', 'N/A')}")
                    text_parts.append(f"- Method: {high.get('method', 'N/A')}")
                    text_parts.append(f"- Cost Level: {high.get('cost', 'N/A')}")
                    text_parts.append(f"- Short-term Impact: {high.get('short_term_impact', 'N/A')}")
                    text_parts.append(f"- Long-term Impact: {high.get('long_term_impact', 'N/A')}")
                    text_parts.append("")
                
                # Medium Investment
                if solution.get('medium_investment'):
                    medium = solution['medium_investment']
                    text_parts.append("### ⚡ Medium Investment Approach")
                    text_parts.append(f"- Product: {medium.get('product', 'N/A')}")
                    text_parts.append(f"- Application Rate: {medium.get('rate', 'N/A')}")
                    text_parts.append(f"- Timing: {medium.get('timing', 'N/A')}")
                    text_parts.append(f"- Method: {medium.get('method', 'N/A')}")
                    text_parts.append(f"- Cost Level: {medium.get('cost', 'N/A')}")
                    text_parts.append(f"- Short-term Impact: {medium.get('short_term_impact', 'N/A')}")
                    text_parts.append(f"- Long-term Impact: {medium.get('long_term_impact', 'N/A')}")
                    text_parts.append("")
                
                # Low Investment
                if solution.get('low_investment'):
                    low = solution['low_investment']
                    text_parts.append("### 💡 Low Investment Approach")
                    text_parts.append(f"- Product: {low.get('product', 'N/A')}")
                    text_parts.append(f"- Application Rate: {low.get('rate', 'N/A')}")
                    text_parts.append(f"- Timing: {low.get('timing', 'N/A')}")
                    text_parts.append(f"- Method: {low.get('method', 'N/A')}")
                    text_parts.append(f"- Cost Level: {low.get('cost', 'N/A')}")
                    text_parts.append(f"- Short-term Impact: {low.get('short_term_impact', 'N/A')}")
                    text_parts.append(f"- Long-term Impact: {low.get('long_term_impact', 'N/A')}")
                    text_parts.append("")
        
        return "\n".join(text_parts)
    
    def _format_step4_text(self, result: Dict[str, Any]) -> str:
        """Format Step 4 (Regenerative Agriculture) to text"""
        text_parts = []
        
        # Summary
        if result.get('summary'):
            text_parts.append(f"## Summary\n{result['summary']}\n")
        
        # Key Findings
        if result.get('key_findings'):
            text_parts.append("## 🔍 Key Findings\n")
            for i, finding in enumerate(result['key_findings'], 1):
                text_parts.append(f"**{i}.** {finding}")
            text_parts.append("")
        
        # Detailed Analysis
        if result.get('detailed_analysis'):
            text_parts.append(f"## 📋 Detailed Analysis\n{result['detailed_analysis']}\n")
        
        # Regenerative Practices
        if result.get('regenerative_practices'):
            text_parts.append("## 🌱 Regenerative Agriculture Strategies\n")
            for practice in result['regenerative_practices']:
                text_parts.append(f"**{practice.get('practice', 'Unknown Practice')}:**")
                text_parts.append(f"- Mechanism: {practice.get('mechanism', 'N/A')}")
                text_parts.append(f"- Benefits: {practice.get('benefits', 'N/A')}")
                text_parts.append(f"- Implementation: {practice.get('implementation', 'N/A')}")
                if practice.get('quantified_benefits'):
                    text_parts.append(f"- Quantified Benefits: {practice['quantified_benefits']}")
                text_parts.append("")
        
        return "\n".join(text_parts)
    
    def _format_step5_text(self, result: Dict[str, Any]) -> str:
        """Format Step 5 (Economic Impact Forecast) to text"""
        text_parts = []
        
        # Summary
        if result.get('summary'):
            text_parts.append(f"## Summary\n{result['summary']}\n")
        
        # Key Findings
        if result.get('key_findings'):
            text_parts.append("## 🔍 Key Findings\n")
            for i, finding in enumerate(result['key_findings'], 1):
                text_parts.append(f"**{i}.** {finding}")
            text_parts.append("")
        
        # Detailed Analysis
        if result.get('detailed_analysis'):
            text_parts.append(f"## 📋 Detailed Analysis\n{result['detailed_analysis']}\n")
        
        # Economic Analysis - Check both economic_analysis and economic_forecast
        econ_data = result.get('economic_analysis', {})
        econ_forecast = result.get('economic_forecast', {})
        
        if econ_forecast:
            # Use the more accurate economic forecast data
            text_parts.append("## 💰 Economic Impact Forecast\n")
            
            current_yield = econ_forecast.get('current_yield_tonnes_per_ha', 0)
            land_size = econ_forecast.get('land_size_hectares', 0)
            scenarios = econ_forecast.get('scenarios', {})
            
            text_parts.append(f"**Current Yield:** {current_yield:.1f} tonnes/hectare")
            text_parts.append(f"**Land Size:** {land_size:.1f} hectares")
            text_parts.append("")
            
            if scenarios:
                text_parts.append("### 📊 Investment Scenarios Analysis\n")
                text_parts.append("| Investment Level | Cost per Hectare (RM) | Total Cost (RM) | New Yield (t/ha) | Additional Yield (t/ha) | Additional Revenue (RM) | ROI (%) | Payback (months) |")
                text_parts.append("|------------------|----------------------|-----------------|------------------|-------------------------|------------------------|---------|------------------|")
                
                for level, data in scenarios.items():
                    if isinstance(data, dict) and 'investment_level' in data:
                        investment_level = data.get('investment_level', level.title())
                        cost_per_ha = data.get('cost_per_hectare', 0)
                        total_cost = data.get('total_cost', 0)
                        new_yield = data.get('new_yield', 0)
                        additional_yield = data.get('additional_yield', 0)
                        additional_revenue = data.get('additional_revenue', 0)
                        roi = data.get('roi_percentage', 0)
                        payback = data.get('payback_months', 0)
                        
                        text_parts.append(f"| {investment_level} | {cost_per_ha:,.0f} | {total_cost:,.0f} | {new_yield:.1f} | {additional_yield:.1f} | {additional_revenue:,.0f} | {roi:.1f}% | {payback:.1f} |")
                
                text_parts.append("")
                
                # Add assumptions
                assumptions = econ_forecast.get('assumptions', [])
                if assumptions:
                    text_parts.append("### 📋 Assumptions\n")
                    for assumption in assumptions:
                        text_parts.append(f"• {assumption}")
                    text_parts.append("")
        
        elif econ_data:
            # Fallback to LLM-generated economic analysis
            text_parts.append("## 💰 Economic Impact Forecast\n")
            text_parts.append(f"**Current Yield:** {econ_data.get('current_yield', 'N/A')} tons/ha")
            text_parts.append(f"**Projected Yield Improvement:** {econ_data.get('yield_improvement', 'N/A')}%")
            text_parts.append(f"**Estimated ROI:** {econ_data.get('roi', 'N/A')}%")
            text_parts.append("")
            
            if econ_data.get('cost_benefit'):
                text_parts.append("### 📊 Cost-Benefit Analysis Table\n")
                text_parts.append("| Investment Level | Total Investment (RM) | Expected Return (RM) | ROI (%) | Payback Period (Years) |")
                text_parts.append("|------------------|----------------------|---------------------|---------|------------------------|")
                
                for scenario in econ_data['cost_benefit']:
                    scenario_name = scenario.get('scenario', 'Unknown Scenario')
                    
                    # Safely format investment value
                    investment = scenario.get('investment', 0)
                    try:
                        investment_formatted = f"{float(investment):,.0f}" if investment != 'N/A' else 'N/A'
                    except (ValueError, TypeError):
                        investment_formatted = str(investment)
                    
                    # Safely format return value
                    return_val = scenario.get('return', 0)
                    try:
                        return_formatted = f"{float(return_val):,.0f}" if return_val != 'N/A' else 'N/A'
                    except (ValueError, TypeError):
                        return_formatted = str(return_val)
                    
                    # Safely format ROI value
                    roi = scenario.get('roi', 0)
                    try:
                        if roi == 'N/A' or roi is None:
                            roi_formatted = 'N/A'
                        else:
                            roi_formatted = f"{float(roi):.1f}"
                    except (ValueError, TypeError):
                        roi_formatted = str(roi) if roi else 'N/A'
                    
                    payback_period = scenario.get('payback_period', 'N/A')
                    
                    text_parts.append(f"| {scenario_name} | {investment_formatted} | {return_formatted} | {roi_formatted} | {payback_period} |")
                
                text_parts.append("")
                text_parts.append("**Note:** RM values are approximate and represent recent historical price and cost ranges.")
                text_parts.append("")
        
        return "\n".join(text_parts)
    
    def _format_step6_text(self, result: Dict[str, Any]) -> str:
        """Format Step 6 (Forecast Graph) to text"""
        text_parts = []
        
        # Summary
        if result.get('summary'):
            text_parts.append(f"## Summary\n{result['summary']}\n")
        
        # Key Findings
        if result.get('key_findings'):
            text_parts.append("## 🔍 Key Findings\n")
            for i, finding in enumerate(result['key_findings'], 1):
                text_parts.append(f"**{i}.** {finding}")
            text_parts.append("")
        
        # Detailed Analysis
        if result.get('detailed_analysis'):
            text_parts.append(f"## 📋 Detailed Analysis\n{result['detailed_analysis']}\n")
        
        # Yield Forecast
        if result.get('yield_forecast'):
            forecast = result['yield_forecast']
            text_parts.append("## 📈 5-Year Yield Forecast\n")
            
            # Show baseline yield
            baseline_yield = forecast.get('baseline_yield', 0)
            if baseline_yield > 0:
                text_parts.append(f"**Current Yield Baseline:** {baseline_yield:.1f} tonnes/hectare")
                text_parts.append("")
            
            # Years including baseline (0-5)
            years = [0, 1, 2, 3, 4, 5]
            year_labels = ['Current', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5']
            
            if forecast.get('high_investment'):
                text_parts.append("### 🚀 High Investment Scenario")
                text_parts.append("| Year | Yield (tonnes/ha) | Improvement |")
                text_parts.append("|------|------------------|-------------|")
                
                for i, year in enumerate(years):
                    if i < len(forecast['high_investment']):
                        yield_val = forecast['high_investment'][i]
                        if i == 0:
                            improvement = "Baseline"
                        else:
                            improvement = f"+{((yield_val - baseline_yield) / baseline_yield * 100):.1f}%" if baseline_yield > 0 else "N/A"
                        text_parts.append(f"| {year_labels[i]} | {yield_val:.1f} | {improvement} |")
                text_parts.append("")
            
            if forecast.get('medium_investment'):
                text_parts.append("### ⚖️ Medium Investment Scenario")
                text_parts.append("| Year | Yield (tonnes/ha) | Improvement |")
                text_parts.append("|------|------------------|-------------|")
                
                for i, year in enumerate(years):
                    if i < len(forecast['medium_investment']):
                        yield_val = forecast['medium_investment'][i]
                        if i == 0:
                            improvement = "Baseline"
                        else:
                            improvement = f"+{((yield_val - baseline_yield) / baseline_yield * 100):.1f}%" if baseline_yield > 0 else "N/A"
                        text_parts.append(f"| {year_labels[i]} | {yield_val:.1f} | {improvement} |")
                text_parts.append("")
            
            if forecast.get('low_investment'):
                text_parts.append("### 💰 Low Investment Scenario")
                text_parts.append("| Year | Yield (tonnes/ha) | Improvement |")
                text_parts.append("|------|------------------|-------------|")
                
                for i, year in enumerate(years):
                    if i < len(forecast['low_investment']):
                        yield_val = forecast['low_investment'][i]
                        if i == 0:
                            improvement = "Baseline"
                        else:
                            improvement = f"+{((yield_val - baseline_yield) / baseline_yield * 100):.1f}%" if baseline_yield > 0 else "N/A"
                        text_parts.append(f"| {year_labels[i]} | {yield_val:.1f} | {improvement} |")
                text_parts.append("")
        
        # Assumptions
        if result.get('assumptions'):
            text_parts.append("## Key Assumptions\n")
            for assumption in result['assumptions']:
                text_parts.append(f"- {assumption}")
            text_parts.append("")
        
        return "\n".join(text_parts)


class ResultsGenerator:
    """Generates comprehensive analysis results and recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ResultsGenerator")
        self.economic_config = get_economic_config()
    
    def generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on identified issues"""
        recommendations = []
        
        try:
            for issue in issues:
                param = issue['parameter']
                status = issue['status']
                severity = issue['severity']
                current_value = issue['current_value']
                optimal_range = issue['optimal_range']
                
                # Generate three-tier recommendations
                rec = {
                    'parameter': param,
                    'issue_description': f"{param} is {status.lower()} (Current: {current_value}, Optimal: {optimal_range})",
                    'investment_options': {
                        'high': self._generate_high_investment_rec(param, status, current_value),
                        'medium': self._generate_medium_investment_rec(param, status, current_value),
                        'low': self._generate_low_investment_rec(param, status, current_value)
                    }
                }
                
                recommendations.append(rec)
            
            self.logger.info(f"Generated {len(recommendations)} recommendations")
            if len(recommendations) == 0:
                self.logger.warning(f"No recommendations generated. Input issues count: {len(issues)}")
                for i, issue in enumerate(issues[:3]):  # Log first 3 issues for debugging
                    self.logger.warning(f"  Issue {i+1}: {issue.get('parameter', 'Unknown')} - {issue.get('status', 'Unknown')}")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _generate_high_investment_rec(self, param: str, status: str, current_value: float) -> Dict[str, Any]:
        """Generate high investment recommendation"""
        if 'pH' in param:
            if status == 'Deficient':
                return {
                    'approach': 'Lime application with precision spreading',
                    'action': 'Apply 2-3 tonnes/ha of agricultural lime',
                    'dosage': '2-3 tonnes/ha',
                    'timeline': 'Apply 2-3 months before planting',
                    'cost': 'RM 400-600/ha',
                    'expected_result': 'pH increase to optimal range within 6 months'
                }
            else:
                return {
                    'approach': 'Sulfur application for pH reduction',
                    'action': 'Apply 500-1000 kg/ha of elemental sulfur',
                    'dosage': '500-1000 kg/ha',
                    'timeline': 'Apply 3-4 months before planting',
                    'cost': 'RM 300-500/ha',
                    'expected_result': 'pH reduction to optimal range within 8 months'
                }
        
        elif 'K' in param:
            return {
                'approach': 'Muriate of Potash (MOP) application',
                'action': 'Apply 200-300 kg/ha of MOP',
                'dosage': '200-300 kg/ha',
                'timeline': 'Apply in 2-3 split applications',
                'cost': 'RM 600-900/ha',
                'expected_result': 'K levels reach optimal range within 3 months'
            }
        
        elif 'P' in param:
            return {
                'approach': 'Triple Superphosphate (TSP) application',
                'action': 'Apply 150-200 kg/ha of TSP',
                'dosage': '150-200 kg/ha',
                'timeline': 'Apply at planting or early growth stage',
                'cost': 'RM 450-600/ha',
                'expected_result': 'P levels reach optimal range within 2 months'
            }
        
        else:
            return {
                'approach': 'High-grade fertilizer application',
                'action': f'Apply appropriate fertilizer for {param}',
                'dosage': 'As per soil test recommendations',
                'timeline': 'Apply in 2-3 split applications',
                'cost': 'RM 500-800/ha',
                'expected_result': f'{param} levels reach optimal range'
            }
    
    def _generate_medium_investment_rec(self, param: str, status: str, current_value: float) -> Dict[str, Any]:
        """Generate medium investment recommendation"""
        if 'pH' in param:
            if status == 'Deficient':
                return {
                    'approach': 'Moderate lime application',
                    'action': 'Apply 1-2 tonnes/ha of agricultural lime',
                    'dosage': '1-2 tonnes/ha',
                    'timeline': 'Apply 3-4 months before planting',
                    'cost': 'RM 200-400/ha',
                    'expected_result': 'Gradual pH increase over 8-12 months'
                }
            else:
                return {
                    'approach': 'Moderate sulfur application',
                    'action': 'Apply 300-500 kg/ha of elemental sulfur',
                    'dosage': '300-500 kg/ha',
                    'timeline': 'Apply 4-6 months before planting',
                    'cost': 'RM 200-300/ha',
                    'expected_result': 'Gradual pH reduction over 10-12 months'
                }
        
        elif 'K' in param:
            return {
                'approach': 'Moderate MOP application',
                'action': 'Apply 100-150 kg/ha of MOP',
                'dosage': '100-150 kg/ha',
                'timeline': 'Apply in 2 applications',
                'cost': 'RM 300-450/ha',
                'expected_result': 'K levels improve within 4-6 months'
            }
        
        elif 'P' in param:
            return {
                'approach': 'Moderate TSP application',
                'action': 'Apply 75-100 kg/ha of TSP',
                'dosage': '75-100 kg/ha',
                'timeline': 'Apply at planting',
                'cost': 'RM 225-300/ha',
                'expected_result': 'P levels improve within 3-4 months'
            }
        
        else:
            return {
                'approach': 'Moderate fertilizer application',
                'action': f'Apply moderate fertilizer for {param}',
                'dosage': 'As per soil test recommendations',
                'timeline': 'Apply in 2 applications',
                'cost': 'RM 250-400/ha',
                'expected_result': f'{param} levels improve gradually'
            }
    
    def _generate_low_investment_rec(self, param: str, status: str, current_value: float) -> Dict[str, Any]:
        """Generate low investment recommendation"""
        if 'pH' in param:
            if status == 'Deficient':
                return {
                    'approach': 'Organic matter incorporation',
                    'action': 'Incorporate 10-15 tonnes/ha of compost',
                    'dosage': '10-15 tonnes/ha',
                    'timeline': 'Apply 6-8 months before planting',
                    'cost': 'RM 100-200/ha',
                    'expected_result': 'Gradual pH improvement over 12-18 months'
                }
            else:
                return {
                    'approach': 'Organic matter and sulfur',
                    'action': 'Apply 200-300 kg/ha sulfur with compost',
                    'dosage': '200-300 kg/ha sulfur + 5-10 tonnes/ha compost',
                    'timeline': 'Apply 6-8 months before planting',
                    'cost': 'RM 150-250/ha',
                    'expected_result': 'Gradual pH adjustment over 12-18 months'
                }
        
        elif 'K' in param:
            return {
                'approach': 'Organic K sources',
                'action': 'Apply 5-10 tonnes/ha of composted EFB',
                'dosage': '5-10 tonnes/ha',
                'timeline': 'Apply 6-8 months before planting',
                'cost': 'RM 100-200/ha',
                'expected_result': 'K levels improve over 12-18 months'
            }
        
        elif 'P' in param:
            return {
                'approach': 'Organic P sources',
                'action': 'Apply 3-5 tonnes/ha of composted manure',
                'dosage': '3-5 tonnes/ha',
                'timeline': 'Apply 6-8 months before planting',
                'cost': 'RM 75-150/ha',
                'expected_result': 'P levels improve over 12-18 months'
            }
        
        else:
            return {
                'approach': 'Organic matter incorporation',
                'action': f'Apply organic matter for {param} improvement',
                'dosage': '5-10 tonnes/ha compost',
                'timeline': 'Apply 6-8 months before planting',
                'cost': 'RM 100-200/ha',
                'expected_result': f'{param} levels improve gradually over 12-18 months'
            }
    
    def generate_economic_forecast(self, land_yield_data: Dict[str, Any], 
                                 recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate economic forecast based on land/yield data and recommendations"""
        try:
            land_size = land_yield_data.get('land_size', 0)
            current_yield = land_yield_data.get('current_yield', 0)
            land_unit = land_yield_data.get('land_unit', 'hectares')
            yield_unit = land_yield_data.get('yield_unit', 'tonnes/hectare')
            
            # Convert to hectares and tonnes/hectare
            if land_unit == 'acres':
                land_size_ha = land_size * 0.404686
            elif land_unit == 'square_meters':
                land_size_ha = land_size / 10000.0
            else:
                land_size_ha = land_size
            
            if yield_unit == 'kg/hectare':
                current_yield_tonnes = current_yield / 1000
            elif yield_unit == 'tonnes/acre':
                current_yield_tonnes = current_yield * 2.47105
            elif yield_unit == 'kg/acre':
                current_yield_tonnes = (current_yield / 1000) * 2.47105
            else:
                current_yield_tonnes = current_yield
            
            if land_size_ha == 0 or current_yield_tonnes == 0:
                return self._get_default_economic_forecast()
            
            # Calculate investment scenarios
            try:
                economic_cfg = get_economic_config()
                oil_palm_price = float(getattr(economic_cfg, 'yield_price_per_ton', 600)) or 600
            except Exception:
                oil_palm_price = 600  # RM per tonne
            
            scenarios = {}
            for investment_level in ['high', 'medium', 'low']:
                # Cost per hectare
                if investment_level == 'high':
                    cost_per_ha = 800
                    yield_increase = 0.25  # 25% increase
                elif investment_level == 'medium':
                    cost_per_ha = 500
                    yield_increase = 0.18  # 18% increase
                else:  # low
                    cost_per_ha = 300
                    yield_increase = 0.12  # 12% increase
                
                total_cost = cost_per_ha * land_size_ha
                new_yield = current_yield_tonnes * (1 + yield_increase)
                additional_yield = new_yield - current_yield_tonnes
                additional_revenue = additional_yield * oil_palm_price * land_size_ha
                roi = (additional_revenue - total_cost) / total_cost * 100 if total_cost > 0 else 0
                payback_months = (total_cost / (additional_revenue / 12)) if additional_revenue > 0 else 0
                
                scenarios[investment_level] = {
                    'investment_level': investment_level.title(),
                    'cost_per_hectare': cost_per_ha,
                    'total_cost': total_cost,
                    'current_yield': current_yield_tonnes,
                    'new_yield': new_yield,
                    'additional_yield': additional_yield,
                    'additional_revenue': additional_revenue,
                    'roi_percentage': roi,
                    'payback_months': payback_months
                }
            
            return {
                'land_size_hectares': land_size_ha,
                'current_yield_tonnes_per_ha': current_yield_tonnes,
                'oil_palm_price_rm_per_tonne': oil_palm_price,
                'scenarios': scenarios,
                'assumptions': [
                    'Yield improvements based on addressing identified nutrient issues',
                    'Oil palm price: RM 600/tonne (current market rate)',
                    'Costs include fertilizer, application, and labor',
                    'ROI calculated over 12-month period'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating economic forecast: {str(e)}")
            return self._get_default_economic_forecast()
    
    def _get_default_economic_forecast(self) -> Dict[str, Any]:
        """Get default economic forecast when data is insufficient"""
        return {
            'land_size_hectares': 0,
            'current_yield_tonnes_per_ha': 0,
            'oil_palm_price_rm_per_tonne': 600,
            'scenarios': {
                'high': {'message': 'Insufficient data for economic forecast'},
                'medium': {'message': 'Insufficient data for economic forecast'},
                'low': {'message': 'Insufficient data for economic forecast'}
            },
            'assumptions': ['Economic forecast requires land size and current yield data']
        }


class AnalysisEngine:
    """Main analysis engine orchestrator"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AnalysisEngine")
        self.data_processor = DataProcessor()
        self.standards_comparator = StandardsComparator()
        self.prompt_analyzer = PromptAnalyzer()
        self.results_generator = ResultsGenerator()
        self.feedback_system = FeedbackLearningSystem()
    
    def generate_comprehensive_analysis(self, soil_data: Dict[str, Any], leaf_data: Dict[str, Any],
                                      land_yield_data: Dict[str, Any], prompt_text: str) -> Dict[str, Any]:
        """Generate comprehensive analysis with all components"""
        try:
            self.logger.info("Starting comprehensive analysis")

            # Enforce daily analysis quota (10/day per user)
            try:
                db = get_firestore_client()
                user_id = None
                try:
                    import streamlit as st
                    user_id = st.session_state.get('user_id') if hasattr(st, 'session_state') else None
                except Exception:
                    user_id = None
                if db is not None and user_id:
                    from datetime import timedelta
                    start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    q = (db.collection('analysis_results')
                         .where('user_id', '==', user_id)
                         .where('created_at', '>=', start_of_day))
                    count_today = len(list(q.stream()))
                    if count_today >= 10:
                        self.logger.warning(f"Daily quota exceeded for user {user_id}: {count_today} analyses today")
                        return {
                            'error': 'Daily analysis limit reached (10/day). Please try again tomorrow.',
                            'analysis_metadata': {
                                'timestamp': datetime.now().isoformat(),
                                'quota': 'exceeded',
                                'limit': 10,
                                'used_today': count_today
                            }
                        }
            except Exception as _:
                # Fail open if quota check fails
                pass
            
            # Step 1: Process data (enhanced all-samples processing)
            soil_params = self.data_processor.extract_soil_parameters(soil_data)
            leaf_params = self.data_processor.extract_leaf_parameters(leaf_data)
            data_quality_score, confidence_level = self.data_processor.validate_data_quality(soil_params, leaf_params)
            
            # Step 2: Compare against standards (all samples)
            soil_issues = self.standards_comparator.compare_soil_parameters(soil_params)
            leaf_issues = self.standards_comparator.compare_leaf_parameters(leaf_params)
            all_issues = soil_issues + leaf_issues
            
            # Step 3: Generate recommendations
            recommendations = self.results_generator.generate_recommendations(all_issues)
            
            # Step 4: Generate economic forecast
            economic_forecast = self.results_generator.generate_economic_forecast(land_yield_data, recommendations)
            
            # Step 5: Process prompt steps with LLM (enhanced with all samples data)
            self.logger.info(f"DEBUG: Prompt text length: {len(prompt_text)} characters")
            self.logger.info(f"DEBUG: Prompt text preview: {prompt_text[:200]}...")
            steps = self.prompt_analyzer.extract_steps_from_prompt(prompt_text)
            self.logger.info(f"DEBUG: Extracted {len(steps)} steps from prompt")
            step_results = []
            
            # Ensure LLM is available for step analysis
            self.logger.info(f"LLM available for step analysis: {self.prompt_analyzer.llm is not None}")
            if not self.prompt_analyzer.ensure_llm_available():
                self.logger.error("LLM is not available for step analysis - cannot proceed")
                # Continue with default results instead of failing completely
            
            for step in steps:
                self.logger.info(f"DEBUG: Processing step {step.get('number', 'unknown')}: {step.get('title', 'unknown')[:50]}...")
                step_result = self.prompt_analyzer.generate_step_analysis(
                    step, soil_params, leaf_params, land_yield_data, step_results, len(steps)
                )
                step_results.append(step_result)
                self.logger.info(f"DEBUG: Step result keys: {list(step_result.keys()) if step_result else 'None'}")
            
            # Compile comprehensive results
            comprehensive_results = {
                'analysis_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'data_quality_score': data_quality_score,
                    'confidence_level': confidence_level,
                    'total_parameters_analyzed': len(soil_params.get('parameter_statistics', {})) + len(leaf_params.get('parameter_statistics', {})),
                    'issues_identified': len(all_issues),
                    'critical_issues': len([i for i in all_issues if i.get('critical', False)])
                },
                'raw_data': {
                    'soil_parameters': soil_params,
                    'leaf_parameters': leaf_params,
                    'land_yield_data': land_yield_data
                },
                'issues_analysis': {
                    'soil_issues': soil_issues,
                    'leaf_issues': leaf_issues,
                    'all_issues': all_issues
                },
                'recommendations': recommendations,
                'economic_forecast': economic_forecast,
                'step_by_step_analysis': step_results,
                'prompt_used': {
                    'steps_count': len(steps),
                    'steps': steps
                }
            }
            
            self.logger.info(f"DEBUG: Final comprehensive_results keys: {list(comprehensive_results.keys())}")
            self.logger.info(f"DEBUG: step_by_step_analysis type: {type(comprehensive_results.get('step_by_step_analysis'))}")
            self.logger.info(f"DEBUG: step_by_step_analysis length: {len(comprehensive_results.get('step_by_step_analysis', []))}")

            # Incorporate feedback learning insights
            self._incorporate_feedback_learning(comprehensive_results)

            # Persist analysis results to Firestore (analysis_results)
            try:
                db = get_firestore_client()
                if db is not None:
                    try:
                        import streamlit as st  # Access user/session if available
                        user_id = st.session_state.get('user_id') if hasattr(st, 'session_state') else None
                    except Exception:
                        user_id = None
                    record = {
                        'user_id': user_id,
                        'created_at': datetime.now(),
                        'analysis_metadata': comprehensive_results.get('analysis_metadata', {}),
                        'raw_data': comprehensive_results.get('raw_data', {}),
                        'issues_analysis': comprehensive_results.get('issues_analysis', {}),
                        'recommendations': comprehensive_results.get('recommendations', {}),
                        'economic_forecast': comprehensive_results.get('economic_forecast', {}),
                        'step_by_step_analysis': comprehensive_results.get('step_by_step_analysis', []),
                        'prompt_used': comprehensive_results.get('prompt_used', {}),
                    }
                    db.collection('analysis_results').add(record)
                    self.logger.info("Analysis results saved to Firestore collection 'analysis_results'.")
                else:
                    self.logger.warning("Firestore client not available. Skipping save to analysis_results.")
            except Exception as e:
                self.logger.error(f"Failed to save analysis results to Firestore: {str(e)}")

            self.logger.info("Comprehensive analysis completed successfully")
            return comprehensive_results
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {str(e)}")
            return {
                'error': f'Analysis failed: {str(e)}',
                'analysis_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'data_quality_score': 0.0,
                    'confidence_level': 'Very Low',
                    'total_parameters_analyzed': 0,
                    'issues_identified': 0,
                    'critical_issues': 0
                }
            }
    
    def _incorporate_feedback_learning(self, analysis_results: Dict[str, Any]):
        """
        Incorporate feedback learning insights to improve analysis quality
        
        Args:
            analysis_results: The analysis results to potentially improve
        """
        try:
            # Get feedback insights
            insights = self.feedback_system.get_learning_insights()
            
            if insights.get('insufficient_data', False):
                self.logger.info("Insufficient feedback data for learning insights")
                return
            
            # Apply learning insights to improve analysis
            improvement_priorities = insights.get('improvement_priorities', [])
            
            for priority in improvement_priorities:
                area = priority['area']
                current_score = priority['current_score']
                
                if area == 'accuracy' and current_score < 3.0:
                    # Enhance accuracy by adding more validation
                    self.logger.info("Applying accuracy improvements based on feedback")
                    analysis_results['feedback_enhancements'] = analysis_results.get('feedback_enhancements', {})
                    analysis_results['feedback_enhancements']['accuracy_boost'] = True
                
                elif area == 'clarity' and current_score < 3.0:
                    # Enhance clarity by improving explanations
                    self.logger.info("Applying clarity improvements based on feedback")
                    analysis_results['feedback_enhancements'] = analysis_results.get('feedback_enhancements', {})
                    analysis_results['feedback_enhancements']['clarity_boost'] = True
                
                elif area == 'visualizations' and current_score < 3.0:
                    # Enhance visualizations
                    self.logger.info("Applying visualization improvements based on feedback")
                    analysis_results['feedback_enhancements'] = analysis_results.get('feedback_enhancements', {})
                    analysis_results['feedback_enhancements']['visualization_boost'] = True
            
            # Add feedback learning metadata
            analysis_results['feedback_learning'] = {
                'insights_applied': len(improvement_priorities),
                'system_performance': insights.get('system_performance', {}),
                'learning_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Applied {len(improvement_priorities)} feedback learning insights")
            
        except Exception as e:
            self.logger.error(f"Error incorporating feedback learning: {str(e)}")
            # Don't fail the analysis if feedback learning fails


# Legacy function for backward compatibility
def analyze_lab_data(soil_data: Dict[str, Any], leaf_data: Dict[str, Any],
                    land_yield_data: Dict[str, Any], prompt_text: str) -> Dict[str, Any]:
    """Legacy function for backward compatibility"""
    engine = AnalysisEngine()
    return engine.generate_comprehensive_analysis(soil_data, leaf_data, land_yield_data, prompt_text)

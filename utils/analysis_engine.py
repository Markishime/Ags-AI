import os
import logging
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

# LangChain imports
from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema import HumanMessage, SystemMessage

# Firebase imports
from .firebase_config import get_firestore_client
from .ai_config_utils import load_ai_configuration, get_prompt_template, get_reference_materials, get_output_format, get_tagging_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MPOBStandards:
    """MPOB standards for oil palm cultivation"""
    
    # Soil standards
    soil_standards = {
        'pH': {'min': 4.5, 'max': 5.5, 'optimal': 5.0, 'unit': '-'},
        'Nitrogen': {'min': 0.10, 'max': 0.15, 'optimal': 0.125, 'unit': '%'},
        'Organic Carbon': {'min': 1.0, 'max': 3.0, 'optimal': 2.0, 'unit': '%'},
        'Total P': {'min': 20, 'max': 40, 'optimal': 30, 'unit': 'mg/kg'},
        'Available P': {'min': 15, 'max': 30, 'optimal': 22, 'unit': 'mg/kg'},
        'Exch. K': {'min': 0.15, 'max': 0.25, 'optimal': 0.20, 'unit': 'meq%'},
        'Exch. Ca': {'min': 2.0, 'max': 4.0, 'optimal': 3.0, 'unit': 'meq%'},
        'Exch. Mg': {'min': 0.8, 'max': 1.5, 'optimal': 1.15, 'unit': 'meq%'},
        'C.E.C': {'min': 8.0, 'max': 15.0, 'optimal': 12.0, 'unit': 'meq%'}
    }
    
    # Leaf standards
    leaf_standards = {
        'N': {'min': 2.4, 'max': 2.8, 'optimal': 2.6, 'unit': '%'},
        'P': {'min': 0.15, 'max': 0.18, 'optimal': 0.165, 'unit': '%'},
        'K': {'min': 0.9, 'max': 1.2, 'optimal': 1.05, 'unit': '%'},
        'Mg': {'min': 0.25, 'max': 0.35, 'optimal': 0.30, 'unit': '%'},
        'Ca': {'min': 0.5, 'max': 0.7, 'optimal': 0.60, 'unit': '%'},
        'B': {'min': 15, 'max': 25, 'optimal': 20, 'unit': 'mg/kg'},
        'Cu': {'min': 5, 'max': 10, 'optimal': 7.5, 'unit': 'mg/kg'},
        'Zn': {'min': 15, 'max': 25, 'optimal': 20, 'unit': 'mg/kg'}
    }

class AnalysisEngine:
    """AI-powered analysis engine for SP LAB reports"""
    
    def __init__(self):
        # Initialize OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.warning("OpenAI API key not found. Using mock responses.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.0,  # Maximum accuracy and predictability
                max_tokens=128000,  # GPT-4o maximum output tokens
                openai_api_key=self.openai_api_key
            )
        
        # Initialize MPOB standards
        self.mpob_standards = MPOBStandards()
    
    def _convert_samples_to_parameters(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert new sample format to parameters format for backward compatibility"""
        try:
            samples = extracted_data.get('samples', [])
            report_type = extracted_data.get('report_type', 'unknown')
            
            if not samples:
                return extracted_data
            
            # Convert samples to parameters format
            parameters = []
            
            for sample in samples:
                sample_no = sample.get('sample_no', 'Unknown')
                lab_no = sample.get('lab_no', 'Unknown')
                
                # Convert each sample's data to parameter format
                for key, value in sample.items():
                    if key in ['sample_no', 'lab_no']:
                        continue
                    
                    if isinstance(value, (int, float)) and value > 0:
                        # Determine parameter name and unit
                        param_name = key
                        unit = self._get_parameter_unit(key, report_type)
                        
                        parameters.append({
                            'Parameter': param_name,
                            'Value': value,
                            'Unit': unit,
                            'Sample_No': sample_no,
                            'Lab_No': lab_no,
                            'Type': report_type
                        })
            
            # Return in the expected format
            return {
                'report_type': report_type,
                'parameters': parameters,
                'samples': samples,  # Keep original samples for reference
                'total_samples': len(samples)
            }
            
        except Exception as e:
            logger.error(f"Error converting samples to parameters: {str(e)}")
            return extracted_data
    
    def _get_parameter_unit(self, param_name: str, report_type: str) -> str:
        """Get the appropriate unit for a parameter"""
        if report_type == 'soil':
            if 'pH' in param_name:
                return '-'
            elif any(nutrient in param_name for nutrient in ['Nitrogen', 'Organic_Carbon']):
                return '%'
            elif any(nutrient in param_name for nutrient in ['Total_P', 'Available_P']):
                return 'mg/kg'
            elif any(nutrient in param_name for nutrient in ['Exchangeable_K', 'Exchangeable_Ca', 'Exchangeable_Mg', 'CEC']):
                return 'meq%'
            else:
                return 'mg/kg'
        else:  # leaf
            if any(nutrient in param_name for nutrient in ['N_', 'P_', 'K_']):
                return '%'
            else:
                return 'mg/kg'
    
    def _get_db(self):
        """Get Firestore client with proper error handling"""
        db = get_firestore_client()
        if not db:
            raise Exception("Failed to get Firestore client. Firebase may not be initialized.")
        return db
    
    def _get_active_prompt(self) -> Optional[Dict[str, Any]]:
        """Fetch active prompt from Firestore analysis_prompts collection"""
        try:
            db = self._get_db()
            prompts_ref = db.collection('analysis_prompts')
            
            # Query for active prompt
            active_prompt_query = prompts_ref.where('is_active', '==', True).limit(1)
            active_prompt_docs = list(active_prompt_query.stream())
            
            if active_prompt_docs:
                prompt_doc = active_prompt_docs[0]
                prompt_data = prompt_doc.to_dict()
                prompt_data['id'] = prompt_doc.id
                logger.info(f"Found active prompt: {prompt_data.get('name', 'Unknown')}")
                return prompt_data
            else:
                logger.warning("No active prompt found in analysis_prompts collection")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching active prompt: {str(e)}")
            return None
    
    def _get_reference_documents(self) -> List[Dict[str, Any]]:
        """Get active reference documents from Firestore"""
        try:
            db = self._get_db()
            docs_ref = db.collection('reference_documents')
            active_docs_query = docs_ref.where('active', '==', True)
            active_docs = list(active_docs_query.stream())
            
            documents = []
            for doc in active_docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                documents.append(doc_data)
            
            logger.info(f"Found {len(documents)} active reference documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error fetching reference documents: {str(e)}")
            return []
    
    def _get_output_formatting_config(self) -> Dict[str, Any]:
        """Get output formatting configuration from Firestore"""
        try:
            db = self._get_db()
            config_ref = db.collection('ai_config').document('output_formatting')
            doc = config_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                # Return default configuration
                return {
                    'format_type': 'Structured',
                    'include_summary': True,
                    'include_recommendations': True,
                    'include_visualizations': True,
                    'sections': [
                        'Executive Summary',
                        'Parameter Analysis',
                        'Issues Identified',
                        'Recommendations',
                        'Economic Impact',
                        'Priority Actions'
                    ],
                    'use_icons': True,
                    'use_colors': True,
                    'max_length': 1000,
                    'language': 'English',
                    'tone': 'Professional'
                }
        
        except Exception as e:
            logger.error(f"Error fetching output formatting config: {str(e)}")
            return {
                'format_type': 'Structured',
                'include_summary': True,
                'include_recommendations': True,
                'include_visualizations': True,
                'sections': [
                    'Executive Summary',
                    'Parameter Analysis',
                    'Issues Identified',
                    'Recommendations',
                    'Economic Impact',
                    'Priority Actions'
                ]
            }
    
    def _get_tagging_config(self) -> Dict[str, Any]:
        """Get tagging configuration from Firestore"""
        try:
            db = self._get_db()
            config_ref = db.collection('ai_config').document('tagging_system')
            doc = config_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                # Return default configuration
                return {
                    'enable_auto_tagging': True,
                    'severity_tags': True,
                    'category_tags': True,
                    'custom_tags': [],
                    'confidence_threshold': 0.7,
                    'auto_rules': [
                        {
                            'keyword': 'deficiency',
                            'tag': 'nutrient_deficiency',
                            'category': 'Issue',
                            'confidence': 0.8
                        },
                        {
                            'keyword': 'excess',
                            'tag': 'nutrient_excess',
                            'category': 'Issue',
                            'confidence': 0.8
                        },
                        {
                            'keyword': 'fertilizer',
                            'tag': 'fertilization_needed',
                            'category': 'Recommendation',
                            'confidence': 0.7
                        }
                    ]
                }
        
        except Exception as e:
            logger.error(f"Error fetching tagging config: {str(e)}")
            return {
                'enable_auto_tagging': True,
                'severity_tags': True,
                'category_tags': True,
                'custom_tags': []
            }
    
    def _get_advanced_settings(self) -> Dict[str, Any]:
        """Get advanced settings configuration from Firestore"""
        try:
            db = self._get_db()
            config_ref = db.collection('ai_config').document('advanced_settings')
            doc = config_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                # Return default configuration
                return {
                    'temperature': 0.0,  # Maximum accuracy and predictability
                    'max_tokens': 128000,  # GPT-4o maximum output tokens
                    'top_p': 0.9,
                    'frequency_penalty': 0.0,
                    'presence_penalty': 0.0,
                    'enable_rag': True,
                    'enable_caching': True,
                    'enable_streaming': False,
                    'retry_attempts': 3,
                    'content_filter': True,
                    'fact_checking': False,
                    'confidence_threshold': 0.7,
                    'response_format': 'structured',
                    'model_version': 'gpt-4o',
                    'timeout_seconds': 30,
                    'max_concurrent_requests': 5
                }
        
        except Exception as e:
            logger.error(f"Error fetching advanced settings: {str(e)}")
            return {
                'temperature': 0.7,
                'max_tokens': 2000,
                'include_confidence_scores': True,
                'enable_rag': True,
                'response_format': 'structured'
            }
    
    def _prepare_llm_context_with_prompt(self, analysis_data: Dict[str, Any], active_prompt: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Prepare LLM context using active prompt and all configurations from Firestore"""
        try:
            prompt_text = active_prompt.get('prompt_text', '')
            # For backward compatibility, use empty strings if instructions/steps don't exist
            prompt_instructions = active_prompt.get('instructions', '')
            prompt_steps = active_prompt.get('steps', [])
            
            # Get reference documents
            reference_docs = self._get_reference_documents()
            reference_context = ""
            if reference_docs:
                reference_context = "\n\nReference Materials:\n"
                for doc in reference_docs:
                    reference_context += f"--- {doc.get('name', 'Unknown')} ({doc.get('type', 'Unknown')}) ---\n"
                    reference_context += f"Category: {doc.get('category', 'General')}\n"
                    reference_context += f"Priority: {doc.get('priority', 'Medium')}\n"
                    reference_context += f"Content: {doc.get('content', '')[:500]}...\n\n"
            
            # Get configuration settings
            output_formatting = self._get_output_formatting_config()
            tagging_config = self._get_tagging_config()
            advanced_settings = self._get_advanced_settings()
            
            # Prepare analysis data
            parameters_summary = self._prepare_parameters_summary(analysis_data)
            issues_summary = self._prepare_issues_summary(analysis_data)
            mpob_standards = self._get_mpob_standards_text(analysis_data.get('report_type', 'soil'))
            
            # Build comprehensive context with all configurations
            context = f"""
{active_prompt.get('name', 'Analysis Prompt')}

{prompt_text}

{reference_context}

Lab Data:
{parameters_summary}

Issues Identified:
{issues_summary}

MPOB Standards:
{mpob_standards}

Output Formatting Requirements:
- Format Type: {output_formatting.get('format_type', 'Structured')}
- Language: {output_formatting.get('language', 'English')}
- Tone: {output_formatting.get('tone', 'Professional')}
- Include Summary: {output_formatting.get('include_summary', True)}
- Include Recommendations: {output_formatting.get('include_recommendations', True)}
- Include Visualizations: {output_formatting.get('include_visualizations', True)}
- Required Sections: {', '.join(output_formatting.get('sections', []))}
- Use Icons: {output_formatting.get('use_icons', True)}
- Use Colors: {output_formatting.get('use_colors', True)}
- Max Length: {output_formatting.get('max_length', 1000)} words

Tagging Requirements:
- Auto Tagging: {tagging_config.get('enable_auto_tagging', True)}
- Severity Tags: {tagging_config.get('severity_tags', True)}
- Category Tags: {tagging_config.get('category_tags', True)}
- Confidence Threshold: {tagging_config.get('confidence_threshold', 0.7)}
- Custom Tags: {', '.join(tagging_config.get('custom_tags', []))}
- Auto Rules: {len(tagging_config.get('auto_rules', []))} rules configured

Advanced Settings:
- Model Version: {advanced_settings.get('model_version', 'gpt-4o')}
- Temperature: {advanced_settings.get('temperature', 0.7)}
- Max Tokens: {advanced_settings.get('max_tokens', 2000)}
- Top P: {advanced_settings.get('top_p', 0.9)}
- Frequency Penalty: {advanced_settings.get('frequency_penalty', 0.0)}
- Presence Penalty: {advanced_settings.get('presence_penalty', 0.0)}
- RAG Enabled: {advanced_settings.get('enable_rag', True)}
- Caching Enabled: {advanced_settings.get('enable_caching', True)}
- Streaming Enabled: {advanced_settings.get('enable_streaming', False)}
- Content Filter: {advanced_settings.get('content_filter', True)}
- Fact Checking: {advanced_settings.get('fact_checking', False)}
- Response Format: {advanced_settings.get('response_format', 'structured')}
- Retry Attempts: {advanced_settings.get('retry_attempts', 3)}
- Timeout: {advanced_settings.get('timeout_seconds', 30)} seconds

Report Type: {analysis_data.get('report_type', 'unknown')}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CRITICAL INSTRUCTIONS:
1. You MUST follow each step in the prompt EXACTLY as numbered (Step 1, Step 2, etc.)
2. Complete each step fully before moving to the next step
3. Provide detailed analysis for each step as specified in the prompt
4. Do not skip any steps or combine steps
5. Use the reference materials to enhance accuracy
6. Apply appropriate tags based on the tagging configuration
7. Format the response according to the output formatting requirements
8. Ensure all calculations, recommendations, and forecasts are accurate and actionable

Please provide a comprehensive analysis following the instructions, steps, and formatting requirements above. Use the reference materials to enhance the accuracy and depth of your analysis. Apply appropriate tags based on the tagging configuration and ensure the response format matches the specified requirements.
"""
            
            return context
            
        except Exception as e:
            logger.error(f"Error preparing LLM context: {str(e)}")
            return self._get_default_prompt()
    
    def analyze_parameters(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze extracted parameters against MPOB standards"""
        try:
            parameters = extracted_data.get('parameters', [])
            report_type = extracted_data.get('report_type', 'unknown')
            
            if not parameters:
                return {'error': 'No parameters found in extracted data'}
            
            # Get appropriate standards
            if report_type == 'soil':
                standards = self.mpob_standards.soil_standards
            elif report_type == 'leaf':
                standards = self.mpob_standards.leaf_standards
            else:
                # Try to determine from parameters
                param_names = [p.get('Parameter', '') for p in parameters]
                if any(p in ['pH', 'Organic Carbon', 'C.E.C'] for p in param_names):
                    standards = self.mpob_standards.soil_standards
                    report_type = 'soil'
                else:
                    standards = self.mpob_standards.leaf_standards
                    report_type = 'leaf'
            
            # Analyze each parameter
            analysis_results = []
            issues = []
            
            for param in parameters:
                param_name = param.get('Parameter', '')
                param_value = param.get('Value', 0)
                param_unit = param.get('Unit', '')
                
                if param_name in standards:
                    standard = standards[param_name]
                    
                    # Determine status
                    status = 'normal'
                    severity = 'low'
                    recommendation = None
                    
                    if param_value < standard['min']:
                        status = 'low'
                        severity = 'medium' if param_value < standard['min'] * 0.8 else 'low'
                        if param_value < standard['min'] * 0.6:
                            severity = 'high'
                        recommendation = self._get_deficiency_recommendation(param_name, param_value, standard, report_type)
                    elif param_value > standard['max']:
                        status = 'high'
                        severity = 'medium' if param_value > standard['max'] * 1.2 else 'low'
                        if param_value > standard['max'] * 1.5:
                            severity = 'high'
                        recommendation = self._get_excess_recommendation(param_name, param_value, standard, report_type)
                    
                    analysis_result = {
                        'parameter': param_name,
                        'value': param_value,
                        'unit': param_unit,
                        'standard_min': standard['min'],
                        'standard_max': standard['max'],
                        'optimal': standard['optimal'],
                        'status': status,
                        'severity': severity,
                        'recommendation': recommendation
                    }
                    
                    analysis_results.append(analysis_result)
                    
                    # Add to issues if not normal
                    if status != 'normal':
                        issues.append({
                            'parameter': param_name,
                            'description': f"{param_name} is {status} ({param_value} {param_unit} vs {standard['min']}-{standard['max']} {standard['unit']})",
                            'severity': severity,
                            'recommendation': recommendation
                        })
            
            return {
                'success': True,
                'report_type': report_type,
                'analysis_results': analysis_results,
                'issues': issues,
                'total_parameters': len(analysis_results),
                'issues_count': len(issues)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing parameters: {str(e)}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _get_deficiency_recommendation(self, param_name: str, value: float, standard: Dict, report_type: str) -> Dict[str, Any]:
        """Get recommendation for parameter deficiency"""
        recommendations = {
            'soil': {
                'pH': {
                    'action': 'Lime Application',
                    'description': 'Apply agricultural lime to increase soil pH',
                    'dosage': f'{2 + (standard["min"] - value) * 2:.1f} tons/hectare',
                    'cost_estimate': f'RM {(2 + (standard["min"] - value) * 2) * 150:.0f}'
                },
                'Nitrogen': {
                    'action': 'Nitrogen Fertilizer',
                    'description': 'Apply urea or ammonium sulfate',
                    'dosage': f'{1.5 + (standard["optimal"] - value) * 10:.1f} kg/palm',
                    'cost_estimate': f'RM {(1.5 + (standard["optimal"] - value) * 10) * 2.5:.0f} per palm'
                },
                'Available P': {
                    'action': 'Phosphorus Fertilizer',
                    'description': 'Apply rock phosphate or triple superphosphate',
                    'dosage': f'{0.5 + (standard["optimal"] - value) * 0.02:.1f} kg/palm',
                    'cost_estimate': f'RM {(0.5 + (standard["optimal"] - value) * 0.02) * 3:.0f} per palm'
                },
                'Exch. K': {
                    'action': 'Potassium Fertilizer',
                    'description': 'Apply muriate of potash (KCl)',
                    'dosage': f'{1.0 + (standard["optimal"] - value) * 5:.1f} kg/palm',
                    'cost_estimate': f'RM {(1.0 + (standard["optimal"] - value) * 5) * 2:.0f} per palm'
                }
            },
            'leaf': {
                'N': {
                    'action': 'Foliar Nitrogen Application',
                    'description': 'Apply foliar urea spray',
                    'dosage': f'{2 + (standard["optimal"] - value) * 2:.1f}% urea solution',
                    'cost_estimate': f'RM {(2 + (standard["optimal"] - value) * 2) * 50:.0f} per hectare'
                },
                'P': {
                    'action': 'Phosphorus Supplement',
                    'description': 'Apply phosphoric acid or DAP',
                    'dosage': f'{0.3 + (standard["optimal"] - value) * 2:.1f} kg/palm',
                    'cost_estimate': f'RM {(0.3 + (standard["optimal"] - value) * 2) * 4:.0f} per palm'
                },
                'K': {
                    'action': 'Potassium Boost',
                    'description': 'Increase KCl application',
                    'dosage': f'{1.5 + (standard["optimal"] - value) * 1.5:.1f} kg/palm',
                    'cost_estimate': f'RM {(1.5 + (standard["optimal"] - value) * 1.5) * 2:.0f} per palm'
                }
            }
        }
        
        return recommendations.get(report_type, {}).get(param_name, {
            'action': f'Address {param_name} deficiency',
            'description': f'Consult agronomist for {param_name} supplementation',
            'dosage': 'As recommended by specialist',
            'cost_estimate': 'Variable'
        })
    
    def _get_excess_recommendation(self, param_name: str, value: float, standard: Dict, report_type: str) -> Dict[str, Any]:
        """Get recommendation for parameter excess"""
        recommendations = {
            'soil': {
                'pH': {
                    'action': 'Soil Acidification',
                    'description': 'Apply sulfur or organic matter to reduce pH',
                    'dosage': f'{(value - standard["max"]) * 100:.0f} kg sulfur/hectare',
                    'cost_estimate': f'RM {(value - standard["max"]) * 100 * 1.5:.0f}'
                },
                'Exch. K': {
                    'action': 'Reduce Potassium Input',
                    'description': 'Temporarily reduce or stop K fertilizer application',
                    'dosage': 'Stop K fertilizer for 3-6 months',
                    'cost_estimate': 'RM 0 (cost saving)'
                }
            },
            'leaf': {
                'K': {
                    'action': 'Balance Nutrition',
                    'description': 'Reduce K fertilizer and increase Mg application',
                    'dosage': 'Reduce K by 30%, increase Mg by 20%',
                    'cost_estimate': 'RM 50-100 per palm'
                }
            }
        }
        
        return recommendations.get(report_type, {}).get(param_name, {
            'action': f'Manage {param_name} excess',
            'description': f'Reduce {param_name} inputs and monitor levels',
            'dosage': 'Reduce by 20-30%',
            'cost_estimate': 'Variable'
        })
    
    def generate_ai_insights(self, analysis_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights using active prompts from Firestore"""
        try:
            if not self.llm:
                return self._generate_mock_insights(analysis_data, options)
            
            # Get active prompt from Firestore
            active_prompt = self._get_active_prompt()
            if not active_prompt:
                logger.warning("No active prompt found, using mock insights")
                return self._generate_mock_insights(analysis_data, options)
            
            # Prepare context with active prompt
            context = self._prepare_llm_context_with_prompt(analysis_data, active_prompt, options)
            
            # Generate AI response using the prepared context
            response = self.llm.invoke([
                SystemMessage(content="You are an expert agricultural consultant specializing in oil palm cultivation and MPOB standards."),
                HumanMessage(content=context)
            ])
            
            # Parse AI response
            insights = self._parse_llm_response(response.content, analysis_data)
            
            # Add prompt metadata
            insights['prompt_used'] = {
                'prompt_id': active_prompt.get('id'),
                'prompt_name': active_prompt.get('name'),
                'prompt_version': active_prompt.get('version', '1.0')
            }
            
            # Add economic analysis if requested
            if options.get('include_economic', True):
                insights['economic_analysis'] = self._calculate_economic_impact(analysis_data)
            
            # Add yield forecast if requested
            if options.get('include_forecast', True):
                insights['yield_forecast'] = self._generate_yield_forecast(analysis_data)
            
            # Auto-save if enabled
            if general_settings.get('auto_save_results', True):
                self._auto_save_results(insights, analysis_data)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return self._generate_mock_insights(analysis_data, options)
    
    def _get_analysis_prompt(self) -> str:
        """Get analysis prompt from Firebase or use default"""
        try:
            db = self._get_db()
            doc_ref = db.collection('analysis_prompts').document('default')
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict().get('prompt_template', self._get_default_prompt())
            else:
                return self._get_default_prompt()
                
        except Exception as e:
            logger.error(f"Error fetching prompt from Firebase: {str(e)}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default analysis prompt"""
        return """
        You are an expert agricultural consultant specializing in oil palm cultivation and MPOB standards.
        
        Analyze the provided SP LAB test report data and provide comprehensive recommendations.
        
        Focus on:
        1. Nutrient deficiencies and excesses
        2. Soil health indicators
        3. Practical fertilizer recommendations
        4. Economic considerations
        5. Timeline for implementation
        6. Expected outcomes
        
        Use MPOB standards as the benchmark and provide specific, actionable advice.
        Consider the Malaysian oil palm industry context and current best practices.
        
        Format your response clearly with sections for summary, recommendations, and economic analysis.
        """
    
    def _prepare_parameters_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Prepare parameters summary for AI analysis"""
        results = analysis_data.get('analysis_results', [])
        summary_lines = []
        
        for result in results:
            status_emoji = {'normal': '✅', 'low': '⬇️', 'high': '⬆️'}.get(result['status'], '❓')
            summary_lines.append(
                f"{status_emoji} {result['parameter']}: {result['value']} {result['unit']} "
                f"(Standard: {result['standard_min']}-{result['standard_max']} {result['unit']})"
            )
        
        return '\n'.join(summary_lines)
    
    def _prepare_issues_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Prepare issues summary for AI analysis"""
        issues = analysis_data.get('issues', [])
        if not issues:
            return "No significant issues identified."
        
        summary_lines = []
        for issue in issues:
            severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(issue['severity'], '❓')
            summary_lines.append(f"{severity_emoji} {issue['description']}")
        
        return '\n'.join(summary_lines)
    
    def _fill_template_placeholders(self, template: str, placeholders: Dict[str, str]) -> str:
        """Fill template placeholders with actual values"""
        filled_template = template
        for key, value in placeholders.items():
            filled_template = filled_template.replace(f"{{{key}}}", str(value))
        return filled_template
    
    def _get_mpob_standards_text(self, report_type: str) -> str:
        """Get MPOB standards as text for AI context"""
        if report_type == 'soil':
            standards = self.mpob_standards.soil_standards
        else:
            standards = self.mpob_standards.leaf_standards
        
        text_lines = []
        for param, values in standards.items():
            text_lines.append(f"{param}: {values['min']}-{values['max']} {values['unit']} (optimal: {values['optimal']})")
        
        return "\n".join(text_lines)
    
    def _prepare_parameters_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Prepare parameters summary for LLM context"""
        try:
            parameters = analysis_data.get('parameters', [])
            if not parameters:
                return "No parameters found"
            
            summary = "Parameters:\n"
            for param in parameters:
                param_name = param.get('Parameter', 'Unknown')
                param_value = param.get('Value', 0)
                param_unit = param.get('Unit', '')
                summary += f"- {param_name}: {param_value} {param_unit}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error preparing parameters summary: {str(e)}")
            return "Error preparing parameters summary"
    
    def _prepare_issues_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Prepare issues summary for LLM context"""
        try:
            issues = analysis_data.get('issues', [])
            if not issues:
                return "No issues identified"
            
            summary = "Issues:\n"
            for issue in issues:
                param = issue.get('parameter', 'Unknown')
                severity = issue.get('severity', 'medium')
                description = issue.get('description', 'No description')
                summary += f"- {param} ({severity}): {description}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error preparing issues summary: {str(e)}")
            return "Error preparing issues summary"
    
    def _parse_llm_response(self, response_content: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response into structured insights"""
        try:
            # Basic parsing - in a real implementation, you might use more sophisticated parsing
            insights = {
                'summary': response_content[:500] + "..." if len(response_content) > 500 else response_content,
                'detailed_analysis': response_content,
                'recommendations': [],
                'risk_assessment': 'Moderate',
                'implementation_timeline': '3-6 months'
            }
            
            # Extract recommendations if present
            if 'recommendation' in response_content.lower():
                lines = response_content.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['apply', 'use', 'add', 'fertilizer', 'lime']):
                        insights['recommendations'].append(line.strip())
            
            return insights
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return {
                'summary': 'Analysis completed',
                'detailed_analysis': response_content,
                'recommendations': [],
                'risk_assessment': 'Unknown',
                'implementation_timeline': 'Unknown'
            }
    
    def _parse_ai_response_dynamic(self, response: str, ai_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response with dynamic formatting"""
        output_format = get_output_format('standard_report')
        
        # Try to parse as JSON if structured format is enabled
        if output_format.get('format_type') == 'json':
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
        
        # Fallback to text parsing
        return {
            'summary': response[:500] + '...' if len(response) > 500 else response,
            'recommendations': [
                {'action': 'Follow AI recommendations', 'description': 'Implement suggested actions', 'priority': 'high'}
            ],
            'risk_analysis': 'AI-generated risk analysis would be parsed here',
            'implementation_timeline': '3-6 months for full implementation'
        }
    
    def _apply_dynamic_tagging(self, insights: Dict[str, Any], analysis_data: Dict[str, Any], ai_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply dynamic tagging based on configuration"""
        tagging_config = get_tagging_config()
        
        if tagging_config.get('enable_auto_tagging', True):
            tags = []
            
            # Add severity tags
            issues = analysis_data.get('issues', [])
            if any(issue.get('severity') == 'high' for issue in issues):
                tags.append('high_priority')
            
            # Add report type tag
            tags.append(f"report_type_{analysis_data.get('report_type', 'unknown')}")
            
            # Add custom tags from config
            custom_tags = tagging_config.get('custom_tags', [])
            tags.extend(custom_tags)
            
            insights['tags'] = tags
        
        return insights
    
    def _auto_save_results(self, insights: Dict[str, Any], analysis_data: Dict[str, Any]) -> None:
        """Auto-save results to Firebase if enabled"""
        try:
            db = self._get_db()
            doc_ref = db.collection('analysis_results').document()
            doc_ref.set({
                'insights': insights,
                'analysis_data': analysis_data,
                'timestamp': datetime.now(),
                'auto_saved': True
            })
            logger.info(f"Results auto-saved to document: {doc_ref.id}")
        except Exception as e:
            logger.error(f"Failed to auto-save results: {str(e)}")
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        # This is a simplified parser - in production, you'd want more sophisticated parsing
        return {
            'summary': response[:500] + '...' if len(response) > 500 else response,
            'recommendations': [
                {'action': 'Follow AI recommendations', 'description': 'Implement suggested actions', 'priority': 'high'}
            ],
            'risk_analysis': 'AI-generated risk analysis would be parsed here',
            'implementation_timeline': '3-6 months for full implementation'
        }
    
    def _calculate_economic_impact(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate economic impact of recommendations"""
        issues = analysis_data.get('issues', [])
        
        total_cost = 0
        cost_breakdown = []
        
        for issue in issues:
            if issue.get('recommendation') and 'cost_estimate' in issue['recommendation']:
                cost_str = issue['recommendation']['cost_estimate']
                # Extract numeric value from cost string
                import re
                cost_match = re.search(r'RM\s*(\d+)', cost_str)
                if cost_match:
                    cost = float(cost_match.group(1))
                    total_cost += cost
                    cost_breakdown.append({
                        'item': issue['parameter'],
                        'cost': cost,
                        'description': issue['recommendation']['action']
                    })
        
        # Calculate ROI estimates
        expected_yield_increase = min(len(issues) * 2, 15)  # Max 15% increase
        current_yield = 20  # tons/hectare (average)
        yield_value_per_ton = 2500  # RM per ton
        
        annual_revenue_increase = current_yield * (expected_yield_increase / 100) * yield_value_per_ton
        roi_percentage = (annual_revenue_increase / total_cost * 100) if total_cost > 0 else 0
        payback_months = (total_cost / (annual_revenue_increase / 12)) if annual_revenue_increase > 0 else 0
        
        return {
            'total_cost': total_cost,
            'cost_breakdown': cost_breakdown,
            'expected_yield_increase': expected_yield_increase,
            'annual_revenue_increase': annual_revenue_increase,
            'roi_percentage': roi_percentage,
            'payback_months': payback_months
        }
    
    def _generate_yield_forecast(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate 5-year yield forecast"""
        issues_count = len(analysis_data.get('issues', []))
        
        # Base yield (current)
        base_yield = 18.5  # tons/hectare
        
        # Calculate improvement potential
        max_improvement = min(issues_count * 1.5, 20)  # Max 20% improvement
        
        # Generate 5-year forecast
        years = list(range(2024, 2030))
        current_scenario = [base_yield + i * 0.2 for i in range(6)]  # Slow natural growth
        improved_scenario = [
            base_yield,  # Year 1: Implementation
            base_yield + max_improvement * 0.3,  # Year 2: 30% of improvement
            base_yield + max_improvement * 0.6,  # Year 3: 60% of improvement
            base_yield + max_improvement * 0.8,  # Year 4: 80% of improvement
            base_yield + max_improvement * 0.9,  # Year 5: 90% of improvement
            base_yield + max_improvement  # Year 6: Full improvement
        ]
        
        return {
            'years': years,
            'current_scenario': current_scenario,
            'improved_scenario': improved_scenario,
            'improvement_potential': max_improvement,
            'total_additional_revenue': sum(improved_scenario) - sum(current_scenario)
        }
    
    def _generate_mock_insights(self, analysis_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock insights when OpenAI is not available"""
        issues = analysis_data.get('issues', [])
        
        mock_insights = {
            'summary': f"Analysis completed for {analysis_data.get('report_type', 'unknown')} report. "
                      f"Found {len(issues)} issues requiring attention. "
                      f"Recommendations focus on nutrient balance and soil health optimization.",
            'recommendations': [
                {
                    'action': 'Nutrient Management',
                    'description': 'Implement balanced fertilization program based on identified deficiencies',
                    'priority': 'high',
                    'timeline': '1-3 months'
                },
                {
                    'action': 'Soil Health Monitoring',
                    'description': 'Establish regular soil testing schedule every 6 months',
                    'priority': 'medium',
                    'timeline': 'Ongoing'
                }
            ],
            'risk_analysis': 'Moderate risk of yield reduction if issues are not addressed within 6 months',
            'implementation_timeline': '3-6 months for full implementation'
        }
        
        if options.get('include_economic', True):
            mock_insights['economic_analysis'] = self._calculate_economic_impact(analysis_data)
        
        if options.get('include_forecast', True):
            mock_insights['yield_forecast'] = self._generate_yield_forecast(analysis_data)
        
        return mock_insights

def analyze_lab_data(extracted_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to analyze lab data"""
    try:
        # Initialize analysis engine
        engine = AnalysisEngine()
        
        # Convert new sample format to parameters format if needed
        if 'samples' in extracted_data and 'parameters' not in extracted_data:
            extracted_data = engine._convert_samples_to_parameters(extracted_data)
        
        # Analyze parameters against MPOB standards
        parameter_analysis = engine.analyze_parameters(extracted_data)
        
        if 'error' in parameter_analysis:
            return parameter_analysis
        
        # Generate AI insights
        ai_insights = engine.generate_ai_insights(parameter_analysis, options)
        
        # Combine results
        final_result = {
            **parameter_analysis,
            **ai_insights,
            'analysis_timestamp': datetime.now().isoformat(),
            'options_used': options
        }
        
        return final_result
        
    except Exception as e:
        logger.error(f"Error in analyze_lab_data: {str(e)}")
        return {'error': f'Analysis failed: {str(e)}'}

# Example usage
if __name__ == "__main__":
    # Test with sample data
    sample_data = {
        'report_type': 'soil',
        'parameters': [
            {'Parameter': 'pH', 'Value': 4.2, 'Unit': '-'},
            {'Parameter': 'Nitrogen', 'Value': 0.08, 'Unit': '%'},
            {'Parameter': 'Available P', 'Value': 12, 'Unit': 'mg/kg'},
            {'Parameter': 'Exch. K', 'Value': 0.10, 'Unit': 'meq%'}
        ]
    }
    
    options = {
        'include_economic': True,
        'include_forecast': True,
        'detailed_recommendations': True
    }
    
    result = analyze_lab_data(sample_data, options)
    print(f"Analysis completed with {result.get('issues_count', 0)} issues identified")
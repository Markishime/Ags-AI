import os
import openai
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import streamlit as st
from firebase_config import get_firestore_client, COLLECTIONS, DEFAULT_MPOB_STANDARDS
import json
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

class AnalysisEngine:
    """Handle AI-powered analysis of lab data"""
    
    def __init__(self):
        # Initialize OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY', st.secrets.get('OPENAI_API_KEY', ''))
        
        # Initialize LangChain components
        self.llm = OpenAI(
            temperature=0.3,
            max_tokens=2000,
            openai_api_key=openai.api_key
        )
        
        # Initialize embeddings for RAG using the best model
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",  # Best embedding model
            openai_api_key=openai.api_key
        )
        
        # Load MPOB standards
        self.mpob_standards = DEFAULT_MPOB_STANDARDS
        
        # Initialize vector store for RAG (will be loaded from knowledge base)
        self.vector_store = None
        self._initialize_rag_system()
        
        # Analysis prompts
        self.analysis_prompts = self._load_analysis_prompts()
    
    def _initialize_rag_system(self):
        """Initialize RAG system with MPOB knowledge base"""
        try:
            # MPOB knowledge base content
            mpob_knowledge = """
            Malaysian Palm Oil Board (MPOB) Nutrient Standards for Oil Palm:
            
            LEAF ANALYSIS STANDARDS:
            - Nitrogen (N): 2.4-2.8% (optimal: 2.6%)
            - Phosphorus (P): 0.15-0.18% (optimal: 0.165%)
            - Potassium (K): 0.9-1.2% (optimal: 1.05%)
            - Magnesium (Mg): 0.25-0.35% (optimal: 0.3%)
            - Calcium (Ca): 0.5-0.7% (optimal: 0.6%)
            - Boron (B): 15-25 mg/kg (optimal: 20 mg/kg)
            - Copper (Cu): 4-8 mg/kg (optimal: 6 mg/kg)
            - Zinc (Zn): 15-25 mg/kg (optimal: 20 mg/kg)
            
            SOIL ANALYSIS STANDARDS:
            - pH: 4.5-5.5 (optimal: 5.0)
            - Nitrogen: 0.08-0.15% (optimal: 0.12%)
            - Organic Carbon: 0.6-1.2% (optimal: 0.9%)
            - Total Phosphorus: 50-100 mg/kg (optimal: 75 mg/kg)
            - Available Phosphorus: 3-8 mg/kg (optimal: 5 mg/kg)
            - Exchangeable Potassium: 0.08-0.15 meq% (optimal: 0.12 meq%)
            - Exchangeable Calcium: 0.2-0.5 meq% (optimal: 0.35 meq%)
            - Exchangeable Magnesium: 0.15-0.25 meq% (optimal: 0.2 meq%)
            - Cation Exchange Capacity (CEC): 5.0-15.0 (optimal: 10.0)
            
            DEFICIENCY SYMPTOMS AND RECOMMENDATIONS:
            
            Nitrogen Deficiency:
            - Symptoms: Yellowing of older leaves, reduced growth
            - Recommendation: Apply 2-3 kg urea per palm, split into 2-3 applications
            - Cost estimate: RM 15-25 per palm annually
            
            Phosphorus Deficiency:
            - Symptoms: Dark green leaves, poor root development
            - Recommendation: Apply 1-2 kg rock phosphate per palm
            - Cost estimate: RM 20-30 per palm annually
            
            Potassium Deficiency:
            - Symptoms: Orange spotting on leaves, poor fruit development
            - Recommendation: Apply 3-4 kg muriate of potash per palm
            - Cost estimate: RM 25-35 per palm annually
            
            Magnesium Deficiency:
            - Symptoms: Yellowing between leaf veins
            - Recommendation: Apply 1-2 kg kieserite per palm
            - Cost estimate: RM 10-20 per palm annually
            
            Soil pH Management:
            - If pH < 4.5: Apply 2-3 kg lime per palm
            - If pH > 5.5: Apply sulfur or organic matter
            - Cost estimate: RM 5-15 per palm
            
            YIELD IMPACT FACTORS:
            - Optimal nutrition can increase yield by 15-25%
            - Nutrient deficiencies can reduce yield by 20-40%
            - Proper soil pH improves nutrient availability by 30%
            - Balanced fertilization increases oil content by 5-10%
            
            ECONOMIC CONSIDERATIONS:
            - Average palm produces 150-200 kg FFB annually
            - Current FFB price: RM 600-800 per tonne
            - Fertilizer cost typically 15-20% of gross income
            - ROI on proper nutrition: 3:1 to 5:1
            """
            
            # Create text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            # Split knowledge base into chunks
            texts = text_splitter.split_text(mpob_knowledge)
            
            # Create vector store
            self.vector_store = FAISS.from_texts(
                texts,
                self.embeddings,
                metadatas=[{"source": "MPOB_standards"} for _ in texts]
            )
            
        except Exception as e:
            st.warning(f"RAG system initialization warning: {str(e)}")
            self.vector_store = None
    
    def _load_analysis_prompts(self) -> Dict[str, str]:
        """Load analysis prompts from Firestore or use defaults"""
        try:
            db = get_firestore_client()
            if db:
                prompts_ref = db.collection(COLLECTIONS['analysis_prompts']).document('default')
                prompts_doc = prompts_ref.get()
                
                if prompts_doc.exists:
                    return prompts_doc.to_dict()
        except Exception as e:
            st.warning(f"Could not load custom prompts: {str(e)}")
        
        # Default prompts
        return {
            'analysis_template': """
            You are an expert agricultural consultant specializing in oil palm cultivation and nutrition analysis.
            
            Based on the following lab analysis data and MPOB standards, provide a comprehensive analysis:
            
            Lab Data:
            {lab_data}
            
            Report Type: {report_type}
            
            MPOB Standards:
            {mpob_standards}
            
            Additional Context:
            {rag_context}
            
            Please provide:
            1. Parameter Analysis: Compare each parameter against MPOB standards
            2. Issues Identified: List any deficiencies or excesses
            3. Recommendations: Specific fertilizer and management recommendations
            4. Economic Impact: Estimated costs and potential yield impact
            5. Priority Actions: Most critical actions to take first
            
            Format your response as a structured analysis with clear sections.
            """,
            
            'recommendation_template': """
            Based on the analysis of {report_type} data, provide specific recommendations:
            
            Issues Found:
            {issues}
            
            For each issue, provide:
            1. Specific fertilizer type and application rate
            2. Application timing and method
            3. Expected cost per palm
            4. Expected improvement timeline
            5. Monitoring recommendations
            
            Consider MPOB best practices and current market conditions.
            """
        }
    
    def analyze_lab_data(self, lab_data: Dict[str, Any], report_type: str, 
                        generate_recommendations: bool = True, 
                        create_forecast: bool = True) -> Dict[str, Any]:
        """Analyze lab data against MPOB standards
        
        Args:
            lab_data: Extracted lab data
            report_type: Type of report ('soil' or 'leaf')
            generate_recommendations: Whether to generate recommendations
            create_forecast: Whether to create yield forecast
            
        Returns:
            dict: Analysis results
        """
        try:
            # Step 1: Compare against MPOB standards
            comparison_results = self._compare_with_standards(lab_data, report_type)
            
            # Step 2: Identify issues
            issues = self._identify_issues(comparison_results, report_type)
            
            # Step 3: Get RAG context
            rag_context = self._get_rag_context(issues, report_type)
            
            # Step 4: Generate AI analysis
            ai_analysis = self._generate_ai_analysis(
                lab_data, report_type, comparison_results, rag_context
            )
            
            # Step 5: Generate recommendations if requested
            recommendations = []
            if generate_recommendations:
                recommendations = self._generate_recommendations(issues, report_type, rag_context)
            
            # Step 6: Create forecast if requested
            forecast = {}
            if create_forecast:
                forecast = self._create_yield_forecast(comparison_results, issues)
            
            # Step 7: Calculate economic impact
            economic_impact = self._calculate_economic_impact(issues, recommendations)
            
            return {
                'success': True,
                'analysis': {
                    'comparison_results': comparison_results,
                    'issues': issues,
                    'ai_analysis': ai_analysis,
                    'recommendations': recommendations,
                    'forecast': forecast,
                    'economic_impact': economic_impact,
                    'summary': self._generate_summary(issues, recommendations, economic_impact)
                },
                'message': 'Analysis completed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'analysis': {},
                'message': f'Analysis error: {str(e)}'
            }
    
    def _compare_with_standards(self, lab_data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Compare lab data with MPOB standards"""
        standards = self.mpob_standards[f'{report_type}_standards']
        comparison_results = {}
        
        for sample_id, sample_data in lab_data.items():
            if isinstance(sample_data, dict):
                sample_comparison = {}
                
                for param, value in sample_data.items():
                    if isinstance(value, (int, float)):
                        # Find matching standard
                        standard_key = self._map_parameter_to_standard(param, report_type)
                        
                        if standard_key in standards:
                            standard = standards[standard_key]
                            
                            status = 'optimal'
                            if value < standard['min']:
                                status = 'deficient'
                            elif value > standard['max']:
                                status = 'excessive'
                            
                            sample_comparison[param] = {
                                'value': value,
                                'standard': standard,
                                'status': status,
                                'deviation': value - standard['optimal']
                            }
                
                comparison_results[sample_id] = sample_comparison
        
        return comparison_results
    
    def _map_parameter_to_standard(self, param: str, report_type: str) -> str:
        """Map parameter name to standard key"""
        if report_type == 'leaf':
            mapping = {
                'N_percent': 'N',
                'P_percent': 'P',
                'K_percent': 'K',
                'Mg_mgkg': 'Mg',
                'Ca_mgkg': 'Ca',
                'B_mgkg': 'B',
                'Cu_mgkg': 'Cu',
                'Zn_mgkg': 'Zn'
            }
        else:  # soil
            mapping = {
                'pH': 'pH',
                'Nitrogen_percent': 'Nitrogen',
                'Organic_Carbon_percent': 'Organic_Carbon',
                'Total_P_mgkg': 'Total_P',
                'Available_P_mgkg': 'Available_P',
                'Exch_K_meq': 'Exch_K',
                'Exch_Ca_meq': 'Exch_Ca',
                'Exch_Mg_meq': 'Exch_Mg',
                'CEC': 'CEC'
            }
        
        return mapping.get(param, param)
    
    def _identify_issues(self, comparison_results: Dict[str, Any], report_type: str) -> List[Dict[str, Any]]:
        """Identify nutrient deficiencies and excesses"""
        issues = []
        
        for sample_id, sample_comparison in comparison_results.items():
            for param, comparison in sample_comparison.items():
                if comparison['status'] != 'optimal':
                    issue = {
                        'sample_id': sample_id,
                        'parameter': param,
                        'value': comparison['value'],
                        'standard': comparison['standard'],
                        'status': comparison['status'],
                        'severity': self._calculate_severity(comparison),
                        'description': self._generate_issue_description(param, comparison, report_type)
                    }
                    issues.append(issue)
        
        # Sort by severity
        issues.sort(key=lambda x: x['severity'], reverse=True)
        
        return issues
    
    def _calculate_severity(self, comparison: Dict[str, Any]) -> float:
        """Calculate issue severity based on deviation from optimal"""
        deviation = abs(comparison['deviation'])
        optimal = comparison['standard']['optimal']
        
        # Calculate percentage deviation
        if optimal != 0:
            severity = (deviation / optimal) * 100
        else:
            severity = deviation * 100
        
        return min(severity, 100)  # Cap at 100%
    
    def _generate_issue_description(self, param: str, comparison: Dict[str, Any], report_type: str) -> str:
        """Generate human-readable issue description"""
        value = comparison['value']
        standard = comparison['standard']
        status = comparison['status']
        
        param_name = param.replace('_', ' ').title()
        
        if status == 'deficient':
            return f"{param_name} is deficient ({value} {standard['unit']}) - below optimal range ({standard['min']}-{standard['max']} {standard['unit']})"
        elif status == 'excessive':
            return f"{param_name} is excessive ({value} {standard['unit']}) - above optimal range ({standard['min']}-{standard['max']} {standard['unit']})"
        
        return f"{param_name}: {value} {standard['unit']}"
    
    def _get_rag_context(self, issues: List[Dict[str, Any]], report_type: str) -> str:
        """Get relevant context from RAG system"""
        if not self.vector_store:
            return "MPOB standards context not available"
        
        try:
            # Create query from issues
            issue_params = [issue['parameter'] for issue in issues[:3]]  # Top 3 issues
            query = f"{report_type} analysis {' '.join(issue_params)} MPOB standards recommendations"
            
            # Retrieve relevant documents
            docs = self.vector_store.similarity_search(query, k=3)
            
            # Combine retrieved content
            context = "\n\n".join([doc.page_content for doc in docs])
            
            return context
            
        except Exception as e:
            st.warning(f"RAG retrieval warning: {str(e)}")
            return "MPOB standards context not available"
    
    def _generate_ai_analysis(self, lab_data: Dict[str, Any], report_type: str, 
                             comparison_results: Dict[str, Any], rag_context: str) -> str:
        """Generate AI-powered analysis using LangChain"""
        try:
            # Prepare prompt
            prompt_template = PromptTemplate(
                input_variables=["lab_data", "report_type", "mpob_standards", "rag_context"],
                template=self.analysis_prompts['analysis_template']
            )
            
            # Create chain
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            
            # Generate analysis
            analysis = chain.run(
                lab_data=json.dumps(lab_data, indent=2),
                report_type=report_type,
                mpob_standards=json.dumps(self.mpob_standards[f'{report_type}_standards'], indent=2),
                rag_context=rag_context
            )
            
            return analysis
            
        except Exception as e:
            return f"AI analysis unavailable: {str(e)}"
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]], 
                                 report_type: str, rag_context: str) -> List[Dict[str, Any]]:
        """Generate specific recommendations for identified issues"""
        recommendations = []
        
        # Predefined recommendations based on MPOB guidelines
        recommendation_map = {
            'N_percent': {
                'deficient': {
                    'action': 'Apply nitrogen fertilizer',
                    'fertilizer': 'Urea (46% N)',
                    'rate': '2-3 kg per palm',
                    'timing': 'Split into 2-3 applications throughout the year',
                    'cost_per_palm': 20,
                    'expected_improvement': '2-3 months'
                }
            },
            'P_percent': {
                'deficient': {
                    'action': 'Apply phosphorus fertilizer',
                    'fertilizer': 'Rock phosphate or TSP',
                    'rate': '1-2 kg per palm',
                    'timing': 'Apply once annually',
                    'cost_per_palm': 25,
                    'expected_improvement': '3-6 months'
                }
            },
            'K_percent': {
                'deficient': {
                    'action': 'Apply potassium fertilizer',
                    'fertilizer': 'Muriate of Potash (MOP)',
                    'rate': '3-4 kg per palm',
                    'timing': 'Split into 2 applications',
                    'cost_per_palm': 30,
                    'expected_improvement': '2-4 months'
                }
            },
            'pH': {
                'deficient': {
                    'action': 'Apply lime to increase pH',
                    'fertilizer': 'Agricultural lime',
                    'rate': '2-3 kg per palm',
                    'timing': 'Apply during dry season',
                    'cost_per_palm': 10,
                    'expected_improvement': '6-12 months'
                }
            }
        }
        
        for issue in issues:
            param = issue['parameter']
            status = issue['status']
            
            if param in recommendation_map and status in recommendation_map[param]:
                rec_data = recommendation_map[param][status]
                
                recommendation = {
                    'parameter': param,
                    'issue': issue['description'],
                    'category': 'Fertilizer Application',
                    'priority': 'High' if issue['severity'] > 50 else 'Medium',
                    'action': rec_data['action'],
                    'fertilizer': rec_data['fertilizer'],
                    'application_rate': rec_data['rate'],
                    'timing': rec_data['timing'],
                    'cost_estimate': rec_data['cost_per_palm'],
                    'expected_improvement': rec_data['expected_improvement'],
                    'monitoring': f"Re-test {param} in 6 months"
                }
                
                recommendations.append(recommendation)
        
        return recommendations
    
    def _create_yield_forecast(self, comparison_results: Dict[str, Any], 
                              issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create 5-year yield forecast based on analysis"""
        try:
            # Base yield assumptions
            base_yield = 20  # tonnes FFB per hectare
            current_efficiency = self._calculate_current_efficiency(comparison_results)
            
            # Calculate potential improvement
            improvement_potential = self._calculate_improvement_potential(issues)
            
            # Generate 5-year forecast
            years = list(range(2025, 2030))
            scenarios = {
                'current': [],
                'with_improvements': [],
                'optimal': []
            }
            
            for i, year in enumerate(years):
                # Current scenario (no improvements)
                current_yield = base_yield * current_efficiency
                scenarios['current'].append(current_yield)
                
                # With improvements scenario
                improvement_factor = min(1.0, (i + 1) * 0.05)  # Gradual improvement
                improved_yield = current_yield * (1 + improvement_potential * improvement_factor)
                scenarios['with_improvements'].append(improved_yield)
                
                # Optimal scenario
                optimal_yield = base_yield * 1.2  # 20% above base
                scenarios['optimal'].append(optimal_yield)
            
            # Calculate economic projections
            ffb_price = 700  # RM per tonne
            economic_projections = {}
            
            for scenario, yields in scenarios.items():
                economic_projections[scenario] = {
                    'yields': yields,
                    'revenue': [yield * ffb_price for yield in yields],
                    'total_5_year': sum(yield * ffb_price for yield in yields)
                }
            
            return {
                'years': years,
                'scenarios': scenarios,
                'economic_projections': economic_projections,
                'assumptions': {
                    'base_yield': base_yield,
                    'current_efficiency': current_efficiency,
                    'improvement_potential': improvement_potential,
                    'ffb_price': ffb_price
                }
            }
            
        except Exception as e:
            return {'error': f'Forecast generation error: {str(e)}'}
    
    def _calculate_current_efficiency(self, comparison_results: Dict[str, Any]) -> float:
        """Calculate current nutrient efficiency"""
        total_parameters = 0
        optimal_parameters = 0
        
        for sample_comparison in comparison_results.values():
            for param_comparison in sample_comparison.values():
                total_parameters += 1
                if param_comparison['status'] == 'optimal':
                    optimal_parameters += 1
        
        if total_parameters == 0:
            return 0.8  # Default efficiency
        
        efficiency = optimal_parameters / total_parameters
        return max(0.5, min(1.0, efficiency))  # Clamp between 50% and 100%
    
    def _calculate_improvement_potential(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate potential yield improvement from addressing issues"""
        if not issues:
            return 0.0
        
        # Weight improvements by severity
        total_improvement = 0
        for issue in issues:
            severity_factor = issue['severity'] / 100
            parameter_impact = self._get_parameter_impact(issue['parameter'])
            total_improvement += severity_factor * parameter_impact
        
        return min(0.25, total_improvement)  # Cap at 25% improvement
    
    def _get_parameter_impact(self, parameter: str) -> float:
        """Get yield impact factor for each parameter"""
        impact_factors = {
            'N_percent': 0.15,  # 15% potential impact
            'P_percent': 0.10,
            'K_percent': 0.12,
            'pH': 0.08,
            'Mg_mgkg': 0.05,
            'Ca_mgkg': 0.05,
            'B_mgkg': 0.03,
            'Cu_mgkg': 0.02,
            'Zn_mgkg': 0.03
        }
        
        return impact_factors.get(parameter, 0.02)
    
    def _calculate_economic_impact(self, issues: List[Dict[str, Any]], 
                                  recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate economic impact of issues and recommendations"""
        # Calculate cost of recommendations
        total_cost = sum(rec.get('cost_estimate', 0) for rec in recommendations)
        
        # Calculate potential revenue loss from issues
        base_revenue_per_palm = 150  # kg FFB per palm * RM 0.7 per kg
        revenue_loss = 0
        
        for issue in issues:
            severity_factor = issue['severity'] / 100
            parameter_impact = self._get_parameter_impact(issue['parameter'])
            revenue_loss += base_revenue_per_palm * severity_factor * parameter_impact
        
        # Calculate ROI
        potential_revenue_gain = revenue_loss * 0.8  # 80% recovery
        roi = (potential_revenue_gain / total_cost) if total_cost > 0 else 0
        
        return {
            'total_cost_per_palm': total_cost,
            'potential_revenue_loss_per_palm': revenue_loss,
            'potential_revenue_gain_per_palm': potential_revenue_gain,
            'roi': roi,
            'payback_period_months': (total_cost / (potential_revenue_gain / 12)) if potential_revenue_gain > 0 else 0,
            'recommendations_count': len(recommendations),
            'issues_count': len(issues)
        }
    
    def _generate_summary(self, issues: List[Dict[str, Any]], 
                         recommendations: List[Dict[str, Any]], 
                         economic_impact: Dict[str, Any]) -> str:
        """Generate analysis summary"""
        summary = f"""
        ANALYSIS SUMMARY:
        
        Issues Identified: {len(issues)}
        - High Priority: {len([i for i in issues if i['severity'] > 50])}
        - Medium Priority: {len([i for i in issues if 25 <= i['severity'] <= 50])}
        - Low Priority: {len([i for i in issues if i['severity'] < 25])}
        
        Recommendations: {len(recommendations)}
        
        Economic Impact:
        - Total Investment Required: RM {economic_impact['total_cost_per_palm']:.2f} per palm
        - Potential Revenue Gain: RM {economic_impact['potential_revenue_gain_per_palm']:.2f} per palm
        - Return on Investment: {economic_impact['roi']:.1f}:1
        - Payback Period: {economic_impact['payback_period_months']:.1f} months
        
        Priority Actions:
        {self._get_priority_actions(issues, recommendations)}
        """
        
        return summary
    
    def _get_priority_actions(self, issues: List[Dict[str, Any]], 
                             recommendations: List[Dict[str, Any]]) -> str:
        """Get top 3 priority actions"""
        high_priority_recs = [rec for rec in recommendations if rec.get('priority') == 'High'][:3]
        
        if not high_priority_recs:
            return "No high priority actions identified."
        
        actions = []
        for i, rec in enumerate(high_priority_recs, 1):
            actions.append(f"{i}. {rec['action']} - {rec['fertilizer']} ({rec['application_rate']})")
        
        return "\n        ".join(actions)
    
    def create_analysis_charts(self, comparison_results: Dict[str, Any], 
                              report_type: str) -> Dict[str, Any]:
        """Create visualization charts for analysis results"""
        charts = {}
        
        try:
            # Prepare data for visualization
            parameters = []
            values = []
            statuses = []
            standards_min = []
            standards_max = []
            
            for sample_id, sample_comparison in comparison_results.items():
                for param, comparison in sample_comparison.items():
                    parameters.append(param.replace('_', ' ').title())
                    values.append(comparison['value'])
                    statuses.append(comparison['status'])
                    standards_min.append(comparison['standard']['min'])
                    standards_max.append(comparison['standard']['max'])
            
            # Create comparison chart
            fig = go.Figure()
            
            # Add value bars
            fig.add_trace(go.Bar(
                x=parameters,
                y=values,
                name='Current Values',
                marker_color=['red' if s == 'deficient' else 'orange' if s == 'excessive' else 'green' 
                             for s in statuses]
            ))
            
            # Add standard range
            fig.add_trace(go.Scatter(
                x=parameters,
                y=standards_min,
                mode='markers',
                name='Min Standard',
                marker=dict(symbol='triangle-down', size=10, color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=parameters,
                y=standards_max,
                mode='markers',
                name='Max Standard',
                marker=dict(symbol='triangle-up', size=10, color='blue')
            ))
            
            fig.update_layout(
                title=f'{report_type.title()} Analysis - Parameter Comparison',
                xaxis_title='Parameters',
                yaxis_title='Values',
                showlegend=True
            )
            
            charts['comparison_chart'] = fig
            
        except Exception as e:
            st.warning(f"Chart creation warning: {str(e)}")
        
        return charts
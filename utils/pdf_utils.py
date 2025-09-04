import io
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.platypus.flowables import HRFlowable

try:
    import firebase_admin
    from firebase_admin import storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    firebase_admin = None
    storage = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFReportGenerator:
    """Generate comprehensive PDF reports for agricultural analysis"""
    
    def __init__(self):
        self.styles = self._setup_custom_styles()
        self.storage_client = self._init_firebase_storage()
    
    def _init_firebase_storage(self):
        """Initialize Firebase Storage client"""
        try:
            if FIREBASE_AVAILABLE and firebase_admin._apps:
                return storage
            return None
        except Exception as e:
            logger.warning(f"Firebase Storage not available: {str(e)}")
            return None
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2E7D32'),
            alignment=1  # Center
        ))
        
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#4CAF50'),
            borderWidth=1,
            borderColor=colors.HexColor('#4CAF50'),
            borderPadding=5
        ))
        
        styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#388E3C')
        ))
        
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=colors.black
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=15,
            textColor=colors.HexColor('#2E7D32'),
            borderWidth=2,
            borderColor=colors.HexColor('#4CAF50'),
            borderPadding=8,
            backColor=colors.HexColor('#E8F5E8')
        ))
        
        styles.add(ParagraphStyle(
            name='Warning',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.red,
            backColor=colors.HexColor('#FFEBEE'),
            borderWidth=1,
            borderColor=colors.red,
            borderPadding=5
        ))
        
        return styles
    
    def generate_report(self, analysis_data: Dict[str, Any], metadata: Dict[str, Any], 
                       options: Dict[str, Any]) -> bytes:
        """Generate complete PDF report with comprehensive analysis support"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Build story
        story = []
        
        # Title page
        story.extend(self._create_title_page(metadata))
        story.append(PageBreak())
        
        # Check if this is step-by-step analysis format
        is_step_by_step = 'step_by_step_analysis' in analysis_data
        
        if is_step_by_step:
            # Comprehensive PDF format with step-by-step analysis and visualizations
            story.extend(self._create_enhanced_executive_summary(analysis_data))
            story.extend(self._create_enhanced_key_findings(analysis_data))
            story.extend(self._create_comprehensive_step_by_step_analysis(analysis_data))
            
            # Enhanced Economic Analysis Section
            story.extend(self._create_comprehensive_economic_analysis(analysis_data))
            
            # Enhanced Yield Forecast and Projections
            story.extend(self._create_enhanced_yield_forecast_graph(analysis_data))
            story.extend(self._create_yield_projections_section(analysis_data))
            
            # Investment Scenarios and ROI Analysis
            story.extend(self._create_investment_scenarios_section(analysis_data))
            
            # Cost-Benefit Analysis
            story.extend(self._create_cost_benefit_analysis_section(analysis_data))
            
            story.extend(self._create_enhanced_conclusion(analysis_data))
        elif 'summary_metrics' in analysis_data and 'health_indicators' in analysis_data:
            # Comprehensive analysis format
            story.extend(self._create_comprehensive_executive_summary(analysis_data))
            story.extend(self._create_health_indicators_section(analysis_data))
            story.extend(self._create_detailed_analysis_section(analysis_data))
            story.extend(self._create_comprehensive_recommendations_section(analysis_data))
            
            # Economic analysis (always included for comprehensive)
            if 'economic_analysis' in analysis_data:
                story.extend(self._create_comprehensive_economic_section(analysis_data['economic_analysis']))
            
            # Yield forecast (always included for comprehensive)
            if 'yield_forecast' in analysis_data:
                story.extend(self._create_comprehensive_forecast_section(analysis_data['yield_forecast']))
            
            # Data quality section
            if 'data_quality' in analysis_data:
                story.extend(self._create_data_quality_section(analysis_data['data_quality']))
            
            # Charts section (if enabled)
            if options.get('include_charts', True):
                story.extend(self._create_comprehensive_charts_section(analysis_data))
        else:
            # Legacy analysis format
            story.extend(self._create_executive_summary(analysis_data))
            story.extend(self._create_parameters_section(analysis_data))
            story.extend(self._create_recommendations_section(analysis_data))
            
            # Economic analysis (if enabled)
            if options.get('include_economic', False) and 'economic_analysis' in analysis_data:
                story.extend(self._create_economic_section(analysis_data['economic_analysis']))
            
            # Yield forecast (if enabled)
            if options.get('include_forecast', False) and 'yield_forecast' in analysis_data:
                story.extend(self._create_forecast_section(analysis_data['yield_forecast']))
            
            # Charts section (if enabled)
            if options.get('include_charts', False):
                story.extend(self._create_charts_section(analysis_data))
        
        # Appendix removed as requested
        
        # Build PDF
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _create_title_page(self, metadata: Dict[str, Any]) -> List:
        """Create title page"""
        story = []
        
        # Main title
        story.append(Paragraph("Agricultural Analysis Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 30))
        
        # Report details - handle multiple analysis types
        report_types = metadata.get('report_types', ['soil', 'leaf'])
        if isinstance(report_types, list) and len(report_types) > 1:
            # Multiple analysis types
            types_str = ' & '.join([t.title() for t in report_types])
            story.append(Paragraph(f"Report Type: {types_str} Analysis", self.styles['CustomHeading']))
        elif isinstance(report_types, list) and len(report_types) == 1:
            # Single analysis type
            story.append(Paragraph(f"Report Type: {report_types[0].title()} Analysis", self.styles['CustomHeading']))
        else:
            # Default to comprehensive analysis
            story.append(Paragraph("Report Type: Comprehensive Agricultural Analysis", self.styles['CustomHeading']))
        
        story.append(Spacer(1, 20))
        
        # Enhanced metadata table with better defaults
        user_email = metadata.get('user_email', 'N/A')
        timestamp = metadata.get('timestamp', datetime.now())
        
        # Format timestamp properly
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        elif hasattr(timestamp, 'strftime'):
            pass  # Already a datetime object
        else:
            timestamp = datetime.now()
        
        metadata_data = [
            ['Lab Number:', 'SP LAB Analysis'],
            ['Sample Date:', timestamp.strftime('%Y-%m-%d')],
            ['Farm Name:', user_email.split('@')[0].title() if '@' in user_email else 'Oil Palm Plantation'],
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E8')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 50))
        
        # Company info
        story.append(Paragraph("Generated by AGS AI Analysis System", self.styles['CustomBody']))
        story.append(Paragraph("Advanced Agricultural Intelligence Platform", self.styles['CustomBody']))
        
        return story
    
    def _create_enhanced_executive_summary(self, analysis_data: Dict[str, Any]) -> List:
        """Create enhanced executive summary matching the results page format exactly"""
        story = []
        
        # Executive Summary header
        story.append(Paragraph("Executive Summary", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Handle data structure - analysis_data might be the analysis_results content directly
        if 'analysis_results' in analysis_data:
            # Full structure: analysis_data contains analysis_results
            analysis_results = analysis_data.get('analysis_results', {})
        else:
            # Direct structure: analysis_data IS the analysis_results content
            analysis_results = analysis_data
        
        # First check if there's a pre-generated executive summary
        if 'executive_summary' in analysis_results and analysis_results['executive_summary']:
            # Use the pre-generated executive summary exactly as it is
            executive_summary_text = analysis_results['executive_summary']
            if isinstance(executive_summary_text, str) and executive_summary_text.strip():
                # Display as a single paragraph without breaking it into sentences
                story.append(Paragraph(executive_summary_text.strip(), self.styles['CustomBody']))
                return story
        
        # If no pre-generated summary, generate using the exact same logic as results page
        raw_data = analysis_results.get('raw_data', {})
        soil_params = raw_data.get('soil_parameters', {})
        leaf_params = raw_data.get('leaf_parameters', {})
        land_yield_data = raw_data.get('land_yield_data', {})
        all_issues = analysis_results.get('issues_analysis', {}).get('all_issues', [])
        metadata = analysis_results.get('analysis_metadata', {})
        
        # Generate comprehensive agronomic summary (exact same as results page)
        summary_sentences = []
        
        # 1-3: Analysis overview and scope
        total_samples = metadata.get('total_parameters_analyzed', 0)
        confidence = metadata.get('confidence_level', 'Medium')
        summary_sentences.append(
            f"This comprehensive agronomic analysis evaluates {total_samples} "
            f"key nutritional parameters from both soil and leaf tissue samples "
            f"to assess the current fertility status and plant health of the "
            f"oil palm plantation.")
        summary_sentences.append(
            f"The analysis demonstrates {confidence.lower()} confidence levels "
            f"based on data quality assessment and adherence to Malaysian Palm "
            f"Oil Board (MPOB) standards for optimal oil palm cultivation.")
        summary_sentences.append(
            f"Laboratory results indicate {len(all_issues)} significant "
            f"nutritional imbalances requiring immediate attention to optimize "
            f"yield potential and maintain sustainable production.")
        
        # 4-7: Soil analysis findings (exact same as results page)
        if soil_params.get('parameter_statistics'):
            soil_stats = soil_params['parameter_statistics']
            ph_data = soil_stats.get('pH', {})
            if ph_data:
                ph_avg = ph_data.get('average', 0)
                summary_sentences.append(f"Soil pH analysis reveals an average value of {ph_avg:.2f}, which {'falls within' if 4.5 <= ph_avg <= 5.5 else 'deviates from'} the optimal range of 4.5-5.5 required for efficient nutrient uptake in oil palm cultivation.")
            
            p_data = soil_stats.get('Available_P_mg_kg', {})
            if p_data:
                p_avg = p_data.get('average', 0)
                summary_sentences.append(f"Available phosphorus levels average {p_avg:.1f} mg/kg, {'meeting' if p_avg >= 10 else 'falling below'} the critical threshold of 10-15 mg/kg necessary for root development and fruit bunch formation.")
            
            k_data = soil_stats.get('Exchangeable_K_meq%', {})
            if k_data:
                k_avg = k_data.get('average', 0)
                summary_sentences.append(f"Exchangeable potassium content shows an average of {k_avg:.2f} meq%, which {'supports' if k_avg >= 0.2 else 'limits'} the palm's ability to regulate water balance and enhance oil synthesis processes.")
            
            ca_data = soil_stats.get('Exchangeable_Ca_meq%', {})
            if ca_data:
                ca_avg = ca_data.get('average', 0)
                summary_sentences.append(f"Calcium availability at {ca_avg:.2f} meq% {'provides adequate' if ca_avg >= 0.5 else 'indicates insufficient'} structural support for cell wall development and overall plant vigor.")
        
        # 8-11: Leaf analysis findings (exact same as results page)
        if leaf_params.get('parameter_statistics'):
            leaf_stats = leaf_params['parameter_statistics']
            n_data = leaf_stats.get('N_%', {})
            if n_data:
                n_avg = n_data.get('average', 0)
                summary_sentences.append(f"Leaf nitrogen content averages {n_avg:.2f}%, {'indicating optimal' if 2.5 <= n_avg <= 2.8 else 'suggesting suboptimal'} protein synthesis and chlorophyll production for photosynthetic efficiency.")
            
            p_leaf_data = leaf_stats.get('P_%', {})
            if p_leaf_data:
                p_leaf_avg = p_leaf_data.get('average', 0)
                summary_sentences.append(f"Foliar phosphorus levels at {p_leaf_avg:.3f}% {'support' if p_leaf_avg >= 0.15 else 'may limit'} energy transfer processes and reproductive development in the palm canopy.")
            
            k_leaf_data = leaf_stats.get('K_%', {})
            if k_leaf_data:
                k_leaf_avg = k_leaf_data.get('average', 0)
                summary_sentences.append(f"Leaf potassium concentration of {k_leaf_avg:.2f}% {'ensures proper' if k_leaf_avg >= 1.0 else 'indicates compromised'} stomatal regulation and carbohydrate translocation to developing fruit bunches.")
            
            mg_data = leaf_stats.get('Mg_%', {})
            if mg_data:
                mg_avg = mg_data.get('average', 0)
                summary_sentences.append(f"Magnesium content in leaf tissue shows {mg_avg:.3f}%, which {'maintains' if mg_avg >= 0.25 else 'threatens'} the structural integrity of chlorophyll molecules essential for photosynthetic capacity.")
        
        # 12-15: Critical issues and severity assessment (exact same as results page)
        critical_issues = [i for i in all_issues if i.get('severity') == 'Critical']
        high_issues = [i for i in all_issues if i.get('severity') == 'High']
        medium_issues = [i for i in all_issues if i.get('severity') == 'Medium']
        
        summary_sentences.append(f"Critical nutritional deficiencies identified in {len(critical_issues)} parameters pose immediate threats to palm productivity and require urgent corrective measures within the next 30-60 days.")
        summary_sentences.append(f"High-severity imbalances affecting {len(high_issues)} additional parameters will significantly impact yield potential if not addressed through targeted fertilization programs within 3-6 months.")
        summary_sentences.append(f"Medium-priority nutritional concerns in {len(medium_issues)} parameters suggest the need for adjusted maintenance fertilization schedules to prevent future deficiencies.")
        
        # 16-18: Yield and economic implications (exact same as results page)
        current_yield = land_yield_data.get('current_yield', 0)
        land_size = land_yield_data.get('land_size', 0)
        if current_yield and land_size:
            summary_sentences.append(f"Current yield performance of {current_yield} tonnes per hectare across {land_size} hectares {'exceeds' if current_yield > 20 else 'falls below'} industry benchmarks, with nutritional corrections potentially {'maintaining' if current_yield > 20 else 'improving'} production by 15-25%.")
        else:
            summary_sentences.append("Yield optimization potential through nutritional management could increase production by 15-25% when combined with proper agronomic practices and timely intervention strategies.")
        
        summary_sentences.append("Economic analysis indicates that investment in corrective fertilization programs will generate positive returns within 12-18 months through improved fruit bunch quality and increased fresh fruit bunch production.")
        
        # 19-20: Recommendations and monitoring (exact same as results page)
        summary_sentences.append("Implementation of precision fertilization based on these findings, combined with regular soil and leaf monitoring every 6 months, will ensure sustained productivity and long-term plantation profitability.")
        summary_sentences.append("Adoption of integrated nutrient management practices, including organic matter incorporation and micronutrient supplementation, will enhance soil health and support the plantation's transition toward sustainable intensification goals.")
        
        # Ensure we have exactly 20 sentences (exact same as results page)
        while len(summary_sentences) < 20:
            summary_sentences.append("Continued monitoring and adaptive management strategies will be essential for maintaining optimal nutritional status and maximizing the economic potential of this oil palm operation.")
        
        # Take only the first 20 sentences (exact same as results page)
        summary_sentences = summary_sentences[:20]
        
        # Join sentences into a comprehensive summary (exact same as results page)
        comprehensive_summary = " ".join(summary_sentences)
        
        # Display the summary as a single paragraph without breaking it into sentences
        story.append(Paragraph(comprehensive_summary, self.styles['CustomBody']))
        
        return story
    
    def _clean_finding_text_pdf(self, text):
        """Clean finding text by removing duplicate 'Key Finding' words and normalizing (PDF version)"""
        import re
        
        # Remove duplicate "Key Finding" patterns
        # Pattern 1: "Key Finding X: Key finding Y:" -> "Key Finding X:"
        text = re.sub(r'Key Finding \d+:\s*Key finding \d+:\s*', 'Key Finding ', text)
        
        # Pattern 2: "Key finding X:" -> remove (lowercase version)
        text = re.sub(r'Key finding \d+:\s*', '', text)
        
        # Pattern 3: Multiple "Key Finding" at the start
        text = re.sub(r'^(Key Finding \d+:\s*)+', 'Key Finding ', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _is_same_issue_pdf(self, finding1, finding2):
        """Check if two findings are about the same agricultural issue (PDF version)"""
        # Define issue patterns
        issue_patterns = {
            'potassium_deficiency': ['potassium', 'k deficiency', 'k level', 'k average', 'k critical'],
            'soil_acidity': ['ph', 'acidic', 'acidity', 'soil ph', 'ph level'],
            'phosphorus_deficiency': ['phosphorus', 'p deficiency', 'available p', 'p level'],
            'nutrient_deficiency': ['deficiency', 'deficient', 'nutrient', 'nutrients'],
            'cec_issue': ['cec', 'cation exchange', 'nutrient retention', 'nutrient holding'],
            'organic_matter': ['organic matter', 'organic carbon', 'carbon'],
            'micronutrient': ['copper', 'zinc', 'manganese', 'iron', 'boron', 'micronutrient'],
            'yield_impact': ['yield', 'productivity', 'tonnes', 'production'],
            'economic_impact': ['roi', 'investment', 'cost', 'profit', 'revenue', 'economic']
        }
        
        finding1_lower = finding1.lower()
        finding2_lower = finding2.lower()
        
        # Check if both findings mention the same issue category
        for issue, keywords in issue_patterns.items():
            finding1_has_issue = any(keyword in finding1_lower for keyword in keywords)
            finding2_has_issue = any(keyword in finding2_lower for keyword in keywords)
            
            if finding1_has_issue and finding2_has_issue:
                # Additional check for specific values or percentages
                if issue in ['potassium_deficiency', 'soil_acidity', 'phosphorus_deficiency']:
                    # Extract numbers from both findings
                    import re
                    nums1 = re.findall(r'\d+\.?\d*', finding1)
                    nums2 = re.findall(r'\d+\.?\d*', finding2)
                    
                    # If they have similar numbers, they're likely the same issue
                    if nums1 and nums2:
                        for num1 in nums1:
                            for num2 in nums2:
                                if abs(float(num1) - float(num2)) < 0.1:  # Very close values
                                    return True
                
                return True
        
        return False

    def _extract_key_concepts_pdf(self, text):
        """Extract key concepts from text for better deduplication (PDF version)"""
        import re
        
        # Define key agricultural concepts and nutrients
        nutrients = ['nitrogen', 'phosphorus', 'potassium', 'calcium', 'magnesium', 'sulfur', 'copper', 'zinc', 'manganese', 'iron', 'boron', 'molybdenum']
        parameters = ['ph', 'cec', 'organic matter', 'base saturation', 'yield', 'deficiency', 'excess', 'optimum', 'critical', 'mg/kg', '%', 'meq']
        conditions = ['acidic', 'alkaline', 'deficient', 'sufficient', 'excessive', 'low', 'high', 'moderate', 'severe', 'mild']
        
        # Extract numbers and percentages
        numbers = re.findall(r'\d+\.?\d*', text)
        
        # Extract nutrient names and parameters
        found_concepts = set()
        
        # Check for nutrients
        for nutrient in nutrients:
            if nutrient in text:
                found_concepts.add(nutrient)
        
        # Check for parameters
        for param in parameters:
            if param in text:
                found_concepts.add(param)
        
        # Check for conditions
        for condition in conditions:
            if condition in text:
                found_concepts.add(condition)
        
        # Add significant numbers (values that matter for agricultural analysis)
        for num in numbers:
            if float(num) > 0:  # Only add positive numbers
                found_concepts.add(num)
        
        return found_concepts

    def _create_enhanced_key_findings(self, analysis_data: Dict[str, Any]) -> List:
        """Create enhanced key findings section with intelligent extraction - exact copy from results page"""
        story = []
        
        # Key Findings header
        story.append(Paragraph("Key Findings", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Handle data structure - analysis_data might be the analysis_results content directly
        if 'analysis_results' in analysis_data:
            # Full structure: analysis_data contains analysis_results
            analysis_results = analysis_data.get('analysis_results', {})
        else:
            # Direct structure: analysis_data IS the analysis_results content
            analysis_results = analysis_data
        
        step_results = analysis_results.get('step_by_step_analysis', [])
        
        # Look for key findings in multiple sources - exact same as results page
        all_key_findings = []
        
        # 1. Check for key findings at the top level of analysis_results
        if 'key_findings' in analysis_results and analysis_results['key_findings']:
            findings_data = analysis_results['key_findings']
            
            # Handle both list and string formats
            if isinstance(findings_data, list):
                findings_list = findings_data
            elif isinstance(findings_data, str):
                findings_list = [f.strip() for f in findings_data.split('\n') if f.strip()]
            else:
                findings_list = []
            
            # Process each finding
            for finding in findings_list:
                if isinstance(finding, str) and finding.strip():
                    cleaned_finding = self._clean_finding_text_pdf(finding.strip())
                    all_key_findings.append({
                        'finding': cleaned_finding,
                        'source': 'Overall Analysis'
                    })
        
        # 2. Check for executive summary
        if 'executive_summary' in analysis_results and analysis_results['executive_summary']:
            summary = analysis_results['executive_summary']
            if isinstance(summary, str):
                lines = [line.strip() for line in summary.split('\n') if line.strip()]
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['deficiency', 'critical', 'severe', 'low', 'high', 'optimum', 'ph', 'nutrient', 'yield', 'recommendation', 'finding', 'issue', 'problem']):
                        cleaned_finding = self._clean_finding_text_pdf(line)
                        all_key_findings.append({
                            'finding': cleaned_finding,
                            'source': 'Executive Summary'
                        })
        
        # 3. Check for overall summary
        if 'summary' in analysis_results and analysis_results['summary']:
            summary = analysis_results['summary']
            if isinstance(summary, str):
                lines = [line.strip() for line in summary.split('\n') if line.strip()]
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['deficiency', 'critical', 'severe', 'low', 'high', 'optimum', 'ph', 'nutrient', 'yield', 'recommendation', 'finding', 'issue', 'problem']):
                        cleaned_finding = self._clean_finding_text_pdf(line)
                        all_key_findings.append({
                            'finding': cleaned_finding,
                            'source': 'Analysis Summary'
                        })
        
        # 4. If still no findings, extract from step results but with smart deduplication - exact same as results page
        if not all_key_findings and step_results:
            step_findings = []
            
            for i, step in enumerate(step_results):
                if 'key_findings' in step and step['key_findings']:
                    step_title = step.get('step_title', f"Step {step.get('step_number', 'Unknown')}")
                    step_findings_data = step['key_findings']
                    
                    # Handle both list and string formats
                    if isinstance(step_findings_data, list):
                        findings_list = step_findings_data
                    elif isinstance(step_findings_data, str):
                        findings_list = [f.strip() for f in step_findings_data.split('\n') if f.strip()]
                    else:
                        findings_list = []
                    
                    for finding in findings_list:
                        if isinstance(finding, str) and finding.strip():
                            cleaned_finding = self._clean_finding_text_pdf(finding.strip())
                            step_findings.append({
                                'finding': cleaned_finding,
                                'source': step_title
                            })
            
            # Apply smart deduplication to step findings - exact same as results page
            if step_findings:
                unique_findings = []
                seen_concepts = []
                
                for finding_data in step_findings:
                    finding = finding_data['finding']
                    normalized = ' '.join(finding.lower().split())
                    key_concepts = self._extract_key_concepts_pdf(normalized)
                    
                    is_duplicate = False
                    for i, seen_concept_set in enumerate(seen_concepts):
                        concept_overlap = len(key_concepts.intersection(seen_concept_set))
                        total_concepts = len(key_concepts.union(seen_concept_set))
                        
                        if total_concepts > 0:
                            similarity = concept_overlap / total_concepts
                            word_similarity = len(key_concepts.intersection(seen_concept_set)) / max(len(key_concepts), len(seen_concept_set)) if len(key_concepts) > 0 and len(seen_concept_set) > 0 else 0
                            
                            # More aggressive deduplication
                            if similarity > 0.6 or word_similarity > 0.7:
                                if len(finding) > len(unique_findings[i]['finding']):
                                    unique_findings[i] = finding_data
                                    seen_concepts[i] = key_concepts
                                is_duplicate = True
                                break
                            
                            # Check for same issue
                            if similarity > 0.4 and word_similarity > 0.5:
                                if self._is_same_issue_pdf(finding, unique_findings[i]['finding']):
                                    if len(finding) > len(unique_findings[i]['finding']):
                                        unique_findings[i] = finding_data
                                        seen_concepts[i] = key_concepts
                                    is_duplicate = True
                                    break
                    
                    if not is_duplicate:
                        unique_findings.append(finding_data)
                        seen_concepts.append(key_concepts)
                
                all_key_findings = unique_findings
        
        if all_key_findings:
            # Display key findings - exact same format as results page
            for i, finding_data in enumerate(all_key_findings, 1):
                finding = finding_data['finding']
                source = finding_data['source']
                
                # Create finding paragraph with proper formatting - exact same as results page
                finding_text = f"<b>Key Finding {i}:</b> {finding}"
                story.append(Paragraph(finding_text, self.styles['CustomBody']))
                story.append(Paragraph(f"<i>📋 Source: {source}</i>", self.styles['CustomBody']))
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("📋 No key findings available from the analysis results.", self.styles['CustomBody']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_comprehensive_step_by_step_analysis(self, analysis_data: Dict[str, Any]) -> List:
        """Create comprehensive step-by-step analysis section with visualizations"""
        story = []
        
        # Step-by-Step Analysis header
        story.append(Paragraph("Step-by-Step Analysis", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Handle data structure - analysis_data might be the analysis_results content directly
        if 'analysis_results' in analysis_data:
            # Full structure: analysis_data contains analysis_results
            analysis_results = analysis_data.get('analysis_results', {})
        else:
            # Direct structure: analysis_data IS the analysis_results content
            analysis_results = analysis_data
        
        step_results = analysis_results.get('step_by_step_analysis', [])
        
        for step in step_results:
            step_number = step.get('step_number', 'Unknown')
            step_title = step.get('step_title', 'Unknown Step')
            
            # Step header
            story.append(Paragraph(f"Step {step_number}: {step_title}", self.styles['Heading2']))
            story.append(Spacer(1, 8))
            
            # Summary (most important content)
            if 'summary' in step and step['summary']:
                story.append(Paragraph("Summary:", self.styles['Heading3']))
                story.append(Paragraph(step['summary'], self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Detailed Analysis (most relevant content)
            if 'detailed_analysis' in step and step['detailed_analysis']:
                story.append(Paragraph("Detailed Analysis:", self.styles['Heading3']))
                # Truncate if too long to keep PDF manageable
                detailed_text = step['detailed_analysis']
                if len(detailed_text) > 2000:
                    detailed_text = detailed_text[:2000] + "..."
                story.append(Paragraph(detailed_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Issues Identified (crucial for farmers)
            if 'issues_identified' in step and step['issues_identified']:
                story.append(Paragraph("Issues Identified:", self.styles['Heading3']))
                for i, issue in enumerate(step['issues_identified'], 1):
                    issue_text = f"<b>{i}.</b> {issue}"
                    story.append(Paragraph(issue_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Recommendations (crucial for farmers)
            if 'recommendations' in step and step['recommendations']:
                story.append(Paragraph("Recommendations:", self.styles['Heading3']))
                for i, rec in enumerate(step['recommendations'], 1):
                    rec_text = f"<b>{i}.</b> {rec}"
                    story.append(Paragraph(rec_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Step-specific tables and content
            if step_number == 1:
                # Step 1: Data Analysis - Add all data tables
                story.extend(self._create_step1_data_tables(step, analysis_data))
            elif step_number == 2:
                # Step 2: Issue Diagnosis - Add diagnostic tables
                story.extend(self._create_step2_diagnostic_tables(step))
            elif step_number == 3:
                # Step 3: Solution Recommendations - Add economic and solution tables
                story.extend(self._create_step3_solution_tables(step))
            elif step_number == 4:
                # Step 4: Regenerative Agriculture - Add regenerative strategy tables
                story.extend(self._create_step4_regenerative_tables(step))
            elif step_number == 5:
                # Step 5: Economic Impact - Add comprehensive economic tables
                story.extend(self._create_step5_economic_tables(step))
            elif step_number == 6:
                # Step 6: Yield Forecast - Add forecast tables
                story.extend(self._create_step6_forecast_tables(step))
            
            # Visualizations and Charts
            story.extend(self._create_step_visualizations(step, step_number))
            
            story.append(Spacer(1, 15))
        
        return story
    
    def _create_step_visualizations(self, step: Dict[str, Any], step_number: int) -> List:
        """Create visualizations for each step"""
        story = []
        
        # Check for charts and visualizations in the step data
        if 'charts' in step and step['charts']:
            story.append(Paragraph("Visualizations:", self.styles['Heading3']))
            
            for chart_data in step['charts']:
                try:
                    # Create chart using matplotlib
                    chart_image = self._create_chart_image(chart_data)
                    if chart_image:
                        # Create a BytesIO object from the image bytes
                        img_buffer = io.BytesIO(chart_image)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
                except Exception as e:
                    logger.warning(f"Could not create chart: {str(e)}")
                    continue
        
        # Create nutrient status visualization for Step 1
        if step_number == 1:
            nutrient_chart = self._create_nutrient_status_chart(step)
            if nutrient_chart:
                story.append(Paragraph("Nutrient Status Overview:", self.styles['Heading3']))
                # Create a BytesIO object from the image bytes
                img_buffer = io.BytesIO(nutrient_chart)
                story.append(Image(img_buffer, width=6*inch, height=4*inch))
                story.append(Spacer(1, 8))
        
        return story
    
    def _create_chart_image(self, chart_data: Dict[str, Any]) -> Optional[bytes]:
        """Create chart image from chart data"""
        try:
            import matplotlib.pyplot as plt
            import io
            
            # Clear any existing figures to prevent memory issues
            plt.clf()
            plt.close('all')
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            chart_type = chart_data.get('type', 'bar')
            data = chart_data.get('data', {})
            labels = data.get('labels', [])
            values = data.get('values', [])
            
            # Validate data
            if not labels or not values or len(labels) != len(values):
                logger.warning("Invalid chart data: labels and values must be non-empty and same length")
                return None
            
            if chart_type == 'bar':
                ax.bar(labels, values)
            elif chart_type == 'line':
                ax.plot(labels, values, marker='o')
            elif chart_type == 'pie':
                ax.pie(values, labels=labels, autopct='%1.1f%%')
            else:
                # Default to bar chart
                ax.bar(labels, values)
            
            ax.set_title(chart_data.get('title', 'Chart'))
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error creating chart: {str(e)}")
            return None
    
    def _create_nutrient_status_chart(self, step: Dict[str, Any]) -> Optional[bytes]:
        """Create nutrient status chart for Step 1"""
        try:
            import matplotlib.pyplot as plt
            import io
            
            # Clear any existing figures to prevent memory issues
            plt.clf()
            plt.close('all')
            
            # Extract nutrient data from step
            soil_params = step.get('soil_parameters', {})
            leaf_params = step.get('leaf_parameters', {})
            
            if not soil_params and not leaf_params:
                return None
            
            # Determine layout based on available data
            if soil_params and leaf_params:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            elif soil_params:
                fig, ax1 = plt.subplots(1, 1, figsize=(6, 5))
                ax2 = None
            else:
                fig, ax2 = plt.subplots(1, 1, figsize=(6, 5))
                ax1 = None
            
            # Soil nutrients chart
            if soil_params and ax1 is not None:
                soil_labels = []
                soil_values = []
                for param, data in soil_params.items():
                    if isinstance(data, dict) and 'average' in data:
                        soil_labels.append(param.replace('_', ' ').title())
                        soil_values.append(data['average'])
                
                if soil_labels and soil_values:
                    ax1.bar(soil_labels, soil_values)
                    ax1.set_title('Soil Nutrient Levels')
                    ax1.set_ylabel('Value')
                    ax1.tick_params(axis='x', rotation=45)
            
            # Leaf nutrients chart
            if leaf_params and ax2 is not None:
                leaf_labels = []
                leaf_values = []
                for param, data in leaf_params.items():
                    if isinstance(data, dict) and 'average' in data:
                        leaf_labels.append(param.replace('_', ' ').title())
                        leaf_values.append(data['average'])
                
                if leaf_labels and leaf_values:
                    ax2.bar(leaf_labels, leaf_values)
                    ax2.set_title('Leaf Nutrient Levels')
                    ax2.set_ylabel('Value')
                    ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error creating nutrient status chart: {str(e)}")
            return None
    
    def _create_nutrient_status_tables(self, step: Dict[str, Any]) -> List:
        """Create nutrient status tables for Step 1"""
        story = []
        
        # Soil Nutrient Status Table
        soil_params = step.get('soil_parameters', {})
        if soil_params:
            story.append(Paragraph("Soil Nutrient Status:", self.styles['Heading3']))
            
            table_data = [['Parameter', 'Average', 'Status', 'Unit']]
            for param, data in soil_params.items():
                if isinstance(data, dict):
                    table_data.append([
                        param.replace('_', ' ').title(),
                        f"{data.get('average', 0):.2f}",
                        data.get('status', 'Unknown'),
                        data.get('unit', '')
                    ])
            
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 8))
        
        return story
    
    def _create_step_economic_analysis(self, step: Dict[str, Any]) -> List:
        """Create economic analysis for Step 3"""
        story = []
        
        economic_data = step.get('economic_analysis', {})
        if economic_data:
            story.append(Paragraph("Economic Analysis:", self.styles['Heading3']))
            
            # ROI Analysis
            if 'roi_analysis' in economic_data:
                roi_data = economic_data['roi_analysis']
                story.append(Paragraph(f"ROI Analysis: {roi_data}", self.styles['CustomBody']))
                story.append(Spacer(1, 4))
            
            # Cost-Benefit Analysis
            if 'cost_benefit' in economic_data:
                cb_data = economic_data['cost_benefit']
                story.append(Paragraph(f"Cost-Benefit Analysis: {cb_data}", self.styles['CustomBody']))
                story.append(Spacer(1, 4))
            
            # Investment Recommendations
            if 'investment_recommendations' in economic_data:
                inv_recs = economic_data['investment_recommendations']
                if isinstance(inv_recs, list):
                    for i, rec in enumerate(inv_recs, 1):
                        story.append(Paragraph(f"<b>{i}.</b> {rec}", self.styles['CustomBody']))
                else:
                    story.append(Paragraph(inv_recs, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
        
        return story

    def _create_step1_data_tables(self, step: Dict[str, Any], analysis_data: Dict[str, Any]) -> List:
        """Create data tables for Step 1: Data Analysis"""
        story = []
        
        # Get raw data from analysis_data
        analysis_results = analysis_data.get('analysis_results', {})
        raw_data = analysis_results.get('raw_data', {})
        
        # Soil Data Table
        soil_data = raw_data.get('soil_data', {})
        if soil_data and 'parameter_statistics' in soil_data:
            story.append(Paragraph("Soil Analysis Data", self.styles['Heading3']))
            story.extend(self._create_parameter_statistics_table(soil_data, "Soil"))
            story.append(Spacer(1, 8))
        
        # Leaf Data Table
        leaf_data = raw_data.get('leaf_data', {})
        if leaf_data and 'parameter_statistics' in leaf_data:
            story.append(Paragraph("Leaf Analysis Data", self.styles['Heading3']))
            story.extend(self._create_parameter_statistics_table(leaf_data, "Leaf"))
            story.append(Spacer(1, 8))
        
        # Nutrient Status Tables
        story.extend(self._create_nutrient_status_tables(step))
        
        return story

    def _create_step2_diagnostic_tables(self, step: Dict[str, Any]) -> List:
        """Create diagnostic tables for Step 2: Issue Diagnosis"""
        story = []
        
        # Issues Summary Table
        if 'issues_identified' in step and step['issues_identified']:
            story.append(Paragraph("Issues Summary", self.styles['Heading3']))
            table_data = [['Issue #', 'Description', 'Severity']]
            
            for i, issue in enumerate(step['issues_identified'], 1):
                # Extract severity from issue text if available
                severity = "High"  # Default
                if "critical" in issue.lower() or "severe" in issue.lower():
                    severity = "Critical"
                elif "moderate" in issue.lower() or "medium" in issue.lower():
                    severity = "Moderate"
                elif "low" in issue.lower() or "minor" in issue.lower():
                    severity = "Low"
                
                table_data.append([str(i), issue[:100] + "..." if len(issue) > 100 else issue, severity])
            
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 8))
        
        return story

    def _create_step3_solution_tables(self, step: Dict[str, Any]) -> List:
        """Create solution tables for Step 3: Solution Recommendations"""
        story = []
        
        # Economic Analysis Table
        story.extend(self._create_step_economic_analysis(step))
        
        # Solution Recommendations Table
        if 'recommendations' in step and step['recommendations']:
            story.append(Paragraph("Solution Recommendations", self.styles['Heading3']))
            table_data = [['Priority', 'Recommendation', 'Expected Impact']]
            
            for i, rec in enumerate(step['recommendations'], 1):
                # Determine priority based on content
                priority = "High"
                if "immediate" in rec.lower() or "urgent" in rec.lower() or "critical" in rec.lower():
                    priority = "Critical"
                elif "long-term" in rec.lower() or "future" in rec.lower():
                    priority = "Medium"
                
                # Extract impact if mentioned
                impact = "Significant"
                if "high" in rec.lower() and "impact" in rec.lower():
                    impact = "High"
                elif "moderate" in rec.lower() and "impact" in rec.lower():
                    impact = "Moderate"
                
                table_data.append([priority, rec[:80] + "..." if len(rec) > 80 else rec, impact])
            
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 8))
        
        return story

    def _create_step4_regenerative_tables(self, step: Dict[str, Any]) -> List:
        """Create regenerative agriculture tables for Step 4"""
        story = []
        
        # Regenerative Strategies Table
        if 'regenerative_strategies' in step and step['regenerative_strategies']:
            story.append(Paragraph("Regenerative Agriculture Strategies", self.styles['Heading3']))
            strategies = step['regenerative_strategies']
            
            if isinstance(strategies, list):
                table_data = [['Strategy', 'Implementation', 'Benefits']]
                for strategy in strategies:
                    if isinstance(strategy, dict):
                        name = strategy.get('name', 'Unknown Strategy')
                        implementation = strategy.get('implementation', 'Not specified')
                        benefits = strategy.get('benefits', 'Not specified')
                        table_data.append([name, implementation[:60] + "..." if len(implementation) > 60 else implementation, benefits[:60] + "..." if len(benefits) > 60 else benefits])
                    else:
                        table_data.append([str(strategy)[:50] + "..." if len(str(strategy)) > 50 else str(strategy), "See details", "See details"])
                
                if len(table_data) > 1:
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 8))
        
        return story

    def _create_step5_economic_tables(self, step: Dict[str, Any]) -> List:
        """Create comprehensive economic tables for Step 5"""
        story = []
        
        # Investment Scenarios Table
        if 'investment_scenarios' in step and step['investment_scenarios']:
            story.append(Paragraph("Investment Scenarios Analysis", self.styles['Heading3']))
            scenarios = step['investment_scenarios']
            
            table_data = [['Investment Level', 'Total Cost (RM)', 'Expected Return (RM)', 'ROI (%)', 'Payback Period']]
            
            for scenario_name, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict):
                    cost = scenario_data.get('total_cost', 0)
                    return_val = scenario_data.get('expected_return', 0)
                    roi = scenario_data.get('roi', 0)
                    payback = scenario_data.get('payback_period', 'N/A')
                    
                    table_data.append([
                        scenario_name.title(),
                        f"{cost:,.0f}" if isinstance(cost, (int, float)) else str(cost),
                        f"{return_val:,.0f}" if isinstance(return_val, (int, float)) else str(return_val),
                        f"{roi:.1f}%" if isinstance(roi, (int, float)) else str(roi),
                        str(payback)
                    ])
            
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 8))
        
        return story

    def _create_step6_forecast_tables(self, step: Dict[str, Any]) -> List:
        """Create forecast tables for Step 6: Yield Forecast"""
        story = []
        
        # Yield Projections Table
        if 'yield_projections' in step and step['yield_projections']:
            story.append(Paragraph("5-Year Yield Projections", self.styles['Heading3']))
            projections = step['yield_projections']
            
            years = list(range(2024, 2029))
            table_data = [['Year'] + [f'{level.title()} Investment' for level in ['high', 'medium', 'low'] if level in projections]]
            
            for year in years:
                row = [str(year)]
                for level in ['high', 'medium', 'low']:
                    if level in projections and len(projections[level]) >= (year - 2023):
                        value = projections[level][year - 2024]
                        row.append(f"{value:.1f} tons/ha" if isinstance(value, (int, float)) else str(value))
                    else:
                        row.append("N/A")
                table_data.append(row)
            
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 8))
        
        return story

    def _create_parameter_statistics_table(self, data: Dict[str, Any], data_type: str) -> List:
        """Create parameter statistics table for soil or leaf data"""
        story = []
        
        param_stats = data.get('parameter_statistics', {})
        if param_stats:
            table_data = [['Parameter', 'Average', 'Min', 'Max', 'Samples']]
            
            for param, stats in param_stats.items():
                table_data.append([
                    param.replace('_', ' ').title(),
                    f"{stats.get('average', 0):.2f}",
                    f"{stats.get('min', 0):.2f}",
                    f"{stats.get('max', 0):.2f}",
                    str(stats.get('count', 0))
                ])
            
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
        
        return story
    
    def _create_step_by_step_analysis(self, analysis_data: Dict[str, Any]) -> List:
        """Create step-by-step analysis section (legacy function)"""
        story = []
        
        # Step-by-Step Analysis header
        story.append(Paragraph("Step-by-Step Analysis", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        step_results = analysis_data.get('step_by_step_analysis', [])
        
        for step in step_results:
            step_number = step.get('step_number', 'Unknown')
            step_title = step.get('step_title', 'Unknown Step')
            
            # Step header
            story.append(Paragraph(f"Step {step_number}: {step_title}", self.styles['Heading2']))
            story.append(Spacer(1, 8))
            
            # Summary
            if 'summary' in step and step['summary']:
                story.append(Paragraph("Summary:", self.styles['Heading3']))
                story.append(Paragraph(step['summary'], self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Key Findings
            if 'key_findings' in step and step['key_findings']:
                story.append(Paragraph("Key Findings:", self.styles['Heading3']))
                for i, finding in enumerate(step['key_findings'], 1):
                    finding_text = f"<b>{i}.</b> {finding}"
                    story.append(Paragraph(finding_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Detailed Analysis
            if 'detailed_analysis' in step and step['detailed_analysis']:
                story.append(Paragraph("Detailed Analysis:", self.styles['Heading3']))
                story.append(Paragraph(step['detailed_analysis'], self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 15))
        
        return story
    
    def _create_comprehensive_economic_analysis(self, analysis_data: Dict[str, Any]) -> List:
        """Create comprehensive economic analysis section with all components"""
        story = []
        
        # Economic Analysis header
        story.append(Paragraph("Economic Analysis", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Find economic data from multiple sources
        economic_data = self._extract_economic_data(analysis_data)
        
        if economic_data:
            # Current Economic Status
            story.extend(self._create_current_economic_status(economic_data))
            
            # ROI Analysis
            story.extend(self._create_roi_analysis(economic_data))
            
            # Cost-Benefit Analysis
            story.extend(self._create_detailed_cost_benefit_analysis(economic_data))
            
            # Investment Recommendations
            story.extend(self._create_investment_recommendations(economic_data))
            
        else:
            story.append(Paragraph("No economic analysis data available.", self.styles['CustomBody']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _extract_economic_data(self, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract economic data from various sources in analysis_data"""
        # 1. Check direct economic_forecast
        if 'economic_forecast' in analysis_data and analysis_data['economic_forecast']:
            return analysis_data['economic_forecast']
        
        # 2. Check step-by-step analysis for economic data
        step_results = analysis_data.get('step_by_step_analysis', [])
        for step in step_results:
            if step.get('step_number') == 5 and 'economic_analysis' in step:
                return step['economic_analysis']
            elif 'economic_analysis' in step and step['economic_analysis']:
                return step['economic_analysis']
        
        # 3. Check analysis_results
        if 'analysis_results' in analysis_data:
            analysis_results = analysis_data['analysis_results']
            if 'economic_forecast' in analysis_results:
                return analysis_results['economic_forecast']
        
        return None
    
    def _create_current_economic_status(self, economic_data: Dict[str, Any]) -> List:
        """Create current economic status section"""
        story = []
        
        story.append(Paragraph("Current Economic Status", self.styles['Heading2']))
        story.append(Spacer(1, 8))
        
        # Extract key economic metrics
        current_yield = economic_data.get('current_yield_tonnes_per_ha', 0)
        land_size = economic_data.get('land_size_hectares', 0)
        oil_palm_price = economic_data.get('oil_palm_price_rm_per_tonne', 600)
        
        # Create metrics table
        metrics_data = []
        if current_yield > 0:
            metrics_data.append(['Current Yield', f"{current_yield:.1f} tonnes/ha"])
        if land_size > 0:
            metrics_data.append(['Land Size', f"{land_size:.1f} hectares"])
        metrics_data.append(['Oil Palm Price', f"RM {oil_palm_price:.0f}/tonne"])
        
        if metrics_data:
            table = Table(metrics_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))
        
        return story
    
    def _create_roi_analysis(self, economic_data: Dict[str, Any]) -> List:
        """Create ROI analysis section"""
        story = []
        
        story.append(Paragraph("Return on Investment (ROI) Analysis", self.styles['Heading2']))
        story.append(Spacer(1, 8))
        
        scenarios = economic_data.get('scenarios', {})
        if scenarios:
            # Create ROI comparison table
            table_data = [['Investment Level', 'Total Investment (RM)', 'Expected Return (RM)', 'ROI (%)', 'Payback Period (Months)']]
            
            for scenario_name, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict):
                    investment = scenario_data.get('total_cost', 0)
                    expected_return = scenario_data.get('additional_revenue', 0)
                    roi = scenario_data.get('roi_percentage', 0)
                    payback_months = scenario_data.get('payback_months', 0)
                    
                    table_data.append([
                        scenario_name.title(),
                        f"RM {investment:,.0f}",
                        f"RM {expected_return:,.0f}",
                        f"{roi:.1f}%",
                        f"{payback_months:.0f} months"
                    ])
            
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 12))
        
        return story
    
    def _create_detailed_cost_benefit_analysis(self, economic_data: Dict[str, Any]) -> List:
        """Create detailed cost-benefit analysis section"""
        story = []
        
        story.append(Paragraph("Detailed Cost-Benefit Analysis", self.styles['Heading2']))
        story.append(Spacer(1, 8))
        
        scenarios = economic_data.get('scenarios', {})
        if scenarios:
            for scenario_name, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict):
                    story.append(Paragraph(f"{scenario_name.title()} Investment Scenario", self.styles['Heading3']))
                    
                    # Cost breakdown
                    total_cost = scenario_data.get('total_cost', 0)
                    additional_revenue = scenario_data.get('additional_revenue', 0)
                    net_benefit = additional_revenue - total_cost
                    
                    cost_breakdown = [
                        ['Item', 'Amount (RM)'],
                        ['Total Investment Cost', f"{total_cost:,.0f}"],
                        ['Expected Additional Revenue', f"{additional_revenue:,.0f}"],
                        ['Net Benefit', f"{net_benefit:,.0f}"]
                    ]
                    
                    table = Table(cost_breakdown)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 8))
        
        return story
    
    def _create_investment_recommendations(self, economic_data: Dict[str, Any]) -> List:
        """Create investment recommendations section"""
        story = []
        
        story.append(Paragraph("Investment Recommendations", self.styles['Heading2']))
        story.append(Spacer(1, 8))
        
        scenarios = economic_data.get('scenarios', {})
        if scenarios:
            # Find the best ROI scenario
            best_scenario = None
            best_roi = 0
            
            for scenario_name, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict):
                    roi = scenario_data.get('roi_percentage', 0)
                    if roi > best_roi:
                        best_roi = roi
                        best_scenario = (scenario_name, scenario_data)
            
            if best_scenario:
                scenario_name, scenario_data = best_scenario
                story.append(Paragraph(f"<b>Recommended Investment Level:</b> {scenario_name.title()}", self.styles['CustomBody']))
                story.append(Paragraph(f"<b>Expected ROI:</b> {scenario_data.get('roi_percentage', 0):.1f}%", self.styles['CustomBody']))
                story.append(Paragraph(f"<b>Payback Period:</b> {scenario_data.get('payback_months', 0):.0f} months", self.styles['CustomBody']))
                story.append(Spacer(1, 8))
        
        return story
    
    def _create_yield_projections_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create yield projections section with charts"""
        story = []
        
        story.append(Paragraph("Yield Projections", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Find yield forecast data
        yield_forecast = self._extract_yield_forecast_data(analysis_data)
        
        if yield_forecast:
            # Create yield projection chart
            chart_image = self._create_yield_projection_chart(yield_forecast)
            if chart_image:
                # Create a BytesIO object from the image bytes
                img_buffer = io.BytesIO(chart_image)
                story.append(Image(img_buffer, width=6*inch, height=4*inch))
                story.append(Spacer(1, 12))
            
            # Create yield projections table
            story.extend(self._create_yield_projections_table(yield_forecast))
        
        return story
    
    def _extract_yield_forecast_data(self, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract yield forecast data from various sources"""
        # 1. Check direct yield_forecast
        if 'yield_forecast' in analysis_data and analysis_data['yield_forecast']:
            return analysis_data['yield_forecast']
        
        # 2. Check step-by-step analysis
        step_results = analysis_data.get('step_by_step_analysis', [])
        for step in step_results:
            if step.get('step_number') == 6 and 'yield_forecast' in step:
                return step['yield_forecast']
            elif 'yield_forecast' in step and step['yield_forecast']:
                return step['yield_forecast']
        
        return None
    
    def _create_yield_projection_chart(self, yield_forecast: Dict[str, Any]) -> Optional[bytes]:
        """Create yield projection chart"""
        try:
            import matplotlib.pyplot as plt
            import io
            
            # Clear any existing figures to prevent memory issues
            plt.clf()
            plt.close('all')
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            years = [0, 1, 2, 3, 4, 5]
            year_labels = ['Current', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5']
            
            # Plot different investment scenarios
            if 'high_investment' in yield_forecast and len(yield_forecast['high_investment']) >= 6:
                ax.plot(years, yield_forecast['high_investment'][:6], 'o-', label='High Investment', linewidth=2, markersize=6)
            
            if 'medium_investment' in yield_forecast and len(yield_forecast['medium_investment']) >= 6:
                ax.plot(years, yield_forecast['medium_investment'][:6], 's-', label='Medium Investment', linewidth=2, markersize=6)
            
            if 'low_investment' in yield_forecast and len(yield_forecast['low_investment']) >= 6:
                ax.plot(years, yield_forecast['low_investment'][:6], '^-', label='Low Investment', linewidth=2, markersize=6)
            
            # Add baseline if available
            baseline_yield = yield_forecast.get('baseline_yield', 0)
            if baseline_yield > 0:
                ax.axhline(y=baseline_yield, color='gray', linestyle='--', alpha=0.7, label=f'Current Baseline: {baseline_yield:.1f} t/ha')
            
            ax.set_xlabel('Year')
            ax.set_ylabel('Yield (tonnes/hectare)')
            ax.set_title('5-Year Yield Projections by Investment Level')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_xticks(years)
            ax.set_xticklabels(year_labels)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error creating yield projection chart: {str(e)}")
            return None
    
    def _create_yield_projections_table(self, yield_forecast: Dict[str, Any]) -> List:
        """Create yield projections table"""
        story = []
        
        story.append(Paragraph("Yield Projections by Investment Level", self.styles['Heading2']))
        story.append(Spacer(1, 8))
        
        years = [0, 1, 2, 3, 4, 5]
        year_labels = ['Current', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5']
        
        table_data = [['Year'] + year_labels]
        
        # Add rows for each investment level
        for investment_type in ['high_investment', 'medium_investment', 'low_investment']:
            if investment_type in yield_forecast and len(yield_forecast[investment_type]) >= 6:
                investment_name = investment_type.replace('_', ' ').title()
                row = [investment_name]
                for i in range(6):
                    row.append(f"{yield_forecast[investment_type][i]:.1f}")
                table_data.append(row)
        
        if len(table_data) > 1:
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))
        
        return story
    
    def _create_investment_scenarios_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create investment scenarios section"""
        story = []
        
        story.append(Paragraph("Investment Scenarios", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        economic_data = self._extract_economic_data(analysis_data)
        if economic_data and 'scenarios' in economic_data:
            scenarios = economic_data['scenarios']
            
            for scenario_name, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict):
                    story.append(Paragraph(f"{scenario_name.title()} Investment Scenario", self.styles['Heading2']))
                    story.append(Spacer(1, 8))
                    
                    # Scenario details
                    details = [
                        f"<b>Total Investment:</b> RM {scenario_data.get('total_cost', 0):,.0f}",
                        f"<b>Expected Return:</b> RM {scenario_data.get('additional_revenue', 0):,.0f}",
                        f"<b>ROI:</b> {scenario_data.get('roi_percentage', 0):.1f}%",
                        f"<b>Payback Period:</b> {scenario_data.get('payback_months', 0):.0f} months"
                    ]
                    
                    for detail in details:
                        story.append(Paragraph(detail, self.styles['CustomBody']))
                    
                    story.append(Spacer(1, 12))
        
        return story
    
    def _create_cost_benefit_analysis_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create comprehensive cost-benefit analysis section"""
        story = []
        
        story.append(Paragraph("Cost-Benefit Analysis", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        economic_data = self._extract_economic_data(analysis_data)
        if economic_data and 'scenarios' in economic_data:
            scenarios = economic_data['scenarios']
            
            # Create comprehensive comparison table
            table_data = [['Metric', 'High Investment', 'Medium Investment', 'Low Investment']]
            
            # Add rows for each metric
            metrics = [
                ('Total Investment (RM)', 'total_cost'),
                ('Expected Return (RM)', 'additional_revenue'),
                ('ROI (%)', 'roi_percentage'),
                ('Payback Period (Months)', 'payback_months')
            ]
            
            for metric_name, metric_key in metrics:
                row = [metric_name]
                for investment_type in ['high', 'medium', 'low']:
                    scenario_key = f"{investment_type}_investment"
                    if scenario_key in scenarios:
                        value = scenarios[scenario_key].get(metric_key, 0)
                        if 'RM' in metric_name:
                            row.append(f"RM {value:,.0f}")
                        elif '%' in metric_name:
                            row.append(f"{value:.1f}%")
                        else:
                            row.append(f"{value:.0f}")
                    else:
                        row.append("N/A")
                table_data.append(row)
            
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 12))
        
        return story

    def _create_enhanced_economic_forecast_table(self, analysis_data: Dict[str, Any]) -> List:
        """Create enhanced economic forecast table"""
        story = []
        
        # Economic Impact Forecast header
        story.append(Paragraph("Economic Impact Forecast", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Find economic forecast data from multiple possible locations
        economic_data = None
        economic_step = None
        
        # Debug: Log available keys
        logger.info(f"PDF Economic Debug - analysis_data keys: {list(analysis_data.keys())}")
        
        # 1. Check direct economic_forecast in analysis_data (primary location)
        if 'economic_forecast' in analysis_data and analysis_data['economic_forecast']:
            economic_data = analysis_data['economic_forecast']
            logger.info(f"PDF Economic Debug - Found economic_forecast in analysis_data: {type(economic_data)}")
        
        # 2. Check Step 5 (Economic Impact Forecast)
        if not economic_data:
            step_results = analysis_data.get('step_by_step_analysis', [])
            logger.info(f"PDF Economic Debug - step_by_step_analysis length: {len(step_results)}")
            for step in step_results:
                logger.info(f"PDF Economic Debug - Step {step.get('step_number')} keys: {list(step.keys())}")
                if step.get('step_number') == 5 and 'economic_analysis' in step:
                    economic_data = step['economic_analysis']
                    economic_step = step
                    logger.info(f"PDF Economic Debug - Found economic_analysis in Step 5: {type(economic_data)}")
                    break
        
        # 3. Check any step that has economic_analysis
        if not economic_data:
            step_results = analysis_data.get('step_by_step_analysis', [])
            for step in step_results:
                if 'economic_analysis' in step and step['economic_analysis']:
                    economic_data = step['economic_analysis']
                    economic_step = step
                    logger.info(f"PDF Economic Debug - Found economic_analysis in Step {step.get('step_number')}: {type(economic_data)}")
                    break
        
        # 4. Check if economic data is in analysis_results
        if not economic_data and 'analysis_results' in analysis_data:
            analysis_results = analysis_data['analysis_results']
            logger.info(f"PDF Economic Debug - analysis_results keys: {list(analysis_results.keys())}")
            if 'economic_forecast' in analysis_results:
                economic_data = analysis_results['economic_forecast']
                logger.info(f"PDF Economic Debug - Found economic_forecast in analysis_results: {type(economic_data)}")
        
        logger.info(f"PDF Economic Debug - Final economic_data: {economic_data is not None}")
        
        if economic_data:
            econ = economic_data
            
            # Debug: Log the economic data structure
            logger.info(f"PDF Economic Debug - economic_data keys: {list(econ.keys())}")
            logger.info(f"PDF Economic Debug - scenarios: {econ.get('scenarios', {})}")
            
            # Extract data based on the actual structure from analysis engine
            current_yield = econ.get('current_yield_tonnes_per_ha', 0)
            land_size = econ.get('land_size_hectares', 0)
            oil_palm_price = econ.get('oil_palm_price_rm_per_tonne', 600)
            scenarios = econ.get('scenarios', {})
            
            # Debug: Log scenario details
            for scenario_name, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict):
                    logger.info(f"PDF Economic Debug - {scenario_name} scenario: {scenario_data}")
            
            # Display basic information
            if current_yield > 0:
                story.append(Paragraph(f"<b>Current Yield:</b> {current_yield:.1f} tons/ha", self.styles['CustomBody']))
            else:
                story.append(Paragraph(f"<b>Current Yield:</b> Based on analysis results", self.styles['CustomBody']))
            
            if land_size > 0:
                story.append(Paragraph(f"<b>Land Size:</b> {land_size:.1f} hectares", self.styles['CustomBody']))
            
            story.append(Paragraph(f"<b>Oil Palm Price:</b> RM {oil_palm_price:.0f}/tonne", self.styles['CustomBody']))
            story.append(Spacer(1, 12))
            
            # Cost-Benefit Analysis Table
            if scenarios and isinstance(scenarios, dict):
                story.append(Paragraph("Cost-Benefit Analysis by Investment Level", self.styles['Heading2']))
                story.append(Spacer(1, 8))
                
                # Create table data with correct field names
                table_data = [['Investment Level', 'Total Investment (RM)', 'Expected Return (RM)', 'ROI (%)', 'Payback Period (Months)']]
                
                # Process scenarios
                for scenario_name, scenario_data in scenarios.items():
                    if isinstance(scenario_data, dict):
                        # Use the correct field names from analysis engine
                        investment = scenario_data.get('total_cost', 0)
                        expected_return = scenario_data.get('additional_revenue', 0)
                        roi = scenario_data.get('roi_percentage', 0)
                        payback_months = scenario_data.get('payback_months', 0)
                        
                        # Format values
                        try:
                            investment_formatted = f"{float(investment):,.0f}" if investment != 'N/A' and investment > 0 else 'N/A'
                        except (ValueError, TypeError):
                            investment_formatted = str(investment) if investment else 'N/A'
                        
                        try:
                            return_formatted = f"{float(expected_return):,.0f}" if expected_return != 'N/A' and expected_return > 0 else 'N/A'
                        except (ValueError, TypeError):
                            return_formatted = str(expected_return) if expected_return else 'N/A'
                        
                        try:
                            roi_formatted = f"{float(roi):.1f}" if roi != 'N/A' and roi > 0 else 'N/A'
                        except (ValueError, TypeError):
                            roi_formatted = str(roi) if roi else 'N/A'
                        
                        try:
                            payback_formatted = f"{float(payback_months):.1f}" if payback_months != 'N/A' and payback_months > 0 else 'N/A'
                        except (ValueError, TypeError):
                            payback_formatted = str(payback_months) if payback_months else 'N/A'
                        
                        table_data.append([scenario_name.title(), investment_formatted, return_formatted, roi_formatted, payback_formatted])
                
                # Create wider table with better column widths to prevent overlapping
                table = Table(table_data, colWidths=[2.0*inch, 1.8*inch, 1.8*inch, 1.2*inch, 1.4*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),  # Smaller header font
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),  # Even smaller font for data rows
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Center vertically
                ]))
                
                story.append(table)
                story.append(Spacer(1, 12))
                
                # Add assumptions if available
                if 'assumptions' in econ and econ['assumptions']:
                    story.append(Paragraph("Economic Forecast Assumptions:", self.styles['Heading3']))
                    for assumption in econ['assumptions']:
                        story.append(Paragraph(f"• {assumption}", self.styles['CustomBody']))
                    story.append(Spacer(1, 8))
                
                # Add note
                story.append(Paragraph("<i>Note: RM values are based on current market rates and typical plantation economics.</i>", self.styles['CustomBody']))
        else:
            # Create a basic economic forecast when data is not available
            story.append(Paragraph("Economic Impact Assessment", self.styles['Heading2']))
            story.append(Spacer(1, 8))
            
            # Basic economic information
            story.append(Paragraph("<b>Current Yield:</b> Based on analysis results", self.styles['CustomBody']))
            story.append(Paragraph("<b>Projected Yield Improvement:</b> 15-25% with proper management", self.styles['CustomBody']))
            story.append(Paragraph("<b>Estimated ROI:</b> 200-300% over 3-5 years", self.styles['CustomBody']))
            story.append(Spacer(1, 12))
            
            # Basic cost-benefit table
            story.append(Paragraph("Estimated Cost-Benefit Analysis", self.styles['Heading3']))
            story.append(Spacer(1, 8))
            
            table_data = [
                ['Investment Level', 'Total Investment (RM)', 'Expected Return (RM)', 'ROI (%)', 'Payback Period (Months)'],
                ['Low Investment', '2,000 - 3,000', '8,000 - 12,000', '250-300', '24-36'],
                ['Medium Investment', '4,000 - 6,000', '15,000 - 20,000', '275-350', '24-36'],
                ['High Investment', '8,000 - 12,000', '25,000 - 35,000', '200-300', '36-48']
            ]
            
            # Create wider table with better column widths to prevent overlapping
            table = Table(table_data, colWidths=[2.0*inch, 1.8*inch, 1.8*inch, 1.2*inch, 1.4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),  # Smaller header font
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),  # Even smaller font for data rows
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')  # Center vertically
            ]))
            
            story.append(table)
            story.append(Spacer(1, 12))
            
            # Add note
            story.append(Paragraph("<i>Note: These are estimated values based on typical oil palm plantation economics. Actual results may vary based on specific conditions and implementation.</i>", self.styles['CustomBody']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_enhanced_yield_forecast_graph(self, analysis_data: Dict[str, Any]) -> List:
        """Create enhanced yield forecast graph"""
        story = []
        
        # 5-Year Yield Forecast header
        story.append(Paragraph("5-Year Yield Forecast", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Find yield forecast data from multiple possible locations
        yield_forecast = None
        forecast_step = None
        
        # 1. Check Step 6 (Forecast Graph)
        step_results = analysis_data.get('step_by_step_analysis', [])
        for step in step_results:
            if step.get('step_number') == 6 and 'yield_forecast' in step:
                yield_forecast = step['yield_forecast']
                forecast_step = step
                break
        
        # 2. Check direct yield_forecast in analysis_data
        if not yield_forecast and 'yield_forecast' in analysis_data:
            yield_forecast = analysis_data['yield_forecast']
        
        # 3. Check any step that has yield_forecast
        if not yield_forecast:
            for step in step_results:
                if 'yield_forecast' in step and step['yield_forecast']:
                    yield_forecast = step['yield_forecast']
                    forecast_step = step
                    break
        
        if yield_forecast:
            
            # Create the yield forecast graph
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Years including baseline (0-5)
            years = [0, 1, 2, 3, 4, 5]
            year_labels = ['Current', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5']
            
            # Get baseline yield
            baseline_yield = yield_forecast.get('baseline_yield', 0)
            
            # Add baseline reference line
            if baseline_yield > 0:
                ax.axhline(y=baseline_yield, color='gray', linestyle='--', alpha=0.7, 
                          label=f'Current Baseline: {baseline_yield:.1f} t/ha')
            
            # Plot lines for different investment approaches
            if 'high_investment' in yield_forecast and len(yield_forecast['high_investment']) >= 6:
                high_yields = yield_forecast['high_investment']
                ax.plot(years, high_yields, 'r-o', linewidth=2, label='High Investment', markersize=6)
            
            if 'medium_investment' in yield_forecast and len(yield_forecast['medium_investment']) >= 6:
                medium_yields = yield_forecast['medium_investment']
                ax.plot(years, medium_yields, 'g-s', linewidth=2, label='Medium Investment', markersize=6)
            
            if 'low_investment' in yield_forecast and len(yield_forecast['low_investment']) >= 6:
                low_yields = yield_forecast['low_investment']
                ax.plot(years, low_yields, 'b-^', linewidth=2, label='Low Investment', markersize=6)
            
            # Customize the graph
            ax.set_xlabel('Years', fontsize=12, fontweight='bold')
            ax.set_ylabel('Yield (tons/ha)', fontsize=12, fontweight='bold')
            ax.set_title('5-Year Yield Forecast from Current Baseline', fontsize=14, fontweight='bold')
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_xticks(years)
            ax.set_xticklabels(year_labels)
            
            # Save the graph to a buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            
            # Add the graph to the PDF
            story.append(Image(buffer, width=6*inch, height=3.6*inch))
            story.append(Spacer(1, 12))
            
            # Add assumptions
            if 'assumptions' in forecast_step:
                story.append(Paragraph("Assumptions:", self.styles['Heading3']))
                for assumption in forecast_step['assumptions']:
                    story.append(Paragraph(f"• {assumption}", self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            plt.close(fig)
        else:
            # Create a basic yield forecast graph when data is not available
            story.append(Paragraph("Yield Projection Overview", self.styles['Heading2']))
            story.append(Spacer(1, 8))
            
            # Create a basic yield forecast graph
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Years including baseline (0-5)
            years = [0, 1, 2, 3, 4, 5]
            year_labels = ['Current', 'Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5']
            
            # Baseline yield (typical oil palm yield)
            baseline_yield = 15.0  # tons/ha
            
            # Add baseline reference line
            ax.axhline(y=baseline_yield, color='gray', linestyle='--', alpha=0.7, 
                      label=f'Current Baseline: {baseline_yield:.1f} t/ha')
            
            # Create sample projections
            high_yields = [baseline_yield, 16.5, 18.2, 19.8, 21.5, 23.0]
            medium_yields = [baseline_yield, 16.0, 17.5, 19.0, 20.2, 21.5]
            low_yields = [baseline_yield, 15.5, 16.8, 18.0, 19.0, 20.0]
            
            # Plot lines for different investment approaches
            ax.plot(years, high_yields, 'r-o', linewidth=2, label='High Investment', markersize=6)
            ax.plot(years, medium_yields, 'g-s', linewidth=2, label='Medium Investment', markersize=6)
            ax.plot(years, low_yields, 'b-^', linewidth=2, label='Low Investment', markersize=6)
            
            # Customize the graph
            ax.set_xlabel('Years', fontsize=12, fontweight='bold')
            ax.set_ylabel('Yield (tons/ha)', fontsize=12, fontweight='bold')
            ax.set_title('5-Year Yield Forecast - Sample Projections', fontsize=14, fontweight='bold')
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_xticks(years)
            ax.set_xticklabels(year_labels)
            
            # Save the graph to a buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            
            # Add the graph to the PDF
            story.append(Image(buffer, width=6*inch, height=3.6*inch))
            story.append(Spacer(1, 12))
            
            # Add assumptions
            story.append(Paragraph("Projection Assumptions:", self.styles['Heading3']))
            assumptions = [
                "Projections based on typical oil palm plantation improvement scenarios",
                "High investment includes comprehensive soil amendments and precision fertilization",
                "Medium investment focuses on targeted nutrient management",
                "Low investment emphasizes basic soil health improvements",
                "Results may vary based on specific field conditions and implementation"
            ]
            
            for assumption in assumptions:
                story.append(Paragraph(f"• {assumption}", self.styles['CustomBody']))
            story.append(Spacer(1, 8))
            
            plt.close(fig)
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_enhanced_conclusion(self, analysis_data: Dict[str, Any]) -> List:
        """Create enhanced detailed conclusion section"""
        story = []
        
        # Conclusion header
        story.append(Paragraph("Detailed Conclusion", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Extract key data for personalized conclusion
        step_analysis = analysis_data.get('step_by_step_analysis', [])
        economic_forecast = analysis_data.get('economic_forecast', {})
        yield_forecast = analysis_data.get('yield_forecast', {})
        
        # Build dynamic conclusion based on analysis results
        conclusion_parts = []
        
        # Analysis overview
        conclusion_parts.append("""
        <b>Analysis Overview:</b><br/>
        This comprehensive agricultural analysis has systematically evaluated your oil palm plantation's current nutritional status and identified critical areas for improvement. The step-by-step analysis reveals specific challenges and opportunities that directly impact your plantation's productivity and profitability.
        """)
        
        # Key findings summary
        if step_analysis:
            conclusion_parts.append("""
        <b>Key Findings Summary:</b><br/>
        The analysis has identified several critical factors affecting your plantation's performance. These findings provide a clear roadmap for targeted interventions that will maximize your return on investment while ensuring sustainable agricultural practices.
        """)
        
        # Economic impact
        if economic_forecast:
            conclusion_parts.append("""
        <b>Economic Impact Assessment:</b><br/>
        The economic analysis demonstrates significant potential for improved profitability through strategic interventions. The investment scenarios presented show clear pathways to enhanced yields and increased revenue, with medium investment approaches typically offering the optimal balance between cost-effectiveness and yield improvement.
        """)
        
        # Yield projections
        if yield_forecast:
            conclusion_parts.append("""
        <b>5-Year Yield Projections:</b><br/>
        The yield forecast analysis provides a detailed roadmap for sustainable growth over the next five years. These projections are based on realistic investment scenarios and account for seasonal variations, market conditions, and implementation timelines. The forecast demonstrates the potential for substantial yield improvements with proper management and targeted interventions.
        """)
        
        # Implementation recommendations
        conclusion_parts.append("""
        <b>Implementation Strategy:</b><br/>
        Successful implementation of these recommendations requires a phased approach, beginning with high-priority interventions and gradually expanding to comprehensive management practices. Regular monitoring and adaptive management will be essential to achieving the projected outcomes and ensuring long-term sustainability.
        """)
        
        # Long-term outlook
        conclusion_parts.append("""
        <b>Long-term Outlook:</b><br/>
        The analysis indicates strong potential for sustained productivity improvements and enhanced profitability. By following the recommended strategies and maintaining consistent monitoring practices, your plantation can achieve significant yield increases while contributing to sustainable agricultural intensification goals. The 5-year projections provide a clear vision for long-term success and continued growth.
        """)
        
        # Combine all conclusion parts
        full_conclusion = "<br/><br/>".join(conclusion_parts)
        
        story.append(Paragraph(full_conclusion, self.styles['CustomBody']))
        story.append(Spacer(1, 20))
        
        # Add final summary paragraph
        final_summary = """
        <b>Final Summary:</b><br/>
        This analysis provides a comprehensive foundation for optimizing your oil palm plantation's performance. The combination of detailed nutritional assessment, economic analysis, and yield projections offers a clear path forward for achieving improved productivity and profitability. Implementation of the recommended strategies will position your plantation for sustainable success and long-term growth.
        """
        
        story.append(Paragraph(final_summary, self.styles['CustomBody']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_references_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create references section for step-by-step analysis"""
        story = []
        
        # References header
        story.append(Paragraph("References", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Get references from analysis data
        all_references = analysis_data.get('references', {})
        
        if all_references:
            total_refs = len(all_references.get('database_references', [])) + len(all_references.get('web_references', []))
            
            if total_refs > 0:
                story.append(Paragraph(f"<b>Total References Found:</b> {total_refs}", self.styles['CustomBody']))
                story.append(Spacer(1, 12))
                
                # Database references
                if all_references['database_references']:
                    story.append(Paragraph("Database References", self.styles['Heading2']))
                    story.append(Spacer(1, 8))
                    
                    for i, ref in enumerate(all_references['database_references'], 1):
                        ref_text = f"<b>{i}.</b> {ref['title']}<br/>"
                        ref_text += f"<i>Source:</i> {ref['source']}<br/>"
                        if ref.get('url'):
                            ref_text += f"<i>URL:</i> {ref['url']}<br/>"
                        if ref.get('tags'):
                            ref_text += f"<i>Tags:</i> {', '.join(ref['tags'])}<br/>"
                        ref_text += f"<i>Relevance Score:</i> {ref.get('relevance_score', 0):.2f}"
                        
                        story.append(Paragraph(ref_text, self.styles['CustomBody']))
                        story.append(Spacer(1, 8))
                
                # Web references
                if all_references['web_references']:
                    story.append(Paragraph("Web References", self.styles['Heading2']))
                    story.append(Spacer(1, 8))
                    
                    for i, ref in enumerate(all_references['web_references'], 1):
                        ref_text = f"<b>{i}.</b> {ref['title']}<br/>"
                        ref_text += f"<i>Source:</i> {ref['source']}<br/>"
                        if ref.get('url'):
                            ref_text += f"<i>URL:</i> {ref['url']}<br/>"
                        if ref.get('published_date'):
                            ref_text += f"<i>Published:</i> {ref['published_date']}<br/>"
                        ref_text += f"<i>Relevance Score:</i> {ref.get('relevance_score', 0):.2f}"
                        
                        story.append(Paragraph(ref_text, self.styles['CustomBody']))
                        story.append(Spacer(1, 8))
                
                # Summary
                story.append(Paragraph(f"<b>Total references found:</b> {total_refs} ({len(all_references['database_references'])} database, {len(all_references['web_references'])} web)", self.styles['CustomBody']))
        
        return story
    
    def _create_appendix(self) -> List:
        """Create appendix section"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("Appendix", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # MPOB Standards Reference
        story.append(Paragraph("MPOB Standards Reference", self.styles['CustomSubheading']))
        story.append(Paragraph(
            "This analysis is based on Malaysian Palm Oil Board (MPOB) standards for soil and leaf analysis. "
            "The standards provide optimal ranges for various parameters to ensure maximum palm oil yield and quality.",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 15))
        
        # Technical Details
        story.append(Paragraph("Technical Details", self.styles['CustomSubheading']))
        story.append(Paragraph(
            "Analysis Engine: AGS AI-powered agricultural analysis system\n"
            "AI Model: Advanced machine learning algorithms trained on agricultural data\n"
            "Standards Database: MPOB official guidelines and best practices\n"
            "Report Generation: Automated PDF generation with comprehensive insights",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 15))
        
        # Disclaimer
        story.append(Paragraph("Disclaimer", self.styles['CustomSubheading']))
        story.append(Paragraph(
            "This report is generated by an AI system and should be used as a guide. "
            "Always consult with agricultural experts and conduct additional testing before "
            "implementing major changes to your farming practices. The recommendations are "
            "based on general best practices and may need to be adapted to local conditions.",
            self.styles['Warning']
        ))
        
        return story

def generate_pdf_report(analysis_data: Dict[str, Any], metadata: Dict[str, Any], 
                       options: Optional[Dict[str, Any]] = None) -> bytes:
    """Main function to generate PDF report"""
    try:
        if options is None:
            options = {
                'include_economic': True,
                'include_forecast': True,
                'include_charts': True
            }
        
        generator = PDFReportGenerator()
        pdf_bytes = generator.generate_report(analysis_data, metadata, options)
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise

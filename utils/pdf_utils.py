import io
import logging
import re
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
        self.page_width = A4[0]
        self.page_height = A4[1]
        self.margin = 72  # 1 inch margins
        self.content_width = self.page_width - (2 * self.margin)
    
    def _create_table_with_proper_layout(self, table_data, col_widths=None, font_size=9):
        """Create a table that fits page width and wraps long text to prevent overlap."""
        if not table_data or len(table_data) < 1:
            return None

        # Convert strings to Paragraphs to enable word wrapping
        body_style = ParagraphStyle(
            'TblBody', fontSize=font_size, leading=font_size + 2, wordWrap='CJK',
            spaceBefore=0, spaceAfter=0
        )
        header_style = ParagraphStyle(
            'TblHeader', fontSize=font_size + 1, leading=font_size + 3, wordWrap='CJK',
            spaceBefore=0, spaceAfter=0
        )

        wrapped = []
        for r_idx, row in enumerate(table_data):
            wrapped_row = []
            for cell in row:
                if isinstance(cell, str):
                    style = header_style if r_idx == 0 else body_style
                    wrapped_row.append(Paragraph(cell.replace('\n', '<br/>'), style))
                else:
                    wrapped_row.append(cell)
            wrapped.append(wrapped_row)

        # Calculate column widths if not provided
        if col_widths is None:
            num_cols = len(wrapped[0])
            if num_cols <= 2:
                col_widths = [self.content_width * 0.4, self.content_width * 0.6]
            elif num_cols == 3:
                col_widths = [self.content_width * 0.3, self.content_width * 0.35, self.content_width * 0.35]
            elif num_cols == 4:
                col_widths = [self.content_width * 0.25] * 4
            elif num_cols == 5:
                col_widths = [self.content_width * 0.2] * 5
            else:
                col_widths = [self.content_width / num_cols] * num_cols

        total_width = sum(col_widths)
        if total_width > self.content_width:
            scale = self.content_width / total_width
            col_widths = [w * scale for w in col_widths]

        table = Table(wrapped, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),           # header centered
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),            # body left for readability
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), font_size + 1),
            ('FONTSIZE', (0, 1), (-1, -1), font_size),
            ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ]))
        return table
    
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
            borderPadding=5,
            alignment=4  # Justify
        ))
        
        styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#388E3C'),
            alignment=4  # Justify
        ))
        
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=colors.black,
            alignment=4  # Justify
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
            backColor=colors.HexColor('#E8F5E8'),
            alignment=4  # Justify
        ))
        
        styles.add(ParagraphStyle(
            name='Warning',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.red,
            backColor=colors.HexColor('#FFEBEE'),
            borderWidth=1,
            borderColor=colors.red,
            borderPadding=5,
            alignment=4  # Justify
        ))
        
        # Add justification to default styles
        styles['Normal'].alignment = 4  # Justify
        styles['Heading1'].alignment = 4  # Justify
        styles['Heading2'].alignment = 4  # Justify
        styles['Heading3'].alignment = 4  # Justify
        styles['BodyText'].alignment = 4  # Justify
        
        return styles
    
    def generate_report(self, analysis_data: Dict[str, Any], metadata: Dict[str, Any], 
                       options: Dict[str, Any]) -> bytes:
        """Generate complete PDF report with comprehensive analysis support"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=54,  # slightly narrower margins to fit tables
            leftMargin=54,
            topMargin=54,
            bottomMargin=36,
        )
        
        # Build story
        story = []
        
        # Title page
        story.extend(self._create_title_page(metadata))
        story.append(PageBreak())
        
        # Check if this is step-by-step analysis format
        is_step_by_step = 'step_by_step_analysis' in analysis_data
        
        if is_step_by_step:
            # Comprehensive PDF format with step-by-step analysis and visualizations
            # Include ALL sections from results page to match exactly what user sees
            
            # 1. Results Header (metadata)
            story.extend(self._create_results_header_section(analysis_data, metadata))
            
            # 2. Executive Summary (if enabled) - COPY EXACTLY FROM RESULTS PAGE
            if options.get('include_summary', True):
                story.extend(self._create_enhanced_executive_summary(analysis_data))
            
            # 4. Key Findings - COPY FROM RESULTS PAGE
            if options.get('include_key_findings', True):
                story.extend(self._create_consolidated_key_findings_section(analysis_data))
            
            # 5. Step-by-Step Analysis (if enabled)
            if options.get('include_step_analysis', True):
                story.extend(self._create_comprehensive_step_by_step_analysis(analysis_data))
            
            # 6. Data Visualizations - ALL GRAPHS AND CHARTS
            if options.get('include_charts', True):
                try:
                    viz_section = self._create_comprehensive_visualizations_section(analysis_data)
                    if viz_section:
                        story.extend(viz_section)
                    else:
                        logger.warning("Visualizations section returned empty")
                        story.append(Paragraph("📊 Data Visualizations", self.styles['Heading2']))
                        story.append(Spacer(1, 12))
                        story.append(Paragraph("No visualizations available for this analysis.", self.styles['Normal']))
                except Exception as e:
                    logger.error(f"Error creating visualizations section: {str(e)}")
                    story.append(Paragraph("📊 Data Visualizations", self.styles['Heading2']))
                    story.append(Spacer(1, 12))
                    story.append(Paragraph("Visualizations could not be generated due to technical issues.", self.styles['Normal']))

            # 7. Economic Forecast Tables (always included for step-by-step)
            story.extend(self._create_enhanced_economic_forecast_table(analysis_data))
            
            # 8. References (if enabled)
            if options.get('include_references', True):
                story.extend(self._create_references_section(analysis_data))
            
            # 7. Conclusion (always included)
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
            
            # Economic forecast tables and charts (always included for comprehensive)
            story.extend(self._create_enhanced_economic_forecast_table(analysis_data))
            story.extend(self._create_enhanced_yield_forecast_graph(analysis_data))
            
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
            story.extend(self._create_enhanced_executive_summary(analysis_data))
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
        
        # Build PDF with page frame (borders)
        def _draw_page_frame(canvas, doc):
            from reportlab.lib.colors import black
            canvas.saveState()
            canvas.setStrokeColor(black)
            canvas.setLineWidth(0.5)
            x0 = doc.leftMargin - 10
            y0 = doc.bottomMargin - 10
            w = doc.width + 20
            h = doc.height + 20
            canvas.rect(x0, y0, w, h)
            canvas.restoreState()

        doc.build(story, onFirstPage=_draw_page_frame, onLaterPages=_draw_page_frame)
        
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
        
        metadata_table = Table(metadata_data, colWidths=[self.content_width*0.35, self.content_width*0.65])
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
    
    def _create_executive_summary(self, analysis_data: Dict[str, Any]) -> List:
        """Create executive summary for legacy format"""
        story = []
        
        # Executive Summary header
        story.append(Paragraph("Executive Summary", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Simple executive summary
        story.append(Paragraph(
            "This comprehensive agronomic analysis evaluates key nutritional parameters from both soil and leaf tissue samples to assess the current fertility status and plant health of the oil palm plantation. The analysis is based on adherence to Malaysian Palm Oil Board (MPOB) standards for optimal oil palm cultivation.",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 20))
        
        return story
        
    def _create_parameters_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create parameters section for legacy format"""
        story = []
        
        # Parameters header
        story.append(Paragraph("Parameters Analysis", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Simple parameters summary
        story.append(Paragraph(
            "Parameter analysis includes soil and leaf nutrient assessment based on MPOB standards.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_recommendations_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create recommendations section for legacy format"""
        story = []
        
        # Recommendations header
        story.append(Paragraph("Recommendations", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Simple recommendations summary
        story.append(Paragraph(
            "Recommendations are based on the analysis results and MPOB standards for optimal oil palm cultivation.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_forecast_section(self, forecast_data: Dict[str, Any]) -> List:
        """Create forecast section for legacy format"""
        story = []
        
        # Forecast header
        story.append(Paragraph("📈 Yield Forecast", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Simple forecast summary
        story.append(Paragraph(
            "Yield forecast analysis is available in the comprehensive analysis section.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_charts_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create charts section for legacy format"""
        story = []
        
        # Charts header
        story.append(Paragraph("📊 Charts and Visualizations", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Simple charts summary
        story.append(Paragraph(
            "Charts and visualizations are available in the comprehensive analysis section.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_comprehensive_charts_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create comprehensive charts section"""
        story = []
        
        # Charts header
        story.append(Paragraph("📊 Data Visualizations", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Simple charts summary
        story.append(Paragraph(
            "Data visualizations include soil and leaf nutrient status charts based on MPOB standards.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_enhanced_executive_summary(self, analysis_data: Dict[str, Any]) -> List:
        """Create executive summary - Generate dynamically like results page"""
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
        
        # Try to get executive summary from analysis_results
        if 'executive_summary' in analysis_results and analysis_results['executive_summary']:
            executive_summary_text = analysis_results['executive_summary']
            if isinstance(executive_summary_text, str) and executive_summary_text.strip():
                # Use the executive summary text exactly as it appears in results page
                story.append(Paragraph(executive_summary_text, self.styles['CustomBody']))
                story.append(Spacer(1, 12))
                return story
        
        # Generate executive summary dynamically from available data
        try:
            # Get metadata and data
            metadata = analysis_results.get('analysis_metadata', {})
            raw_data = analysis_results.get('raw_data', {})
            issues_analysis = analysis_results.get('issues_analysis', {})
            
            # Generate comprehensive agronomic summary
            summary_sentences = []
            
            # 1-3: Analysis overview and scope
            total_samples = metadata.get('total_parameters_analyzed', 0)
            summary_sentences.append(
                f"This comprehensive agronomic analysis evaluates {total_samples} key nutritional parameters from both soil and leaf tissue samples to assess the current fertility status and plant health of the oil palm plantation."
            )
            summary_sentences.append(
                "The analysis is based on adherence to Malaysian Palm Oil Board (MPOB) standards for optimal oil palm cultivation."
            )
            
            # 4-6: Issues identified
            all_issues = issues_analysis.get('all_issues', [])
            critical_issues = len([i for i in all_issues if i.get('severity') == 'Critical'])
            high_issues = len([i for i in all_issues if i.get('severity') == 'High'])
            medium_issues = len([i for i in all_issues if i.get('severity') == 'Medium'])
            
            if critical_issues > 0:
                summary_sentences.append(
                    f"Laboratory results indicate {critical_issues} significant nutritional imbalances requiring immediate attention to optimize yield potential and maintain sustainable production."
                )
                summary_sentences.append(
                    f"Critical nutritional deficiencies identified in {critical_issues} parameters pose immediate threats to palm productivity and require urgent corrective measures within the next 30-60 days."
                )
            
            if high_issues > 0:
                summary_sentences.append(
                    f"High-severity imbalances affecting {high_issues} additional parameters will significantly impact yield potential if not addressed through targeted fertilization programs within 3-6 months."
                )
            
            if medium_issues > 0:
                summary_sentences.append(
                    f"Medium-priority nutritional concerns in {medium_issues} parameters suggest the need for adjusted maintenance fertilization schedules to prevent future deficiencies."
                )
            
            # 7-9: Yield and economic impact
            land_yield_data = raw_data.get('land_yield_data', {})
            current_yield = land_yield_data.get('current_yield', 0)
            land_size = land_yield_data.get('land_size', 0)
            
            if current_yield > 0:
                summary_sentences.append(
                    f"Current yield performance of {current_yield} tonnes per hectare across {land_size} hectares exceeds industry benchmarks, with nutritional corrections potentially maintaining production by 15-25%."
                )
                summary_sentences.append(
                    "Economic analysis indicates that investment in corrective fertilization programs will generate positive returns within 12-18 months through improved fruit bunch quality and increased fresh fruit bunch production."
                )
            
            # 10-12: Implementation and monitoring
            summary_sentences.append(
                "Implementation of precision fertilization based on these findings, combined with regular soil and leaf monitoring every 6 months, will ensure sustained productivity and long-term plantation profitability."
            )
            summary_sentences.append(
                "Adoption of integrated nutrient management practices, including organic matter incorporation and micronutrient supplementation, will enhance soil health and support the plantation's transition toward sustainable intensification goals."
            )
            summary_sentences.append(
                "Continued monitoring and adaptive management strategies will be essential for maintaining optimal nutritional status and maximizing the economic potential of this oil palm operation."
            )
            
            # Combine all sentences into executive summary
            executive_summary_text = " ".join(summary_sentences)
            
            # Add the generated executive summary
            story.append(Paragraph(executive_summary_text, self.styles['CustomBody']))
            story.append(Spacer(1, 12))
            
            logger.info("✅ Generated dynamic executive summary for PDF")
            return story
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
        
        # Fallback: Use a generic executive summary
        fallback_summary = (
            "This comprehensive agronomic analysis evaluates key nutritional parameters from both soil and leaf tissue samples to assess the current fertility status and plant health of the oil palm plantation. "
            "The analysis is based on adherence to Malaysian Palm Oil Board (MPOB) standards for optimal oil palm cultivation. "
            "Laboratory results indicate nutritional imbalances requiring attention to optimize yield potential and maintain sustainable production. "
            "Implementation of precision fertilization based on these findings, combined with regular soil and leaf monitoring every 6 months, will ensure sustained productivity and long-term plantation profitability."
        )
        
        story.append(Paragraph(fallback_summary, self.styles['CustomBody']))
        story.append(Spacer(1, 12))
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
    
    def _merge_similar_findings(self, finding1: str, finding2: str) -> str:
        """Merge two similar findings into one comprehensive finding"""
        import re
        
        # Extract parameter names with comprehensive mapping for all 9 soil and 8 leaf parameters
        param_mapping = {
            # Soil Parameters (9)
            'ph': ['ph', 'ph level', 'soil ph', 'acidity', 'alkalinity'],
            'nitrogen': ['nitrogen', 'n', 'n%', 'n_%', 'nitrogen%', 'nitrogen_%'],
            'organic_carbon': ['organic carbon', 'organic_carbon', 'carbon', 'c', 'c%', 'c_%', 'organic_carbon_%'],
            'total_phosphorus': ['total phosphorus', 'total p', 'total_p', 'total phosphorus mg/kg', 'total_p_mg_kg'],
            'available_phosphorus': ['available phosphorus', 'available p', 'available_p', 'available phosphorus mg/kg', 'available_p_mg_kg'],
            'exchangeable_potassium': ['exchangeable potassium', 'exch k', 'exch_k', 'exchangeable k', 'exchangeable_k', 'k meq%', 'k_meq%', 'exchangeable_k_meq%'],
            'exchangeable_calcium': ['exchangeable calcium', 'exch ca', 'exch_ca', 'exchangeable ca', 'exchangeable_ca', 'ca meq%', 'ca_meq%', 'exchangeable_ca_meq%'],
            'exchangeable_magnesium': ['exchangeable magnesium', 'exch mg', 'exch_mg', 'exchangeable mg', 'exchangeable_mg', 'mg meq%', 'mg_meq%', 'exchangeable_mg_meq%'],
            'cec': ['cec', 'cation exchange capacity', 'c.e.c', 'cec meq%', 'cec_meq%'],
            
            # Leaf Parameters (8)
            'leaf_nitrogen': ['leaf nitrogen', 'leaf n', 'leaf_n', 'n%', 'n_%', 'nitrogen%', 'nitrogen_%'],
            'leaf_phosphorus': ['leaf phosphorus', 'leaf p', 'leaf_p', 'p%', 'p_%', 'phosphorus%', 'phosphorus_%'],
            'leaf_potassium': ['leaf potassium', 'leaf k', 'leaf_k', 'k%', 'k_%', 'potassium%', 'potassium_%'],
            'leaf_magnesium': ['leaf magnesium', 'leaf mg', 'leaf_mg', 'mg%', 'mg_%', 'magnesium%', 'magnesium_%'],
            'leaf_calcium': ['leaf calcium', 'leaf ca', 'leaf_ca', 'ca%', 'ca_%', 'calcium%', 'calcium_%'],
            'leaf_boron': ['leaf boron', 'leaf b', 'leaf_b', 'b mg/kg', 'b_mg_kg', 'boron mg/kg', 'boron_mg_kg'],
            'leaf_copper': ['leaf copper', 'leaf cu', 'leaf_cu', 'cu mg/kg', 'cu_mg_kg', 'copper mg/kg', 'copper_mg_kg'],
            'leaf_zinc': ['leaf zinc', 'leaf zn', 'leaf_zn', 'zn mg/kg', 'zn_mg_kg', 'zinc mg/kg', 'zinc_mg_kg'],
            
            # Land & Yield Parameters
            'land_size': ['land size', 'land_size', 'farm size', 'farm_size', 'area', 'hectares', 'acres', 'square meters', 'square_meters'],
            'current_yield': ['current yield', 'current_yield', 'yield', 'production', 'tonnes/hectare', 'kg/hectare', 'tonnes/acre', 'kg/acre', 'yield per hectare', 'yield per acre'],
            'yield_forecast': ['yield forecast', 'yield_forecast', 'projected yield', 'projected_yield', 'future yield', 'future_yield', 'yield projection', 'yield_projection'],
            'economic_impact': ['economic impact', 'economic_impact', 'roi', 'return on investment', 'cost benefit', 'cost_benefit', 'profitability', 'revenue', 'income'],
            
            # Legacy mappings for backward compatibility
            'phosphorus': ['phosphorus', 'p', 'p%', 'p_%', 'phosphorus%', 'available p'],
            'potassium': ['potassium', 'k', 'k%', 'k_%', 'potassium%'],
            'calcium': ['calcium', 'ca', 'ca%', 'ca_%', 'calcium%'],
            'magnesium': ['magnesium', 'mg', 'mg%', 'mg_%', 'magnesium%'],
            'copper': ['copper', 'cu', 'cu mg/kg', 'cu_mg/kg', 'copper mg/kg'],
            'zinc': ['zinc', 'zn', 'zn mg/kg', 'zn_mg/kg', 'zinc mg/kg'],
            'boron': ['boron', 'b', 'b mg/kg', 'b_mg/kg', 'boron mg/kg']
        }
        
        def extract_parameters(text):
            """Extract all parameters mentioned in text"""
            found_params = set()
            text_lower = text.lower()
            for param, variations in param_mapping.items():
                if any(var in text_lower for var in variations):
                    found_params.add(param)
            return found_params
        
        def extract_values(text):
            """Extract all numerical values from text"""
            return re.findall(r'\d+\.?\d*%?', text)
        
        def extract_severity_keywords(text):
            """Extract severity and impact keywords"""
            severity_words = ['critical', 'severe', 'high', 'low', 'deficiency', 'excess', 'optimum', 'below', 'above']
            found_severity = [word for word in severity_words if word in text.lower()]
            return found_severity
        
        # Extract information from both findings
        params1 = extract_parameters(finding1)
        params2 = extract_parameters(finding2)
        values1 = extract_values(finding1)
        values2 = extract_values(finding2)
        severity1 = extract_severity_keywords(finding1)
        severity2 = extract_severity_keywords(finding2)
        
        # If both findings are about the same parameter(s), merge them comprehensively
        if params1 and params2 and params1.intersection(params2):
            # Get the common parameter
            common_params = list(params1.intersection(params2))
            param_name = common_params[0].upper() if common_params[0] != 'ph' else 'pH'
            
            # Combine all values
            all_values = list(set(values1 + values2))
            
            # Combine all severity keywords
            all_severity = list(set(severity1 + severity2))
            
            # Create comprehensive finding
            if 'critical' in all_severity or 'severe' in all_severity:
                severity_desc = "critical"
            elif 'high' in all_severity:
                severity_desc = "significant"
            elif 'low' in all_severity:
                severity_desc = "moderate"
            else:
                severity_desc = "notable"
            
            # Build comprehensive finding
            if param_name == 'pH':
                comprehensive_finding = f"Soil {param_name} shows {severity_desc} issues with values of {', '.join(all_values)}. "
            else:
                comprehensive_finding = f"{param_name} levels show {severity_desc} issues with values of {', '.join(all_values)}. "
            
            # Add context from both findings
            context_parts = []
            if 'deficiency' in all_severity:
                context_parts.append("deficiency")
            if 'excess' in all_severity:
                context_parts.append("excess")
            if 'below' in all_severity:
                context_parts.append("below optimal levels")
            if 'above' in all_severity:
                context_parts.append("above optimal levels")
            
            if context_parts:
                comprehensive_finding += f"This indicates {', '.join(context_parts)}. "
            
            # Add impact information
            if 'critical' in all_severity or 'severe' in all_severity:
                comprehensive_finding += "This directly impacts crop yield and requires immediate attention."
            elif 'high' in all_severity:
                comprehensive_finding += "This significantly affects plant health and productivity."
            else:
                comprehensive_finding += "This affects overall plant performance and should be addressed."
            
            return comprehensive_finding
        
        # If findings are about different parameters, combine them
        return f"{finding1} Additionally, {finding2.lower()}"
    
    def _group_and_merge_findings_by_parameter_pdf(self, findings_list):
        """Group findings by parameter and merge all findings about the same parameter into one comprehensive finding"""
        import re
        
        # Parameter mapping for grouping - comprehensive mapping for all 9 soil and 8 leaf parameters
        param_mapping = {
            # Soil Parameters (9)
            'ph': ['ph', 'ph level', 'soil ph', 'acidity', 'alkalinity'],
            'nitrogen': ['nitrogen', 'n', 'n%', 'n_%', 'nitrogen%', 'nitrogen_%'],
            'organic_carbon': ['organic carbon', 'organic_carbon', 'carbon', 'c', 'c%', 'c_%', 'organic_carbon_%'],
            'total_phosphorus': ['total phosphorus', 'total p', 'total_p', 'total phosphorus mg/kg', 'total_p_mg_kg'],
            'available_phosphorus': ['available phosphorus', 'available p', 'available_p', 'available phosphorus mg/kg', 'available_p_mg_kg'],
            'exchangeable_potassium': ['exchangeable potassium', 'exch k', 'exch_k', 'exchangeable k', 'exchangeable_k', 'k meq%', 'k_meq%', 'exchangeable_k_meq%'],
            'exchangeable_calcium': ['exchangeable calcium', 'exch ca', 'exch_ca', 'exchangeable ca', 'exchangeable_ca', 'ca meq%', 'ca_meq%', 'exchangeable_ca_meq%'],
            'exchangeable_magnesium': ['exchangeable magnesium', 'exch mg', 'exch_mg', 'exchangeable mg', 'exchangeable_mg', 'mg meq%', 'mg_meq%', 'exchangeable_mg_meq%'],
            'cec': ['cec', 'cation exchange capacity', 'c.e.c', 'cec meq%', 'cec_meq%'],
            
            # Leaf Parameters (8)
            'leaf_nitrogen': ['leaf nitrogen', 'leaf n', 'leaf_n', 'n%', 'n_%', 'nitrogen%', 'nitrogen_%'],
            'leaf_phosphorus': ['leaf phosphorus', 'leaf p', 'leaf_p', 'p%', 'p_%', 'phosphorus%', 'phosphorus_%'],
            'leaf_potassium': ['leaf potassium', 'leaf k', 'leaf_k', 'k%', 'k_%', 'potassium%', 'potassium_%'],
            'leaf_magnesium': ['leaf magnesium', 'leaf mg', 'leaf_mg', 'mg%', 'mg_%', 'magnesium%', 'magnesium_%'],
            'leaf_calcium': ['leaf calcium', 'leaf ca', 'leaf_ca', 'ca%', 'ca_%', 'calcium%', 'calcium_%'],
            'leaf_boron': ['leaf boron', 'leaf b', 'leaf_b', 'b mg/kg', 'b_mg_kg', 'boron mg/kg', 'boron_mg_kg'],
            'leaf_copper': ['leaf copper', 'leaf cu', 'leaf_cu', 'cu mg/kg', 'cu_mg_kg', 'copper mg/kg', 'copper_mg_kg'],
            'leaf_zinc': ['leaf zinc', 'leaf zn', 'leaf_zn', 'zn mg/kg', 'zn_mg_kg', 'zinc mg/kg', 'zinc_mg_kg'],
            
            # Land & Yield Parameters
            'land_size': ['land size', 'land_size', 'farm size', 'farm_size', 'area', 'hectares', 'acres', 'square meters', 'square_meters'],
            'current_yield': ['current yield', 'current_yield', 'yield', 'production', 'tonnes/hectare', 'kg/hectare', 'tonnes/acre', 'kg/acre', 'yield per hectare', 'yield per acre'],
            'yield_forecast': ['yield forecast', 'yield_forecast', 'projected yield', 'projected_yield', 'future yield', 'future_yield', 'yield projection', 'yield_projection'],
            'economic_impact': ['economic impact', 'economic_impact', 'roi', 'return on investment', 'cost benefit', 'cost_benefit', 'profitability', 'revenue', 'income'],
            
            # Legacy mappings for backward compatibility
            'phosphorus': ['phosphorus', 'p', 'p%', 'p_%', 'phosphorus%', 'available p'],
            'potassium': ['potassium', 'k', 'k%', 'k_%', 'potassium%'],
            'calcium': ['calcium', 'ca', 'ca%', 'ca_%', 'calcium%'],
            'magnesium': ['magnesium', 'mg', 'mg%', 'mg_%', 'magnesium%'],
            'copper': ['copper', 'cu', 'cu mg/kg', 'cu_mg/kg', 'copper mg/kg'],
            'zinc': ['zinc', 'zn', 'zn mg/kg', 'zn_mg/kg', 'zinc mg/kg'],
            'boron': ['boron', 'b', 'b mg/kg', 'b_mg/kg', 'boron mg/kg']
        }
        
        def extract_parameter(text):
            """Extract the primary parameter from text"""
            text_lower = text.lower()
            for param, variations in param_mapping.items():
                if any(var in text_lower for var in variations):
                    return param
            return 'other'
        
        def extract_values(text):
            """Extract all numerical values from text"""
            return re.findall(r'\d+\.?\d*%?', text)
        
        def extract_severity_keywords(text):
            """Extract severity and impact keywords"""
            severity_words = ['critical', 'severe', 'high', 'low', 'deficiency', 'excess', 'optimum', 'below', 'above']
            return [word for word in severity_words if word in text.lower()]
        
        # Group findings by parameter
        parameter_groups = {}
        for finding_data in findings_list:
            finding = finding_data['finding']
            param = extract_parameter(finding)
            
            if param not in parameter_groups:
                parameter_groups[param] = []
            parameter_groups[param].append(finding_data)
        
        # Merge findings within each parameter group
        merged_findings = []
        for param, group_findings in parameter_groups.items():
            if len(group_findings) == 1:
                # Single finding, keep as is
                merged_findings.append(group_findings[0])
            else:
                # Multiple findings about same parameter, merge them
                merged_finding = self._merge_parameter_group_findings_pdf(param, group_findings)
                if merged_finding:
                    merged_findings.append(merged_finding)
        
        return merged_findings
    
    def _merge_parameter_group_findings_pdf(self, param, group_findings):
        """Merge all findings in a parameter group into one comprehensive finding"""
        import re
        
        # Extract all values and severity keywords from all findings in the group
        all_values = []
        all_severity = []
        all_sources = []
        
        for finding_data in group_findings:
            finding = finding_data['finding']
            source = finding_data['source']
            
            # Extract values
            values = re.findall(r'\d+\.?\d*%?', finding)
            all_values.extend(values)
            
            # Extract severity keywords
            severity_words = ['critical', 'severe', 'high', 'low', 'deficiency', 'excess', 'optimum', 'below', 'above']
            severity = [word for word in severity_words if word in finding.lower()]
            all_severity.extend(severity)
            
            all_sources.append(source)
        
        # Remove duplicates
        unique_values = list(set(all_values))
        unique_severity = list(set(all_severity))
        unique_sources = list(set(all_sources))
        
        # Determine parameter name
        param_name = param.upper() if param != 'ph' else 'pH'
        
        # Determine severity level
        if 'critical' in unique_severity or 'severe' in unique_severity:
            severity_desc = "critical"
        elif 'high' in unique_severity:
            severity_desc = "significant"
        elif 'low' in unique_severity:
            severity_desc = "moderate"
        else:
            severity_desc = "notable"
        
        # Build comprehensive finding
        if param == 'ph':
            comprehensive_finding = f"Soil {param_name} shows {severity_desc} issues with values of {', '.join(unique_values)}. "
        else:
            comprehensive_finding = f"{param_name} levels show {severity_desc} issues with values of {', '.join(unique_values)}. "
        
        # Add context
        context_parts = []
        if 'deficiency' in unique_severity:
            context_parts.append("deficiency")
        if 'excess' in unique_severity:
            context_parts.append("excess")
        if 'below' in unique_severity:
            context_parts.append("below optimal levels")
        if 'above' in unique_severity:
            context_parts.append("above optimal levels")
        
        if context_parts:
            comprehensive_finding += f"This indicates {', '.join(context_parts)}. "
        
        # Add impact information
        if 'critical' in unique_severity or 'severe' in unique_severity:
            comprehensive_finding += "This directly impacts crop yield and requires immediate attention."
        elif 'high' in unique_severity:
            comprehensive_finding += "This significantly affects plant health and productivity."
        else:
            comprehensive_finding += "This affects overall plant performance and should be addressed."
        
        return {
            'finding': comprehensive_finding,
            'source': ', '.join(unique_sources)
        }
    
    def _create_enhanced_key_findings(self, analysis_data: Dict[str, Any]) -> List:
        """Create enhanced key findings section with intelligent extraction and deduplication"""
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
        
        # Generate intelligent key findings with proper deduplication using the same logic as results page
        from modules.history import _generate_intelligent_key_findings
        all_key_findings = _generate_intelligent_key_findings(analysis_results, step_results)
        
        if all_key_findings:
            # Display key findings - exact same format as results page
            for i, finding_data in enumerate(all_key_findings, 1):
                finding = finding_data['finding']
                
                # Create finding paragraph with proper formatting - exact same as results page
                finding_text = f"<b>Key Finding {i}:</b> {finding}"
                story.append(Paragraph(finding_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("📋 No key findings available from the analysis results.", self.styles['CustomBody']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _generate_intelligent_key_findings_pdf_OLD(self, analysis_results, step_results):
        """Generate comprehensive intelligent key findings grouped by parameter with proper deduplication - PDF version"""
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
        
        # 2. Extract comprehensive key findings from step-by-step analysis
        if step_results:
            step_findings = []
            
            for step in step_results:
                step_number = step.get('step_number', 0)
                step_title = step.get('step_title', f"Step {step_number}")
                
                # Extract findings from multiple step sources
                step_sources = []
                
                # Direct key_findings field
                if 'key_findings' in step and step['key_findings']:
                    step_sources.append(('key_findings', step['key_findings']))
                
                # Summary field
                if 'summary' in step and step['summary']:
                    step_sources.append(('summary', step['summary']))
                
                # Detailed analysis field
                if 'detailed_analysis' in step and step['detailed_analysis']:
                    step_sources.append(('detailed_analysis', step['detailed_analysis']))
                
                # Issues identified
                if 'issues_identified' in step and step['issues_identified']:
                    step_sources.append(('issues_identified', step['issues_identified']))
                
                # Recommendations
                if 'recommendations' in step and step['recommendations']:
                    step_sources.append(('recommendations', step['recommendations']))
                
                # Process each source
                for source_type, source_data in step_sources:
                    findings_list = []
                    
                    # Handle different data formats
                    if isinstance(source_data, list):
                        findings_list = source_data
                    elif isinstance(source_data, str):
                        # Split by common delimiters and clean
                        lines = source_data.split('\n')
                        findings_list = [line.strip() for line in lines if line.strip()]
                    else:
                        continue
                    
                    # Extract key findings from each item
                    for finding in findings_list:
                        if isinstance(finding, str) and finding.strip():
                            # Enhanced keyword filtering for better relevance
                            finding_lower = finding.lower()
                            relevant_keywords = [
                                'deficiency', 'critical', 'severe', 'low', 'high', 'optimum', 'ph', 'nutrient', 'yield',
                                'recommendation', 'finding', 'issue', 'problem', 'analysis', 'result', 'conclusion',
                                'soil', 'leaf', 'land', 'hectares', 'acres', 'tonnes', 'production', 'economic',
                                'roi', 'investment', 'cost', 'benefit', 'profitability', 'forecast', 'projection',
                                'improvement', 'increase', 'decrease', 'balance', 'ratio', 'level', 'status',
                                'nitrogen', 'phosphorus', 'potassium', 'calcium', 'magnesium', 'carbon', 'cec',
                                'boron', 'zinc', 'copper', 'manganese', 'iron', 'sulfur', 'chlorine'
                            ]
                            
                            # Check if finding contains relevant keywords
                            if any(keyword in finding_lower for keyword in relevant_keywords):
                                cleaned_finding = self._clean_finding_text_pdf(finding.strip())
                                if cleaned_finding and len(cleaned_finding) > 20:  # Minimum length filter
                                    step_findings.append({
                                        'finding': cleaned_finding,
                                        'source': f"{step_title} ({source_type.replace('_', ' ').title()})"
                                    })
            
            # Apply intelligent deduplication to step findings
            if step_findings:
                # First group findings by parameter and merge within each group
                parameter_merged_findings = self._group_and_merge_findings_by_parameter_pdf(step_findings)
                
                # Then apply additional deduplication for any remaining similar findings
                unique_findings = []
                seen_concepts = []
                
                for finding_data in parameter_merged_findings:
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
                            
                            # More aggressive deduplication - consolidate similar issues
                            if similarity > 0.5 or word_similarity > 0.6:
                                # Merge findings for the same issue
                                existing_finding = unique_findings[i]['finding']
                                merged_finding = self._merge_similar_findings(existing_finding, finding)
                                unique_findings[i]['finding'] = merged_finding
                                is_duplicate = True
                                break
                            
                            # Check for same issue with stricter criteria
                            if similarity > 0.3 and word_similarity > 0.4:
                                if self._is_same_issue_pdf(finding, unique_findings[i]['finding']):
                                    # Merge findings for the same issue
                                    existing_finding = unique_findings[i]['finding']
                                    merged_finding = self._merge_similar_findings(existing_finding, finding)
                                    unique_findings[i]['finding'] = merged_finding
                                    is_duplicate = True
                                    break
                    
                    if not is_duplicate:
                        unique_findings.append(finding_data)
                        seen_concepts.append(key_concepts)
                
                # Combine step findings with existing findings
                all_key_findings.extend(unique_findings)
        
        # Note: Comprehensive parameter-specific key findings are now handled by the history module function
        
        # 4. Extract key findings from other analysis sources
        # Land and yield data
        land_yield_data = analysis_results.get('land_yield_data', {})
        if land_yield_data:
            land_size = land_yield_data.get('land_size', 0)
            current_yield = land_yield_data.get('current_yield', 0)
            land_unit = land_yield_data.get('land_unit', 'hectares')
            yield_unit = land_yield_data.get('yield_unit', 'tonnes/hectare')
            
            if land_size > 0:
                all_key_findings.append({
                    'finding': f"Farm analysis covers {land_size} {land_unit} of agricultural land with current production of {current_yield} {yield_unit}.",
                    'source': 'Land & Yield Data'
                })
        
        # Economic forecast
        economic_forecast = analysis_results.get('economic_forecast', {})
        if economic_forecast:
            scenarios = economic_forecast.get('scenarios', {})
            if scenarios:
                best_roi = 0
                best_scenario = ""
                for level, data in scenarios.items():
                    if isinstance(data, dict) and data.get('roi_percentage', 0) > best_roi:
                        best_roi = data.get('roi_percentage', 0)
                        best_scenario = level
                
                if best_roi > 0:
                    all_key_findings.append({
                        'finding': f"Economic analysis shows {best_scenario} investment level offers the best ROI of {best_roi:.1f}% with {scenarios[best_scenario].get('payback_months', 0):.1f} months payback period.",
                        'source': 'Economic Forecast'
                    })
        
        # Yield forecast
        yield_forecast = analysis_results.get('yield_forecast', {})
        if yield_forecast:
            projected_yield = yield_forecast.get('projected_yield', 0)
            current_yield = yield_forecast.get('current_yield', 0)
            if projected_yield > 0 and current_yield > 0:
                increase = ((projected_yield - current_yield) / current_yield) * 100
                all_key_findings.append({
                    'finding': f"Yield projection indicates potential increase from {current_yield} to {projected_yield} tonnes/hectare ({increase:.1f}% improvement) with proper management.",
                    'source': 'Yield Forecast'
                })
        
        # Apply final parameter-based grouping to all findings
        if all_key_findings:
            all_key_findings = self._group_and_merge_findings_by_parameter_pdf(all_key_findings)
            
        return all_key_findings
    
    def _generate_comprehensive_parameter_findings_pdf(self, analysis_results, step_results):
        """Generate comprehensive key findings grouped by specific parameters - PDF version"""
        findings = []
        
        # Get raw data for analysis
        raw_data = analysis_results.get('raw_data', {})
        soil_params = raw_data.get('soil_parameters', {}).get('parameter_statistics', {})
        leaf_params = raw_data.get('leaf_parameters', {}).get('parameter_statistics', {})
        
        # Get MPOB standards for comparison
        try:
            from utils.mpob_standards import get_mpob_standards
            mpob = get_mpob_standards()
        except:
            mpob = None
        
        # 1. Soil pH Analysis
        if 'pH' in soil_params and mpob:
            ph_value = soil_params['pH'].get('average', 0)
            ph_optimal = mpob.get('soil', {}).get('ph', {}).get('optimal', 6.5)
            
            if ph_value > 0:
                if ph_value < 5.5:
                    findings.append({
                        'finding': f"Soil pH is critically low at {ph_value:.1f}, significantly below optimal range of 5.5-7.0. This acidic condition severely limits nutrient availability and root development.",
                        'source': 'Soil Analysis - pH'
                    })
                elif ph_value > 7.5:
                    findings.append({
                        'finding': f"Soil pH is high at {ph_value:.1f}, above optimal range of 5.5-7.0. This alkaline condition reduces availability of essential micronutrients like iron and zinc.",
                        'source': 'Soil Analysis - pH'
                    })
                else:
                    findings.append({
                        'finding': f"Soil pH is within optimal range at {ph_value:.1f}, providing good conditions for nutrient availability and root development.",
                        'source': 'Soil Analysis - pH'
                    })
        
        # 2. Soil Nitrogen Analysis
        if 'Nitrogen_%' in soil_params and mpob:
            n_value = soil_params['Nitrogen_%'].get('average', 0)
            n_optimal = mpob.get('soil', {}).get('nitrogen', {}).get('optimal', 0.2)
            
            if n_value > 0:
                if n_value < n_optimal * 0.7:
                    findings.append({
                        'finding': f"Soil nitrogen is critically deficient at {n_value:.2f}%, well below optimal level of {n_optimal:.2f}%. This severely limits plant growth and leaf development.",
                        'source': 'Soil Analysis - Nitrogen'
                    })
                elif n_value > n_optimal * 1.3:
                    findings.append({
                        'finding': f"Soil nitrogen is excessive at {n_value:.2f}%, above optimal level of {n_optimal:.2f}%. This may cause nutrient imbalances and environmental concerns.",
                        'source': 'Soil Analysis - Nitrogen'
                    })
                else:
                    findings.append({
                        'finding': f"Soil nitrogen is adequate at {n_value:.2f}%, within optimal range for healthy plant growth.",
                        'source': 'Soil Analysis - Nitrogen'
                    })
        
        # 3. Soil Phosphorus Analysis
        if 'Available_P_mg_kg' in soil_params and mpob:
            p_value = soil_params['Available_P_mg_kg'].get('average', 0)
            p_optimal = mpob.get('soil', {}).get('available_phosphorus', {}).get('optimal', 15)
            
            if p_value > 0:
                if p_value < p_optimal * 0.5:
                    findings.append({
                        'finding': f"Available phosphorus is critically low at {p_value:.1f} mg/kg, severely below optimal level of {p_optimal} mg/kg. This limits root development and energy transfer.",
                        'source': 'Soil Analysis - Phosphorus'
                    })
                elif p_value > p_optimal * 2:
                    findings.append({
                        'finding': f"Available phosphorus is excessive at {p_value:.1f} mg/kg, well above optimal level of {p_optimal} mg/kg. This may cause nutrient lockup and environmental issues.",
                        'source': 'Soil Analysis - Phosphorus'
                    })
                else:
                    findings.append({
                        'finding': f"Available phosphorus is adequate at {p_value:.1f} mg/kg, within optimal range for proper plant development.",
                        'source': 'Soil Analysis - Phosphorus'
                    })
        
        # 4. Soil Potassium Analysis
        if 'Exchangeable_K_meq%' in soil_params and mpob:
            k_value = soil_params['Exchangeable_K_meq%'].get('average', 0)
            k_optimal = mpob.get('soil', {}).get('exchangeable_potassium', {}).get('optimal', 0.3)
            
            if k_value > 0:
                if k_value < k_optimal * 0.6:
                    findings.append({
                        'finding': f"Exchangeable potassium is deficient at {k_value:.2f} meq%, below optimal level of {k_optimal:.2f} meq%. This affects water regulation and disease resistance.",
                        'source': 'Soil Analysis - Potassium'
                    })
                elif k_value > k_optimal * 1.5:
                    findings.append({
                        'finding': f"Exchangeable potassium is high at {k_value:.2f} meq%, above optimal level of {k_optimal:.2f} meq%. This may cause nutrient imbalances.",
                        'source': 'Soil Analysis - Potassium'
                    })
                else:
                    findings.append({
                        'finding': f"Exchangeable potassium is adequate at {k_value:.2f} meq%, within optimal range for healthy plant function.",
                        'source': 'Soil Analysis - Potassium'
                    })
        
        # 5. Leaf Nutrient Analysis
        if leaf_params:
            # Leaf Nitrogen
            if 'N_%' in leaf_params:
                leaf_n = leaf_params['N_%'].get('average', 0)
                if leaf_n > 0:
                    if leaf_n < 2.5:
                        findings.append({
                            'finding': f"Leaf nitrogen is deficient at {leaf_n:.1f}%, below optimal range of 2.5-3.5%. This indicates poor nitrogen uptake and affects photosynthesis.",
                            'source': 'Leaf Analysis - Nitrogen'
                        })
                    elif leaf_n > 3.5:
                        findings.append({
                            'finding': f"Leaf nitrogen is excessive at {leaf_n:.1f}%, above optimal range of 2.5-3.5%. This may cause nutrient imbalances and delayed maturity.",
                            'source': 'Leaf Analysis - Nitrogen'
                        })
                    else:
                        findings.append({
                            'finding': f"Leaf nitrogen is optimal at {leaf_n:.1f}%, within recommended range for healthy palm growth.",
                            'source': 'Leaf Analysis - Nitrogen'
                        })
            
            # Leaf Phosphorus
            if 'P_%' in leaf_params:
                leaf_p = leaf_params['P_%'].get('average', 0)
                if leaf_p > 0:
                    if leaf_p < 0.15:
                        findings.append({
                            'finding': f"Leaf phosphorus is deficient at {leaf_p:.2f}%, below optimal range of 0.15-0.25%. This limits energy transfer and root development.",
                            'source': 'Leaf Analysis - Phosphorus'
                        })
                    elif leaf_p > 0.25:
                        findings.append({
                            'finding': f"Leaf phosphorus is high at {leaf_p:.2f}%, above optimal range of 0.15-0.25%. This may indicate over-fertilization.",
                            'source': 'Leaf Analysis - Phosphorus'
                        })
                    else:
                        findings.append({
                            'finding': f"Leaf phosphorus is adequate at {leaf_p:.2f}%, within optimal range for proper plant function.",
                            'source': 'Leaf Analysis - Phosphorus'
                        })
            
            # Leaf Potassium
            if 'K_%' in leaf_params:
                leaf_k = leaf_params['K_%'].get('average', 0)
                if leaf_k > 0:
                    if leaf_k < 1.0:
                        findings.append({
                            'finding': f"Leaf potassium is deficient at {leaf_k:.1f}%, below optimal range of 1.0-1.5%. This affects water regulation and disease resistance.",
                            'source': 'Leaf Analysis - Potassium'
                        })
                    elif leaf_k > 1.5:
                        findings.append({
                            'finding': f"Leaf potassium is high at {leaf_k:.1f}%, above optimal range of 1.0-1.5%. This may cause nutrient imbalances.",
                            'source': 'Leaf Analysis - Potassium'
                        })
                    else:
                        findings.append({
                            'finding': f"Leaf potassium is optimal at {leaf_k:.1f}%, within recommended range for healthy palm growth.",
                            'source': 'Leaf Analysis - Potassium'
                        })
            
            # Leaf Magnesium
            if 'Mg_%' in leaf_params:
                leaf_mg = leaf_params['Mg_%'].get('average', 0)
                if leaf_mg > 0:
                    if leaf_mg < 0.2:
                        findings.append({
                            'finding': f"Leaf magnesium is deficient at {leaf_mg:.2f}%, below optimal range of 0.2-0.3%. This affects chlorophyll production and photosynthesis.",
                            'source': 'Leaf Analysis - Magnesium'
                        })
                    elif leaf_mg > 0.3:
                        findings.append({
                            'finding': f"Leaf magnesium is high at {leaf_mg:.2f}%, above optimal range of 0.2-0.3%. This may indicate over-fertilization.",
                            'source': 'Leaf Analysis - Magnesium'
                        })
                    else:
                        findings.append({
                            'finding': f"Leaf magnesium is adequate at {leaf_mg:.2f}%, within optimal range for healthy palm growth.",
                            'source': 'Leaf Analysis - Magnesium'
                        })
            
            # Leaf Calcium
            if 'Ca_%' in leaf_params:
                leaf_ca = leaf_params['Ca_%'].get('average', 0)
                if leaf_ca > 0:
                    if leaf_ca < 0.5:
                        findings.append({
                            'finding': f"Leaf calcium is deficient at {leaf_ca:.1f}%, below optimal range of 0.5-1.0%. This affects cell wall strength and fruit quality.",
                            'source': 'Leaf Analysis - Calcium'
                        })
                    elif leaf_ca > 1.0:
                        findings.append({
                            'finding': f"Leaf calcium is high at {leaf_ca:.1f}%, above optimal range of 0.5-1.0%. This may cause nutrient imbalances.",
                            'source': 'Leaf Analysis - Calcium'
                        })
                    else:
                        findings.append({
                            'finding': f"Leaf calcium is optimal at {leaf_ca:.1f}%, within recommended range for healthy palm growth.",
                            'source': 'Leaf Analysis - Calcium'
                        })
            
            # Leaf Boron
            if 'B_mg_kg' in leaf_params:
                leaf_b = leaf_params['B_mg_kg'].get('average', 0)
                if leaf_b > 0:
                    if leaf_b < 10:
                        findings.append({
                            'finding': f"Leaf boron is deficient at {leaf_b:.1f} mg/kg, below optimal range of 10-20 mg/kg. This affects fruit development and pollen viability.",
                            'source': 'Leaf Analysis - Boron'
                        })
                    elif leaf_b > 20:
                        findings.append({
                            'finding': f"Leaf boron is high at {leaf_b:.1f} mg/kg, above optimal range of 10-20 mg/kg. This may cause toxicity symptoms.",
                            'source': 'Leaf Analysis - Boron'
                        })
                    else:
                        findings.append({
                            'finding': f"Leaf boron is adequate at {leaf_b:.1f} mg/kg, within optimal range for healthy palm growth.",
                            'source': 'Leaf Analysis - Boron'
                        })
        
        return findings
    
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
            
            # Check if step instructions contain visual keywords
            step_instructions = step.get('instructions', '') + ' ' + step.get('summary', '') + ' ' + step.get('detailed_analysis', '')
            has_visual_keywords = any(keyword in step_instructions.lower() for keyword in [
                'visual', 'visualization', 'chart', 'graph', 'plot', 'diagram', 'comparison', 
                'compare', 'visual comparison', 'visualize', 'display', 'show', 'illustrate'
            ])
            
            # Summary (most important content)
            if 'summary' in step and step['summary']:
                story.append(Paragraph("Summary:", self.styles['Heading3']))
                story.append(Paragraph(step['summary'], self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Detailed Analysis (most relevant content)
            if 'detailed_analysis' in step and step['detailed_analysis']:
                story.append(Paragraph("Detailed Analysis:", self.styles['Heading3']))
                # Include full detailed analysis without truncation
                detailed_text = step['detailed_analysis']
                story.append(Paragraph(detailed_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Detailed Data Tables (from enhanced LLM output) - SKIP FOR STEP 1
            if 'tables' in step and step['tables'] and step_number != 1:
                story.append(Paragraph("Data Tables:", self.styles['Heading3']))
                for table in step['tables']:
                    if isinstance(table, dict) and 'title' in table and 'headers' in table and 'rows' in table:
                        story.append(Paragraph(f"<b>{table['title']}</b>", self.styles['CustomBody']))
                        # Create table
                        table_data = [table['headers']] + table['rows']
                        pdf_table = self._create_table_with_proper_layout(table_data, font_size=10)
                        pdf_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        story.append(pdf_table)
                        story.append(Spacer(1, 8))
                story.append(Spacer(1, 8))
            
            # Detailed Interpretations (from enhanced LLM output)
            if 'interpretations' in step and step['interpretations']:
                story.append(Paragraph("Detailed Interpretations:", self.styles['Heading3']))
                for i, interpretation in enumerate(step['interpretations'], 1):
                    story.append(Paragraph(f"<b>Interpretation {i}:</b>", self.styles['CustomBody']))
                    story.append(Paragraph(interpretation, self.styles['CustomBody']))
                    story.append(Spacer(1, 6))
                story.append(Spacer(1, 8))
            
            # Statistical Analysis (from enhanced LLM output)
            if 'statistical_analysis' in step and step['statistical_analysis']:
                story.append(Paragraph("Statistical Analysis:", self.styles['Heading3']))
                if isinstance(step['statistical_analysis'], dict):
                    for key, value in step['statistical_analysis'].items():
                        story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", self.styles['CustomBody']))
                else:
                    story.append(Paragraph(str(step['statistical_analysis']), self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Issues Identified (crucial for farmers)
            if 'issues_identified' in step and step['issues_identified']:
                story.append(Paragraph("Issues Identified:", self.styles['Heading3']))
                for i, issue in enumerate(step['issues_identified'], 1):
                    issue_text = f"<b>{i}.</b> {issue}"
                    story.append(Paragraph(issue_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Key Findings (from enhanced LLM output)
            if 'key_findings' in step and step['key_findings']:
                story.append(Paragraph("Key Findings:", self.styles['Heading3']))
                for i, finding in enumerate(step['key_findings'], 1):
                    finding_text = f"<b>{i}.</b> {finding}"
                    story.append(Paragraph(finding_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Specific Recommendations (from enhanced LLM output)
            if 'specific_recommendations' in step and step['specific_recommendations']:
                story.append(Paragraph("Specific Recommendations:", self.styles['Heading3']))
                for i, rec in enumerate(step['specific_recommendations'], 1):
                    rec_text = f"<b>{i}.</b> {rec}"
                    story.append(Paragraph(rec_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Legacy recommendations (for backward compatibility)
            if 'recommendations' in step and step['recommendations']:
                story.append(Paragraph("Additional Recommendations:", self.styles['Heading3']))
                for i, rec in enumerate(step['recommendations'], 1):
                    rec_text = f"<b>{i}.</b> {rec}"
                    story.append(Paragraph(rec_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
            
            # Step-specific tables and content
            if step_number == 1:
                # Step 1: Data Analysis - Add ONLY bar graphs (no data tables)
                # Add Step 1 visualizations (bar graphs)
                story.extend(self._create_step1_bar_graphs(analysis_data))
            elif step_number == 2:
                # Step 2: Issue Diagnosis - Add diagnostic tables
                story.extend(self._create_step2_diagnostic_tables(step))
            elif step_number == 3:
                # Step 3: Omit Solution Recommendations/Economic tables in PDF per requirements
                pass
            elif step_number == 4:
                # Step 4: Regenerative Agriculture - Add regenerative strategy tables
                story.extend(self._create_step4_regenerative_tables(step))
            elif step_number == 5:
                # Step 5: Economic Impact - Add comprehensive economic tables only
                story.extend(self._create_step5_economic_tables(step))
                # Add economic forecast tables only (no yield forecast graph)
                story.extend(self._create_enhanced_economic_forecast_table(analysis_data))
            elif step_number == 6:
                # Step 6: Yield Forecast - Add forecast graph only (no tables)
                story.extend(self._create_enhanced_yield_forecast_graph(analysis_data))
            
            # Visualizations and Charts - omit for Step 3 per requirements
            if step_number != 3 and 'visualizations' in step and step['visualizations']:
                story.append(Paragraph("Visualizations:", self.styles['Heading3']))
                for viz in step['visualizations']:
                    if isinstance(viz, dict) and 'type' in viz:
                        story.append(Paragraph(f"<b>{viz.get('title', 'Chart')}</b>", self.styles['CustomBody']))
                        # Add chart description if available
                        if 'description' in viz:
                            story.append(Paragraph(viz['description'], self.styles['CustomBody']))
                        story.append(Spacer(1, 6))
                story.append(Spacer(1, 8))
            
            # Generate contextual visualizations for all steps
            # Omit visualizations for Step 3 entirely
            if step_number != 3:
                story.extend(self._create_step_visualizations(step, step_number))
                story.extend(self._create_contextual_visualizations(step, step_number, analysis_data))
            
            story.append(Spacer(1, 15))
        
        return story
    
    def _create_step_visualizations(self, step: Dict[str, Any], step_number: int) -> List:
        """Create visualizations for each step with enhanced contextual support"""
        story = []
        
        # Check for charts and visualizations in the step data
        if 'charts' in step and step['charts']:
            story.append(Paragraph("Visualizations:", self.styles['Heading3']))
            
            for chart_data in step['charts']:
                try:
                    # Create chart using enhanced matplotlib
                    chart_image = self._create_enhanced_chart_image(chart_data)
                    if chart_image:
                        # Create a BytesIO object from the image bytes
                        img_buffer = io.BytesIO(chart_image)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
                except Exception as e:
                    logger.warning(f"Could not create chart: {str(e)}")
                    continue
        
        # Generate contextual visualizations based on step content
        contextual_viz = self._generate_contextual_visualizations_pdf(step, step_number)
        if contextual_viz:
            for viz_data in contextual_viz:
                try:
                    chart_image = self._create_enhanced_chart_image(viz_data)
                    if chart_image:
                        img_buffer = io.BytesIO(chart_image)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
                except Exception as e:
                    logger.warning(f"Could not create contextual chart: {str(e)}")
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
    
    def _generate_contextual_visualizations_pdf(self, step: Dict[str, Any], step_number: int) -> List[Dict[str, Any]]:
        """Generate contextual visualizations for PDF based on step content"""
        try:
            visualizations = []
            
            # Get step content to check for specific visualization requests
            step_instructions = step.get('instructions', '')
            step_summary = step.get('summary', '')
            step_analysis = step.get('detailed_analysis', '')
            combined_text = f"{step_instructions} {step_summary} {step_analysis}".lower()
            
            # Generate visualizations based on step number and content
            if step_number == 1:  # Data Analysis
                # Note: Yield projection chart removed from contextual visualizations
                # as it's now handled in the dedicated forecast graph section
                pass
            
            elif step_number == 2:  # Issue Diagnosis
                # Charts removed as requested
                pass
            
            elif step_number == 3:  # Solution Recommendations
                # Create solution priority chart
                solution_viz = self._create_solution_priority_viz_pdf(step)
                if solution_viz:
                    visualizations.append(solution_viz)
                
                # Create cost-benefit analysis chart
                cost_benefit_viz = self._create_cost_benefit_viz_pdf(step)
                if cost_benefit_viz:
                    visualizations.append(cost_benefit_viz)
            
            return visualizations
            
        except Exception as e:
            logger.warning(f"Error generating contextual visualizations: {str(e)}")
            return []
    
    
    def _create_yield_projection_viz_pdf(self, yield_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create yield projection visualization for PDF"""
        try:
            years = [1, 2, 3, 4, 5]
            current_yield = yield_data.get('current_yield', 15)
            projected_yield = yield_data.get('projected_yield', 25)
            
            # Create multiple investment scenarios
            scenarios = {
                'High Investment': [],
                'Medium Investment': [],
                'Low Investment': [],
                'Current (No Change)': []
            }
            
            # Calculate yield progression for each scenario
            for year in years:
                # High investment: reaches projected yield by year 3
                high_yield = current_yield + (projected_yield - current_yield) * min(year / 3, 1)
                scenarios['High Investment'].append(high_yield)
                
                # Medium investment: reaches 80% of projected yield by year 4
                medium_yield = current_yield + (projected_yield - current_yield) * 0.8 * min(year / 4, 1)
                scenarios['Medium Investment'].append(medium_yield)
                
                # Low investment: reaches 60% of projected yield by year 5
                low_yield = current_yield + (projected_yield - current_yield) * 0.6 * min(year / 5, 1)
                scenarios['Low Investment'].append(low_yield)
                
                # Current (no change): stays at current yield
                scenarios['Current (No Change)'].append(current_yield)
            
            # Create series data for line chart
            series = []
            colors = ['#28a745', '#17a2b8', '#ffc107', '#6c757d']
            
            for i, (scenario_name, values) in enumerate(scenarios.items()):
                series.append({
                    'name': scenario_name,
                    'data': values,
                    'color': colors[i]
                })
            
            return {
                'type': 'line_chart',
                'title': '5-Year Yield Forecast by Investment Scenario',
                'subtitle': 'Projected yield increase over 5 years with different investment levels',
                'data': {
                    'categories': [f'Year {year}' for year in years],
                    'series': series
                },
                'options': {
                    'x_axis_title': 'Years',
                    'y_axis_title': 'Yield (tons/hectare)',
                    'show_legend': True,
                    'show_grid': True,
                    'markers': True
                }
            }
        except Exception as e:
            logger.warning(f"Error creating yield projection visualization: {str(e)}")
            return None
    
    
    
    def _create_solution_priority_viz_pdf(self, step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create solution priority visualization for PDF"""
        try:
            return {
                'type': 'bar_chart',
                'title': '🎯 Solution Priority Distribution',
                'subtitle': 'Breakdown of recommendations by priority level',
                'data': {
                    'categories': ['High', 'Medium', 'Low'],
                    'values': [4, 6, 2]
                },
                'options': {
                    'show_legend': True,
                    'show_values': True,
                    'y_axis_title': 'Number of Recommendations',
                    'x_axis_title': 'Priority Level'
                }
            }
        except Exception as e:
            logger.warning(f"Error creating solution priority visualization: {str(e)}")
            return None
    
    def _create_cost_benefit_viz_pdf(self, step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create cost-benefit analysis visualization for PDF"""
        try:
            return {
                'type': 'multi_axis_chart',
                'title': '💰 Cost-Benefit Analysis',
                'subtitle': 'ROI and payback period for different investment levels',
                'data': {
                    'categories': ['Low', 'Medium', 'High'],
                    'series': [
                        {
                            'name': 'ROI (%)',
                            'data': [15, 25, 35],
                            'color': '#2ecc71',
                            'axis': 'left'
                        },
                        {
                            'name': 'Payback (months)',
                            'data': [24, 18, 12],
                            'color': '#e74c3c',
                            'axis': 'right'
                        }
                    ]
                },
                'options': {
                    'show_legend': True,
                    'show_values': True,
                    'left_axis_title': 'ROI (%)',
                    'right_axis_title': 'Payback Period (months)',
                    'x_axis_title': 'Investment Level'
                }
            }
        except Exception as e:
            logger.warning(f"Error creating cost-benefit visualization: {str(e)}")
            return None
    
    def _create_chart_image(self, chart_data: Dict[str, Any]) -> Optional[bytes]:
        """Create chart image from chart data with enhanced support for new visualization types"""
        try:
            import matplotlib.pyplot as plt
            import io
            import numpy as np
            
            # Clear any existing figures to prevent memory issues
            plt.clf()
            plt.close('all')
            
            chart_type = chart_data.get('type', 'bar')
            data = chart_data.get('data', {})
            title = chart_data.get('title', 'Chart')
            options = chart_data.get('options', {})
            
            # Handle different chart types
            if chart_type == 'line_chart':
                return self._create_line_chart_pdf(data, title, options)
            elif chart_type == 'actual_vs_optimal_bar':
                return self._create_actual_vs_optimal_chart_pdf(data, title, options)
            elif chart_type == 'pie_chart':
                return self._create_pie_chart_pdf(data, title, options)
            elif chart_type == 'multi_axis_chart':
                return self._create_multi_axis_chart_pdf(data, title, options)
            elif chart_type == 'heatmap':
                return self._create_heatmap_pdf(data, title, options)
            elif chart_type == 'radar_chart':
                return self._create_radar_chart_pdf(data, title, options)
            else:
                # Default to bar chart
                return self._create_bar_chart_pdf(data, title, options)
            
        except Exception as e:
            logger.warning(f"Error creating chart: {str(e)}")
            return None
    
    def _create_enhanced_chart_image(self, chart_data: Dict[str, Any]) -> Optional[bytes]:
        """Enhanced chart creation with better error handling"""
        return self._create_chart_image(chart_data)
    
    def _create_line_chart_pdf(self, data: Dict[str, Any], title: str, options: Dict[str, Any]) -> Optional[bytes]:
        """Create line chart for PDF"""
        try:
            import matplotlib.pyplot as plt
            import io
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Handle different data formats
            if 'categories' in data and 'series' in data:
                categories = data['categories']
                series = data['series']
                
                colors = ['#2E7D32', '#1976D2', '#F57C00', '#7B1FA2', '#D32F2F']
                
                for i, series_data in enumerate(series):
                    if isinstance(series_data, dict):
                        series_name = series_data.get('name', f'Series {i+1}')
                        series_values = series_data.get('data', [])
                        series_color = series_data.get('color', colors[i % len(colors)])
                        
                        ax.plot(categories, series_values, 
                              marker='o', linewidth=3, markersize=8,
                              label=series_name, color=series_color)
                
                ax.legend()
                ax.set_xlabel(options.get('x_axis_title', 'Categories'))
                ax.set_ylabel(options.get('y_axis_title', 'Values'))
                
            elif 'x_values' in data and 'y_values' in data:
                x_values = data['x_values']
                y_values = data['y_values']
                series_name = data.get('series_name', 'Data')
                
                ax.plot(x_values, y_values, marker='o', linewidth=3, markersize=8,
                       label=series_name, color='#2E7D32')
                ax.legend()
                ax.set_xlabel(options.get('x_axis_title', 'X Axis'))
                ax.set_ylabel(options.get('y_axis_title', 'Y Axis'))
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error creating line chart: {str(e)}")
            return None
    
    def _create_actual_vs_optimal_chart_pdf(self, data: Dict[str, Any], title: str, options: Dict[str, Any]) -> Optional[bytes]:
        """Create actual vs optimal bar chart for PDF with separate charts for each parameter"""
        try:
            import matplotlib.pyplot as plt
            import io
            import numpy as np
            
            categories = data.get('categories', [])
            series = data.get('series', [])
            
            if not categories or not series:
                return None
            
            # Extract actual and optimal values
            actual_values = series[0]['values'] if len(series) > 0 else []
            optimal_values = series[1]['values'] if len(series) > 1 else []
            
            if not actual_values or not optimal_values:
                return None
            
            # Create subplots - one for each parameter
            num_params = len(categories)
            
            # Calculate optimal layout - if more than 4 parameters, use 2 rows
            if num_params > 4:
                rows = 2
                cols = (num_params + 1) // 2
            else:
                rows = 1
                cols = num_params
            
            fig, axes = plt.subplots(rows, cols, figsize=(6*cols, 4*rows))
            
            # If only one parameter, axes won't be a list
            if num_params == 1:
                axes = [axes]
            elif rows == 1:
                axes = axes.flatten() if hasattr(axes, 'flatten') else axes
            else:
                axes = axes.flatten()
            
            # Define colors
            actual_color = series[0].get('color', '#3498db')
            optimal_color = series[1].get('color', '#e74c3c')
            
            # Create chart for each parameter
            for i, param in enumerate(categories):
                actual_val = actual_values[i]
                optimal_val = optimal_values[i]
                
                # Calculate appropriate scale for this parameter
                max_val = max(actual_val, optimal_val)
                min_val = min(actual_val, optimal_val)
                
                # Add some padding to the scale
                range_val = max_val - min_val
                if range_val == 0:
                    range_val = max_val * 0.1 if max_val > 0 else 1
                
                y_max = max_val + (range_val * 0.2)
                y_min = max(0, min_val - (range_val * 0.1))
                
                # Create bars
                x_pos = [0, 1]
                heights = [actual_val, optimal_val]
                colors = [actual_color, optimal_color]
                labels = ['Observed', 'Recommended']
                
                bars = axes[i].bar(x_pos, heights, color=colors, alpha=0.8, width=0.6)
                
                # Add value labels on bars
                for bar, height in zip(bars, heights):
                    axes[i].text(bar.get_x() + bar.get_width()/2., height + (y_max - y_min) * 0.02,
                               f'{height:.1f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
                
                # Customize subplot
                axes[i].set_title(param, fontsize=14, fontweight='bold', pad=15)
                axes[i].set_ylim(y_min, y_max)
                axes[i].set_xticks(x_pos)
                axes[i].set_xticklabels(labels, fontsize=12)
                axes[i].grid(True, alpha=0.3, linestyle='--')
                axes[i].set_ylabel('Values', fontsize=12)
                axes[i].tick_params(axis='both', which='major', labelsize=10)
                
                # Only show legend on first chart
                if i == 0:
                    axes[i].legend(['Observed', 'Recommended'], loc='upper right', fontsize=10)
            
            # Set main title
            fig.suptitle(title, fontsize=14, fontweight='bold', y=0.95)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error creating actual vs optimal chart: {str(e)}")
            return None
    
    def _create_pie_chart_pdf(self, data: Dict[str, Any], title: str, options: Dict[str, Any]) -> Optional[bytes]:
        """Create pie chart for PDF"""
        try:
            import matplotlib.pyplot as plt
            import io
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            categories = data.get('categories', [])
            values = data.get('values', [])
            colors = data.get('colors', ['#2E7D32', '#1976D2', '#F57C00', '#7B1FA2', '#D32F2F'])
            
            if not categories or not values:
                return None
            
            wedges, texts, autotexts = ax.pie(values, labels=categories, colors=colors[:len(categories)],
                                             autopct='%1.1f%%', startangle=90)
            
            # Enhance text appearance
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error creating pie chart: {str(e)}")
            return None
    
    def _create_multi_axis_chart_pdf(self, data: Dict[str, Any], title: str, options: Dict[str, Any]) -> Optional[bytes]:
        """Create multi-axis chart for PDF"""
        try:
            import matplotlib.pyplot as plt
            import io
            import numpy as np
            
            fig, ax1 = plt.subplots(figsize=(12, 8))
            
            categories = data.get('categories', [])
            series = data.get('series', [])
            
            if not categories or not series:
                return None
            
            # Create second y-axis
            ax2 = ax1.twinx()
            
            colors = ['#2E7D32', '#D32F2F']
            
            for i, series_data in enumerate(series):
                series_name = series_data.get('name', f'Series {i+1}')
                series_values = series_data.get('data', [])
                series_color = series_data.get('color', colors[i % len(colors)])
                axis = series_data.get('axis', 'left')
                
                if axis == 'left':
                    ax1.plot(categories, series_values, marker='o', linewidth=3, markersize=8,
                            label=series_name, color=series_color)
            else:
                    ax2.plot(categories, series_values, marker='s', linewidth=3, markersize=8,
                            label=series_name, color=series_color)
            
            ax1.set_xlabel(options.get('x_axis_title', 'Categories'))
            ax1.set_ylabel(options.get('left_axis_title', 'Left Axis'), color='#2E7D32')
            ax2.set_ylabel(options.get('right_axis_title', 'Right Axis'), color='#D32F2F')
            
            ax1.tick_params(axis='y', labelcolor='#2E7D32')
            ax2.tick_params(axis='y', labelcolor='#D32F2F')
            
            ax1.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax1.grid(True, alpha=0.3)
            
            # Combine legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error creating multi-axis chart: {str(e)}")
            return None
    
    def _create_heatmap_pdf(self, data: Dict[str, Any], title: str, options: Dict[str, Any]) -> Optional[bytes]:
        """Create heatmap for PDF"""
        try:
            import matplotlib.pyplot as plt
            import io
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            parameters = data.get('parameters', [])
            levels = data.get('levels', [])
            color_scale = data.get('color_scale', {})
            
            if not parameters or not levels:
                return None
            
            # Create heatmap data
            heatmap_data = []
            for i, param in enumerate(parameters):
                level_value = 0
                if levels[i] == 'Critical':
                    level_value = 0
                elif levels[i] == 'High':
                    level_value = 1
                elif levels[i] == 'Medium':
                    level_value = 2
                elif levels[i] == 'Low':
                    level_value = 3
                
                heatmap_data.append([level_value])
            
            im = ax.imshow(heatmap_data, cmap='RdYlGn', aspect='auto')
            
            # Set ticks and labels
            ax.set_xticks([0])
            ax.set_xticklabels(['Deficiency Level'])
            ax.set_yticks(range(len(parameters)))
            ax.set_yticklabels(parameters)
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_ticks([0, 1, 2, 3])
            cbar.set_ticklabels(['Critical', 'High', 'Medium', 'Low'])
            cbar.set_label('Deficiency Level')
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error creating heatmap: {str(e)}")
            return None
    
    def _create_radar_chart_pdf(self, data: Dict[str, Any], title: str, options: Dict[str, Any]) -> Optional[bytes]:
        """Create radar chart for PDF"""
        try:
            import matplotlib.pyplot as plt
            import io
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            
            categories = data.get('categories', [])
            series = data.get('series', [])
            
            if not categories or not series:
                return None
            
            # Calculate angles for each category
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]  # Complete the circle
            
            colors = ['#2E7D32', '#D32F2F', '#1976D2', '#F57C00']
            
            for i, series_data in enumerate(series):
                series_name = series_data.get('name', f'Series {i+1}')
                series_values = series_data.get('data', [])
                series_color = series_data.get('color', colors[i % len(colors)])
                
                # Complete the circle
                values = series_values + series_values[:1]
                
                ax.plot(angles, values, 'o-', linewidth=3, label=series_name, color=series_color)
                ax.fill(angles, values, alpha=0.25, color=series_color)
            
            # Add category labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
            ax.grid(True)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error creating radar chart: {str(e)}")
            return None
    
    def _create_bar_chart_pdf(self, data: Dict[str, Any], title: str, options: Dict[str, Any]) -> Optional[bytes]:
        """Create bar chart for PDF with separate charts for each parameter"""
        try:
            import matplotlib.pyplot as plt
            import io
            import numpy as np
            
            categories = data.get('categories', [])
            values = data.get('values', [])
            series = data.get('series', [])
            
            if not categories:
                return None
            
            # Check if we have series data (actual vs optimal format)
            if series and len(series) >= 2 and isinstance(series[0], dict) and 'values' in series[0]:
                # Multiple series format - create separate charts for each parameter
                actual_values = series[0]['values'] if len(series) > 0 else []
                optimal_values = series[1]['values'] if len(series) > 1 else []
                
                if actual_values and optimal_values:
                    # Create subplots - one for each parameter
                    num_params = len(categories)
                    
                    # Calculate optimal layout - if more than 4 parameters, use 2 rows
                    if num_params > 4:
                        rows = 2
                        cols = (num_params + 1) // 2
                    else:
                        rows = 1
                        cols = num_params
                    
                    fig, axes = plt.subplots(rows, cols, figsize=(6*cols, 4*rows))
                    
                    # If only one parameter, axes won't be a list
                    if num_params == 1:
                        axes = [axes]
                    elif rows == 1:
                        axes = axes.flatten() if hasattr(axes, 'flatten') else axes
                    else:
                        axes = axes.flatten()
                    
                    # Define colors
                    actual_color = series[0].get('color', '#3498db')
                    optimal_color = series[1].get('color', '#e74c3c')
                    
                    # Create chart for each parameter
                    for i, param in enumerate(categories):
                        actual_val = actual_values[i]
                        optimal_val = optimal_values[i]
                        
                        # Calculate appropriate scale for this parameter
                        max_val = max(actual_val, optimal_val)
                        min_val = min(actual_val, optimal_val)
                        
                        # Add some padding to the scale
                        range_val = max_val - min_val
                        if range_val == 0:
                            range_val = max_val * 0.1 if max_val > 0 else 1
                        
                        y_max = max_val + (range_val * 0.2)
                        y_min = max(0, min_val - (range_val * 0.1))
                        
                        # Create bars
                        x_pos = [0, 1]
                        heights = [actual_val, optimal_val]
                        colors = [actual_color, optimal_color]
                        labels = ['Observed', 'Recommended']
                        
                        bars = axes[i].bar(x_pos, heights, color=colors, alpha=0.8, width=0.6)
            
            # Add value labels on bars
                        for bar, height in zip(bars, heights):
                            axes[i].text(bar.get_x() + bar.get_width()/2., height + (y_max - y_min) * 0.02,
                                       f'{height:.1f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
                        
                        # Customize subplot
                        axes[i].set_title(param, fontsize=14, fontweight='bold', pad=15)
                        axes[i].set_ylim(y_min, y_max)
                        axes[i].set_xticks(x_pos)
                        axes[i].set_xticklabels(labels, fontsize=12)
                        axes[i].grid(True, alpha=0.3, linestyle='--')
                        axes[i].set_ylabel('Values', fontsize=12)
                        axes[i].tick_params(axis='both', which='major', labelsize=10)
                        
                        # Only show legend on first chart
                        if i == 0:
                            axes[i].legend(['Observed', 'Recommended'], loc='upper right', fontsize=10)
                    
                    # Set main title
                    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.95)
            
                    plt.tight_layout()
                    
                    # Save to bytes
                    img_buffer = io.BytesIO()
                    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    plt.close(fig)
                    
                    return img_buffer.getvalue()
            
            elif values:
                # Single values format - create simple bar chart
                if len(values) != len(categories):
                    return None
                
                # Create subplots - one for each parameter
                num_params = len(categories)
                
                # Calculate optimal layout - if more than 4 parameters, use 2 rows
                if num_params > 4:
                    rows = 2
                    cols = (num_params + 1) // 2
                else:
                    rows = 1
                    cols = num_params
                
                fig, axes = plt.subplots(rows, cols, figsize=(6*cols, 4*rows))
                
                # If only one parameter, axes won't be a list
                if num_params == 1:
                    axes = [axes]
                elif rows == 1:
                    axes = axes.flatten() if hasattr(axes, 'flatten') else axes
                else:
                    axes = axes.flatten()
                
                # Create chart for each parameter
                for i, param in enumerate(categories):
                    val = values[i]
                    
                    # Calculate appropriate scale for this parameter
                    y_max = val * 1.2 if val > 0 else 1
                    y_min = 0
                    
                    # Create bar
                    bars = axes[i].bar([0], [val], color='#3498db', alpha=0.8, width=0.6)
                    
                    # Add value label on bar
                    axes[i].text(0, val + (y_max - y_min) * 0.02,
                               f'{val:.1f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
                    
                    # Customize subplot
                    axes[i].set_title(param, fontsize=14, fontweight='bold', pad=15)
                    axes[i].set_ylim(y_min, y_max)
                    axes[i].set_xticks([0])
                    axes[i].set_xticklabels(['Value'], fontsize=12)
                    axes[i].grid(True, alpha=0.3, linestyle='--')
                    axes[i].set_ylabel('Values', fontsize=12)
                    axes[i].tick_params(axis='both', which='major', labelsize=10)
                
                # Set main title
                fig.suptitle(title, fontsize=14, fontweight='bold', y=0.95)
                
                plt.tight_layout()
                
                # Save to bytes
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                img_buffer.seek(0)
                plt.close(fig)
                
                return img_buffer.getvalue()
            
            return None
            
        except Exception as e:
            logger.warning(f"Error creating bar chart: {str(e)}")
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
                # Use proper column widths for nutrient status table
                col_widths = [self.content_width * 0.3, self.content_width * 0.2, self.content_width * 0.3, self.content_width * 0.2]
                table = self._create_table_with_proper_layout(table_data, col_widths, font_size=10)
                if table:
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
    
    def _create_contextual_visualizations(self, step: Dict[str, Any], step_number: int, analysis_data: Dict[str, Any]) -> List:
        """Create contextual visualizations based on step content and visual keywords"""
        story = []
        
        try:
            # Get raw data for visualization
            raw_data = analysis_data.get('raw_data', {})
            soil_params = raw_data.get('soil_parameters', {})
            leaf_params = raw_data.get('leaf_parameters', {})
            
            # Generate visualizations based on step number and content
            if step_number == 1:  # Data Analysis
                # Create nutrient comparison charts
                if soil_params.get('parameter_statistics') or leaf_params.get('parameter_statistics'):
                    chart_image = self._create_nutrient_comparison_chart(soil_params, leaf_params)
                    if chart_image:
                        story.append(Paragraph("Nutrient Analysis Visualization:", self.styles['Heading3']))
                        img_buffer = io.BytesIO(chart_image)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
                
                # Create actual vs optimal bar charts
                if soil_params.get('parameter_statistics'):
                    soil_chart = _create_actual_vs_optimal_chart(soil_params['parameter_statistics'], 'soil')
                    if soil_chart:
                        story.append(Paragraph("Soil Nutrients: Actual vs Optimal Levels:", self.styles['Heading3']))
                        img_buffer = io.BytesIO(soil_chart)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
                
                if leaf_params.get('parameter_statistics'):
                    leaf_chart = _create_actual_vs_optimal_chart(leaf_params['parameter_statistics'], 'leaf')
                    if leaf_chart:
                        story.append(Paragraph("Leaf Nutrients: Actual vs Optimal Levels:", self.styles['Heading3']))
                        img_buffer = io.BytesIO(leaf_chart)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
                
                # Create nutrient ratio charts
                if soil_params.get('parameter_statistics'):
                    soil_ratio_chart = _create_nutrient_ratio_chart(soil_params['parameter_statistics'], 'soil')
                    if soil_ratio_chart:
                        story.append(Paragraph("Soil Nutrient Ratios:", self.styles['Heading3']))
                        img_buffer = io.BytesIO(soil_ratio_chart)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
                
                if leaf_params.get('parameter_statistics'):
                    leaf_ratio_chart = _create_nutrient_ratio_chart(leaf_params['parameter_statistics'], 'leaf')
                    if leaf_ratio_chart:
                        story.append(Paragraph("Leaf Nutrient Ratios:", self.styles['Heading3']))
                        img_buffer = io.BytesIO(leaf_ratio_chart)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
                
            
            elif step_number == 2:  # Issue Diagnosis
                # Charts removed as requested
                pass
            
            elif step_number == 3:  # Solution Recommendations
                # Create solution impact chart
                recommendations = analysis_data.get('recommendations', [])
                if recommendations:
                    chart_image = self._create_solution_impact_chart(recommendations)
                    if chart_image:
                        story.append(Paragraph("Solution Impact Analysis:", self.styles['Heading3']))
                        img_buffer = io.BytesIO(chart_image)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
            
            elif step_number == 5:  # Economic Impact
                # Economic Impact Visualization removed as requested
                pass
            
            elif step_number == 6:  # Yield Forecast
                # Create yield projection chart
                yield_data = analysis_data.get('yield_forecast', {})
                if yield_data:
                    chart_image = self._create_yield_projection_chart(yield_data)
                    if chart_image:
                        story.append(Paragraph("Yield Projection Visualization:", self.styles['Heading3']))
                        img_buffer = io.BytesIO(chart_image)
                        story.append(Image(img_buffer, width=6*inch, height=4*inch))
                        story.append(Spacer(1, 8))
        
        except Exception as e:
            logger.warning(f"Could not create contextual visualizations: {str(e)}")
        
        return story
    
    def _create_nutrient_comparison_chart(self, soil_params: Dict[str, Any], leaf_params: Dict[str, Any]) -> Optional[bytes]:
        """Create nutrient comparison chart"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            plt.clf()
            plt.close('all')
            
            # Extract nutrient data
            soil_stats = soil_params.get('parameter_statistics', {})
            leaf_stats = leaf_params.get('parameter_statistics', {})
            
            if not soil_stats and not leaf_stats:
                return None
            
            # Create subplot
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Prepare data for comparison
            nutrients = []
            soil_values = []
            leaf_values = []
            
            # Common nutrients to compare
            nutrient_mapping = {
                'N_%': 'Nitrogen (%)',
                'P_%': 'Phosphorus (%)', 
                'K_%': 'Potassium (%)',
                'Mg_%': 'Magnesium (%)',
                'Ca_%': 'Calcium (%)'
            }
            
            for soil_key, display_name in nutrient_mapping.items():
                if soil_key in soil_stats and soil_key in leaf_stats:
                    soil_avg = soil_stats[soil_key].get('average', 0)
                    leaf_avg = leaf_stats[soil_key].get('average', 0)
                    
                    if soil_avg > 0 or leaf_avg > 0:
                        nutrients.append(display_name)
                        soil_values.append(soil_avg)
                        leaf_values.append(leaf_avg)
            
            if not nutrients:
                return None
            
            # Create bar chart
            x = np.arange(len(nutrients))
            width = 0.35
            
            ax.bar(x - width/2, soil_values, width, label='Soil', alpha=0.8)
            ax.bar(x + width/2, leaf_values, width, label='Leaf', alpha=0.8)
            
            ax.set_xlabel('Nutrients')
            ax.set_ylabel('Values (%)')
            ax.set_title('Soil vs Leaf Nutrient Comparison')
            ax.set_xticks(x)
            ax.set_xticklabels(nutrients, rotation=45)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            result = img_buffer.getvalue()
            
            plt.close(fig)
            return result
            
        except Exception as e:
            logger.warning(f"Could not create nutrient comparison chart: {str(e)}")
            return None
    
    
    def _create_solution_impact_chart(self, recommendations: List[Dict[str, Any]]) -> Optional[bytes]:
        """Create solution impact chart"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            plt.clf()
            plt.close('all')
            
            if not recommendations:
                return None
            
            # Extract solution data
            solutions = []
            impacts = []
            
            for rec in recommendations:
                if isinstance(rec, dict):
                    param = rec.get('parameter', 'Unknown')
                    solutions.append(param)
                    # Mock impact score based on severity
                    severity = rec.get('severity', 'Medium')
                    impact_scores = {'Critical': 5, 'High': 4, 'Medium': 3, 'Low': 2, 'Unknown': 1}
                    impacts.append(impact_scores.get(severity, 3))
                else:
                    solutions.append(str(rec)[:20])
                    impacts.append(3)
            
            if not solutions:
                return None
            
            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            
            y_pos = np.arange(len(solutions))
            ax.barh(y_pos, impacts, alpha=0.8)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(solutions)
            ax.set_xlabel('Impact Score')
            ax.set_title('Solution Impact Analysis')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            result = img_buffer.getvalue()
            
            plt.close(fig)
            return result
            
        except Exception as e:
            logger.warning(f"Could not create solution impact chart: {str(e)}")
            return None
    
    
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
    
    def _create_step1_bar_graphs(self, analysis_data: Dict[str, Any]) -> List:
        """Create Step 1 bar graphs - Soil and Leaf Nutrient Status from results page"""
        story = []
        
        try:
            # Import the visualization functions from results module
            from modules.results import (
                create_soil_vs_mpob_visualization_with_robust_mapping,
                create_leaf_vs_mpob_visualization_with_robust_mapping
            )
            
            # Create soil bar graph
            soil_viz = create_soil_vs_mpob_visualization_with_robust_mapping(None)
            if soil_viz:
                story.append(Paragraph("🌱 Soil Nutrient Status (Average vs. MPOB Standard)", self.styles['Heading3']))
                story.append(Spacer(1, 8))
                
                # Convert visualization to image for PDF
                soil_image = self._create_chart_image_for_pdf(soil_viz)
                if soil_image:
                    story.append(soil_image)
                    story.append(Spacer(1, 12))
                else:
                    story.append(Paragraph("Soil visualization could not be generated.", self.styles['Normal']))
            
            # Create leaf bar graph
            leaf_viz = create_leaf_vs_mpob_visualization_with_robust_mapping(None)
            if leaf_viz:
                story.append(Paragraph("🍃 Leaf Nutrient Status (Average vs. MPOB Standard)", self.styles['Heading3']))
                story.append(Spacer(1, 8))
                
                # Convert visualization to image for PDF
                leaf_image = self._create_chart_image_for_pdf(leaf_viz)
                if leaf_image:
                    story.append(leaf_image)
                    story.append(Spacer(1, 12))
                else:
                    story.append(Paragraph("Leaf visualization could not be generated.", self.styles['Normal']))
            
            logger.info("✅ Created Step 1 bar graphs for PDF")
            
        except Exception as e:
            logger.error(f"❌ Error creating Step 1 bar graphs: {e}")
            story.append(Paragraph("Bar graphs could not be generated due to technical issues.", self.styles['Normal']))
        
        return story
    
    def _create_step1_visualizations_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create Step 1 visualizations section with all charts and graphs"""
        story = []
        
        # Step 1 Visualizations header
        story.append(Paragraph("Step 1 Visualizations", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        try:
            # Get raw data for visualization
            analysis_results = analysis_data.get('analysis_results', {})
            raw_data = analysis_results.get('raw_data', {})
            soil_params = raw_data.get('soil_parameters', {})
            leaf_params = raw_data.get('leaf_parameters', {})
            
            # Create nutrient comparison charts
            if soil_params.get('parameter_statistics') or leaf_params.get('parameter_statistics'):
                chart_image = self._create_nutrient_comparison_chart(soil_params, leaf_params)
                if chart_image:
                    story.append(Paragraph("Nutrient Analysis Visualization:", self.styles['Heading3']))
                    img_buffer = io.BytesIO(chart_image)
                    story.append(Image(img_buffer, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 8))
            
            # Create actual vs optimal bar charts
            if soil_params.get('parameter_statistics'):
                soil_chart = _create_actual_vs_optimal_chart(soil_params['parameter_statistics'], 'soil')
                if soil_chart:
                    story.append(Paragraph("Soil Nutrients: Actual vs Optimal Levels:", self.styles['Heading3']))
                    img_buffer = io.BytesIO(soil_chart)
                    story.append(Image(img_buffer, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 8))
            
            if leaf_params.get('parameter_statistics'):
                leaf_chart = _create_actual_vs_optimal_chart(leaf_params['parameter_statistics'], 'leaf')
                if leaf_chart:
                    story.append(Paragraph("Leaf Nutrients: Actual vs Optimal Levels:", self.styles['Heading3']))
                    img_buffer = io.BytesIO(leaf_chart)
                    story.append(Image(img_buffer, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 8))
            
            # Create nutrient ratio charts
            if soil_params.get('parameter_statistics'):
                soil_ratio_chart = _create_nutrient_ratio_chart(soil_params['parameter_statistics'], 'soil')
                if soil_ratio_chart:
                    story.append(Paragraph("Soil Nutrient Ratios:", self.styles['Heading3']))
                    img_buffer = io.BytesIO(soil_ratio_chart)
                    story.append(Image(img_buffer, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 8))
            
            if leaf_params.get('parameter_statistics'):
                leaf_ratio_chart = _create_nutrient_ratio_chart(leaf_params['parameter_statistics'], 'leaf')
                if leaf_ratio_chart:
                    story.append(Paragraph("Leaf Nutrient Ratios:", self.styles['Heading3']))
                    img_buffer = io.BytesIO(leaf_ratio_chart)
                    story.append(Image(img_buffer, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 8))
        
        except Exception as e:
            logger.warning(f"Could not create Step 1 visualizations: {str(e)}")
            story.append(Paragraph("Step 1 visualizations not available.", self.styles['CustomBody']))
        
        story.append(Spacer(1, 20))
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
                # Fit to page width
                table = self._create_table_with_proper_layout(table_data)
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
                table = self._create_table_with_proper_layout(table_data)
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
                    table = self._create_table_with_proper_layout(table_data)
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
                # Use proper column widths for investment scenarios table
                col_widths = [self.content_width * 0.2, self.content_width * 0.2, self.content_width * 0.2, self.content_width * 0.2, self.content_width * 0.2]
                table = self._create_table_with_proper_layout(table_data, col_widths, font_size=9)
                if table:
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
            
            years = list(range(2025, 2030))
            table_data = [['Year'] + [f'{level.title()} Investment' for level in ['high', 'medium', 'low'] if level in projections]]
            
            for year in years:
                row = [str(year)]
                for level in ['high', 'medium', 'low']:
                    if level in projections and len(projections[level]) >= (year - 2023):
                        value = projections[level][year - 2025]
                        row.append(f"{value:.1f} tons/ha" if isinstance(value, (int, float)) else str(value))
                    else:
                        row.append("N/A")
                table_data.append(row)
            
            if len(table_data) > 1:
                table = self._create_table_with_proper_layout(table_data)
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
                table = self._create_table_with_proper_layout(table_data)
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
        # 1. Check direct economic_forecast in analysis_data
        if 'economic_forecast' in analysis_data and analysis_data['economic_forecast']:
            return analysis_data['economic_forecast']
        
        # 2. Check analysis_results for economic_forecast
        if 'analysis_results' in analysis_data:
            analysis_results = analysis_data['analysis_results']
            if 'economic_forecast' in analysis_results and analysis_results['economic_forecast']:
                return analysis_results['economic_forecast']
        
        # 3. Check for investment_scenarios in analysis_data
        if 'investment_scenarios' in analysis_data and analysis_data['investment_scenarios']:
            # Convert investment_scenarios to the expected format
            investment_scenarios = analysis_data['investment_scenarios']
            scenarios = {}
            for level, data in investment_scenarios.items():
                if isinstance(data, dict):
                    scenarios[level] = {
                        'total_cost': data.get('total_cost', 0),
                        'additional_revenue': data.get('additional_revenue', data.get('return', 0)),
                        'roi_percentage': data.get('roi_percentage', data.get('roi', 0)),
                        'payback_months': data.get('payback_months', data.get('payback_period', 0))
                    }
            return {'scenarios': scenarios}
        
        # 4. Check analysis_results for investment_scenarios
        if 'analysis_results' in analysis_data:
            analysis_results = analysis_data['analysis_results']
            if 'investment_scenarios' in analysis_results and analysis_results['investment_scenarios']:
                investment_scenarios = analysis_results['investment_scenarios']
                scenarios = {}
                for level, data in investment_scenarios.items():
                    if isinstance(data, dict):
                        scenarios[level] = {
                            'total_cost': data.get('total_cost', 0),
                            'additional_revenue': data.get('additional_revenue', data.get('return', 0)),
                            'roi_percentage': data.get('roi_percentage', data.get('roi', 0)),
                            'payback_months': data.get('payback_months', data.get('payback_period', 0))
                        }
                return {'scenarios': scenarios}
        
        # 5. Check step-by-step analysis for economic data
        step_results = analysis_data.get('step_by_step_analysis', [])
        for step in step_results:
            if step.get('step_number') == 5 and 'economic_analysis' in step:
                return step['economic_analysis']
            elif 'economic_analysis' in step and step['economic_analysis']:
                return step['economic_analysis']
        
        # 6. Check for economic_forecast in nested analysis_results
        if 'analysis_results' in analysis_data:
            analysis_results = analysis_data['analysis_results']
            if 'analysis_results' in analysis_results and 'economic_forecast' in analysis_results['analysis_results']:
                return analysis_results['analysis_results']['economic_forecast']
        
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
            # Use proper column widths for economic metrics table
            col_widths = [self.content_width * 0.4, self.content_width * 0.6]
            table = self._create_table_with_proper_layout(metrics_data, col_widths, font_size=10)
            if table:
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
            
            # Plot different investment scenarios - handle both old array format and new range format
            for investment_type, style, marker in [('high_investment', 'o-', 'o'), ('medium_investment', 's-', 's'), ('low_investment', '^-', '^')]:
                if investment_type in yield_forecast:
                    investment_data = yield_forecast[investment_type]
                    investment_name = investment_type.replace('_', ' ').title()
                    
                    if isinstance(investment_data, list) and len(investment_data) >= 6:
                        # Old array format
                        ax.plot(years, investment_data[:6], style, label=investment_name, linewidth=2, markersize=6)
                    elif isinstance(investment_data, dict):
                        # New range format - extract midpoint values for plotting
                        range_values = []
                        for year in ['year_1', 'year_2', 'year_3', 'year_4', 'year_5']:
                            if year in investment_data:
                                range_str = investment_data[year]
                                if isinstance(range_str, str) and '-' in range_str:
                                    try:
                                        # Extract midpoint from range like "25.5-27.0 t/ha"
                                        low, high = range_str.replace(' t/ha', '').split('-')
                                        midpoint = (float(low) + float(high)) / 2
                                        range_values.append(midpoint)
                                    except:
                                        range_values.append(0)
                                else:
                                    range_values.append(0)
                            else:
                                range_values.append(0)
                        
                        if range_values:
                            # Add baseline as first point
                            full_values = [baseline_yield] + range_values
                            ax.plot(years, full_values, style, label=investment_name, linewidth=2, markersize=6)
            
            # Add baseline if available
            baseline_yield = yield_forecast.get('baseline_yield', 0)
            # Ensure baseline_yield is numeric
            try:
                baseline_yield = float(baseline_yield) if baseline_yield is not None else 0
            except (ValueError, TypeError):
                baseline_yield = 0
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
        
        # Add rows for each investment level - handle both old array format and new range format
        for investment_type in ['high_investment', 'medium_investment', 'low_investment']:
            if investment_type in yield_forecast:
                investment_data = yield_forecast[investment_type]
                investment_name = investment_type.replace('_', ' ').title()
                row = [investment_name]
                
                if isinstance(investment_data, list) and len(investment_data) >= 6:
                    # Old array format
                    for i in range(6):
                        row.append(f"{investment_data[i]:.1f}")
                elif isinstance(investment_data, dict):
                    # New range format
                    row.append("Current")  # Baseline
                    for year in ['year_1', 'year_2', 'year_3', 'year_4', 'year_5']:
                        if year in investment_data:
                            row.append(investment_data[year])  # Keep the range format
                        else:
                            row.append("N/A")
                
                table_data.append(row)
        
        if len(table_data) > 1:
            table = self._create_table_with_proper_layout(table_data)
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
        
        # Check if economic data is available
        
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
                    # Check both the direct key and the _investment suffix
                    scenario_key = investment_type
                    if scenario_key not in scenarios:
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
                table = self._create_table_with_proper_layout(table_data)
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
        else:
            # No economic data available
            story.append(Paragraph("Economic forecast data not available.", self.styles['CustomBody']))
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
        
        # 1. Check direct economic_forecast in analysis_data (primary location)
        if 'economic_forecast' in analysis_data and analysis_data['economic_forecast']:
            economic_data = analysis_data['economic_forecast']
        
        # 2. Check Step 5 (Economic Impact Forecast)
        if not economic_data:
            step_results = analysis_data.get('step_by_step_analysis', [])
            for step in step_results:
                if step.get('step_number') == 5 and 'economic_analysis' in step:
                    economic_data = step['economic_analysis']
                    economic_step = step
                    break
        
        # 3. Check any step that has economic_analysis
        if not economic_data:
            step_results = analysis_data.get('step_by_step_analysis', [])
            for step in step_results:
                if 'economic_analysis' in step and step['economic_analysis']:
                    economic_data = step['economic_analysis']
                    economic_step = step
                    break
        
        # 4. Check if economic data is in analysis_results
        if not economic_data and 'analysis_results' in analysis_data:
            analysis_results = analysis_data['analysis_results']
            if 'economic_forecast' in analysis_results:
                economic_data = analysis_results['economic_forecast']
        
        if economic_data:
            econ = economic_data
            
            # Extract data based on the actual structure from analysis engine
            current_yield = econ.get('current_yield_tonnes_per_ha', 0)
            land_size = econ.get('land_size_hectares', 0)
            oil_palm_price = econ.get('oil_palm_price_rm_per_tonne', 600)
            scenarios = econ.get('scenarios', {})
            
            # Process scenario data
            for scenario_name, scenario_data in scenarios.items():
                if isinstance(scenario_data, dict):
                    pass  # Process scenario data as needed
            
            # Display basic information
            if current_yield > 0:
                story.append(Paragraph(f"<b>Current Yield:</b> {current_yield:.1f} tons/ha", self.styles['CustomBody']))
            else:
                story.append(Paragraph(f"<b>Current Yield:</b> Based on analysis results", self.styles['CustomBody']))
            
            if land_size > 0:
                story.append(Paragraph(f"<b>Land Size:</b> {land_size:.1f} hectares", self.styles['CustomBody']))
            
            # Add palm density information if available
            palm_density = econ.get('palm_density_per_hectare', 0)
            total_palms = econ.get('total_palms', 0)
            if palm_density > 0:
                story.append(Paragraph(f"<b>Palm Density:</b> {palm_density} palms/hectare", self.styles['CustomBody']))
            if total_palms > 0:
                story.append(Paragraph(f"<b>Total Palms:</b> {total_palms:,} palms", self.styles['CustomBody']))
            
            # Handle both old single price and new range format
            if isinstance(oil_palm_price, str) and '-' in oil_palm_price:
                story.append(Paragraph(f"<b>Oil Palm Price:</b> {oil_palm_price}", self.styles['CustomBody']))
            else:
                story.append(Paragraph(f"<b>Oil Palm Price:</b> RM {oil_palm_price:.0f}/tonne", self.styles['CustomBody']))
            story.append(Spacer(1, 12))
            
            # Cost-Benefit Analysis Table
            if scenarios and isinstance(scenarios, dict):
                story.append(Paragraph("Cost-Benefit Analysis by Investment Level", self.styles['Heading2']))
                story.append(Spacer(1, 8))
                
                # Create table data with correct field names - handle both old and new range format
                table_data = [['Investment Level', 'Total Investment (RM)', 'Expected Return (RM)', 'ROI (%)', 'Payback Period (Months)']]
                
                # Process scenarios
                for scenario_name, scenario_data in scenarios.items():
                    if isinstance(scenario_data, dict):
                        # Handle new range format fields
                        investment = scenario_data.get('total_cost_range', scenario_data.get('total_cost', 0))
                        expected_return = scenario_data.get('additional_revenue_range', scenario_data.get('additional_revenue', 0))
                        roi = scenario_data.get('roi_percentage_range', scenario_data.get('roi_percentage', 0))
                        payback_months = scenario_data.get('payback_months_range', scenario_data.get('payback_months', 0))
                        
                        # Format values - handle both string ranges and numeric values
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
                
                # Fit to page width using helper (wrap + proportional widths)
                col_widths = [
                    self.content_width*0.22,  # Investment Level
                    self.content_width*0.20,  # Total Investment
                    self.content_width*0.20,  # Expected Return
                    self.content_width*0.18,  # ROI
                    self.content_width*0.20,  # Payback
                ]
                table = self._create_table_with_proper_layout(table_data, col_widths, font_size=8)
                if table:
                    story.append(table)
                story.append(Spacer(1, 12))
                
                # Assumptions section removed as requested
                
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
            
            col_widths = [
                self.content_width*0.22,
                self.content_width*0.20,
                self.content_width*0.20,
                self.content_width*0.18,
                self.content_width*0.20,
            ]
            table = self._create_table_with_proper_layout(table_data, col_widths, font_size=8)
            if table:
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
            # Ensure baseline_yield is numeric
            try:
                baseline_yield = float(baseline_yield) if baseline_yield is not None else 0
            except (ValueError, TypeError):
                baseline_yield = 0
            
            # Add baseline reference line
            if baseline_yield > 0:
                ax.axhline(y=baseline_yield, color='gray', linestyle='--', alpha=0.7, 
                          label=f'Current Baseline: {baseline_yield:.1f} t/ha')
            
            # Plot lines for different investment approaches
            if 'high_investment' in yield_forecast:
                high_data = yield_forecast['high_investment']
                if isinstance(high_data, list) and len(high_data) >= 6:
                    # Old array format
                    ax.plot(years, high_data, 'r-o', linewidth=2, label='High Investment', markersize=6)
                elif isinstance(high_data, dict):
                    # New range format - extract numeric values for plotting
                    high_yields = [baseline_yield]  # Start with baseline
                    for year in ['year_1', 'year_2', 'year_3', 'year_4', 'year_5']:
                        if year in high_data:
                            # Extract numeric value from range string like "25.5-27.0 t/ha"
                            try:
                                range_str = high_data[year]
                                if isinstance(range_str, str) and '-' in range_str:
                                    # Extract the first number from the range
                                    numeric_part = range_str.split('-')[0].strip()
                                    high_yields.append(float(numeric_part))
                                else:
                                    high_yields.append(float(range_str))
                            except (ValueError, TypeError):
                                high_yields.append(baseline_yield)
                        else:
                            high_yields.append(baseline_yield)
                    ax.plot(years, high_yields, 'r-o', linewidth=2, label='High Investment', markersize=6)
            
            if 'medium_investment' in yield_forecast:
                medium_data = yield_forecast['medium_investment']
                if isinstance(medium_data, list) and len(medium_data) >= 6:
                    # Old array format
                    ax.plot(years, medium_data, 'g-s', linewidth=2, label='Medium Investment', markersize=6)
                elif isinstance(medium_data, dict):
                    # New range format - extract numeric values for plotting
                    medium_yields = [baseline_yield]  # Start with baseline
                    for year in ['year_1', 'year_2', 'year_3', 'year_4', 'year_5']:
                        if year in medium_data:
                            # Extract numeric value from range string like "25.5-27.0 t/ha"
                            try:
                                range_str = medium_data[year]
                                if isinstance(range_str, str) and '-' in range_str:
                                    # Extract the first number from the range
                                    numeric_part = range_str.split('-')[0].strip()
                                    medium_yields.append(float(numeric_part))
                                else:
                                    medium_yields.append(float(range_str))
                            except (ValueError, TypeError):
                                medium_yields.append(baseline_yield)
                        else:
                            medium_yields.append(baseline_yield)
                    ax.plot(years, medium_yields, 'g-s', linewidth=2, label='Medium Investment', markersize=6)
            
            if 'low_investment' in yield_forecast:
                low_data = yield_forecast['low_investment']
                if isinstance(low_data, list) and len(low_data) >= 6:
                    # Old array format
                    ax.plot(years, low_data, 'b-^', linewidth=2, label='Low Investment', markersize=6)
                elif isinstance(low_data, dict):
                    # New range format - extract numeric values for plotting
                    low_yields = [baseline_yield]  # Start with baseline
                    for year in ['year_1', 'year_2', 'year_3', 'year_4', 'year_5']:
                        if year in low_data:
                            # Extract numeric value from range string like "25.5-27.0 t/ha"
                            try:
                                range_str = low_data[year]
                                if isinstance(range_str, str) and '-' in range_str:
                                    # Extract the first number from the range
                                    numeric_part = range_str.split('-')[0].strip()
                                    low_yields.append(float(numeric_part))
                                else:
                                    low_yields.append(float(range_str))
                            except (ValueError, TypeError):
                                low_yields.append(baseline_yield)
                        else:
                            low_yields.append(baseline_yield)
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
            
            # Assumptions section removed as requested
            
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
            
            # Assumptions section removed as requested
            
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
    
    def _create_results_header_section(self, analysis_data: Dict[str, Any], metadata: Dict[str, Any]) -> List:
        """Create results header section with metadata matching the results page"""
        story = []
        
        # Results header
        story.append(Paragraph("Analysis Results", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Create simplified metadata table without debug information
        metadata_data = []
        
        # Analysis Date only
        timestamp = metadata.get('timestamp') or analysis_data.get('timestamp')
        if timestamp:
            if hasattr(timestamp, 'strftime'):
                formatted_time = timestamp.strftime("%Y-%m-%d")
            else:
                formatted_time = str(timestamp)[:10]  # Just the date part
            metadata_data.append(['Analysis Date', formatted_time])
        
        # Report Types only
        report_types = analysis_data.get('report_types', ['soil', 'leaf'])
        if report_types:
            metadata_data.append(['Report Types', ', '.join(report_types)])
        
        if metadata_data:
            metadata_table = self._create_table_with_proper_layout(metadata_data)
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 12))
        
        return story
    
    def _create_raw_data_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create raw data section for PDF"""
        story = []
        
        # Raw Data header
        story.append(Paragraph("Raw Analysis Data", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Get raw data from analysis
        raw_data = analysis_data.get('raw_data', {})
        soil_params = raw_data.get('soil_parameters', {}).get('parameter_statistics', {})
        leaf_params = raw_data.get('leaf_parameters', {}).get('parameter_statistics', {})
        
        # Soil parameters table
        if soil_params:
            story.append(Paragraph("Soil Analysis Parameters", self.styles['Heading2']))
            story.append(Spacer(1, 8))
            
            # Create soil parameters table
            soil_data = [['Parameter', 'Average', 'Min', 'Max', 'Unit']]
            for param, data in soil_params.items():
                if isinstance(data, dict) and 'average' in data:
                    unit = data.get('unit', '')
                    soil_data.append([
                        param.replace('_', ' ').title(),
                        f"{data.get('average', 0):.2f}",
                        f"{data.get('min', 0):.2f}",
                        f"{data.get('max', 0):.2f}",
                        unit
                    ])
            
            if len(soil_data) > 1:
                soil_table = self._create_table_with_proper_layout(soil_data)
                soil_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(soil_table)
                story.append(Spacer(1, 12))
        
        # Leaf parameters table
        if leaf_params:
            story.append(Paragraph("Leaf Analysis Parameters", self.styles['Heading2']))
            story.append(Spacer(1, 8))
            
            # Create leaf parameters table
            leaf_data = [['Parameter', 'Average', 'Min', 'Max', 'Unit']]
            for param, data in leaf_params.items():
                if isinstance(data, dict) and 'average' in data:
                    unit = data.get('unit', '')
                    leaf_data.append([
                        param.replace('_', ' ').title(),
                        f"{data.get('average', 0):.2f}",
                        f"{data.get('min', 0):.2f}",
                        f"{data.get('max', 0):.2f}",
                        unit
                    ])
            
            if len(leaf_data) > 1:
                leaf_table = self._create_table_with_proper_layout(leaf_data)
                leaf_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(leaf_table)
                story.append(Spacer(1, 12))
        
        if not soil_params and not leaf_params:
            story.append(Paragraph("No raw data available for this analysis.", self.styles['CustomBody']))
        
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
            total_refs = len(all_references.get('database_references', []))
            
            if total_refs > 0:
                story.append(Paragraph(f"<b>Total References Found:</b> {total_refs}", self.styles['CustomBody']))
                story.append(Spacer(1, 12))
                
                # Database references only
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
                
                # Summary
                story.append(Paragraph(f"<b>Total references found:</b> {total_refs} ({len(all_references['database_references'])} database)", self.styles['CustomBody']))
        
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
        
        # Technical details section omitted for clarity
        
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

    def _create_comprehensive_data_tables_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create comprehensive data tables section with WORLD-CLASS robust mapping"""
        story = []

        try:
            # Section header
            story.append(Paragraph("📊 Comprehensive Data Analysis Tables", self.styles['Heading2']))
            story.append(Spacer(1, 12))

            # Use the same world-class robust mapping system as results page
            soil_data = self._extract_soil_data_with_robust_mapping_pdf(analysis_data)
            leaf_data = self._extract_leaf_data_with_robust_mapping_pdf(analysis_data)
            
            logger.info(f"🎯 PDF Robust extraction results - Soil: {bool(soil_data)}, Leaf: {bool(leaf_data)}")

            # Soil Parameters Table with robust mapping
            if soil_data and 'parameter_statistics' in soil_data:
                story.extend(self._create_soil_parameters_pdf_table(soil_data['parameter_statistics']))
                logger.info(f"✅ Created soil parameters table with {len(soil_data['parameter_statistics'])} parameters")
            else:
                logger.warning("❌ No soil parameter statistics found for PDF table")

            # Leaf Parameters Table with robust mapping
            if leaf_data and 'parameter_statistics' in leaf_data:
                story.extend(self._create_leaf_parameters_pdf_table(leaf_data['parameter_statistics']))
                logger.info(f"✅ Created leaf parameters table with {len(leaf_data['parameter_statistics'])} parameters")
            else:
                logger.warning("❌ No leaf parameter statistics found for PDF table")

            # Raw Sample Data Tables with robust extraction
            if soil_data and 'raw_samples' in soil_data and soil_data['raw_samples']:
                story.extend(self._create_raw_samples_pdf_table(soil_data['raw_samples'], 'Soil'))
                logger.info(f"✅ Created soil raw samples table with {len(soil_data['raw_samples'])} samples")

            if leaf_data and 'raw_samples' in leaf_data and leaf_data['raw_samples']:
                story.extend(self._create_raw_samples_pdf_table(leaf_data['raw_samples'], 'Leaf'))
                logger.info(f"✅ Created leaf raw samples table with {len(leaf_data['raw_samples'])} samples")

            # Data Quality Summary with robust data
            story.extend(self._create_data_quality_pdf_table_with_robust_data(analysis_data, soil_data, leaf_data))
        
        except Exception as e:
            logger.error(f"❌ Error creating comprehensive data tables section: {str(e)}")
            story.append(Paragraph("Error generating data tables section", self.styles['Normal']))

        return story

    def _extract_soil_data_with_robust_mapping_pdf(self, analysis_data):
        """WORLD-CLASS robust soil data extraction for PDF - same as results page"""
        try:
            logger.info("🔍 Starting robust soil data extraction for PDF")
            
            # Same comprehensive parameter mapping as results page
            soil_parameter_mappings = {
                'ph': 'pH', 'pH': 'pH', 'soil_ph': 'pH', 'soil_p_h': 'pH',
                'p_h': 'pH', 'soil_ph_value': 'pH', 'ph_value': 'pH',
                'n': 'N (%)', 'nitrogen': 'N (%)', 'n_percent': 'N (%)', 'n_%': 'N (%)',
                'soil_n': 'N (%)', 'soil_nitrogen': 'N (%)', 'nitrogen_percent': 'N (%)',
                'org_c': 'Org. C (%)', 'organic_carbon': 'Org. C (%)', 'org_carbon': 'Org. C (%)',
                'organic_c': 'Org. C (%)', 'soil_organic_carbon': 'Org. C (%)', 'oc': 'Org. C (%)',
                'soil_oc': 'Org. C (%)', 'carbon': 'Org. C (%)', 'soil_carbon': 'Org. C (%)',
                'total_p': 'Total P (mg/kg)', 'total_phosphorus': 'Total P (mg/kg)', 'tp': 'Total P (mg/kg)',
                'soil_total_p': 'Total P (mg/kg)', 'total_p_mg_kg': 'Total P (mg/kg)', 'p_total': 'Total P (mg/kg)',
                'avail_p': 'Avail P (mg/kg)', 'available_p': 'Avail P (mg/kg)', 'ap': 'Avail P (mg/kg)',
                'soil_avail_p': 'Avail P (mg/kg)', 'available_phosphorus': 'Avail P (mg/kg)', 'p_available': 'Avail P (mg/kg)',
                'avail_p_mg_kg': 'Avail P (mg/kg)', 'p_avail': 'Avail P (mg/kg)',
                'exch_k': 'Exch. K (meq%)', 'exchangeable_k': 'Exch. K (meq%)', 'ek': 'Exch. K (meq%)',
                'soil_exch_k': 'Exch. K (meq%)', 'k_exchangeable': 'Exch. K (meq%)', 'exch_k_meq': 'Exch. K (meq%)',
                'k_exch': 'Exch. K (meq%)', 'exchangeable_potassium': 'Exch. K (meq%)',
                'exch_ca': 'Exch. Ca (meq%)', 'exchangeable_ca': 'Exch. Ca (meq%)', 'eca': 'Exch. Ca (meq%)',
                'soil_exch_ca': 'Exch. Ca (meq%)', 'ca_exchangeable': 'Exch. Ca (meq%)', 'exch_ca_meq': 'Exch. Ca (meq%)',
                'ca_exch': 'Exch. Ca (meq%)', 'exchangeable_calcium': 'Exch. Ca (meq%)',
                'exch_mg': 'Exch. Mg (meq%)', 'exchangeable_mg': 'Exch. Mg (meq%)', 'emg': 'Exch. Mg (meq%)',
                'soil_exch_mg': 'Exch. Mg (meq%)', 'mg_exchangeable': 'Exch. Mg (meq%)', 'exch_mg_meq': 'Exch. Mg (meq%)',
                'mg_exch': 'Exch. Mg (meq%)', 'exchangeable_magnesium': 'Exch. Mg (meq%)',
                'cec': 'CEC (meq%)', 'cation_exchange_capacity': 'CEC (meq%)', 'cec_meq': 'CEC (meq%)',
                'soil_cec': 'CEC (meq%)', 'exchange_capacity': 'CEC (meq%)', 'c_e_c': 'CEC (meq%)'
            }
            
            # Same search locations as results page
            search_locations = [
                'raw_data.soil_parameters',
                'analysis_results.soil_parameters', 
                'step_by_step_analysis',
                'raw_ocr_data.soil_data.structured_ocr_data',
                'soil_parameters',
                'soil_data',
                'soil_analysis',
                'soil_samples'
            ]
            
            soil_data = None
            
            # Try each location
            for location in search_locations:
                try:
                    if '.' in location:
                        parts = location.split('.')
                        current = analysis_data
                        for part in parts:
                            if isinstance(current, dict) and part in current:
                                current = current[part]
                            else:
                                current = None
                                break
                        if current:
                            soil_data = current
                            logger.info(f"✅ Found soil data in: {location}")
                            break
                    else:
                        if location in analysis_data:
                            soil_data = analysis_data[location]
                            logger.info(f"✅ Found soil data in: {location}")
                            break
                except Exception as e:
                    logger.debug(f"Location {location} failed: {e}")
                    continue
            
            if not soil_data:
                logger.warning("❌ No soil data found in any location")
                return None
                
            # Extract parameter statistics with robust mapping
            param_stats = None
            if isinstance(soil_data, dict):
                for key in ['parameter_statistics', 'statistics', 'data', 'parameters', 'param_stats', 'stats']:
                    if key in soil_data and isinstance(soil_data[key], dict):
                        param_stats = soil_data[key]
                        logger.info(f"✅ Found parameter statistics in key: {key}")
                        break
                
                if not param_stats:
                    param_stats = soil_data
                    logger.info("✅ Using soil_data directly as parameter statistics")
            
            if not param_stats or not isinstance(param_stats, dict):
                logger.warning("❌ No valid parameter statistics found")
                return None
                
            # Apply robust parameter mapping
            mapped_params = {}
            for param_key, param_data in param_stats.items():
                normalized_key = param_key.lower().strip().replace(' ', '_').replace('(', '').replace(')', '').replace('%', '').replace('.', '')
                
                mapped_name = soil_parameter_mappings.get(normalized_key)
                if mapped_name:
                    mapped_params[mapped_name] = param_data
                    logger.info(f"✅ PDF Mapped {param_key} -> {mapped_name}")
                else:
                    # Try partial matching
                    for mapping_key, mapping_value in soil_parameter_mappings.items():
                        if mapping_key in normalized_key or normalized_key in mapping_key:
                            mapped_params[mapping_value] = param_data
                            logger.info(f"✅ PDF Partial mapped {param_key} -> {mapping_value}")
                            break
                    else:
                        mapped_params[param_key] = param_data
                        logger.info(f"⚠️ PDF No mapping found for {param_key}, keeping original")
            
            logger.info(f"🎯 PDF Robust soil data extraction complete: {len(mapped_params)} parameters")
            return {
                'parameter_statistics': mapped_params,
                'raw_samples': soil_data.get('raw_samples', []),
                'metadata': soil_data.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"❌ Error in PDF robust soil data extraction: {e}")
            return None

    def _extract_leaf_data_with_robust_mapping_pdf(self, analysis_data):
        """WORLD-CLASS robust leaf data extraction for PDF - same as results page"""
        try:
            logger.info("🔍 Starting robust leaf data extraction for PDF")
            
            # Same comprehensive parameter mapping as results page
            leaf_parameter_mappings = {
                'n': 'N (%)', 'nitrogen': 'N (%)', 'n_percent': 'N (%)', 'n_%': 'N (%)',
                'leaf_n': 'N (%)', 'leaf_nitrogen': 'N (%)', 'nitrogen_percent': 'N (%)',
                'p': 'P (%)', 'phosphorus': 'P (%)', 'p_percent': 'P (%)', 'p_%': 'P (%)',
                'leaf_p': 'P (%)', 'leaf_phosphorus': 'P (%)', 'phosphorus_percent': 'P (%)',
                'k': 'K (%)', 'potassium': 'K (%)', 'k_percent': 'K (%)', 'k_%': 'K (%)',
                'leaf_k': 'K (%)', 'leaf_potassium': 'K (%)', 'potassium_percent': 'K (%)',
                'mg': 'Mg (%)', 'magnesium': 'Mg (%)', 'mg_percent': 'Mg (%)', 'mg_%': 'Mg (%)',
                'leaf_mg': 'Mg (%)', 'leaf_magnesium': 'Mg (%)', 'magnesium_percent': 'Mg (%)',
                'ca': 'Ca (%)', 'calcium': 'Ca (%)', 'ca_percent': 'Ca (%)', 'ca_%': 'Ca (%)',
                'leaf_ca': 'Ca (%)', 'leaf_calcium': 'Ca (%)', 'calcium_percent': 'Ca (%)',
                'b': 'B (mg/kg)', 'boron': 'B (mg/kg)', 'b_mg_kg': 'B (mg/kg)', 'b_mg/kg': 'B (mg/kg)',
                'leaf_b': 'B (mg/kg)', 'leaf_boron': 'B (mg/kg)', 'boron_mg_kg': 'B (mg/kg)',
                'cu': 'Cu (mg/kg)', 'copper': 'Cu (mg/kg)', 'cu_mg_kg': 'Cu (mg/kg)', 'cu_mg/kg': 'Cu (mg/kg)',
                'leaf_cu': 'Cu (mg/kg)', 'leaf_copper': 'Cu (mg/kg)', 'copper_mg_kg': 'Cu (mg/kg)',
                'zn': 'Zn (mg/kg)', 'zinc': 'Zn (mg/kg)', 'zn_mg_kg': 'Zn (mg/kg)', 'zn_mg/kg': 'Zn (mg/kg)',
                'leaf_zn': 'Zn (mg/kg)', 'leaf_zinc': 'Zn (mg/kg)', 'zinc_mg_kg': 'Zn (mg/kg)'
            }
            
            # Same search locations as results page
            search_locations = [
                'raw_data.leaf_parameters',
                'analysis_results.leaf_parameters',
                'step_by_step_analysis',
                'raw_ocr_data.leaf_data.structured_ocr_data',
                'leaf_parameters',
                'leaf_data',
                'leaf_analysis',
                'leaf_samples'
            ]
            
            leaf_data = None
            
            # Try each location
            for location in search_locations:
                try:
                    if '.' in location:
                        parts = location.split('.')
                        current = analysis_data
                        for part in parts:
                            if isinstance(current, dict) and part in current:
                                current = current[part]
                            else:
                                current = None
                                break
                        if current:
                            leaf_data = current
                            logger.info(f"✅ Found leaf data in: {location}")
                            break
                    else:
                        if location in analysis_data:
                            leaf_data = analysis_data[location]
                            logger.info(f"✅ Found leaf data in: {location}")
                            break
                except Exception as e:
                    logger.debug(f"Location {location} failed: {e}")
                    continue
            
            if not leaf_data:
                logger.warning("❌ No leaf data found in any location")
            return None
        
            # Extract parameter statistics with robust mapping
            param_stats = None
            if isinstance(leaf_data, dict):
                for key in ['parameter_statistics', 'statistics', 'data', 'parameters', 'param_stats', 'stats']:
                    if key in leaf_data and isinstance(leaf_data[key], dict):
                        param_stats = leaf_data[key]
                        logger.info(f"✅ Found parameter statistics in key: {key}")
                        break
                
                if not param_stats:
                    param_stats = leaf_data
                    logger.info("✅ Using leaf_data directly as parameter statistics")
            
            if not param_stats or not isinstance(param_stats, dict):
                logger.warning("❌ No valid parameter statistics found")
                return None
                
            # Apply robust parameter mapping
            mapped_params = {}
            for param_key, param_data in param_stats.items():
                normalized_key = param_key.lower().strip().replace(' ', '_').replace('(', '').replace(')', '').replace('%', '').replace('.', '')
                
                mapped_name = leaf_parameter_mappings.get(normalized_key)
                if mapped_name:
                    mapped_params[mapped_name] = param_data
                    logger.info(f"✅ PDF Mapped {param_key} -> {mapped_name}")
                else:
                    # Try partial matching
                    for mapping_key, mapping_value in leaf_parameter_mappings.items():
                        if mapping_key in normalized_key or normalized_key in mapping_key:
                            mapped_params[mapping_value] = param_data
                            logger.info(f"✅ PDF Partial mapped {param_key} -> {mapping_value}")
                            break
                    else:
                        mapped_params[param_key] = param_data
                        logger.info(f"⚠️ PDF No mapping found for {param_key}, keeping original")
            
            logger.info(f"🎯 PDF Robust leaf data extraction complete: {len(mapped_params)} parameters")
            return {
                'parameter_statistics': mapped_params,
                'raw_samples': leaf_data.get('raw_samples', []),
                'metadata': leaf_data.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"❌ Error in PDF robust leaf data extraction: {e}")
            return None

    def _create_data_quality_pdf_table_with_robust_data(self, analysis_data: Dict[str, Any], soil_data: Dict[str, Any], leaf_data: Dict[str, Any]) -> List:
        """Create data quality summary table with robust data"""
        story = []
        
        try:
            story.append(Paragraph("■ Data Quality Summary", self.styles['Heading3']))
            story.append(Spacer(1, 8))
            
            # Calculate actual counts from robust data
            soil_sample_count = 0
            soil_param_count = 0
            if soil_data and 'parameter_statistics' in soil_data:
                soil_param_count = len(soil_data['parameter_statistics'])
                if 'raw_samples' in soil_data:
                    soil_sample_count = len(soil_data['raw_samples'])
            
            leaf_sample_count = 0
            leaf_param_count = 0
            if leaf_data and 'parameter_statistics' in leaf_data:
                leaf_param_count = len(leaf_data['parameter_statistics'])
                if 'raw_samples' in leaf_data:
                    leaf_sample_count = len(leaf_data['raw_samples'])
            
            # Create table data with actual counts
            headers = ['Data Type', 'Samples Count', 'Parameters Count', 'Quality Score', 'Status']
            table_data = [headers]
            
            # Soil quality assessment
            soil_quality = "Good" if soil_param_count >= 7 else "Fair" if soil_param_count >= 5 else "Poor"
            soil_status = "Complete" if soil_param_count >= 7 else "Partial" if soil_param_count >= 5 else "Limited"
            
            table_data.append([
                'Soil Analysis',
                str(soil_sample_count),
                str(soil_param_count),
                soil_quality,
                soil_status
            ])
            
            # Leaf quality assessment
            leaf_quality = "Good" if leaf_param_count >= 6 else "Fair" if leaf_param_count >= 4 else "Poor"
            leaf_status = "Complete" if leaf_param_count >= 6 else "Partial" if leaf_param_count >= 4 else "Limited"
            
            table_data.append([
                'Leaf Analysis',
                str(leaf_sample_count),
                str(leaf_param_count),
                leaf_quality,
                leaf_status
            ])
            
            # Create table
            col_widths = [doc.width * 0.25, doc.width * 0.15, doc.width * 0.20, doc.width * 0.15, doc.width * 0.15]
            table = self._create_table_with_proper_layout(table_data, col_widths, 9)
            story.append(table)
            story.append(Spacer(1, 12))
            
            logger.info(f"✅ Created robust data quality table - Soil: {soil_param_count} params, Leaf: {leaf_param_count} params")
            
        except Exception as e:
            logger.error(f"❌ Error creating robust data quality table: {e}")
            story.append(Paragraph("Error generating data quality summary", self.styles['Normal']))
            
        return story

    def _create_consolidated_key_findings_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create consolidated key findings section by calling the results module function"""
        story = []
        
        try:
            # Import the results module function directly
            from modules.results import generate_consolidated_key_findings
            
            # Extract step results for key findings generation
            step_results = analysis_data.get('step_by_step_analysis', [])
            if not step_results:
                # Try alternative locations
                step_results = analysis_data.get('analysis_results', [])
                if not step_results:
                    step_results = [analysis_data]  # Use the whole analysis data as a single step
            
            # Generate consolidated key findings
            consolidated_findings = generate_consolidated_key_findings(analysis_data, step_results)
            
            if consolidated_findings:
                story.append(Paragraph("🌱 Consolidated Findings", self.styles['Heading2']))
                story.append(Spacer(1, 12))
                
                for finding in consolidated_findings:
                    if isinstance(finding, dict):
                        title = finding.get('title', 'Finding')
                        description = finding.get('description', 'No description available')
                        
                        story.append(Paragraph(title, self.styles['Heading4']))
                        story.append(Paragraph(description, self.styles['Normal']))
                        story.append(Spacer(1, 8))
                    else:
                        story.append(Paragraph(str(finding), self.styles['Normal']))
                        story.append(Spacer(1, 6))
            else:
                story.append(Paragraph("🌱 Consolidated Findings", self.styles['Heading2']))
                story.append(Spacer(1, 12))
                story.append(Paragraph("No consolidated findings available.", self.styles['Normal']))
        
        except Exception as e:
            logger.error(f"Error creating consolidated key findings section: {str(e)}")
            story.append(Paragraph("Error generating key findings section", self.styles['Normal']))

        return story

    def _create_comprehensive_visualizations_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create comprehensive visualizations section with all charts and graphs"""
        story = []
        
        try:
            # Section header
            story.append(Paragraph("📊 Data Visualizations", self.styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Extract visualizations from step-by-step analysis
            visualizations = self._extract_visualizations_from_analysis(analysis_data)
            
            if visualizations:
                for viz_data in visualizations:
                    if not isinstance(viz_data, dict):
                        continue
                        
                    viz_type = viz_data.get('type', 'unknown')
                    title = viz_data.get('title', 'Visualization')

                    # Create chart image for PDF
                    try:
                        chart_image = self._create_chart_image_for_pdf(viz_data)
                        if chart_image is not None and hasattr(chart_image, 'width') and chart_image.width is not None:
                            story.append(Paragraph(title, self.styles['Heading4']))
                            story.append(Spacer(1, 6))
                            story.append(chart_image)
                            story.append(Spacer(1, 12))
                            logger.info(f"Successfully added chart to PDF: {title}")
                        else:
                            logger.warning(f"Chart image is None or invalid for {title}")
                            story.append(Paragraph(f"{title} - Chart generation failed", self.styles['Normal']))
                    except Exception as e:
                        logger.error(f"Error creating chart for {title}: {str(e)}")
                        story.append(Paragraph(f"{title} - Chart generation error", self.styles['Normal']))
            else:
                story.append(Paragraph("No visualizations available", self.styles['Normal']))

        except Exception as e:
            logger.error(f"Error creating comprehensive visualizations section: {str(e)}")
            story.append(Paragraph("Error generating visualizations section", self.styles['Normal']))

        return story

    def _extract_visualizations_from_analysis(self, analysis_data: Dict[str, Any]) -> List:
        """Extract all visualizations from the analysis data"""
        visualizations = []
        
        try:
            # Check step-by-step analysis
            step_analysis = analysis_data.get('step_by_step_analysis', [])
            for step in step_analysis:
                if isinstance(step, dict) and 'visualizations' in step:
                    step_viz = step['visualizations']
                    if isinstance(step_viz, list):
                        visualizations.extend(step_viz)
                    elif isinstance(step_viz, dict):
                        visualizations.append(step_viz)
            
            # Check raw data for visualizations
            raw_data = analysis_data.get('raw_data', {})
            if 'visualizations' in raw_data:
                raw_viz = raw_data['visualizations']
                if isinstance(raw_viz, list):
                    visualizations.extend(raw_viz)
                elif isinstance(raw_viz, dict):
                    visualizations.append(raw_viz)
                    
        except Exception as e:
            logger.error(f"Error extracting visualizations: {str(e)}")
            return []

        return visualizations

    def _create_chart_image_for_pdf(self, viz_data: Dict[str, Any]) -> Optional[Image]:
        """Create individual parameter bar charts for PDF - matching results page format"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from io import BytesIO
            
            # Extract chart information from viz_data
            title = viz_data.get('title', 'Chart')
            chart_type = viz_data.get('type', 'bar_chart')
            data = viz_data.get('data', {})
            options = viz_data.get('options', {})
            
            if chart_type == 'actual_vs_optimal_bar' and 'categories' in data and 'series' in data:
                categories = data['categories']
                series = data['series']
                
                if len(series) >= 2:
                    # Get observed and recommended values
                    observed_values = series[0].get('values', [])
                    recommended_values = series[1].get('values', [])
                    observed_color = series[0].get('color', '#3498db')
                    recommended_color = series[1].get('color', '#e74c3c')
                    
                    # Calculate layout - same as results page
                    num_params = len(categories)
                    if num_params > 4:
                        rows = 2
                        cols = (num_params + 1) // 2
                    else:
                        rows = 1
                        cols = num_params
                    
                    # Create subplots with conservative spacing to fit PDF borders
                    fig, axes = plt.subplots(rows, cols, figsize=(12, 8))
                    if rows == 1:
                        axes = [axes] if cols == 1 else axes
                    else:
                        axes = axes.flatten()
                    
                    # Set conservative spacing to ensure content stays within PDF borders
                    plt.subplots_adjust(
                        left=0.12,    # Increased left margin
                        right=0.88,   # Increased right margin
                        top=0.85,     # Increased top margin
                        bottom=0.15,  # Increased bottom margin
                        wspace=0.25,  # Increased horizontal spacing
                        hspace=0.35   # Increased vertical spacing
                    )
                    
                    # Create individual charts for each parameter
                    for i, param in enumerate(categories):
                        ax = axes[i]
                        actual_val = observed_values[i]
                        optimal_val = recommended_values[i]
                        
                        # Calculate appropriate scale for this parameter
                        max_val = max(actual_val, optimal_val)
                        min_val = min(actual_val, optimal_val)
                        range_val = max_val - min_val
                        if range_val == 0:
                            range_val = max_val * 0.1 if max_val > 0 else 1
                        
                        y_max = max_val + (range_val * 0.4)
                        y_min = max(0, min_val - (range_val * 0.2))
                        
                        # Create bars for this parameter
                        x_pos = [0, 1]  # Observed and Recommended positions
                        heights = [actual_val, optimal_val]
                        colors = [observed_color, recommended_color]
                        labels = ['Observed', 'Recommended']
                        
                        bars = ax.bar(x_pos, heights, color=colors, alpha=0.8)
                        
                        # Add value labels on bars
                        for j, (bar, height) in enumerate(zip(bars, heights)):
                            if height > 0:
                                ax.annotate(f'{height:.2f}',
                                          xy=(bar.get_x() + bar.get_width() / 2, height),
                                          xytext=(0, 3),
                                          textcoords="offset points",
                                          ha='center', va='bottom', fontsize=8, fontweight='bold')
                        
                        # Customize this subplot with conservative spacing for PDF borders
                        ax.set_title(param, fontsize=9, fontweight='bold', pad=4)
                        ax.set_ylim(y_min, y_max)
                        ax.set_xticks(x_pos)
                        ax.set_xticklabels(labels, fontsize=7)
                        ax.grid(True, alpha=0.3)
                        ax.set_ylabel('Value', fontsize=7)
                        
                        # Adjust tick parameters for conservative spacing
                        ax.tick_params(axis='x', labelsize=6, pad=1)
                        ax.tick_params(axis='y', labelsize=6, pad=1)
                        
                        # Add legend only to first subplot with smaller size
                        if i == 0:
                            ax.legend(['Observed', 'Recommended'], loc='upper right', fontsize=6, framealpha=0.9)
                    
                    # Hide unused subplots
                    for i in range(num_params, len(axes)):
                        axes[i].set_visible(False)
        
                    # Set main title with conservative positioning
                    fig.suptitle(title, fontsize=12, fontweight='bold', y=0.92)
                    
                    # Final layout adjustment to ensure content stays within borders
                    plt.tight_layout(rect=[0.12, 0.15, 0.88, 0.85])
                    
                    logger.info(f"✅ Created individual parameter charts for: {title}")
                else:
                    # Fallback to simple text if no series data
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.text(0.5, 0.5, f'Chart: {title}\nType: {chart_type}\nNo data available',
                           transform=ax.transAxes, ha='center', va='center', fontsize=12)
                    ax.set_title(title)
                    ax.axis('off')
            else:
                # Fallback for other chart types
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, f'Chart: {title}\nType: {chart_type}',
                       transform=ax.transAxes, ha='center', va='center', fontsize=12)
                ax.set_title(title)
                ax.axis('off')

            # Save to buffer
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            # Get buffer data and reset position
            buffer_data = buffer.getvalue()
            buffer.seek(0)
            
            # Validate buffer data
            if not buffer_data or len(buffer_data) == 0:
                logger.warning(f"Empty buffer for chart: {title}")
                return None
            
            # Create new buffer with the data
            image_buffer = BytesIO(buffer_data)
            
            # Create reportlab Image with conservative sizing for PDF borders
            try:
                chart_image = Image(image_buffer, width=7*inch, height=5*inch)
                logger.info(f"Successfully created individual parameter charts for: {title}")
                return chart_image
            except Exception as img_error:
                logger.error(f"Error creating Image object for {title}: {str(img_error)}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating chart image for PDF: {str(e)}")
            return None
        
    def _create_soil_parameters_pdf_table(self, soil_stats: Dict[str, Any]) -> List:
        """Create soil parameters PDF table with actual values from results page"""
        story = []
        
        try:
            story.append(Paragraph("🌱 Soil Parameters Summary", self.styles['Heading3']))
            story.append(Spacer(1, 8))
            
            # Create table data
            table_data = [['Parameter', 'Average', 'Min', 'Max', 'Std Dev', 'MPOB Optimal', 'Status']]
            
            # Use the exact same MPOB standards as the results page
            soil_mpob_standards = {
                'pH': (5.0, 6.0),
                'N (%)': (0.15, 0.25),
                'Org. C (%)': (2.0, 4.0),
                'Total P (mg/kg)': (20, 50),
                'Avail P (mg/kg)': (20, 50),
                'Exch. K (meq%)': (0.2, 0.5),
                'Exch. Ca (meq%)': (3.0, 6.0),
                'Exch. Mg (meq%)': (0.4, 0.8),
                'CEC (meq%)': (12.0, 25.0)
            }
            
            for param_name, param_data in soil_stats.items():
                # Handle different data formats
                if isinstance(param_data, dict):
                    avg_val = param_data.get('average', 0)
                    min_val = param_data.get('min', 0)
                    max_val = param_data.get('max', 0)
                    std_dev = param_data.get('std_dev', 0)
                elif isinstance(param_data, (int, float)):
                    avg_val = param_data
                    min_val = param_data
                    max_val = param_data
                    std_dev = 0
                else:
                    avg_val = 0
                    min_val = 0
                    max_val = 0
                    std_dev = 0
                
                logger.info(f"PDF Soil param {param_name}: avg={avg_val}, min={min_val}, max={max_val}")
                
                # Get MPOB optimal range
                optimal_range = soil_mpob_standards.get(param_name)
                if optimal_range:
                    opt_min, opt_max = optimal_range
                    opt_display = f"{opt_min}-{opt_max}"
                    
                    # Determine status
                    if avg_val is not None and avg_val != 0:
                        if opt_min <= avg_val <= opt_max:
                            status = "Optimal"
                        elif avg_val < opt_min:
                            status = "Critical Low"
                        else:
                            status = "Critical High"
                    else:
                        status = "No Data"
                else:
                    opt_display = "N/A"
                    status = "No Standard"
                
                table_data.append([
                    param_name,
                    f"{avg_val:.2f}" if avg_val is not None else "0.00",
                    f"{min_val:.2f}" if min_val is not None else "0.00",
                    f"{max_val:.2f}" if max_val is not None else "0.00",
                    f"{std_dev:.2f}" if std_dev is not None else "0.00",
                    opt_display,
                    status
                ])
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 12))
            
        except Exception as e:
            logger.error(f"Error creating soil parameters PDF table: {str(e)}")
            story.append(Paragraph("Error generating soil parameters table", self.styles['Normal']))
        
        return story

    def _create_leaf_parameters_pdf_table(self, leaf_stats: Dict[str, Any]) -> List:
        """Create leaf parameters PDF table with actual values from results page"""
        story = []
        
        try:
            story.append(Paragraph("🍃 Leaf Parameters Summary", self.styles['Heading3']))
            story.append(Spacer(1, 8))
            
            # Create table data
            table_data = [['Parameter', 'Average', 'Min', 'Max', 'Std Dev', 'MPOB Optimal', 'Status']]
            
            # Use the exact same MPOB standards as the results page
            leaf_mpob_standards = {
                'N (%)': (2.6, 3.2),
                'P (%)': (0.16, 0.22),
                'K (%)': (1.3, 1.7),
                'Mg (%)': (0.28, 0.38),
                'Ca (%)': (0.5, 0.7),
                'B (mg/kg)': (18, 28),
                'Cu (mg/kg)': (6.0, 10.0),
                'Zn (mg/kg)': (15, 25)
            }
            
            for param_name, param_data in leaf_stats.items():
                # Handle different data formats
                if isinstance(param_data, dict):
                    avg_val = param_data.get('average', 0)
                    min_val = param_data.get('min', 0)
                    max_val = param_data.get('max', 0)
                    std_dev = param_data.get('std_dev', 0)
                elif isinstance(param_data, (int, float)):
                    avg_val = param_data
                    min_val = param_data
                    max_val = param_data
                    std_dev = 0
            else:
                avg_val = 0
                min_val = 0
                max_val = 0
                std_dev = 0
                
            logger.info(f"PDF Leaf param {param_name}: avg={avg_val}, min={min_val}, max={max_val}")
            
            # Get MPOB optimal range
            optimal_range = leaf_mpob_standards.get(param_name)
            if optimal_range:
                opt_min, opt_max = optimal_range
                opt_display = f"{opt_min}-{opt_max}"
                
                # Determine status
                if avg_val is not None and avg_val != 0:
                    if opt_min <= avg_val <= opt_max:
                        status = "Optimal"
                    elif avg_val < opt_min:
                        status = "Critical Low"
                    else:
                        status = "Critical High"
                else:
                    status = "No Data"
            else:
                opt_display = "N/A"
                status = "No Standard"
            
            table_data.append([
                param_name,
                f"{avg_val:.2f}" if avg_val is not None else "0.00",
                f"{min_val:.2f}" if min_val is not None else "0.00",
                f"{max_val:.2f}" if max_val is not None else "0.00",
                f"{std_dev:.2f}" if std_dev is not None else "0.00",
                opt_display,
                status
            ])
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 12))
            
        except Exception as e:
            logger.error(f"Error creating leaf parameters PDF table: {str(e)}")
            story.append(Paragraph("Error generating leaf parameters table", self.styles['Normal']))
        
        return story

    def _create_raw_samples_pdf_table(self, raw_samples: List[Dict], sample_type: str) -> List:
        """Create raw samples PDF table with actual values from results page"""
        story = []
        
        try:
            story.append(Paragraph(f"📊 Raw {sample_type} Sample Data", self.styles['Heading3']))
            story.append(Spacer(1, 8))
            
            if not raw_samples:
                story.append(Paragraph(f"No {sample_type.lower()} sample data available", self.styles['Normal']))
                return story
            
            # Get all parameter names from the first sample
            first_sample = raw_samples[0] if raw_samples else {}
            param_names = [key for key in first_sample.keys() if key != 'sample_id']
            
            # Create table headers
            headers = ['Sample ID'] + param_names
            table_data = [headers]
            
            # Add sample data
            for sample in raw_samples[:10]:  # Limit to first 10 samples for readability
                row = [sample.get('sample_id', 'Unknown')]
                for param in param_names:
                    value = sample.get(param, 0)
                    if isinstance(value, (int, float)):
                        row.append(f"{value:.2f}")
                    else:
                        row.append(str(value))
                table_data.append(row)
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 12))
        
        except Exception as e:
            logger.error(f"Error creating raw samples PDF table: {str(e)}")
            story.append(Paragraph(f"Error generating {sample_type.lower()} samples table", self.styles['Normal']))
        
        return story

    def _create_data_quality_pdf_table(self, analysis_data: Dict[str, Any]) -> List:
        """Create data quality summary PDF table"""
        story = []
        
        try:
            story.append(Paragraph("📈 Data Quality Summary", self.styles['Heading3']))
            story.append(Spacer(1, 8))
            
            # Extract data quality information
            raw_data = analysis_data.get('raw_data', {})
            soil_params = raw_data.get('soil_parameters', {})
            leaf_params = raw_data.get('leaf_parameters', {})
            
            table_data = [
                ['Data Type', 'Samples Count', 'Parameters Count', 'Quality Score', 'Status']
            ]
            
            # Soil data quality
            if soil_params:
                soil_samples = soil_params.get('raw_samples', [])
                soil_stats = soil_params.get('parameter_statistics', {})
                soil_count = len(soil_samples)
                param_count = len(soil_stats)
                quality_score = "Good" if soil_count > 0 and param_count > 0 else "Poor"
                status = "Complete" if soil_count > 5 else "Limited"
                table_data.append(['Soil Analysis', str(soil_count), str(param_count), quality_score, status])
            
            # Leaf data quality
            if leaf_params:
                leaf_samples = leaf_params.get('raw_samples', [])
                leaf_stats = leaf_params.get('parameter_statistics', {})
                leaf_count = len(leaf_samples)
                param_count = len(leaf_stats)
                quality_score = "Good" if leaf_count > 0 and param_count > 0 else "Poor"
                status = "Complete" if leaf_count > 5 else "Limited"
                table_data.append(['Leaf Analysis', str(leaf_count), str(param_count), quality_score, status])
            
            if len(table_data) == 1:
                table_data.append(['No Data Available', '0', '0', 'Poor', 'Incomplete'])
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 12))
            
        except Exception as e:
            logger.error(f"Error creating data quality PDF table: {str(e)}")
            story.append(Paragraph("Error generating data quality table", self.styles['Normal']))
        
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

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
            # Simplified PDF format - only include requested sections
            story.extend(self._create_enhanced_executive_summary(analysis_data))
            story.extend(self._create_enhanced_key_findings(analysis_data))
            story.extend(self._create_enhanced_economic_forecast_table(analysis_data))
            story.extend(self._create_enhanced_yield_forecast_graph(analysis_data))
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
        """Create enhanced executive summary for step-by-step analysis"""
        story = []
        
        # Executive Summary header
        story.append(Paragraph("Executive Summary", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Get comprehensive summary from analysis data
        comprehensive_summary = analysis_data.get('comprehensive_summary', '')
        if comprehensive_summary:
            story.append(Paragraph(comprehensive_summary, self.styles['CustomBody']))
        else:
            story.append(Paragraph("Executive summary not available.", self.styles['CustomBody']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_enhanced_key_findings(self, analysis_data: Dict[str, Any]) -> List:
        """Create enhanced key findings section"""
        story = []
        
        # Key Findings header
        story.append(Paragraph("Key Findings", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Get step results
        step_results = analysis_data.get('step_by_step_analysis', [])
        all_key_findings = []
        
        for step in step_results:
            if 'key_findings' in step and step['key_findings']:
                step_title = step.get('step_title', f"Step {step.get('step_number', 'Unknown')}")
                for finding in step['key_findings']:
                    all_key_findings.append({
                        'finding': finding,
                        'step_title': step_title
                    })
        
        if all_key_findings:
            for i, finding_data in enumerate(all_key_findings, 1):
                finding = finding_data['finding']
                step_title = finding_data['step_title']
                
                # Create finding with step context
                finding_text = f"<b>{i}.</b> {finding}<br/><i>Source: {step_title}</i>"
                story.append(Paragraph(finding_text, self.styles['CustomBody']))
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("No key findings available from the analysis steps.", self.styles['CustomBody']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_step_by_step_analysis(self, analysis_data: Dict[str, Any]) -> List:
        """Create step-by-step analysis section"""
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

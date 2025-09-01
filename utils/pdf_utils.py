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
        
        # Check if this is comprehensive analysis format
        is_comprehensive = 'summary_metrics' in analysis_data and 'health_indicators' in analysis_data
        
        if is_comprehensive:
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
        
        # Appendix
        story.extend(self._create_appendix())
        
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
        report_type = metadata.get('report_type', 'Unknown').title()
        analysis_types = metadata.get('analysis_types', [])
        
        if analysis_types and len(analysis_types) > 1:
            # Multiple analysis types
            types_str = ' & '.join([t.title() for t in analysis_types])
            story.append(Paragraph(f"Report Type: {types_str} Analysis", self.styles['CustomHeading']))
        elif analysis_types and len(analysis_types) == 1:
            # Single analysis type
            story.append(Paragraph(f"Report Type: {analysis_types[0].title()} Analysis", self.styles['CustomHeading']))
        else:
            # Fallback to report_type
            story.append(Paragraph(f"Report Type: {report_type} Analysis", self.styles['CustomHeading']))
        
        story.append(Spacer(1, 20))
        
        # Metadata table
        metadata_data = [
            ['Lab Number:', metadata.get('lab_number', 'N/A')],
            ['Sample Date:', metadata.get('sample_date', 'N/A')],
            ['Farm Name:', metadata.get('farm_name', 'N/A')],
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
    
    def _create_executive_summary(self, analysis_data: Dict[str, Any]) -> List:
        """Create executive summary section"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Summary statistics
        total_params = analysis_data.get('total_parameters', 0)
        issues_count = analysis_data.get('issues_count', 0)
        
        summary_text = f"""
        This report analyzes {total_params} key parameters from your agricultural sample.
        Our AI-powered analysis has identified {issues_count} areas requiring attention.
        
        {analysis_data.get('summary', 'Analysis completed successfully.')}
        """
        
        story.append(Paragraph(summary_text, self.styles['CustomBody']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_parameters_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create parameters analysis section for both soil and leaf analysis"""
        story = []
        
        story.append(Paragraph("Parameters Analysis", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Handle both soil and leaf parameters
        soil_params = analysis_data.get('soil_parameters', {})
        leaf_params = analysis_data.get('leaf_parameters', {})
        analysis_results = analysis_data.get('analysis_results', [])
        
        # Create soil parameters section if available
        if soil_params:
            story.append(Paragraph("Soil Analysis Results", self.styles['Heading3']))
            story.append(Spacer(1, 10))
            
            soil_data = [['Parameter', 'Value', 'Unit', 'Status']]
            for param, value in soil_params.items():
                if isinstance(value, dict):
                    soil_data.append([
                        param.replace('_', ' ').title(),
                        str(value.get('value', 'N/A')),
                        value.get('unit', ''),
                        value.get('status', 'Normal')
                    ])
                else:
                    soil_data.append([param.replace('_', ' ').title(), str(value), '', 'Normal'])
            
            soil_table = Table(soil_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
            soil_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
            ]))
            
            story.append(soil_table)
            story.append(Spacer(1, 20))
        
        # Create leaf parameters section if available
        if leaf_params:
            story.append(Paragraph("Leaf Analysis Results", self.styles['Heading3']))
            story.append(Spacer(1, 10))
            
            leaf_data = [['Parameter', 'Value', 'Unit', 'Status']]
            for param, value in leaf_params.items():
                if isinstance(value, dict):
                    leaf_data.append([
                        param.replace('_', ' ').title(),
                        str(value.get('value', 'N/A')),
                        value.get('unit', ''),
                        value.get('status', 'Normal')
                    ])
                else:
                    leaf_data.append([param.replace('_', ' ').title(), str(value), '', 'Normal'])
            
            leaf_table = Table(leaf_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
            leaf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
            ]))
            
            story.append(leaf_table)
            story.append(Spacer(1, 20))
        
        # Handle legacy analysis_results format for backward compatibility
        if analysis_results:
            story.append(Paragraph("Detailed Analysis Results", self.styles['Heading3']))
            story.append(Spacer(1, 10))
            
            # Table headers
            table_data = [[
                'Parameter',
                'Value',
                'Unit',
                'Standard Range',
                'Status',
                'Severity'
            ]]
            
            # Add data rows
            for result in analysis_results:
                status_symbol = {
                    'normal': '✅',
                    'low': '⬇️',
                    'high': '⬆️'
                }.get(result.get('status', 'normal'), '❓')
                
                severity_symbol = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🔴'
                }.get(result.get('severity', 'low'), '⚪')
                
                table_data.append([
                    result.get('parameter', 'N/A'),
                    str(result.get('value', 'N/A')),
                    result.get('unit', ''),
                    f"{result.get('standard_min', 'N/A')}-{result.get('standard_max', 'N/A')}",
                    f"{status_symbol} {result.get('status', 'unknown').title()}",
                    f"{severity_symbol} {result.get('severity', 'unknown').title()}"
                ])
            
            # Create table
            params_table = Table(table_data, colWidths=[1.5*inch, 0.8*inch, 0.6*inch, 1.2*inch, 1*inch, 1*inch])
            params_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data styling
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
            ]))
            
            story.append(params_table)
        else:
            story.append(Paragraph("No parameter data available.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_recommendations_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create recommendations section"""
        story = []
        
        story.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        issues = analysis_data.get('issues', [])
        recommendations = analysis_data.get('recommendations', [])
        
        if issues:
            for i, issue in enumerate(issues, 1):
                # Issue header
                story.append(Paragraph(f"{i}. {issue.get('parameter', 'Parameter')} Issue", self.styles['Heading3']))
                
                # Issue description
                story.append(Paragraph(f"Problem: {issue.get('description', 'No description available')}", self.styles['Normal']))
                
                # Recommendation details
                if 'recommendation' in issue and issue['recommendation']:
                    rec = issue['recommendation']
                    
                    rec_data = [
                        ['Action:', rec.get('action', 'N/A')],
                        ['Description:', rec.get('description', 'N/A')],
                        ['Dosage:', rec.get('dosage', 'N/A')],
                        ['Cost Estimate:', rec.get('cost_estimate', 'N/A')]
                    ]
                    
                    rec_table = Table(rec_data, colWidths=[1.5*inch, 4*inch])
                    rec_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E8')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(rec_table)
                
                story.append(Spacer(1, 15))
        
        # General recommendations
        if recommendations:
            story.append(Paragraph("General Recommendations:", self.styles['Heading3']))
            
            for rec in recommendations:
                priority_color = {
                    'high': colors.red,
                    'medium': colors.orange,
                    'low': colors.blue
                }.get(rec.get('priority', 'medium'), colors.black)
                
                rec_text = f"• {rec.get('action', 'Action')}: {rec.get('description', 'Description')}"
                story.append(Paragraph(rec_text, self.styles['Normal']))
            
            story.append(Spacer(1, 15))
        
        return story
    
    def _create_economic_section(self, economic_data: Dict[str, Any]) -> List:
        """Create economic analysis section"""
        story = []
        
        story.append(Paragraph("Economic Analysis", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Economic summary table
        economic_summary = [
            ['Total Implementation Cost:', f"RM {economic_data.get('total_cost', 0):,.2f}"],
            ['Expected Yield Increase:', f"{economic_data.get('expected_yield_increase', 0):.1f}%"],
            ['Annual Revenue Increase:', f"RM {economic_data.get('annual_revenue_increase', 0):,.2f}"],
            ['Return on Investment:', f"{economic_data.get('roi_percentage', 0):.1f}%"],
            ['Payback Period:', f"{economic_data.get('payback_months', 0):.1f} months"]
        ]
        
        econ_table = Table(economic_summary, colWidths=[2.5*inch, 2*inch])
        econ_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E8')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(econ_table)
        story.append(Spacer(1, 20))
        
        # Cost breakdown
        cost_breakdown = economic_data.get('cost_breakdown', [])
        if cost_breakdown:
            story.append(Paragraph("Cost Breakdown:", self.styles['CustomSubheading']))
            
            breakdown_data = [['Item', 'Description', 'Cost (RM)']]
            for item in cost_breakdown:
                breakdown_data.append([
                    item.get('item', 'N/A'),
                    item.get('description', 'N/A'),
                    f"{item.get('cost', 0):,.2f}"
                ])
            
            breakdown_table = Table(breakdown_data, colWidths=[1.5*inch, 2.5*inch, 1*inch])
            breakdown_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(breakdown_table)
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_forecast_section(self, forecast_data: Dict[str, Any]) -> List:
        """Create yield forecast section"""
        story = []
        
        story.append(Paragraph("Yield Forecast", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Forecast summary
        forecast_summary = [
            ['Improvement Potential:', f"{forecast_data.get('improvement_potential', 0):.1f}%"],
            ['Total Additional Revenue (5 years):', f"RM {forecast_data.get('total_additional_revenue', 0):,.2f}"]
        ]
        
        forecast_table = Table(forecast_summary, colWidths=[2.5*inch, 2*inch])
        forecast_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E8')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(forecast_table)
        story.append(Spacer(1, 20))
        
        # Add forecast chart
        chart_image = self._create_forecast_chart(forecast_data)
        if chart_image:
            story.append(chart_image)
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_forecast_chart(self, forecast_data: Dict[str, Any]) -> Optional[Image]:
        """Create yield forecast chart"""
        try:
            years = forecast_data.get('years', [])
            current_scenario = forecast_data.get('current_scenario', [])
            improved_scenario = forecast_data.get('improved_scenario', [])
            
            if not years or not current_scenario or not improved_scenario:
                return None
            
            plt.figure(figsize=(8, 6))
            plt.plot(years, current_scenario, 'r-', label='Current Scenario', linewidth=2)
            plt.plot(years, improved_scenario, 'g-', label='Improved Scenario', linewidth=2)
            
            plt.xlabel('Year')
            plt.ylabel('Yield (tons/hectare)')
            plt.title('5-Year Yield Forecast Comparison')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image
            img = Image(img_buffer, width=6*inch, height=4.5*inch)
            return img
            
        except Exception as e:
            logger.error(f"Error creating forecast chart: {str(e)}")
            return None
    
    def _create_charts_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create charts section"""
        story = []
        
        story.append(Paragraph("Visual Analysis", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Parameters chart
        params_chart = self._create_parameters_chart(analysis_data)
        if params_chart:
            story.append(Paragraph("Parameter Comparison:", self.styles['CustomSubheading']))
            story.append(params_chart)
            story.append(Spacer(1, 20))
        
        # Issues severity chart
        issues_chart = self._create_issues_chart(analysis_data)
        if issues_chart:
            story.append(Paragraph("Issues by Severity:", self.styles['CustomSubheading']))
            story.append(issues_chart)
            story.append(Spacer(1, 20))
        
        return story
    
    def _create_parameters_chart(self, analysis_data: Dict[str, Any]) -> Optional[Image]:
        """Create parameters comparison chart"""
        try:
            analysis_results = analysis_data.get('analysis_results', [])
            if not analysis_results:
                return None
            
            # Extract data for chart
            parameters = []
            values = []
            min_standards = []
            max_standards = []
            
            for result in analysis_results[:8]:  # Limit to 8 parameters for readability
                parameters.append(result.get('parameter', 'N/A'))
                values.append(float(result.get('value', 0)))
                min_standards.append(float(result.get('standard_min', 0)))
                max_standards.append(float(result.get('standard_max', 0)))
            
            if not parameters:
                return None
            
            # Create chart
            x = np.arange(len(parameters))
            width = 0.25
            
            plt.figure(figsize=(10, 6))
            plt.bar(x - width, values, width, label='Actual Values', color='blue', alpha=0.7)
            plt.bar(x, min_standards, width, label='Min Standard', color='green', alpha=0.7)
            plt.bar(x + width, max_standards, width, label='Max Standard', color='red', alpha=0.7)
            
            plt.xlabel('Parameters')
            plt.ylabel('Values')
            plt.title('Parameter Values vs MPOB Standards')
            plt.xticks(x, parameters, rotation=45, ha='right')
            plt.legend()
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image
            img = Image(img_buffer, width=7*inch, height=4.2*inch)
            return img
            
        except Exception as e:
            logger.error(f"Error creating parameters chart: {str(e)}")
            return None
    
    def _create_issues_chart(self, analysis_data: Dict[str, Any]) -> Optional[Image]:
        """Create issues severity pie chart"""
        try:
            issues = analysis_data.get('issues', [])
            if not issues:
                return None
            
            # Count issues by severity
            severity_counts = {'high': 0, 'medium': 0, 'low': 0}
            for issue in issues:
                severity = issue.get('severity', 'low')
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            # Filter out zero counts
            labels = []
            sizes = []
            colors_list = []
            
            color_map = {'high': '#FF6B6B', 'medium': '#FFD93D', 'low': '#6BCF7F'}
            
            for severity, count in severity_counts.items():
                if count > 0:
                    labels.append(f'{severity.title()} ({count})')
                    sizes.append(count)
                    colors_list.append(color_map[severity])
            
            if not sizes:
                return None
            
            # Create pie chart
            plt.figure(figsize=(8, 6))
            plt.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
            plt.title('Distribution of Issues by Severity')
            plt.axis('equal')
            
            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image
            img = Image(img_buffer, width=6*inch, height=4.5*inch)
            return img
            
        except Exception as e:
            logger.error(f"Error creating issues chart: {str(e)}")
            return None
    
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
    
    def _create_comprehensive_executive_summary(self, analysis_data: Dict[str, Any]) -> List:
        """Create comprehensive executive summary with key metrics"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Get metrics
        metrics = analysis_data.get('summary_metrics', {})
        metadata = analysis_data.get('analysis_metadata', {})
        
        # Analysis overview
        total_params = metrics.get('total_parameters_analyzed', 0)
        total_issues = metrics.get('total_issues_identified', 0)
        overall_health = metrics.get('overall_health_score', 0)
        
        summary_text = f"""
        This comprehensive analysis evaluated {total_params} key parameters from your agricultural samples.
        Our AI-powered system identified {total_issues} areas requiring attention, resulting in an overall 
        plantation health score of {overall_health:.1f}/100.
        
        Analysis conducted on: {metadata.get('timestamp', 'N/A')[:10]}
        Data sources: {', '.join(metadata.get('data_sources', []))}
        """
        
        story.append(Paragraph(summary_text, self.styles['CustomBody']))
        story.append(Spacer(1, 15))
        
        # Key metrics table
        metrics_data = [
            ['Metric', 'Value', 'Status'],
            ['Overall Health Score', f"{overall_health:.1f}/100", self._get_health_status(overall_health)],
            ['Soil Health Score', f"{metrics.get('soil_health_score', 0):.1f}/100", self._get_health_status(metrics.get('soil_health_score', 0))],
            ['Leaf Health Score', f"{metrics.get('leaf_health_score', 0):.1f}/100", self._get_health_status(metrics.get('leaf_health_score', 0))],
            ['Nutrient Balance Score', f"{metrics.get('nutrient_balance_score', 0):.1f}/100", self._get_health_status(metrics.get('nutrient_balance_score', 0))],
            ['Critical Issues', str(metrics.get('critical_issues_count', 0)), 'High Priority' if metrics.get('critical_issues_count', 0) > 0 else 'Good'],
            ['Improvement Potential', f"{metrics.get('improvement_potential', 0):.1f}%", 'Opportunity']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_health_indicators_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create health indicators section"""
        story = []
        
        story.append(Paragraph("Health Indicators & Risk Assessment", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        indicators = analysis_data.get('health_indicators', {})
        
        # Positive indicators
        positive = indicators.get('positive_indicators', [])
        if positive:
            story.append(Paragraph("✓ Positive Indicators", self.styles['CustomSubheading']))
            for indicator in positive:
                story.append(Paragraph(f"• {indicator}", self.styles['CustomBody']))
            story.append(Spacer(1, 10))
        
        # Critical issues
        critical = indicators.get('critical_issues', [])
        if critical:
            story.append(Paragraph("⚠ Critical Issues Requiring Immediate Attention", self.styles['CustomSubheading']))
            for issue in critical[:5]:  # Limit to top 5
                story.append(Paragraph(f"• {issue.get('parameter', 'Unknown')}: {issue.get('description', '')}", self.styles['CustomBody']))
            story.append(Spacer(1, 10))
        
        # Improvement areas
        improvements = indicators.get('improvement_areas', [])
        if improvements:
            story.append(Paragraph("📈 Areas for Improvement", self.styles['CustomSubheading']))
            for area in improvements:
                story.append(Paragraph(f"• {area}", self.styles['CustomBody']))
            story.append(Spacer(1, 10))
        
        # Risk factors
        risks = indicators.get('risk_factors', [])
        if risks:
            story.append(Paragraph("⚡ Risk Factors", self.styles['CustomSubheading']))
            for risk in risks:
                story.append(Paragraph(f"• {risk}", self.styles['CustomBody']))
            story.append(Spacer(1, 20))
        
        return story
    
    def _create_detailed_analysis_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create detailed analysis section"""
        story = []
        
        story.append(Paragraph("Detailed Parameter Analysis", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        detailed = analysis_data.get('detailed_analysis', {})
        
        # Soil parameters
        soil_params = detailed.get('soil_parameters', {})
        if soil_params:
            story.append(Paragraph("Soil Analysis Summary", self.styles['CustomSubheading']))
            
            soil_data = [
                ['Metric', 'Count', 'Percentage'],
                ['Total Parameters Tested', str(soil_params.get('total_tested', 0)), '100%'],
                ['Parameters with Issues', str(soil_params.get('with_issues', 0)), f"{(soil_params.get('with_issues', 0) / max(soil_params.get('total_tested', 1), 1) * 100):.1f}%"],
                ['Optimal Parameters', str(soil_params.get('optimal', 0)), f"{(soil_params.get('optimal', 0) / max(soil_params.get('total_tested', 1), 1) * 100):.1f}%"]
            ]
            
            soil_table = Table(soil_data, colWidths=[2.5*inch, 1*inch, 1*inch])
            soil_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8BC34A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(soil_table)
            story.append(Spacer(1, 15))
        
        # Leaf parameters
        leaf_params = detailed.get('leaf_parameters', {})
        if leaf_params:
            story.append(Paragraph("Leaf Analysis Summary", self.styles['CustomSubheading']))
            
            leaf_data = [
                ['Metric', 'Count', 'Percentage'],
                ['Total Parameters Tested', str(leaf_params.get('total_tested', 0)), '100%'],
                ['Parameters with Issues', str(leaf_params.get('with_issues', 0)), f"{(leaf_params.get('with_issues', 0) / max(leaf_params.get('total_tested', 1), 1) * 100):.1f}%"],
                ['Optimal Parameters', str(leaf_params.get('optimal', 0)), f"{(leaf_params.get('optimal', 0) / max(leaf_params.get('total_tested', 1), 1) * 100):.1f}%"]
            ]
            
            leaf_table = Table(leaf_data, colWidths=[2.5*inch, 1*inch, 1*inch])
            leaf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#66BB6A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(leaf_table)
            story.append(Spacer(1, 20))
        
        return story
    
    def _create_comprehensive_recommendations_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create comprehensive recommendations section"""
        story = []
        
        story.append(Paragraph("Recommendations & Action Plan", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        indicators = analysis_data.get('health_indicators', {})
        
        # Group recommendations by priority
        critical_issues = indicators.get('critical_issues', [])
        medium_issues = indicators.get('medium_priority_issues', [])
        
        # Critical priority recommendations
        if critical_issues:
            story.append(Paragraph("🔴 Critical Priority Actions (Immediate)", self.styles['CustomSubheading']))
            for i, issue in enumerate(critical_issues[:5], 1):
                recommendation = issue.get('recommendation', {})
                if recommendation:
                    story.append(Paragraph(f"{i}. {issue.get('parameter', 'Unknown Parameter')}", self.styles['CustomBody']))
                    story.append(Paragraph(f"   Issue: {issue.get('description', '')}", self.styles['CustomBody']))
                    story.append(Paragraph(f"   Action: {recommendation.get('action', 'No action specified')}", self.styles['CustomBody']))
                    if 'cost_estimate' in recommendation:
                        story.append(Paragraph(f"   Cost: {recommendation['cost_estimate']}", self.styles['CustomBody']))
                    story.append(Spacer(1, 8))
        
        # Medium priority recommendations
        if medium_issues:
            story.append(Paragraph("🟡 Medium Priority Actions (1-3 months)", self.styles['CustomSubheading']))
            for i, issue in enumerate(medium_issues[:3], 1):
                recommendation = issue.get('recommendation', {})
                if recommendation:
                    story.append(Paragraph(f"{i}. {issue.get('parameter', 'Unknown Parameter')}", self.styles['CustomBody']))
                    story.append(Paragraph(f"   Issue: {issue.get('description', '')}", self.styles['CustomBody']))
                    story.append(Paragraph(f"   Action: {recommendation.get('action', 'No action specified')}", self.styles['CustomBody']))
                    story.append(Spacer(1, 8))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_comprehensive_economic_section(self, economic_data: Dict[str, Any]) -> List:
        """Create comprehensive economic analysis section"""
        story = []
        
        story.append(Paragraph("Economic Analysis & Investment Returns", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Economic summary
        total_cost = economic_data.get('total_treatment_cost', 0)
        expected_increase = economic_data.get('expected_yield_increase', 0)
        annual_revenue = economic_data.get('annual_revenue_increase', 0)
        roi = economic_data.get('roi_percentage', 0)
        payback = economic_data.get('payback_months', 0)
        
        story.append(Paragraph("Investment Summary", self.styles['CustomSubheading']))
        
        economic_summary = f"""
        Total Investment Required: RM {total_cost:,.2f}
        Expected Yield Increase: {expected_increase:.1f}%
        Annual Revenue Increase: RM {annual_revenue:,.2f}
        Return on Investment: {roi:.1f}%
        Payback Period: {payback:.1f} months
        """
        
        story.append(Paragraph(economic_summary, self.styles['CustomBody']))
        story.append(Spacer(1, 15))
        
        # Cost breakdown
        cost_breakdown = economic_data.get('cost_breakdown', [])
        if cost_breakdown:
            story.append(Paragraph("Cost Breakdown", self.styles['CustomSubheading']))
            
            cost_data = [['Item', 'Description', 'Cost (RM)', 'Priority']]
            for item in cost_breakdown:
                cost_data.append([
                    item.get('item', 'Unknown'),
                    item.get('description', '')[:40] + '...' if len(item.get('description', '')) > 40 else item.get('description', ''),
                    f"RM {item.get('cost', 0):,.2f}",
                    item.get('priority', 'medium').title()
                ])
            
            cost_table = Table(cost_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 0.8*inch])
            cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF3E0')])
            ]))
            
            story.append(cost_table)
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_comprehensive_forecast_section(self, forecast_data: Dict[str, Any]) -> List:
        """Create comprehensive yield forecast section"""
        story = []
        
        story.append(Paragraph("5-Year Yield Forecast & Projections", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Forecast overview
        current_yield = forecast_data.get('current_yield_estimate', 18.5)
        improvement = forecast_data.get('projected_yield_improvement', 0)
        
        story.append(Paragraph("Forecast Overview", self.styles['CustomSubheading']))
        story.append(Paragraph(f"Current Yield Estimate: {current_yield:.1f} tons/hectare", self.styles['CustomBody']))
        story.append(Paragraph(f"Projected Improvement: {improvement:.1f}%", self.styles['CustomBody']))
        story.append(Spacer(1, 15))
        
        # 5-year projection table
        projections = forecast_data.get('five_year_projection', [])
        if projections:
            story.append(Paragraph("5-Year Yield Projections", self.styles['CustomSubheading']))
            
            projection_data = [['Year', 'Projected Yield (tons/ha)', 'Revenue Estimate (RM)']]
            for proj in projections:
                projection_data.append([
                    str(proj.get('year', 'N/A')),
                    f"{proj.get('projected_yield', 0):.1f}",
                    f"RM {proj.get('revenue_estimate', 0):,.2f}"
                ])
            
            projection_table = Table(projection_data, colWidths=[1*inch, 2*inch, 2*inch])
            projection_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E3F2FD')])
            ]))
            
            story.append(projection_table)
        
        # Add forecast chart
        chart = self._create_comprehensive_forecast_chart(forecast_data)
        if chart:
            story.append(Spacer(1, 15))
            story.append(chart)
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_comprehensive_forecast_chart(self, forecast_data: Dict[str, Any]) -> Optional[Image]:
        """Create comprehensive 5-year forecast chart"""
        try:
            projections = forecast_data.get('five_year_projection', [])
            if not projections:
                return None
            
            years = [proj.get('year', 0) for proj in projections]
            yields = [proj.get('projected_yield', 0) for proj in projections]
            
            if not years or not yields:
                return None
            
            # Create line chart
            plt.figure(figsize=(10, 6))
            plt.plot(years, yields, marker='o', linewidth=3, markersize=8, color='#4CAF50')
            plt.title('5-Year Yield Forecast', fontsize=16, fontweight='bold')
            plt.xlabel('Year', fontsize=12)
            plt.ylabel('Yield (tons/hectare)', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(years)
            
            # Add value labels on points
            for i, (year, yield_val) in enumerate(zip(years, yields)):
                plt.annotate(f'{yield_val:.1f}', (year, yield_val), 
                           textcoords="offset points", xytext=(0,10), ha='center')
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image
            img = Image(img_buffer, width=7*inch, height=4.2*inch)
            return img
            
        except Exception as e:
            logger.error(f"Error creating comprehensive forecast chart: {str(e)}")
            return None
    
    def _create_data_quality_section(self, data_quality: Dict[str, Any]) -> List:
        """Create data quality assessment section"""
        story = []
        
        story.append(Paragraph("Data Quality Assessment", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Quality metrics
        soil_completeness = data_quality.get('soil_data_completeness', 0)
        leaf_completeness = data_quality.get('leaf_data_completeness', 0)
        overall_confidence = data_quality.get('overall_confidence', 0)
        reliability = data_quality.get('data_reliability', 'unknown')
        
        quality_data = [
            ['Quality Metric', 'Score', 'Assessment'],
            ['Soil Data Completeness', f"{soil_completeness:.1f}%", self._get_quality_assessment(soil_completeness)],
            ['Leaf Data Completeness', f"{leaf_completeness:.1f}%", self._get_quality_assessment(leaf_completeness)],
            ['Overall Confidence', f"{overall_confidence:.1f}%", self._get_quality_assessment(overall_confidence)],
            ['Data Reliability', reliability.replace('_', ' ').title(), self._get_reliability_description(reliability)]
        ]
        
        quality_table = Table(quality_data, colWidths=[2*inch, 1.5*inch, 2*inch])
        quality_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9C27B0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3E5F5')])
        ]))
        
        story.append(quality_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_comprehensive_charts_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create comprehensive charts section"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("Visual Analysis & Charts", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#4CAF50')))
        story.append(Spacer(1, 15))
        
        # Health scores chart
        health_chart = self._create_health_scores_chart(analysis_data)
        if health_chart:
            story.append(Paragraph("Health Scores Overview", self.styles['CustomSubheading']))
            story.append(health_chart)
            story.append(Spacer(1, 20))
        
        # Issues distribution chart
        issues_chart = self._create_comprehensive_issues_chart(analysis_data)
        if issues_chart:
            story.append(Paragraph("Issues Distribution by Severity", self.styles['CustomSubheading']))
            story.append(issues_chart)
            story.append(Spacer(1, 20))
        
        return story
    
    def _create_health_scores_chart(self, analysis_data: Dict[str, Any]) -> Optional[Image]:
        """Create health scores bar chart"""
        try:
            metrics = analysis_data.get('summary_metrics', {})
            
            scores = {
                'Overall Health': metrics.get('overall_health_score', 0),
                'Soil Health': metrics.get('soil_health_score', 0),
                'Leaf Health': metrics.get('leaf_health_score', 0),
                'Nutrient Balance': metrics.get('nutrient_balance_score', 0),
                'Risk Assessment': metrics.get('risk_assessment_score', 0)
            }
            
            categories = list(scores.keys())
            values = list(scores.values())
            
            # Create bar chart
            plt.figure(figsize=(10, 6))
            bars = plt.bar(categories, values, color=['#4CAF50', '#8BC34A', '#66BB6A', '#FFC107', '#FF5722'])
            plt.title('Health Scores Assessment', fontsize=16, fontweight='bold')
            plt.ylabel('Score (0-100)', fontsize=12)
            plt.ylim(0, 100)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image
            img = Image(img_buffer, width=7*inch, height=4.2*inch)
            return img
            
        except Exception as e:
            logger.error(f"Error creating health scores chart: {str(e)}")
            return None
    
    def _create_comprehensive_issues_chart(self, analysis_data: Dict[str, Any]) -> Optional[Image]:
        """Create comprehensive issues pie chart"""
        try:
            metrics = analysis_data.get('summary_metrics', {})
            
            issue_counts = {
                'Critical': metrics.get('critical_issues_count', 0),
                'High Priority': metrics.get('high_priority_issues_count', 0) - metrics.get('critical_issues_count', 0),
                'Medium Priority': metrics.get('medium_priority_issues_count', 0),
                'Low Priority': metrics.get('low_priority_issues_count', 0)
            }
            
            # Filter out zero values
            filtered_counts = {k: v for k, v in issue_counts.items() if v > 0}
            
            if not filtered_counts:
                return None
            
            labels = list(filtered_counts.keys())
            sizes = list(filtered_counts.values())
            colors_list = ['#F44336', '#FF9800', '#FFC107', '#4CAF50']
            
            # Create pie chart
            plt.figure(figsize=(8, 8))
            plt.pie(sizes, labels=labels, colors=colors_list[:len(labels)], 
                   autopct='%1.1f%%', startangle=90, textprops={'fontsize': 12})
            plt.title('Issues Distribution by Priority Level', fontsize=16, fontweight='bold')
            plt.axis('equal')
            
            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image
            img = Image(img_buffer, width=6*inch, height=6*inch)
            return img
            
        except Exception as e:
            logger.error(f"Error creating comprehensive issues chart: {str(e)}")
            return None
    
    def _get_health_status(self, score: float) -> str:
        """Get health status based on score"""
        if score >= 80:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"
    
    def _get_quality_assessment(self, score: float) -> str:
        """Get quality assessment based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Adequate"
        else:
            return "Needs Improvement"
    
    def _get_reliability_description(self, reliability: str) -> str:
        """Get reliability description"""
        descriptions = {
            'very_high': 'Highly Reliable',
            'high': 'Reliable',
            'medium': 'Moderately Reliable',
            'low': 'Limited Reliability',
            'unknown': 'Unknown'
        }
        return descriptions.get(reliability, 'Unknown')
    
    def save_to_firebase(self, pdf_bytes: bytes, filename: str) -> Optional[str]:
        """Save PDF to Firebase Storage"""
        try:
            if not self.storage_client:
                logger.warning("Firebase Storage not available")
                return None
            
            bucket = self.storage_client.bucket()
            blob = bucket.blob(f"reports/{filename}")
            
            blob.upload_from_string(
                pdf_bytes,
                content_type='application/pdf'
            )
            
            # Make the blob publicly readable
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Error saving PDF to Firebase: {str(e)}")
            return None

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

# Example usage
if __name__ == "__main__":
    # Sample data for testing
    sample_analysis_data = {
        'report_type': 'soil',
        'total_parameters': 10,
        'issues_count': 3,
        'summary': 'Analysis shows moderate nutrient deficiencies requiring attention.',
        'analysis_results': [
            {
                'parameter': 'pH',
                'value': 4.2,
                'unit': '',
                'standard_min': 4.5,
                'standard_max': 5.5,
                'status': 'low',
                'severity': 'medium'
            },
            {
                'parameter': 'Nitrogen',
                'value': 0.08,
                'unit': '%',
                'standard_min': 0.10,
                'standard_max': 0.15,
                'status': 'low',
                'severity': 'high'
            }
        ],
        'issues': [
            {
                'parameter': 'pH',
                'description': 'Soil pH is below optimal range',
                'severity': 'medium',
                'recommendation': {
                    'action': 'Apply lime',
                    'description': 'Apply agricultural lime to raise soil pH',
                    'dosage': '2-3 tons per hectare',
                    'cost_estimate': 'RM 500-750 per hectare'
                }
            }
        ],
        'economic_analysis': {
            'total_cost': 2500.0,
            'expected_yield_increase': 15.0,
            'annual_revenue_increase': 8000.0,
            'roi_percentage': 220.0,
            'payback_months': 4.5,
            'cost_breakdown': [
                {'item': 'Lime Application', 'description': 'Agricultural lime for pH correction', 'cost': 750.0},
                {'item': 'Fertilizer', 'description': 'Nitrogen-rich fertilizer', 'cost': 1200.0},
                {'item': 'Labor', 'description': 'Application and monitoring', 'cost': 550.0}
            ]
        },
        'yield_forecast': {
            'years': [2024, 2025, 2026, 2027, 2028],
            'current_scenario': [18.5, 18.3, 18.0, 17.8, 17.5],
            'improved_scenario': [19.2, 20.1, 21.3, 22.0, 22.5],
            'improvement_potential': 25.0,
            'total_additional_revenue': 45000.0
        }
    }
    
    sample_metadata = {
        'report_type': 'soil',
        'lab_number': 'SPL001',
        'sample_date': '2024-01-15',
        'farm_name': 'Test Farm'
    }
    
    sample_options = {
        'include_economic': True,
        'include_forecast': True,
        'include_charts': True
    }
    
    # Generate PDF
    pdf_bytes = generate_pdf_report(sample_analysis_data, sample_metadata, sample_options)
    
    # Save to file
    with open('sample_report.pdf', 'wb') as f:
        f.write(pdf_bytes)
    
    print("Sample PDF report generated successfully!")
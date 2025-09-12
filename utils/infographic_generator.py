"""
Infographic Generator for Ecosystem Valuation Results
Creates compelling social media-ready infographics
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from datetime import datetime
from typing import Dict, Any, Optional
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import warnings
warnings.filterwarnings('ignore')

# Set style for beautiful visualizations
plt.style.use('default')
sns.set_palette("husl")

class EcosystemInfographicGenerator:
    """Generate compelling infographics from ecosystem analysis results"""
    
    def __init__(self):
        self.colors = {
            'primary': '#2E8B57',      # Sea Green
            'secondary': '#90EE90',    # Light Green  
            'accent': '#FFD700',       # Gold
            'provisioning': '#4CAF50', # Green
            'regulating': '#2196F3',   # Blue
            'cultural': '#FF9800',     # Orange
            'supporting': '#9C27B0',   # Purple
            'background': '#F8F9FA',   # Light Gray
            'text_dark': '#2C3E50',    # Dark Blue Gray
            'text_light': '#7F8C8D'    # Light Gray
        }
    
    def generate_social_media_infographic(self, results: Dict[str, Any], area_name: str = None) -> str:
        """Generate a complete social media infographic"""
        
        # Create figure with high DPI for social media
        fig = plt.figure(figsize=(12, 16), dpi=300, facecolor=self.colors['background'])
        
        # Main title section
        self._add_title_section(fig, results, area_name)
        
        # Key metrics section
        self._add_key_metrics_section(fig, results)
        
        # Services breakdown pie chart
        self._add_services_breakdown(fig, results)
        
        # Ecosystem composition (if multiple ecosystems)
        self._add_ecosystem_composition(fig, results)
        
        # Value per hectare comparison
        self._add_value_comparison(fig, results)
        
        # Footer with branding
        self._add_footer(fig)
        
        # Convert to base64 string for web display
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                   facecolor=self.colors['background'], edgecolor='none')
        buffer.seek(0)
        
        # Convert to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return image_base64
    
    def _add_title_section(self, fig, results: Dict[str, Any], area_name: str):
        """Add compelling title section"""
        # Title area
        title_ax = fig.add_subplot(6, 1, 1)
        title_ax.axis('off')
        
        # Main title
        area_display = area_name if area_name else "Selected Area"
        total_value = results.get('total_value', 0)
        
        title_ax.text(0.5, 0.8, f"🌱 {area_display}", 
                     fontsize=28, fontweight='bold', ha='center', va='center',
                     color=self.colors['text_dark'])
        
        title_ax.text(0.5, 0.5, f"Natural Capital Value", 
                     fontsize=20, ha='center', va='center',
                     color=self.colors['text_light'])
        
        title_ax.text(0.5, 0.2, f"${total_value:,.0f}/year", 
                     fontsize=36, fontweight='bold', ha='center', va='center',
                     color=self.colors['primary'])
    
    def _add_key_metrics_section(self, fig, results: Dict[str, Any]):
        """Add key metrics with visual appeal"""
        metrics_ax = fig.add_subplot(6, 2, (3, 4))
        metrics_ax.axis('off')
        
        area_ha = results.get('area_ha', 0)
        value_per_ha = results.get('total_value', 0) / area_ha if area_ha > 0 else 0
        ecosystem_type = results.get('ecosystem_type') or results.get('primary_ecosystem', 'Unknown')
        
        # Create metric boxes
        metrics = [
            ("Area", f"{area_ha:,.0f} ha", self.colors['accent']),
            ("Per Hectare", f"${value_per_ha:,.0f}/ha/yr", self.colors['secondary']),
            ("Ecosystem", ecosystem_type, self.colors['primary'])
        ]
        
        for i, (label, value, color) in enumerate(metrics):
            x_pos = 0.15 + (i * 0.3)
            
            # Add colored background box
            bbox = FancyBboxPatch((x_pos - 0.1, 0.3), 0.2, 0.4,
                                boxstyle="round,pad=0.02",
                                facecolor=color, alpha=0.2,
                                edgecolor=color, linewidth=2)
            metrics_ax.add_patch(bbox)
            
            # Add text
            metrics_ax.text(x_pos, 0.6, value, fontsize=16, fontweight='bold',
                           ha='center', va='center', color=color)
            metrics_ax.text(x_pos, 0.4, label, fontsize=12,
                           ha='center', va='center', color=self.colors['text_dark'])
    
    def _add_services_breakdown(self, fig, results: Dict[str, Any]):
        """Add ecosystem services breakdown pie chart"""
        pie_ax = fig.add_subplot(6, 2, (5, 6))
        
        # Extract service values
        esvd_results = results.get('esvd_results', {})
        services_data = []
        service_labels = []
        service_colors = []
        
        for service_name, service_color in [
            ('provisioning', self.colors['provisioning']),
            ('regulating', self.colors['regulating']),
            ('cultural', self.colors['cultural']),
            ('supporting', self.colors['supporting'])
        ]:
            value = esvd_results.get(service_name, {}).get('total', 0)
            if value > 0:
                services_data.append(value)
                service_labels.append(service_name.title())
                service_colors.append(service_color)
        
        if services_data:
            # Create pie chart
            wedges, texts, autotexts = pie_ax.pie(services_data, labels=service_labels, 
                                                 colors=service_colors, autopct='%1.1f%%',
                                                 startangle=90, textprops={'fontsize': 10})
            
            # Enhance text
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            pie_ax.set_title("Ecosystem Services Breakdown", fontsize=14, fontweight='bold',
                           color=self.colors['text_dark'], pad=20)
    
    def _add_ecosystem_composition(self, fig, results: Dict[str, Any]):
        """Add ecosystem composition if multiple ecosystems detected"""
        comp_ax = fig.add_subplot(6, 1, 4)
        comp_ax.axis('off')
        
        # Check if we have ecosystem distribution
        ecosystem_distribution = results.get('ecosystem_distribution', {})
        
        if len(ecosystem_distribution) > 1:
            # Create horizontal bar chart
            ecosystems = list(ecosystem_distribution.keys())
            percentages = []
            
            total_samples = results.get('successful_queries', 1)
            for eco_name in ecosystems:
                eco_data = ecosystem_distribution[eco_name]
                percentage = (eco_data.get('count', 0) / total_samples) * 100
                percentages.append(percentage)
            
            # Create bars
            y_positions = np.arange(len(ecosystems))
            bars = comp_ax.barh(y_positions, percentages, 
                              color=sns.color_palette("husl", len(ecosystems)))
            
            # Customize
            comp_ax.set_yticks(y_positions)
            comp_ax.set_yticklabels(ecosystems)
            comp_ax.set_xlabel("Composition (%)", fontsize=12)
            comp_ax.set_title("Mixed Ecosystem Composition", fontsize=14, fontweight='bold',
                            color=self.colors['text_dark'])
            
            # Add percentage labels on bars
            for i, (bar, pct) in enumerate(zip(bars, percentages)):
                comp_ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                           f'{pct:.1f}%', ha='left', va='center', fontweight='bold')
        else:
            # Single ecosystem - show confidence
            primary_eco = results.get('primary_ecosystem') or results.get('ecosystem_type', 'Unknown')
            confidence = results.get('confidence', 0.5)
            
            comp_ax.text(0.5, 0.6, f"Primary Ecosystem: {primary_eco}", 
                        fontsize=16, fontweight='bold', ha='center', va='center',
                        color=self.colors['text_dark'])
            comp_ax.text(0.5, 0.4, f"Detection Confidence: {confidence:.0%}", 
                        fontsize=14, ha='center', va='center',
                        color=self.colors['text_light'])
    
    def _add_value_comparison(self, fig, results: Dict[str, Any]):
        """Add value comparison with global averages"""
        comp_ax = fig.add_subplot(6, 1, 5)
        
        # Get current value per hectare
        area_ha = results.get('area_ha', 1)
        current_value = results.get('total_value', 0) / area_ha
        
        # Updated global averages by ecosystem type (based on latest ESVD data)
        global_averages = {
            'Forest': 7129,              # Generic forest (using tropical as baseline)
            'Tropical Forest': 7129,
            'Temperate Forest': 25796,
            'Boreal Forest': 7966,
            'Wetland': 105085,
            'Coastal': 75142,
            'Marine': 67759,
            'Grassland': 2601,
            'Shrubland': 1084,
            'Agricultural': 26524,       # Cropland
            'Cropland': 26524,
            'Urban': 330342,
            'Desert': 750,
            'Polar': 107659
        }
        
        ecosystem_type = results.get('ecosystem_type') or results.get('primary_ecosystem', 'Forest')
        global_avg = global_averages.get(ecosystem_type, 3000)
        
        # Create comparison bars
        categories = ['Your Area', f'Global {ecosystem_type} Average']
        values = [current_value, global_avg]
        colors = [self.colors['primary'], self.colors['secondary']]
        
        bars = comp_ax.bar(categories, values, color=colors, alpha=0.8)
        
        # Customize
        comp_ax.set_ylabel("Value ($/ha/year)", fontsize=12)
        comp_ax.set_title("Value Comparison", fontsize=14, fontweight='bold',
                         color=self.colors['text_dark'])
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            comp_ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values) * 0.01,
                        f'${value:,.0f}', ha='center', va='bottom', fontweight='bold')
        
        # Format y-axis
        comp_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    def _add_footer(self, fig):
        """Add footer with branding and date"""
        footer_ax = fig.add_subplot(6, 1, 6)
        footer_ax.axis('off')
        
        # Add branding
        footer_ax.text(0.5, 0.7, "Generated by Ecosystem Valuation Engine", 
                      fontsize=12, fontweight='bold', ha='center', va='center',
                      color=self.colors['primary'])
        
        # Add date
        current_date = datetime.now().strftime("%B %d, %Y")
        footer_ax.text(0.5, 0.5, f"Analysis Date: {current_date}", 
                      fontsize=10, ha='center', va='center',
                      color=self.colors['text_light'])
        
        # Add methodology note
        footer_ax.text(0.5, 0.3, "Values based on ESVD/TEEB research database with regional adjustments", 
                      fontsize=8, ha='center', va='center', style='italic',
                      color=self.colors['text_light'])
        
        # Add hashtags for social media
        footer_ax.text(0.5, 0.1, "#NaturalCapital #EcosystemServices #Sustainability #EnvironmentalValue", 
                      fontsize=10, ha='center', va='center',
                      color=self.colors['accent'])

    def generate_compact_summary_card(self, results: Dict[str, Any], area_name: str = None) -> str:
        """Generate a compact summary card for quick sharing"""
        
        fig, ax = plt.subplots(figsize=(8, 6), dpi=300, facecolor=self.colors['background'])
        ax.axis('off')
        
        # Background gradient effect
        gradient = np.linspace(0, 1, 100).reshape(1, -1)
        ax.imshow(gradient, extent=[0, 1, 0, 1], aspect='auto', cmap='Greens', alpha=0.3)
        
        # Title
        area_display = area_name if area_name else "Ecosystem Analysis"
        ax.text(0.5, 0.9, f"🌱 {area_display}", fontsize=24, fontweight='bold', 
               ha='center', va='center', color=self.colors['text_dark'])
        
        # Main value
        total_value = results.get('total_value', 0)
        ax.text(0.5, 0.7, f"${total_value:,.0f}/year", fontsize=32, fontweight='bold',
               ha='center', va='center', color=self.colors['primary'])
        
        # Key details
        area_ha = results.get('area_ha', 0)
        ecosystem_type = results.get('ecosystem_type') or results.get('primary_ecosystem', 'Mixed')
        
        details_text = f"{area_ha:,.0f} hectares • {ecosystem_type} Ecosystem"
        ax.text(0.5, 0.5, details_text, fontsize=16, ha='center', va='center',
               color=self.colors['text_light'])
        
        # Quick stats
        value_per_ha = total_value / area_ha if area_ha > 0 else 0
        ax.text(0.5, 0.3, f"${value_per_ha:,.0f} per hectare annually", fontsize=14,
               ha='center', va='center', color=self.colors['text_dark'])
        
        # Footer
        ax.text(0.5, 0.1, f"Ecosystem Valuation Engine • {datetime.now().strftime('%Y-%m-%d')}", 
               fontsize=10, ha='center', va='center', color=self.colors['text_light'])
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight',
                   facecolor=self.colors['background'], edgecolor='none')
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return image_base64

# Convenience function for use in main app
def generate_results_infographic(results: Dict[str, Any], area_name: str = None, style: str = 'full') -> str:
    """Generate infographic from ecosystem analysis results"""
    generator = EcosystemInfographicGenerator()
    
    if style == 'compact':
        return generator.generate_compact_summary_card(results, area_name)
    else:
        return generator.generate_social_media_infographic(results, area_name)
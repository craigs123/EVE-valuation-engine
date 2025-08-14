"""
Data Export Module
Handles exporting analysis results to various formats (CSV, JSON, PDF reports)
"""

import pandas as pd
import json
import io
from datetime import datetime
from typing import Dict, Any, List
import base64

def export_to_csv(analysis_results: Dict[str, Any]) -> str:
    """
    Export analysis results to CSV format
    
    Args:
        analysis_results: Complete analysis results dictionary
        
    Returns:
        CSV data as string
    """
    try:
        # Prepare data for CSV export
        export_data = []
        
        if 'metrics' in analysis_results:
            metrics_data = analysis_results['metrics']
            
            # Export time series data for each metric
            for metric_name, metric_data in metrics_data.items():
                if isinstance(metric_data, dict) and 'time_series' in metric_data:
                    time_series = metric_data['time_series']
                    
                    for point in time_series:
                        row = {
                            'metric_name': metric_name,
                            'date': point.get('date', ''),
                            'value': point.get('value', 0),
                            'quality': point.get('quality', 'unknown')
                        }
                        
                        # Add metric-specific fields
                        for key, value in point.items():
                            if key not in ['date', 'value', 'quality']:
                                row[f'{metric_name}_{key}'] = value
                        
                        export_data.append(row)
        
        # Create DataFrame and convert to CSV
        if export_data:
            df = pd.DataFrame(export_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            return csv_buffer.getvalue()
        else:
            # Export summary data if no time series available
            summary_data = []
            if 'metrics' in analysis_results:
                for metric_name, metric_data in analysis_results['metrics'].items():
                    if isinstance(metric_data, dict):
                        row = {'metric_name': metric_name}
                        for key, value in metric_data.items():
                            if key != 'time_series' and not isinstance(value, (list, dict)):
                                row[key] = value
                        summary_data.append(row)
            
            if summary_data:
                df = pd.DataFrame(summary_data)
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                return csv_buffer.getvalue()
            else:
                return "No data available for export"
    
    except Exception as e:
        return f"Error exporting to CSV: {str(e)}"

def export_to_json(analysis_results: Dict[str, Any]) -> str:
    """
    Export analysis results to JSON format
    
    Args:
        analysis_results: Complete analysis results dictionary
        
    Returns:
        JSON data as string
    """
    try:
        # Create a clean export structure
        export_structure = {
            'export_timestamp': datetime.now().isoformat(),
            'analysis_metadata': {
                'time_range': analysis_results.get('time_range', {}),
                'area_bounds': analysis_results.get('area_bounds', {}),
            },
            'metrics': {},
            'summary': {}
        }
        
        if 'metrics' in analysis_results:
            for metric_name, metric_data in analysis_results['metrics'].items():
                if isinstance(metric_data, dict):
                    # Clean the metric data for JSON export
                    clean_metric_data = {}
                    for key, value in metric_data.items():
                        if not isinstance(value, type(lambda: None)):  # Skip functions
                            clean_metric_data[key] = value
                    
                    export_structure['metrics'][metric_name] = clean_metric_data
                    
                    # Add to summary
                    export_structure['summary'][metric_name] = {
                        'current_value': metric_data.get('current_value', 0),
                        'trend': metric_data.get('trend_slope', 0),
                        'mean_value': metric_data.get('mean_value', 0)
                    }
        
        return json.dumps(export_structure, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': f'Error exporting to JSON: {str(e)}'}, indent=2)

def export_report(analysis_results: Dict[str, Any], area_info: Dict[str, Any]) -> bytes:
    """
    Generate a PDF report of the analysis results
    
    Args:
        analysis_results: Complete analysis results dictionary
        area_info: Information about the selected area
        
    Returns:
        PDF data as bytes
    """
    try:
        # Since we can't generate actual PDFs without additional dependencies,
        # we'll create a comprehensive text report that can be saved as a file
        
        report_content = generate_text_report(analysis_results, area_info)
        
        # Convert to bytes
        return report_content.encode('utf-8')
    
    except Exception as e:
        error_report = f"Error generating PDF report: {str(e)}\n\nFallback text report:\n"
        error_report += generate_text_report(analysis_results, area_info)
        return error_report.encode('utf-8')

def generate_text_report(analysis_results: Dict[str, Any], area_info: Dict[str, Any]) -> str:
    """
    Generate a comprehensive text report
    
    Args:
        analysis_results: Complete analysis results dictionary
        area_info: Information about the selected area
        
    Returns:
        Formatted text report
    """
    report_lines = []
    
    # Header
    report_lines.extend([
        "=" * 80,
        "ECOSYSTEM VALUATION ENGINE (EVE) REPORT",
        "=" * 80,
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ])
    
    # Area Information
    report_lines.extend([
        "AREA INFORMATION",
        "-" * 40,
    ])
    
    if area_info:
        report_lines.append(f"Area Type: {area_info.get('type', 'Unknown')}")
        if 'coordinates' in area_info:
            coords = area_info['coordinates']
            if coords:
                lats = [coord[1] for coord in coords]
                lons = [coord[0] for coord in coords]
                report_lines.extend([
                    f"Number of boundary points: {len(coords)}",
                    f"Latitude range: {min(lats):.6f} to {max(lats):.6f}",
                    f"Longitude range: {min(lons):.6f} to {max(lons):.6f}",
                ])
    else:
        report_lines.append("No area information available")
    
    report_lines.append("")
    
    # Time Range
    if 'time_range' in analysis_results:
        time_range = analysis_results['time_range']
        report_lines.extend([
            "ANALYSIS TIME RANGE",
            "-" * 40,
            f"Start Date: {time_range[0] if isinstance(time_range, (list, tuple)) else 'Unknown'}",
            f"End Date: {time_range[1] if isinstance(time_range, (list, tuple)) else 'Unknown'}",
            "",
        ])
    
    # Metrics Summary
    if 'metrics' in analysis_results:
        report_lines.extend([
            "NATURAL CAPITAL METRICS SUMMARY",
            "-" * 40,
        ])
        
        metrics_data = analysis_results['metrics']
        
        for metric_name, metric_data in metrics_data.items():
            report_lines.extend([
                f"\n{metric_name.upper()}",
                "." * 30,
            ])
            
            if isinstance(metric_data, dict):
                # Current status
                current_value = metric_data.get('current_value', 'N/A')
                previous_value = metric_data.get('previous_value', 'N/A')
                mean_value = metric_data.get('mean_value', 'N/A')
                trend = metric_data.get('trend_slope', 'N/A')
                
                report_lines.extend([
                    f"Current Value: {format_value(current_value)}",
                    f"Previous Value: {format_value(previous_value)}",
                    f"Mean Value: {format_value(mean_value)}",
                    f"Trend (slope): {format_value(trend)}",
                ])
                
                # Change calculation
                if (isinstance(current_value, (int, float)) and 
                    isinstance(previous_value, (int, float)) and 
                    previous_value != 0):
                    change_pct = ((current_value - previous_value) / previous_value) * 100
                    change_direction = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "→"
                    report_lines.append(f"Change: {change_direction} {abs(change_pct):.2f}%")
                
                # Interpretation
                interpretation = get_metric_interpretation(metric_name, current_value, trend)
                if interpretation:
                    report_lines.extend([
                        "Interpretation:",
                        f"  {interpretation}",
                    ])
                
                # Spatial data
                if 'spatial_data' in metric_data and metric_data['spatial_data']:
                    report_lines.append("Spatial Statistics:")
                    spatial_data = metric_data['spatial_data']
                    for key, value in spatial_data.items():
                        if not isinstance(value, (list, dict)):
                            report_lines.append(f"  {key.replace('_', ' ').title()}: {format_value(value)}")
                
                # Time series summary
                if 'time_series' in metric_data and metric_data['time_series']:
                    ts_data = metric_data['time_series']
                    report_lines.extend([
                        f"Time Series Points: {len(ts_data)}",
                        f"Date Range: {ts_data[0].get('date', 'Unknown')} to {ts_data[-1].get('date', 'Unknown')}",
                    ])
                    
                    # Quality assessment
                    good_quality = sum(1 for point in ts_data if point.get('quality') == 'good')
                    quality_pct = (good_quality / len(ts_data)) * 100 if ts_data else 0
                    report_lines.append(f"Data Quality: {quality_pct:.1f}% good quality points")
            else:
                report_lines.append(f"Value: {format_value(metric_data)}")
    
    # Recommendations
    recommendations = generate_recommendations(analysis_results)
    if recommendations:
        report_lines.extend([
            "\n",
            "RECOMMENDATIONS",
            "-" * 40,
        ])
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
    
    # Data Quality Assessment
    quality_assessment = assess_overall_quality(analysis_results)
    report_lines.extend([
        "\n",
        "DATA QUALITY ASSESSMENT",
        "-" * 40,
        f"Overall Quality Rating: {quality_assessment['rating']}",
        f"Confidence Level: {quality_assessment['confidence']}",
    ])
    
    if quality_assessment['issues']:
        report_lines.append("Issues Identified:")
        for issue in quality_assessment['issues']:
            report_lines.append(f"  - {issue}")
    
    # Footer
    report_lines.extend([
        "\n",
        "=" * 80,
        "End of Report",
        "Generated by Ecosystem Valuation Engine (EVE)",
        "=" * 80,
    ])
    
    return "\n".join(report_lines)

def format_value(value: Any) -> str:
    """Format a value for display in reports"""
    if isinstance(value, float):
        if abs(value) < 0.001:
            return f"{value:.6f}"
        else:
            return f"{value:.4f}"
    elif isinstance(value, int):
        return str(value)
    else:
        return str(value)

def get_metric_interpretation(metric_name: str, current_value: Any, trend: Any) -> str:
    """Get interpretation text for a metric"""
    if not isinstance(current_value, (int, float)) or not isinstance(trend, (int, float)):
        return ""
    
    interpretations = {
        'NDVI': {
            'ranges': [
                (0.8, float('inf'), "Very dense vegetation"),
                (0.6, 0.8, "Dense vegetation"),
                (0.3, 0.6, "Moderate vegetation"),
                (0.1, 0.3, "Sparse vegetation"),
                (float('-inf'), 0.1, "Bare soil or water")
            ]
        },
        'forest_cover': {
            'ranges': [
                (70, float('inf'), "High forest coverage"),
                (30, 70, "Moderate forest coverage"),
                (10, 30, "Low forest coverage"),
                (float('-inf'), 10, "Very low forest coverage")
            ]
        },
        'water_quality': {
            'ranges': [
                (80, float('inf'), "Excellent water quality"),
                (60, 80, "Good water quality"),
                (40, 60, "Fair water quality"),
                (20, 40, "Poor water quality"),
                (float('-inf'), 20, "Very poor water quality")
            ]
        },
        'biodiversity_index': {
            'ranges': [
                (80, float('inf'), "Very high biodiversity"),
                (60, 80, "High biodiversity"),
                (40, 60, "Medium biodiversity"),
                (20, 40, "Low biodiversity"),
                (float('-inf'), 20, "Very low biodiversity")
            ]
        }
    }
    
    if metric_name not in interpretations:
        return f"Current value: {format_value(current_value)}"
    
    # Find the appropriate range
    for low, high, description in interpretations[metric_name]['ranges']:
        if low <= current_value < high:
            base_interpretation = description
            break
    else:
        base_interpretation = f"Value: {format_value(current_value)}"
    
    # Add trend information
    if trend > 0.001:
        trend_text = " with improving trend"
    elif trend < -0.001:
        trend_text = " with declining trend"
    else:
        trend_text = " with stable trend"
    
    return base_interpretation + trend_text

def generate_recommendations(analysis_results: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on analysis results"""
    recommendations = []
    
    if 'metrics' not in analysis_results:
        return recommendations
    
    metrics_data = analysis_results['metrics']
    
    # NDVI recommendations
    if 'NDVI' in metrics_data:
        ndvi_data = metrics_data['NDVI']
        if isinstance(ndvi_data, dict):
            current_ndvi = ndvi_data.get('current_value', 0)
            trend = ndvi_data.get('trend_slope', 0)
            
            if current_ndvi < 0.3:
                recommendations.append("Consider vegetation restoration programs to improve ecosystem health")
            elif current_ndvi > 0.6 and trend < -0.001:
                recommendations.append("Monitor for potential vegetation stress or degradation")
            elif trend > 0.001:
                recommendations.append("Positive vegetation trend detected - continue current management practices")
    
    # Forest cover recommendations
    if 'forest_cover' in metrics_data:
        forest_data = metrics_data['forest_cover']
        if isinstance(forest_data, dict):
            current_cover = forest_data.get('current_value', 0)
            trend = forest_data.get('trend_slope', 0)
            
            if current_cover < 30:
                recommendations.append("Implement reforestation initiatives to increase forest coverage")
            elif trend < -0.5:
                recommendations.append("Address potential deforestation causes and implement conservation measures")
    
    # Water quality recommendations
    if 'water_quality' in metrics_data:
        water_data = metrics_data['water_quality']
        if isinstance(water_data, dict):
            current_quality = water_data.get('current_value', 0)
            
            if current_quality < 60:
                recommendations.append("Investigate water quality issues and implement pollution control measures")
    
    # Carbon storage recommendations
    if 'carbon_storage' in metrics_data:
        carbon_data = metrics_data['carbon_storage']
        if isinstance(carbon_data, dict):
            trend = carbon_data.get('trend_slope', 0)
            
            if trend < -10:
                recommendations.append("Focus on carbon sequestration activities to reverse declining storage trend")
            elif trend > 10:
                recommendations.append("Excellent carbon storage growth - consider carbon offset certification")
    
    # Biodiversity recommendations
    if 'biodiversity_index' in metrics_data:
        bio_data = metrics_data['biodiversity_index']
        if isinstance(bio_data, dict):
            current_bio = bio_data.get('current_value', 0)
            
            if current_bio < 40:
                recommendations.append("Enhance habitat diversity and connectivity to support biodiversity")
    
    # General recommendations
    if not recommendations:
        recommendations.append("Continue monitoring ecosystem health with regular assessments")
    
    recommendations.append("Consider increasing monitoring frequency for better trend analysis")
    recommendations.append("Integrate ground-truth data collection to validate satellite-based measurements")
    
    return recommendations

def assess_overall_quality(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the overall quality of the analysis"""
    quality_assessment = {
        'rating': 'Good',
        'confidence': 'High',
        'issues': [],
        'strengths': []
    }
    
    if 'metrics' not in analysis_results:
        quality_assessment['rating'] = 'Poor'
        quality_assessment['confidence'] = 'Low'
        quality_assessment['issues'].append('No metrics data available')
        return quality_assessment
    
    metrics_data = analysis_results['metrics']
    total_metrics = len(metrics_data)
    successful_metrics = 0
    total_data_points = 0
    good_quality_points = 0
    
    for metric_name, metric_data in metrics_data.items():
        if isinstance(metric_data, dict) and 'current_value' in metric_data:
            successful_metrics += 1
            
            # Check time series quality
            if 'time_series' in metric_data and metric_data['time_series']:
                ts_data = metric_data['time_series']
                total_data_points += len(ts_data)
                good_quality_points += sum(1 for point in ts_data if point.get('quality') == 'good')
    
    # Calculate success rate
    success_rate = (successful_metrics / total_metrics) * 100 if total_metrics > 0 else 0
    data_quality_rate = (good_quality_points / total_data_points) * 100 if total_data_points > 0 else 0
    
    # Determine overall rating
    if success_rate >= 90 and data_quality_rate >= 80:
        quality_assessment['rating'] = 'Excellent'
        quality_assessment['confidence'] = 'Very High'
    elif success_rate >= 70 and data_quality_rate >= 60:
        quality_assessment['rating'] = 'Good'
        quality_assessment['confidence'] = 'High'
    elif success_rate >= 50 and data_quality_rate >= 40:
        quality_assessment['rating'] = 'Fair'
        quality_assessment['confidence'] = 'Medium'
    else:
        quality_assessment['rating'] = 'Poor'
        quality_assessment['confidence'] = 'Low'
    
    # Add specific issues
    if success_rate < 100:
        quality_assessment['issues'].append(f"Only {success_rate:.1f}% of metrics calculated successfully")
    
    if data_quality_rate < 80:
        quality_assessment['issues'].append(f"Data quality concerns: only {data_quality_rate:.1f}% high-quality data points")
    
    if total_data_points < 6:
        quality_assessment['issues'].append("Limited temporal data - consider longer analysis period")
    
    # Add strengths
    if success_rate >= 90:
        quality_assessment['strengths'].append("High metric calculation success rate")
    
    if data_quality_rate >= 80:
        quality_assessment['strengths'].append("Good data quality across time series")
    
    if total_data_points >= 12:
        quality_assessment['strengths'].append("Sufficient temporal coverage for trend analysis")
    
    return quality_assessment

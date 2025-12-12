"""Export service for generating reports in various formats."""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting analysis results to various formats."""
    
    def __init__(self):
        """Initialize export service."""
        logger.info("Export service initialized")
    
    def export_to_json(
        self,
        analysis_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export analysis to JSON format.
        
        Args:
            analysis_data: Analysis data dictionary
            filename: Optional filename
            
        Returns:
            JSON string
        """
        return json.dumps(analysis_data, indent=2, default=str)
    
    def export_to_markdown(
        self,
        analysis_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export analysis to Markdown format.
        
        Args:
            analysis_data: Analysis data dictionary
            filename: Optional filename
            
        Returns:
            Markdown string
        """
        md = []
        md.append("# Business Analysis Report\n")
        md.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Executive Summary
        if "executive_summary" in analysis_data:
            md.append("## Executive Summary\n\n")
            md.append(analysis_data["executive_summary"])
            md.append("\n\n")
        
        # KPIs
        if "json_output" in analysis_data:
            json_output = analysis_data["json_output"]
            kpis = json_output.get("kpis", {})
            
            if kpis.get("revenue"):
                md.append("## Key Performance Indicators\n\n")
                md.append("### Revenue\n\n")
                for revenue in kpis["revenue"][:5]:
                    if isinstance(revenue, dict):
                        md.append(f"- **{revenue.get('period', 'Period')}**: {revenue.get('value', 0)}M\n")
                md.append("\n")
        
        # Financial Ratios
        if "json_output" in analysis_data:
            json_output = analysis_data["json_output"]
            if "financial_ratios" in json_output:
                md.append("## Financial Ratios\n\n")
                ratios = json_output["financial_ratios"]
                if ratios:
                    md.append("### Profitability Ratios\n\n")
                    profitability = ratios.get("profitability", {})
                    if profitability.get("ebitda_margin"):
                        margin = profitability["ebitda_margin"]
                        md.append(f"- EBITDA Margin: {margin.get('value', 0)}%\n")
        
        return "".join(md)
    
    def export_to_csv(
        self,
        analysis_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export KPIs to CSV format.
        
        Args:
            analysis_data: Analysis data dictionary
            filename: Optional filename
            
        Returns:
            CSV string
        """
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write KPIs
        if "json_output" in analysis_data:
            json_output = analysis_data["json_output"]
            kpis = json_output.get("kpis", {})
            
            writer.writerow(["Metric", "Period", "Value", "Unit"])
            
            for revenue in kpis.get("revenue", []):
                if isinstance(revenue, dict):
                    writer.writerow([
                        "Revenue",
                        revenue.get("period", ""),
                        revenue.get("value", ""),
                        revenue.get("unit", "")
                    ])
        
        return output.getvalue()


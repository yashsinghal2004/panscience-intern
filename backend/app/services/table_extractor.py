"""Table extraction service for parsing financial tables from PDFs."""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class TableExtractor:
    """Service for extracting and parsing tables from document content."""
    
    def __init__(self):
        """Initialize table extractor."""
        logger.info("Table extractor initialized")
    
    def extract_tables(
        self,
        content: List[Tuple[str, float, Dict]]
    ) -> List[Dict[str, Any]]:
        """Extract tables from document content.
        
        Args:
            content: List of (chunk, score, metadata) tuples
            
        Returns:
            List of extracted tables
        """
        tables = []
        
        for chunk, score, metadata in content:
            # Look for table-like structures in text
            table_data = self._detect_table_in_text(chunk, metadata)
            if table_data:
                tables.append(table_data)
        
        logger.info(f"Extracted {len(tables)} tables from content")
        return tables
    
    def _detect_table_in_text(
        self,
        text: str,
        metadata: Dict
    ) -> Optional[Dict[str, Any]]:
        """Detect and extract table structure from text.
        
        Args:
            text: Text content
            metadata: Chunk metadata
            
        Returns:
            Table dictionary or None
        """
        # Look for patterns that indicate tables
        # Pattern 1: Multiple lines with consistent separators (|, tabs, multiple spaces)
        lines = text.split('\n')
        
        # Check if text has table-like structure
        if len(lines) < 3:
            return None
        
        # Look for separator patterns
        separator_patterns = [
            r'\s*\|\s*',  # Pipe separators
            r'\s{3,}',     # Multiple spaces
            r'\t+',        # Tabs
        ]
        
        table_rows = []
        header_found = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line contains table-like structure
            for pattern in separator_patterns:
                if re.search(pattern, line):
                    # Split by pattern
                    cells = re.split(pattern, line)
                    cells = [c.strip() for c in cells if c.strip()]
                    
                    if len(cells) >= 2:  # At least 2 columns
                        # First row might be header
                        if not header_found and len(table_rows) == 0:
                            table_rows.append({
                                "type": "header",
                                "cells": cells
                            })
                            header_found = True
                        else:
                            table_rows.append({
                                "type": "data",
                                "cells": cells
                            })
                        break
        
        if len(table_rows) >= 2:  # At least header + 1 data row
            return {
                "rows": table_rows,
                "column_count": len(table_rows[0]["cells"]) if table_rows else 0,
                "row_count": len(table_rows),
                "page": metadata.get("page") or metadata.get("page_number"),
                "source": metadata.get("source", ""),
                "metadata": metadata
            }
        
        return None
    
    def parse_financial_table(
        self,
        table: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Parse a financial table into structured data.
        
        Args:
            table: Table dictionary
            
        Returns:
            Parsed financial data dictionary
        """
        if not table or "rows" not in table:
            return None
        
        rows = table["rows"]
        if len(rows) < 2:
            return None
        
        # Extract header
        header_row = rows[0] if rows[0]["type"] == "header" else None
        if not header_row:
            return None
        
        headers = header_row["cells"]
        
        # Look for financial metrics in headers
        financial_metrics = []
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if any(keyword in header_lower for keyword in [
                "revenue", "sales", "ebitda", "profit", "income",
                "margin", "growth", "capex", "opex", "cash"
            ]):
                financial_metrics.append({
                    "column_index": i,
                    "metric_name": header,
                    "values": []
                })
        
        # Extract values from data rows
        data_rows = [r for r in rows if r["type"] == "data"]
        periods = []
        
        for row in data_rows:
            cells = row["cells"]
            if len(cells) != len(headers):
                continue
            
            # First column might be period identifier
            period = cells[0] if cells else None
            
            # Extract values for each financial metric
            for metric in financial_metrics:
                col_idx = metric["column_index"]
                if col_idx < len(cells):
                    value_str = cells[col_idx]
                    # Try to parse as number
                    value = self._parse_table_value(value_str)
                    if value is not None:
                        metric["values"].append({
                            "period": period,
                            "value": value,
                            "raw_text": value_str
                        })
            
            if period:
                periods.append(period)
        
        return {
            "table_type": "financial",
            "headers": headers,
            "periods": periods,
            "metrics": financial_metrics,
            "source": table.get("source", ""),
            "page": table.get("page")
        }
    
    def _parse_table_value(self, value_str: str) -> Optional[float]:
        """Parse a table cell value to number.
        
        Args:
            value_str: String value from table cell
            
        Returns:
            Parsed number or None
        """
        if not value_str:
            return None
        
        # Remove common formatting
        value_str = value_str.strip()
        value_str = value_str.replace(',', '')
        value_str = value_str.replace('(', '-').replace(')', '')  # Negative in parentheses
        
        # Remove currency symbols
        value_str = re.sub(r'[€$£¥]', '', value_str)
        
        # Check for units (B, M, K)
        multiplier = 1.0
        if 'B' in value_str.upper() or 'billion' in value_str.lower():
            multiplier = 1e9
            value_str = re.sub(r'[Bb]illion?', '', value_str, flags=re.IGNORECASE)
        elif 'M' in value_str.upper() or 'million' in value_str.lower():
            multiplier = 1e6
            value_str = re.sub(r'[Mm]illion?', '', value_str, flags=re.IGNORECASE)
        elif 'K' in value_str.upper() or 'thousand' in value_str.lower():
            multiplier = 1e3
            value_str = re.sub(r'[Kk]|thousand', '', value_str, flags=re.IGNORECASE)
        
        # Remove percentage sign
        is_percentage = '%' in value_str
        value_str = value_str.replace('%', '')
        
        try:
            value = float(value_str) * multiplier
            if is_percentage:
                return value  # Keep as percentage value
            return value / 1e6  # Convert to millions for consistency
        except ValueError:
            return None




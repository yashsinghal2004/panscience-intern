"""Numeric parser service for robust extraction and normalization of numeric values."""

import logging
import re
from typing import Optional, Tuple, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class Unit(Enum):
    """Numeric unit types."""
    BILLION = ("B", "billion", "bn", 1e9)
    MILLION = ("M", "million", "mn", 1e6)
    THOUSAND = ("K", "thousand", "k", 1e3)
    HUNDRED = ("H", "hundred", 1e2)
    BASE = ("", "", 1)


class Currency(Enum):
    """Currency symbols."""
    EURO = ("€", "euro", "EUR")
    DOLLAR = ("$", "dollar", "USD")
    POUND = ("£", "pound", "GBP")
    YEN = ("¥", "yen", "JPY")


class NumericParser:
    """Service for parsing and normalizing numeric values from text."""
    
    def __init__(self):
        """Initialize numeric parser."""
        # Build regex patterns
        self.unit_patterns = self._build_unit_patterns()
        self.currency_patterns = self._build_currency_patterns()
        self.number_patterns = self._build_number_patterns()
        logger.info("Numeric parser initialized")
    
    def _build_unit_patterns(self) -> Dict[Unit, re.Pattern]:
        """Build regex patterns for unit detection."""
        patterns = {}
        for unit in Unit:
            if unit == Unit.BASE:
                continue
            # Create pattern for all unit variants
            variants = "|".join([re.escape(v) for v in unit.value[:-1]])
            patterns[unit] = re.compile(
                rf'\b({variants})\b',
                re.IGNORECASE
            )
        return patterns
    
    def _build_currency_patterns(self) -> Dict[Currency, re.Pattern]:
        """Build regex patterns for currency detection."""
        patterns = {}
        for currency in Currency:
            variants = "|".join([re.escape(v) for v in currency.value])
            patterns[currency] = re.compile(
                rf'({variants})',
                re.IGNORECASE
            )
        return patterns
    
    def _build_number_patterns(self) -> List[re.Pattern]:
        """Build regex patterns for number extraction."""
        patterns = [
            # Pattern 1: Currency symbol + number + unit (e.g., €2.5B, $100M)
            re.compile(
                r'[€$£¥]\s*([\d.,]+)\s*([BMK]?)\b',
                re.IGNORECASE
            ),
            # Pattern 2: Number + unit + currency (e.g., 2.5 billion €)
            re.compile(
                r'([\d.,]+)\s*([BMK]|billion|million|thousand)\s*([€$£¥]?)\b',
                re.IGNORECASE
            ),
            # Pattern 3: Number with parentheses for negatives (e.g., (2.5) = -2.5)
            re.compile(
                r'\(([\d.,]+)\)',
                re.IGNORECASE
            ),
            # Pattern 4: Number with commas and decimals (e.g., 1,234.56)
            re.compile(
                r'([\d,]+\.?\d*)',
                re.IGNORECASE
            ),
            # Pattern 5: Number with footnotes (e.g., 2.5B¹, 100M*)
            re.compile(
                r'([\d.,]+)\s*([BMK]?)\s*[¹²³*†‡]',
                re.IGNORECASE
            ),
        ]
        return patterns
    
    def parse_number(
        self,
        text: str,
        target_unit: Unit = Unit.MILLION,
        return_metadata: bool = False
    ) -> Optional[float]:
        """Parse a single number from text.
        
        Args:
            text: Input text containing number
            target_unit: Target unit for normalization (default: MILLION)
            return_metadata: Whether to return parsing metadata
            
        Returns:
            Parsed number in target unit, or None if not found
            If return_metadata=True, returns tuple (number, metadata)
        """
        if not text:
            return None
        
        text = text.strip()
        
        # Try each pattern
        for pattern in self.number_patterns:
            match = pattern.search(text)
            if match:
                try:
                    # Extract number part
                    number_str = match.group(1)
                    
                    # Remove commas
                    number_str = number_str.replace(',', '')
                    
                    # Check for negative in parentheses
                    is_negative = False
                    if '(' in text and ')' in text:
                        is_negative = True
                    
                    # Parse number
                    number = float(number_str)
                    if is_negative:
                        number = -number
                    
                    # Extract unit
                    unit = Unit.BASE
                    if len(match.groups()) > 1:
                        unit_str = match.group(2).upper() if match.lastindex >= 2 else ""
                        unit = self._parse_unit(unit_str)
                    
                    # Normalize to target unit
                    normalized = self._normalize_to_unit(number, unit, target_unit)
                    
                    # Extract currency if present
                    currency = self._extract_currency(text)
                    
                    metadata = {
                        'original_text': text,
                        'original_value': number,
                        'original_unit': unit.name,
                        'currency': currency.name if currency else None,
                        'is_negative': is_negative,
                        'normalized_value': normalized,
                        'target_unit': target_unit.name
                    }
                    
                    if return_metadata:
                        return (normalized, metadata)
                    return normalized
                    
                except (ValueError, IndexError) as e:
                    logger.debug(f"Error parsing number from '{text}': {e}")
                    continue
        
        # Log ambiguous parse
        logger.warning(f"Ambiguous numeric parse for: {text[:100]}")
        
        if return_metadata:
            return (None, {'original_text': text, 'error': 'ambiguous_parse'})
        return None
    
    def parse_all_numbers(
        self,
        text: str,
        target_unit: Unit = Unit.MILLION
    ) -> List[Tuple[float, Dict]]:
        """Parse all numbers from text.
        
        Args:
            text: Input text
            target_unit: Target unit for normalization
            
        Returns:
            List of tuples (normalized_value, metadata)
        """
        results = []
        
        # Split text into potential number-containing segments
        # Look for patterns that might contain numbers
        segments = re.split(r'[.;]\s+', text)
        
        for segment in segments:
            parsed = self.parse_number(segment, target_unit, return_metadata=True)
            if parsed and parsed[0] is not None:
                results.append(parsed)
        
        return results
    
    def _parse_unit(self, unit_str: str) -> Unit:
        """Parse unit string to Unit enum.
        
        Args:
            unit_str: Unit string (B, M, K, billion, million, etc.)
            
        Returns:
            Unit enum
        """
        if not unit_str:
            return Unit.BASE
        
        unit_str = unit_str.upper().strip()
        
        for unit in Unit:
            if unit == Unit.BASE:
                continue
            if unit_str in [v.upper() for v in unit.value[:-1]]:
                return unit
        
        return Unit.BASE
    
    def _normalize_to_unit(
        self,
        value: float,
        source_unit: Unit,
        target_unit: Unit
    ) -> float:
        """Normalize value from source unit to target unit.
        
        Args:
            value: Numeric value
            source_unit: Source unit
            target_unit: Target unit
            
        Returns:
            Normalized value
        """
        # Convert to base units first
        source_multiplier = source_unit.value[-1]
        target_multiplier = target_unit.value[-1]
        
        base_value = value * source_multiplier
        normalized = base_value / target_multiplier
        
        return normalized
    
    def _extract_currency(self, text: str) -> Optional[Currency]:
        """Extract currency from text.
        
        Args:
            text: Input text
            
        Returns:
            Currency enum or None
        """
        for currency, pattern in self.currency_patterns.items():
            if pattern.search(text):
                return currency
        return None
    
    def normalize_number_string(
        self,
        value: str,
        target_unit: Unit = Unit.MILLION
    ) -> Optional[float]:
        """Normalize a number string (e.g., "2.5B", "100M", "50K").
        
        Args:
            value: Number string
            target_unit: Target unit for normalization
            
        Returns:
            Normalized numeric value
        """
        return self.parse_number(value, target_unit)
    
    def format_number(
        self,
        value: float,
        unit: Unit = Unit.MILLION,
        currency: Optional[Currency] = None,
        decimals: int = 2
    ) -> str:
        """Format a number for display.
        
        Args:
            value: Numeric value
            unit: Unit to display
            currency: Optional currency symbol
            decimals: Number of decimal places
            
        Returns:
            Formatted string
        """
        currency_str = currency.value[0] if currency else ""
        unit_str = unit.value[0] if unit != Unit.BASE else ""
        
        formatted = f"{value:,.{decimals}f}"
        if unit_str:
            formatted += unit_str
        
        if currency_str:
            formatted = f"{currency_str}{formatted}"
        
        return formatted







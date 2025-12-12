"""Financial ratio calculator service for comprehensive financial analysis."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FinancialRatioCalculator:
    """Service for calculating financial ratios from extracted KPIs."""
    
    def __init__(self):
        """Initialize financial ratio calculator."""
        logger.info("Financial ratio calculator initialized")
    
    def calculate_ratios(
        self,
        kpis: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive financial ratios from KPIs.
        
        Args:
            kpis: Dictionary containing extracted KPIs
            market_data: Optional market data (market cap, share price, shares outstanding)
            
        Returns:
            Dictionary of calculated ratios
        """
        ratios = {
            "profitability": {},
            "liquidity": {},
            "leverage": {},
            "efficiency": {},
            "valuation": {},
            "growth": {}
        }
        
        try:
            # Extract key metrics
            revenues = self._extract_metric_values(kpis.get("revenue", []))
            ebitda_values = self._extract_metric_values(kpis.get("ebitda", []))
            profit_values = self._extract_metric_values(kpis.get("profit", []))
            margins = kpis.get("margins", {})
            growth = kpis.get("growth", {})
            capex = self._extract_metric_values(kpis.get("capex", []))
            opex = self._extract_metric_values(kpis.get("opex", []))
            
            # Profitability Ratios
            ratios["profitability"] = self._calculate_profitability_ratios(
                revenues, ebitda_values, profit_values, margins
            )
            
            # Growth Ratios
            ratios["growth"] = self._calculate_growth_ratios(
                revenues, ebitda_values, profit_values, growth
            )
            
            # Efficiency Ratios (if we have asset data)
            ratios["efficiency"] = self._calculate_efficiency_ratios(
                revenues, ebitda_values
            )
            
            # Valuation Ratios (if market data available)
            if market_data:
                ratios["valuation"] = self._calculate_valuation_ratios(
                    profit_values, market_data
                )
            
            logger.info(f"Calculated {sum(len(v) for v in ratios.values())} financial ratios")
            
        except Exception as e:
            logger.error(f"Error calculating financial ratios: {e}")
        
        return ratios
    
    def _extract_metric_values(self, metric_list: List[Dict]) -> List[float]:
        """Extract numeric values from metric list.
        
        Args:
            metric_list: List of metric dictionaries
            
        Returns:
            List of numeric values
        """
        values = []
        for metric in metric_list:
            if isinstance(metric, dict) and "value" in metric:
                try:
                    value = float(metric["value"])
                    values.append(value)
                except (ValueError, TypeError):
                    continue
        return values
    
    def _calculate_profitability_ratios(
        self,
        revenues: List[float],
        ebitda_values: List[float],
        profit_values: List[float],
        margins: Dict[str, List]
    ) -> Dict[str, Any]:
        """Calculate profitability ratios.
        
        Args:
            revenues: List of revenue values
            ebitda_values: List of EBITDA values
            profit_values: List of profit/net income values
            margins: Dictionary of margin data
            
        Returns:
            Dictionary of profitability ratios
        """
        ratios = {}
        
        # EBITDA Margin
        if ebitda_values and revenues:
            latest_ebitda = ebitda_values[-1] if ebitda_values else None
            latest_revenue = revenues[-1] if revenues else None
            if latest_ebitda and latest_revenue and latest_revenue > 0:
                ratios["ebitda_margin"] = {
                    "value": (latest_ebitda / latest_revenue) * 100,
                    "unit": "percentage",
                    "description": "EBITDA Margin = EBITDA / Revenue",
                    "interpretation": self._interpret_margin((latest_ebitda / latest_revenue) * 100, "EBITDA")
                }
        
        # Net Profit Margin
        if profit_values and revenues:
            latest_profit = profit_values[-1] if profit_values else None
            latest_revenue = revenues[-1] if revenues else None
            if latest_profit and latest_revenue and latest_revenue > 0:
                ratios["net_profit_margin"] = {
                    "value": (latest_profit / latest_revenue) * 100,
                    "unit": "percentage",
                    "description": "Net Profit Margin = Net Income / Revenue",
                    "interpretation": self._interpret_margin((latest_profit / latest_revenue) * 100, "Net Profit")
                }
        
        # Gross Margin (if available)
        gross_margins = margins.get("gross_margin", [])
        if gross_margins:
            latest_gross = gross_margins[-1].get("value") if isinstance(gross_margins[-1], dict) else None
            if latest_gross:
                ratios["gross_margin"] = {
                    "value": latest_gross,
                    "unit": "percentage",
                    "description": "Gross Margin",
                    "interpretation": self._interpret_margin(latest_gross, "Gross")
                }
        
        # Return on Revenue (ROR)
        if profit_values and revenues:
            latest_profit = profit_values[-1] if profit_values else None
            latest_revenue = revenues[-1] if revenues else None
            if latest_profit and latest_revenue and latest_revenue > 0:
                ratios["return_on_revenue"] = {
                    "value": (latest_profit / latest_revenue) * 100,
                    "unit": "percentage",
                    "description": "Return on Revenue = Net Income / Revenue"
                }
        
        return ratios
    
    def _calculate_growth_ratios(
        self,
        revenues: List[float],
        ebitda_values: List[float],
        profit_values: List[float],
        growth: Dict[str, List]
    ) -> Dict[str, Any]:
        """Calculate growth ratios.
        
        Args:
            revenues: List of revenue values
            ebitda_values: List of EBITDA values
            profit_values: List of profit values
            growth: Dictionary of growth data
            
        Returns:
            Dictionary of growth ratios
        """
        ratios = {}
        
        # Revenue Growth Rate (YoY if we have multiple periods)
        if len(revenues) >= 2:
            current_revenue = revenues[-1]
            previous_revenue = revenues[-2]
            if previous_revenue > 0:
                revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
                ratios["revenue_growth_rate"] = {
                    "value": revenue_growth,
                    "unit": "percentage",
                    "description": "Revenue Growth Rate (YoY)",
                    "interpretation": self._interpret_growth(revenue_growth)
                }
        
        # EBITDA Growth Rate
        if len(ebitda_values) >= 2:
            current_ebitda = ebitda_values[-1]
            previous_ebitda = ebitda_values[-2]
            if previous_ebitda > 0:
                ebitda_growth = ((current_ebitda - previous_ebitda) / previous_ebitda) * 100
                ratios["ebitda_growth_rate"] = {
                    "value": ebitda_growth,
                    "unit": "percentage",
                    "description": "EBITDA Growth Rate (YoY)",
                    "interpretation": self._interpret_growth(ebitda_growth)
                }
        
        # Profit Growth Rate
        if len(profit_values) >= 2:
            current_profit = profit_values[-1]
            previous_profit = profit_values[-2]
            if previous_profit > 0:
                profit_growth = ((current_profit - previous_profit) / previous_profit) * 100
                ratios["profit_growth_rate"] = {
                    "value": profit_growth,
                    "unit": "percentage",
                    "description": "Profit Growth Rate (YoY)",
                    "interpretation": self._interpret_growth(profit_growth)
                }
        
        # CAGR (Compound Annual Growth Rate) if we have 3+ periods
        if len(revenues) >= 3:
            first_revenue = revenues[0]
            last_revenue = revenues[-1]
            periods = len(revenues) - 1
            if first_revenue > 0 and periods > 0:
                cagr = (((last_revenue / first_revenue) ** (1 / periods)) - 1) * 100
                ratios["revenue_cagr"] = {
                    "value": cagr,
                    "unit": "percentage",
                    "description": f"Revenue CAGR over {periods} periods",
                    "interpretation": self._interpret_growth(cagr)
                }
        
        return ratios
    
    def _calculate_efficiency_ratios(
        self,
        revenues: List[float],
        ebitda_values: List[float]
    ) -> Dict[str, Any]:
        """Calculate efficiency ratios.
        
        Args:
            revenues: List of revenue values
            ebitda_values: List of EBITDA values
            
        Returns:
            Dictionary of efficiency ratios
        """
        ratios = {}
        
        # Revenue per Employee (if we had employee data)
        # This is a placeholder for when employee data is available
        
        # EBITDA to Revenue Ratio (already in profitability, but useful here too)
        if ebitda_values and revenues:
            latest_ebitda = ebitda_values[-1] if ebitda_values else None
            latest_revenue = revenues[-1] if revenues else None
            if latest_ebitda and latest_revenue and latest_revenue > 0:
                ratios["ebitda_to_revenue"] = {
                    "value": latest_ebitda / latest_revenue,
                    "unit": "ratio",
                    "description": "EBITDA to Revenue Ratio"
                }
        
        return ratios
    
    def _calculate_valuation_ratios(
        self,
        profit_values: List[float],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate valuation ratios.
        
        Args:
            profit_values: List of profit/net income values
            market_data: Market data dictionary (market_cap, share_price, shares_outstanding)
            
        Returns:
            Dictionary of valuation ratios
        """
        ratios = {}
        
        market_cap = market_data.get("market_cap")
        share_price = market_data.get("share_price")
        shares_outstanding = market_data.get("shares_outstanding")
        latest_profit = profit_values[-1] if profit_values else None
        
        # P/E Ratio (Price-to-Earnings)
        if market_cap and latest_profit and latest_profit > 0:
            pe_ratio = market_cap / latest_profit
            ratios["pe_ratio"] = {
                "value": pe_ratio,
                "unit": "ratio",
                "description": "Price-to-Earnings Ratio = Market Cap / Net Income",
                "interpretation": self._interpret_pe_ratio(pe_ratio)
            }
        
        # Earnings per Share (EPS)
        if latest_profit and shares_outstanding and shares_outstanding > 0:
            eps = latest_profit / shares_outstanding
            ratios["eps"] = {
                "value": eps,
                "unit": "currency_per_share",
                "description": "Earnings per Share = Net Income / Shares Outstanding"
            }
        
        return ratios
    
    def _interpret_margin(self, margin: float, margin_type: str) -> str:
        """Interpret margin value.
        
        Args:
            margin: Margin percentage
            margin_type: Type of margin (EBITDA, Gross, Net Profit)
            
        Returns:
            Interpretation string
        """
        if margin_type == "EBITDA":
            if margin > 20:
                return "Excellent - Strong operational efficiency"
            elif margin > 10:
                return "Good - Healthy operational margins"
            elif margin > 5:
                return "Moderate - Acceptable operational margins"
            else:
                return "Low - May indicate operational challenges"
        elif margin_type == "Net Profit":
            if margin > 15:
                return "Excellent - Very profitable"
            elif margin > 10:
                return "Good - Strong profitability"
            elif margin > 5:
                return "Moderate - Reasonable profitability"
            else:
                return "Low - Thin profit margins"
        else:
            if margin > 40:
                return "Excellent"
            elif margin > 30:
                return "Good"
            elif margin > 20:
                return "Moderate"
            else:
                return "Low"
    
    def _interpret_growth(self, growth_rate: float) -> str:
        """Interpret growth rate.
        
        Args:
            growth_rate: Growth percentage
            
        Returns:
            Interpretation string
        """
        if growth_rate > 20:
            return "Excellent - Strong growth trajectory"
        elif growth_rate > 10:
            return "Good - Healthy growth"
        elif growth_rate > 5:
            return "Moderate - Steady growth"
        elif growth_rate > 0:
            return "Slow - Minimal growth"
        else:
            return "Declining - Negative growth"
    
    def _interpret_pe_ratio(self, pe_ratio: float) -> str:
        """Interpret P/E ratio.
        
        Args:
            pe_ratio: Price-to-Earnings ratio
            
        Returns:
            Interpretation string
        """
        if pe_ratio < 10:
            return "Potentially undervalued or high risk"
        elif pe_ratio < 20:
            return "Reasonable valuation"
        elif pe_ratio < 30:
            return "Moderately overvalued"
        else:
            return "Potentially overvalued"
    
    def calculate_industry_benchmarks(
        self,
        ratios: Dict[str, Any],
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare ratios against industry benchmarks.
        
        Args:
            ratios: Calculated ratios
            industry: Industry name (optional)
            
        Returns:
            Dictionary with benchmark comparisons
        """
        # Placeholder for industry benchmark data
        # In production, this would query a database of industry benchmarks
        benchmarks = {
            "note": "Industry benchmarks require industry classification and benchmark database",
            "industry": industry
        }
        
        return benchmarks




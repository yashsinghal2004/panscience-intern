"""Data validation service for cross-checking and validating extracted financial data."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class DataValidator:
    """Service for validating and cross-checking extracted financial data."""
    
    def __init__(self):
        """Initialize data validator."""
        logger.info("Data validator initialized")
    
    def validate_kpis(
        self,
        kpis: Dict[str, Any],
        content: List[Tuple[str, float, Dict]]
    ) -> Dict[str, Any]:
        """Validate extracted KPIs for consistency and accuracy.
        
        Args:
            kpis: Dictionary of extracted KPIs
            content: Retrieved content chunks for cross-validation
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "consistency_score": 1.0,
            "validated_metrics": {},
            "cross_references": []
        }
        
        try:
            # Validate revenue data
            revenue_validation = self._validate_revenue(kpis.get("revenue", []), content)
            validation_results["validated_metrics"]["revenue"] = revenue_validation
            
            # Validate EBITDA data
            ebitda_validation = self._validate_ebitda(kpis.get("ebitda", []), content)
            validation_results["validated_metrics"]["ebitda"] = ebitda_validation
            
            # Validate profit data
            profit_validation = self._validate_profit(kpis.get("profit", []), content)
            validation_results["validated_metrics"]["profit"] = profit_validation
            
            # Cross-check relationships
            relationship_checks = self._check_relationships(kpis)
            validation_results["cross_references"] = relationship_checks
            
            # Check for contradictions
            contradictions = self._detect_contradictions(kpis, content)
            validation_results["errors"].extend(contradictions)
            
            # Check for missing expected data
            missing_data = self._check_missing_data(kpis)
            validation_results["warnings"].extend(missing_data)
            
            # Calculate consistency score
            validation_results["consistency_score"] = self._calculate_consistency_score(
                validation_results
            )
            
            # Overall validation status
            validation_results["is_valid"] = (
                len(validation_results["errors"]) == 0 and
                validation_results["consistency_score"] > 0.7
            )
            
            logger.info(
                f"Validation complete: {len(validation_results['errors'])} errors, "
                f"{len(validation_results['warnings'])} warnings, "
                f"consistency score: {validation_results['consistency_score']:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            validation_results["errors"].append(f"Validation error: {str(e)}")
            validation_results["is_valid"] = False
        
        return validation_results
    
    def _validate_revenue(
        self,
        revenue_list: List[Dict],
        content: List[Tuple[str, float, Dict]]
    ) -> Dict[str, Any]:
        """Validate revenue data.
        
        Args:
            revenue_list: List of revenue KPIs
            content: Content chunks for cross-reference
            
        Returns:
            Validation result dictionary
        """
        validation = {
            "count": len(revenue_list),
            "values": [],
            "periods": [],
            "warnings": [],
            "is_valid": True
        }
        
        if not revenue_list:
            validation["warnings"].append("No revenue data found")
            validation["is_valid"] = False
            return validation
        
        # Extract values and check for consistency
        seen_periods = set()
        for revenue in revenue_list:
            if not isinstance(revenue, dict):
                continue
            
            value = revenue.get("value")
            period = revenue.get("period")
            
            if value is None:
                validation["warnings"].append(f"Revenue entry missing value: {revenue}")
                continue
            
            if period:
                if period in seen_periods:
                    validation["warnings"].append(f"Duplicate period found: {period}")
                seen_periods.add(period)
            
            validation["values"].append(value)
            validation["periods"].append(period)
        
        # Check for reasonable values (revenue should be positive)
        negative_values = [v for v in validation["values"] if v < 0]
        if negative_values:
            validation["warnings"].append(f"Found {len(negative_values)} negative revenue values")
        
        return validation
    
    def _validate_ebitda(
        self,
        ebitda_list: List[Dict],
        content: List[Tuple[str, float, Dict]]
    ) -> Dict[str, Any]:
        """Validate EBITDA data.
        
        Args:
            ebitda_list: List of EBITDA KPIs
            content: Content chunks for cross-reference
            
        Returns:
            Validation result dictionary
        """
        validation = {
            "count": len(ebitda_list),
            "values": [],
            "periods": [],
            "warnings": [],
            "is_valid": True
        }
        
        if not ebitda_list:
            validation["warnings"].append("No EBITDA data found")
            return validation
        
        for ebitda in ebitda_list:
            if not isinstance(ebitda, dict):
                continue
            
            value = ebitda.get("value")
            period = ebitda.get("period")
            
            if value is None:
                validation["warnings"].append(f"EBITDA entry missing value: {ebitda}")
                continue
            
            validation["values"].append(value)
            validation["periods"].append(period)
        
        return validation
    
    def _validate_profit(
        self,
        profit_list: List[Dict],
        content: List[Tuple[str, float, Dict]]
    ) -> Dict[str, Any]:
        """Validate profit/net income data.
        
        Args:
            profit_list: List of profit KPIs
            content: Content chunks for cross-reference
            
        Returns:
            Validation result dictionary
        """
        validation = {
            "count": len(profit_list),
            "values": [],
            "periods": [],
            "warnings": [],
            "is_valid": True
        }
        
        if not profit_list:
            validation["warnings"].append("No profit data found")
            return validation
        
        for profit in profit_list:
            if not isinstance(profit, dict):
                continue
            
            value = profit.get("value")
            period = profit.get("period")
            
            if value is None:
                validation["warnings"].append(f"Profit entry missing value: {profit}")
                continue
            
            validation["values"].append(value)
            validation["periods"].append(period)
        
        return validation
    
    def _check_relationships(
        self,
        kpis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check relationships between different KPIs.
        
        Args:
            kpis: Dictionary of KPIs
            
        Returns:
            List of relationship check results
        """
        checks = []
        
        revenues = kpis.get("revenue", [])
        ebitda_list = kpis.get("ebitda", [])
        profit_list = kpis.get("profit", [])
        
        # Check: EBITDA should generally be less than Revenue
        if revenues and ebitda_list:
            latest_revenue = revenues[-1].get("value") if revenues else None
            latest_ebitda = ebitda_list[-1].get("value") if ebitda_list else None
            
            if latest_revenue and latest_ebitda:
                if latest_ebitda > latest_revenue:
                    checks.append({
                        "type": "relationship_check",
                        "metric": "EBITDA vs Revenue",
                        "status": "warning",
                        "message": f"EBITDA ({latest_ebitda}) exceeds Revenue ({latest_revenue}) - unusual but possible",
                        "value1": latest_ebitda,
                        "value2": latest_revenue
                    })
                elif latest_ebitda < 0 and latest_revenue > 0:
                    checks.append({
                        "type": "relationship_check",
                        "metric": "EBITDA vs Revenue",
                        "status": "warning",
                        "message": "Negative EBITDA with positive Revenue - may indicate operational issues",
                        "value1": latest_ebitda,
                        "value2": latest_revenue
                    })
        
        # Check: Profit should generally be less than EBITDA
        if ebitda_list and profit_list:
            latest_ebitda = ebitda_list[-1].get("value") if ebitda_list else None
            latest_profit = profit_list[-1].get("value") if profit_list else None
            
            if latest_ebitda and latest_profit:
                if latest_profit > latest_ebitda:
                    checks.append({
                        "type": "relationship_check",
                        "metric": "Profit vs EBITDA",
                        "status": "info",
                        "message": f"Profit ({latest_profit}) exceeds EBITDA ({latest_ebitda}) - unusual but possible with non-operating income",
                        "value1": latest_profit,
                        "value2": latest_ebitda
                    })
        
        # Check margins consistency
        margins = kpis.get("margins", {})
        if margins:
            ebitda_margins = margins.get("ebitda_margin", [])
            if ebitda_margins and revenues and ebitda_list:
                latest_revenue = revenues[-1].get("value") if revenues else None
                latest_ebitda = ebitda_list[-1].get("value") if ebitda_list else None
                latest_margin = ebitda_margins[-1].get("value") if ebitda_margins else None
                
                if latest_revenue and latest_ebitda and latest_margin:
                    calculated_margin = (latest_ebitda / latest_revenue) * 100 if latest_revenue > 0 else 0
                    margin_diff = abs(calculated_margin - latest_margin)
                    
                    if margin_diff > 5:  # More than 5% difference
                        checks.append({
                            "type": "consistency_check",
                            "metric": "EBITDA Margin",
                            "status": "warning",
                            "message": f"Calculated margin ({calculated_margin:.2f}%) differs from reported margin ({latest_margin:.2f}%)",
                            "calculated": calculated_margin,
                            "reported": latest_margin,
                            "difference": margin_diff
                        })
        
        return checks
    
    def _detect_contradictions(
        self,
        kpis: Dict[str, Any],
        content: List[Tuple[str, float, Dict]]
    ) -> List[Dict[str, Any]]:
        """Detect contradictions in extracted data.
        
        Args:
            kpis: Dictionary of KPIs
            content: Content chunks
            
        Returns:
            List of detected contradictions
        """
        contradictions = []
        
        # Check for duplicate periods with different values
        revenue_by_period = defaultdict(list)
        for revenue in kpis.get("revenue", []):
            if isinstance(revenue, dict):
                period = revenue.get("period")
                value = revenue.get("value")
                if period and value is not None:
                    revenue_by_period[period].append(value)
        
        for period, values in revenue_by_period.items():
            if len(values) > 1:
                unique_values = set(values)
                if len(unique_values) > 1:
                    max_diff = max(values) - min(values)
                    if max_diff > max(values) * 0.1:  # More than 10% difference
                        contradictions.append({
                            "type": "contradiction",
                            "metric": "revenue",
                            "period": period,
                            "values": values,
                            "message": f"Contradicting revenue values for {period}: {values}",
                            "severity": "high" if max_diff > max(values) * 0.2 else "medium"
                        })
        
        # Similar check for EBITDA
        ebitda_by_period = defaultdict(list)
        for ebitda in kpis.get("ebitda", []):
            if isinstance(ebitda, dict):
                period = ebitda.get("period")
                value = ebitda.get("value")
                if period and value is not None:
                    ebitda_by_period[period].append(value)
        
        for period, values in ebitda_by_period.items():
            if len(values) > 1:
                unique_values = set(values)
                if len(unique_values) > 1:
                    max_diff = max(values) - min(values)
                    if max_diff > max(values) * 0.1:
                        contradictions.append({
                            "type": "contradiction",
                            "metric": "ebitda",
                            "period": period,
                            "values": values,
                            "message": f"Contradicting EBITDA values for {period}: {values}",
                            "severity": "high" if max_diff > max(values) * 0.2 else "medium"
                        })
        
        return contradictions
    
    def _check_missing_data(
        self,
        kpis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for missing expected data.
        
        Args:
            kpis: Dictionary of KPIs
            
        Returns:
            List of missing data warnings
        """
        warnings = []
        
        # Check if we have revenue but no profit
        if kpis.get("revenue") and not kpis.get("profit"):
            warnings.append({
                "type": "missing_data",
                "metric": "profit",
                "message": "Revenue data found but no profit/net income data",
                "severity": "medium"
            })
        
        # Check if we have revenue but no EBITDA
        if kpis.get("revenue") and not kpis.get("ebitda"):
            warnings.append({
                "type": "missing_data",
                "metric": "ebitda",
                "message": "Revenue data found but no EBITDA data",
                "severity": "low"
            })
        
        # Check if we have margins but no corresponding base metrics
        margins = kpis.get("margins", {})
        if margins.get("ebitda_margin") and not kpis.get("ebitda"):
            warnings.append({
                "type": "missing_data",
                "metric": "ebitda",
                "message": "EBITDA margin found but no EBITDA value",
                "severity": "medium"
            })
        
        return warnings
    
    def _calculate_consistency_score(
        self,
        validation_results: Dict[str, Any]
    ) -> float:
        """Calculate overall consistency score.
        
        Args:
            validation_results: Validation results dictionary
            
        Returns:
            Consistency score between 0 and 1
        """
        score = 1.0
        
        # Deduct for errors
        error_count = len(validation_results.get("errors", []))
        score -= error_count * 0.2
        
        # Deduct for warnings
        warning_count = len(validation_results.get("warnings", []))
        score -= warning_count * 0.05
        
        # Deduct for cross-reference issues
        cross_ref_issues = [
            ref for ref in validation_results.get("cross_references", [])
            if ref.get("status") in ["warning", "error"]
        ]
        score -= len(cross_ref_issues) * 0.1
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return score




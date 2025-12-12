"""Business insights service for extracting business intelligence from queries and documents."""

import logging
import re
from typing import List, Dict, Optional
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.database import Query, Document, get_db

logger = logging.getLogger(__name__)


class BusinessInsightsService:
    """Service for extracting business insights from queries and documents."""
    
    # Business category keywords
    CATEGORY_KEYWORDS = {
        "Financial": ["revenue", "profit", "loss", "cost", "price", "financial", "earnings", "income", "budget", "expense", "growth", "million", "billion", "€", "$", "%"],
        "Operations": ["production", "manufacturing", "operation", "process", "efficiency", "capacity", "supply chain", "logistics"],
        "Sales & Marketing": ["sales", "marketing", "customer", "market", "brand", "advertising", "campaign", "revenue", "market share"],
        "Human Resources": ["employee", "staff", "workforce", "hiring", "training", "personnel", "headcount"],
        "Strategy": ["strategy", "plan", "goal", "objective", "vision", "mission", "roadmap", "initiative"],
        "Technology": ["technology", "digital", "innovation", "IT", "software", "system", "platform", "automation"],
        "Risk & Compliance": ["risk", "compliance", "regulation", "legal", "audit", "security", "governance"]
    }
    
    # Business metric patterns
    METRIC_PATTERNS = {
        "revenue": r"(?:revenue|sales|income).*?(?:€|\$|million|billion|thousand)[\s\d.,]+",
        "growth": r"(?:growth|increase|decrease|change).*?\d+\.?\d*\s*%",
        "profit": r"(?:profit|margin|earnings).*?(?:€|\$|million|billion|thousand)[\s\d.,]+",
        "customers": r"(?:\d+[\s,]*)?(?:customers|clients|users|contracts)",
        "employees": r"(?:\d+[\s,]*)?(?:employees|staff|workforce|personnel)"
    }
    
    def categorize_query(self, query_text: str) -> str:
        """Categorize a query into business categories.
        
        Args:
            query_text: The query text
            
        Returns:
            Category name
        """
        query_lower = query_text.lower()
        category_scores = defaultdict(int)
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    category_scores[category] += 1
        
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return "General"
    
    def extract_topics(self, queries: List[str], answers: List[str]) -> List[Dict]:
        """Extract topics from queries and answers.
        
        Args:
            queries: List of query texts
            answers: List of answer texts
            
        Returns:
            List of topics with counts
        """
        # Combine queries and answers
        all_text = " ".join(queries + answers).lower()
        
        # Extract common business terms
        business_terms = [
            "revenue", "growth", "profit", "sales", "market", "customer", 
            "product", "service", "strategy", "financial", "operation",
            "technology", "innovation", "competition", "performance",
            "efficiency", "quality", "brand", "marketing", "investment"
        ]
        
        topic_counts = Counter()
        for term in business_terms:
            count = all_text.count(term)
            if count > 0:
                topic_counts[term] = count
        
        # Also extract from query patterns
        for query in queries:
            words = query.lower().split()
            # Extract key nouns/phrases (simple heuristic)
            for i, word in enumerate(words):
                if len(word) > 5 and word not in ["what", "which", "where", "when", "about", "question"]:
                    topic_counts[word] += 1
        
        # Return top topics
        return [
            {"topic": topic, "count": count}
            for topic, count in topic_counts.most_common(10)
        ]
    
    def extract_business_metrics(self, answers: List[str]) -> Dict:
        """Extract business metrics from answers.
        
        Args:
            answers: List of answer texts
            
        Returns:
            Dictionary of extracted metrics
        """
        metrics = {
            "revenue_mentions": 0,
            "growth_mentions": 0,
            "profit_mentions": 0,
            "customer_mentions": 0,
            "employee_mentions": 0,
            "key_numbers": []
        }
        
        combined_text = " ".join(answers)
        
        # Count metric mentions
        for answer in answers:
            answer_lower = answer.lower()
            if re.search(self.METRIC_PATTERNS["revenue"], answer_lower, re.IGNORECASE):
                metrics["revenue_mentions"] += 1
            if re.search(self.METRIC_PATTERNS["growth"], answer_lower, re.IGNORECASE):
                metrics["growth_mentions"] += 1
            if re.search(self.METRIC_PATTERNS["profit"], answer_lower, re.IGNORECASE):
                metrics["profit_mentions"] += 1
            if re.search(self.METRIC_PATTERNS["customers"], answer_lower, re.IGNORECASE):
                metrics["customer_mentions"] += 1
            if re.search(self.METRIC_PATTERNS["employees"], answer_lower, re.IGNORECASE):
                metrics["employee_mentions"] += 1
        
        # Extract key numbers (percentages, large numbers)
        numbers = re.findall(r'\d+\.?\d*\s*%', combined_text)
        metrics["key_numbers"] = numbers[:10]  # Top 10 numbers
        
        return metrics
    
    def get_query_categories(self, days: int = 30) -> List[Dict]:
        """Get query category distribution.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of categories with counts
        """
        try:
            with get_db() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                queries = db.query(Query.query_text).filter(
                    Query.created_at >= cutoff_date,
                    Query.success == True
                ).all()
                
                categories = Counter()
                for (query_text,) in queries:
                    category = self.categorize_query(query_text)
                    categories[category] += 1
                
                return [
                    {"category": cat, "count": count}
                    for cat, count in categories.most_common()
                ]
        except Exception as e:
            logger.error(f"Error getting query categories: {e}")
            return []
    
    def get_business_topics(self, days: int = 30) -> List[Dict]:
        """Get business topics from queries and answers.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of topics with counts
        """
        try:
            with get_db() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                queries_data = db.query(Query.query_text, Query.answer).filter(
                    Query.created_at >= cutoff_date,
                    Query.success == True,
                    Query.answer.isnot(None)
                ).all()
                
                queries = [q[0] for q in queries_data]
                answers = [q[1] for q in queries_data if q[1]]
                
                return self.extract_topics(queries, answers)
        except Exception as e:
            logger.error(f"Error getting business topics: {e}")
            return []
    
    def get_business_metrics_summary(self, days: int = 30) -> Dict:
        """Get business metrics summary.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary of business metrics
        """
        try:
            with get_db() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                answers = db.query(Query.answer).filter(
                    Query.created_at >= cutoff_date,
                    Query.success == True,
                    Query.answer.isnot(None)
                ).all()
                
                answer_texts = [a[0] for a in answers]
                return self.extract_business_metrics(answer_texts)
        except Exception as e:
            logger.error(f"Error getting business metrics: {e}")
            return {}
    
    def extract_numerical_data(self, answers: List[str]) -> Dict:
        """Extract actual numerical values from answers for visualization.
        
        Args:
            answers: List of answer texts
            
        Returns:
            Dictionary with extracted numerical data organized by metric type
        """
        numerical_data = {
            "ebitda": [],
            "revenue": [],
            "profit": [],
            "growth_percentages": [],
            "margins": [],
            "financial_figures": [],
            "percentages": [],
            "employee_counts": [],
            "customer_counts": []
        }
        
        combined_text = " ".join(answers)
        
        # Extract EBITDA values (e.g., "€2.5 billion", "Euro 2.7 billion")
        ebitda_patterns = [
            r"ebitda.*?(?:€|euro|\$)\s*([\d.,]+)\s*(?:billion|million|thousand)",
            r"ebitda.*?([\d.,]+)\s*(?:billion|million|thousand)",
            r"ebitda.*?(?:between|to|of)\s*(?:€|euro|\$)?\s*([\d.,]+)\s*(?:and|to)\s*(?:€|euro|\$)?\s*([\d.,]+)\s*(?:billion|million)"
        ]
        
        for pattern in ebitda_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()
                    values = [v.replace(',', '') for v in groups if v is not None and v.strip()]
                    for val in values:
                        try:
                            num_val = float(val)
                            match_text = match.group(0).lower()
                            if 'billion' in match_text:
                                num_val *= 1000  # Convert to millions for consistency
                            numerical_data["ebitda"].append({
                                "value": num_val,
                                "unit": "million",
                                "text": match.group(0)
                            })
                        except (ValueError, AttributeError):
                            pass
                except (AttributeError, IndexError):
                    pass
        
        # Extract Revenue values
        revenue_patterns = [
            r"revenue.*?(?:€|euro|\$)\s*([\d.,]+)\s*(?:billion|million|thousand)",
            r"revenue.*?([\d.,]+)\s*(?:billion|million|thousand)",
            r"sales.*?(?:€|euro|\$)\s*([\d.,]+)\s*(?:billion|million|thousand)"
        ]
        
        for pattern in revenue_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                try:
                    if match.groups() and match.group(1):
                        val = match.group(1).replace(',', '')
                        num_val = float(val)
                        match_text = match.group(0).lower()
                        if 'billion' in match_text:
                            num_val *= 1000
                        numerical_data["revenue"].append({
                            "value": num_val,
                            "unit": "million",
                            "text": match.group(0)
                        })
                except (ValueError, AttributeError, IndexError):
                    pass
        
        # Extract percentages (growth rates, margins)
        percentage_patterns = [
            r"(\d+\.?\d*)\s*%",  # Simple percentage
            r"(?:growth|increase|decrease|margin|rate).*?(\d+\.?\d*)\s*%",
            r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*%"  # Range like "38%-40%"
        ]
        
        for pattern in percentage_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()
                    if groups and len(groups) == 2 and groups[0] and groups[1]:  # Range
                        try:
                            val1 = float(match.group(1))
                            val2 = float(match.group(2))
                            numerical_data["percentages"].append({
                                "value": (val1 + val2) / 2,  # Average
                                "range": [val1, val2],
                                "text": match.group(0)
                            })
                        except (ValueError, AttributeError):
                            pass
                    elif groups and groups[0]:
                        try:
                            val = float(match.group(1))
                            context = match.group(0).lower()
                            if 'margin' in context or 'ebitda margin' in context:
                                numerical_data["margins"].append({
                                    "value": val,
                                    "text": match.group(0)
                                })
                            elif 'growth' in context or 'increase' in context or 'decrease' in context:
                                numerical_data["growth_percentages"].append({
                                    "value": val,
                                    "text": match.group(0)
                                })
                            else:
                                numerical_data["percentages"].append({
                                    "value": val,
                                    "text": match.group(0)
                                })
                        except (ValueError, AttributeError, IndexError):
                            pass
                except (AttributeError, IndexError):
                    pass
        
        # Extract profit/earnings
        profit_patterns = [
            r"(?:profit|earnings|ebit).*?(?:€|euro|\$)\s*([\d.,]+)\s*(?:billion|million|thousand)",
            r"(?:profit|earnings|ebit).*?([\d.,]+)\s*(?:billion|million|thousand)"
        ]
        
        for pattern in profit_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                try:
                    if match.groups() and match.group(1):
                        val = match.group(1).replace(',', '')
                        num_val = float(val)
                        match_text = match.group(0).lower()
                        if 'billion' in match_text:
                            num_val *= 1000
                        numerical_data["profit"].append({
                            "value": num_val,
                            "unit": "million",
                            "text": match.group(0)
                        })
                except (ValueError, AttributeError, IndexError):
                    pass
        
        # Extract employee counts
        employee_patterns = [
            r"(\d+[\d,]*)\s*(?:employees|staff|workforce|personnel)",
            r"(?:employees|staff|workforce).*?(\d+[\d,]*)"
        ]
        
        for pattern in employee_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                try:
                    if match.groups() and match.group(1):
                        val = match.group(1).replace(',', '')
                        numerical_data["employee_counts"].append({
                            "value": int(float(val)),
                            "text": match.group(0)
                        })
                except (ValueError, AttributeError, IndexError):
                    pass
        
        # Extract customer counts
        customer_patterns = [
            r"(\d+[\d,]*)\s*(?:customers|clients|users|contracts)",
            r"(?:customers|clients|users|contracts).*?(\d+[\d,]*)"
        ]
        
        for pattern in customer_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                try:
                    if match.groups() and match.group(1):
                        val = match.group(1).replace(',', '')
                        numerical_data["customer_counts"].append({
                            "value": int(float(val)),
                            "text": match.group(0)
                        })
                except (ValueError, AttributeError, IndexError):
                    pass
        
        return numerical_data
    
    def get_numerical_data(self, days: int = 30) -> Dict:
        """Get numerical data extracted from answers.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with numerical data organized by metric type
        """
        try:
            with get_db() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                answers = db.query(Query.answer).filter(
                    Query.created_at >= cutoff_date,
                    Query.success == True,
                    Query.answer.isnot(None)
                ).all()
                
                answer_texts = [a[0] for a in answers]
                return self.extract_numerical_data(answer_texts)
        except Exception as e:
            logger.error(f"Error getting numerical data: {e}")
            return {}
    
    def get_key_insights(self, days: int = 30) -> List[str]:
        """Generate key business insights.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of insight strings
        """
        insights = []
        
        try:
            # Get analytics
            from app.services.analytics import AnalyticsService
            analytics_service = AnalyticsService()
            analytics = analytics_service.get_analytics(days=days)
            
            # Get categories
            categories = self.get_query_categories(days=days)
            
            # Get metrics
            metrics = self.get_business_metrics_summary(days=days)
            
            # Generate insights
            if analytics.get("total_queries", 0) > 0:
                insights.append(f"Total of {analytics['total_queries']} queries analyzed in the last {days} days")
            
            if categories:
                top_category = categories[0]
                insights.append(f"Most analyzed category: {top_category['category']} ({top_category['count']} queries)")
            
            if metrics.get("growth_mentions", 0) > 0:
                insights.append(f"Growth metrics mentioned {metrics['growth_mentions']} times in answers")
            
            if metrics.get("revenue_mentions", 0) > 0:
                insights.append(f"Revenue discussed in {metrics['revenue_mentions']} responses")
            
            if analytics.get("success_rate", 0) > 80:
                insights.append(f"High query success rate: {analytics['success_rate']:.1f}%")
            
            # Document coverage
            documents = analytics_service.get_documents()
            if documents:
                total_chunks = sum(d.get("chunks_count", 0) for d in documents)
                insights.append(f"Knowledge base contains {len(documents)} documents with {total_chunks} total chunks")
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights[:5]  # Return top 5 insights


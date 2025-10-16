import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class ValidationManager:
    """
    Validation manager for checking task completion quality and data integrity.
    """
    
    def __init__(self):
        self.validation_history = []
        self.quality_thresholds = {
            "min_response_length": 50,
            "required_data_fields": ["revenue", "net_income", "total_assets"],
            "min_confidence_score": 0.7
        }
    
    def validate_task_result(self, task_description: str, task_result: str, task_data: Optional[Dict] = None) -> Tuple[bool, str, float]:
        """
        Comprehensive validation of a task result.
        
        Returns:
            - bool: Whether the task is valid
            - str: Reason for validation result
            - float: Confidence score (0-1)
        """
        validation_checks = []
        
        # Check 1: Response completeness
        completeness_score, completeness_reason = self._check_completeness(task_result)
        validation_checks.append(("completeness", completeness_score, completeness_reason))
        
        # Check 2: Data relevance
        relevance_score, relevance_reason = self._check_relevance(task_description, task_result)
        validation_checks.append(("relevance", relevance_score, relevance_reason))
        
        # Check 3: Data quality (if data is provided)
        if task_data:
            data_quality_score, data_quality_reason = self._check_data_quality(task_data)
            validation_checks.append(("data_quality", data_quality_score, data_quality_reason))
        
        # Check 4: Quantitative analysis presence
        quant_score, quant_reason = self._check_quantitative_analysis(task_result)
        validation_checks.append(("quantitative", quant_score, quant_reason))
        
        # Check 5: Logical consistency
        logic_score, logic_reason = self._check_logical_consistency(task_result)
        validation_checks.append(("logic", logic_score, logic_reason))
        
        # Calculate overall score and determine validity
        overall_score = sum(score for _, score, _ in validation_checks) / len(validation_checks)
        is_valid = overall_score >= self.quality_thresholds["min_confidence_score"]
        
        # Compile reason
        failed_checks = [f"{name}: {reason}" for name, score, reason in validation_checks if score < 0.6]
        if failed_checks:
            reason = f"Validation failed on: {'; '.join(failed_checks)}"
        else:
            reason = "Task completed successfully with adequate quality"
        
        # Record validation
        self._record_validation(task_description, task_result, is_valid, overall_score, validation_checks)
        
        return is_valid, reason, overall_score
    
    def _check_completeness(self, result: str) -> Tuple[float, str]:
        """
        Check if the result is complete and substantial.
        """
        if not result or len(result.strip()) < self.quality_thresholds["min_response_length"]:
            return 0.2, f"Response too short (< {self.quality_thresholds['min_response_length']} chars)"
        
        # Check for key indicators of complete analysis
        indicators = [
            r'\$[\d,]+',  # Dollar amounts
            r'\d+\.?\d*%',  # Percentages
            r'\d{4}',  # Years
            r'(increase|decrease|growth|decline)',  # Trend words
            r'(revenue|profit|margin|assets|equity)',  # Financial terms
        ]
        
        matches = sum(1 for pattern in indicators if re.search(pattern, result, re.IGNORECASE))
        completeness_score = min(1.0, matches / 3)  # Need at least 3 indicators for full score
        
        if completeness_score < 0.6:
            return completeness_score, "Missing key financial indicators or analysis depth"
        
        return completeness_score, "Response appears complete with financial analysis"
    
    def _check_relevance(self, task_description: str, result: str) -> Tuple[float, str]:
        """
        Check if the result is relevant to the task description.
        """
        # Extract key terms from task description
        task_keywords = set(re.findall(r'\b\w+\b', task_description.lower()))
        result_keywords = set(re.findall(r'\b\w+\b', result.lower()))
        
        # Remove common words
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were'}
        task_keywords -= common_words
        result_keywords -= common_words
        
        if not task_keywords:
            return 0.8, "Unable to extract keywords from task description"
        
        # Calculate overlap
        overlap = len(task_keywords.intersection(result_keywords))
        relevance_score = min(1.0, overlap / len(task_keywords))
        
        if relevance_score < 0.4:
            return relevance_score, "Result does not address key terms from the task"
        
        return relevance_score, "Result addresses relevant aspects of the task"
    
    def _check_data_quality(self, data: Dict) -> Tuple[float, str]:
        """
        Check the quality and completeness of financial data.
        """
        if not data:
            return 0.3, "No data provided"
        
        quality_indicators = []
        
        # Check for error messages
        if any("error" in str(v).lower() for v in data.values()):
            quality_indicators.append(("errors_present", 0.2))
        else:
            quality_indicators.append(("no_errors", 1.0))
        
        # Check for required financial fields
        required_fields_found = 0
        total_required = len(self.quality_thresholds["required_data_fields"])
        
        for field in self.quality_thresholds["required_data_fields"]:
            if self._find_field_in_data(data, field):
                required_fields_found += 1
        
        field_score = required_fields_found / total_required if total_required > 0 else 1.0
        quality_indicators.append(("required_fields", field_score))
        
        # Check data freshness (recent timestamps)
        has_recent_data = self._check_data_freshness(data)
        quality_indicators.append(("freshness", 1.0 if has_recent_data else 0.7))
        
        # Calculate overall data quality score
        overall_score = sum(score for _, score in quality_indicators) / len(quality_indicators)
        
        if overall_score < 0.6:
            return overall_score, "Data quality issues detected"
        
        return overall_score, "Data quality appears adequate"
    
    def _check_quantitative_analysis(self, result: str) -> Tuple[float, str]:
        """
        Check if the result contains quantitative analysis.
        """
        # Look for quantitative indicators
        quant_patterns = [
            r'\$[\d,]+\.?\d*[MBK]?',  # Dollar amounts with suffixes
            r'\d+\.?\d*%',  # Percentages
            r'\d+\.?\d*x',  # Multiples (e.g., "2.5x")
            r'ratio.*?\d+\.?\d*',  # Ratios with numbers
            r'(increased|decreased|grew|declined).*?\d+',  # Growth statements with numbers
        ]
        
        matches = sum(1 for pattern in quant_patterns if re.search(pattern, result, re.IGNORECASE))
        
        if matches == 0:
            return 0.3, "No quantitative analysis detected"
        elif matches < 3:
            return 0.6, "Limited quantitative analysis"
        else:
            return 1.0, "Strong quantitative analysis present"
    
    def _check_logical_consistency(self, result: str) -> Tuple[float, str]:
        """
        Check for logical consistency in the analysis.
        """
        # This is a simplified check - in practice, you might use more sophisticated NLP
        consistency_issues = []
        
        # Check for contradictory statements
        if re.search(r'(increased|grew|rose).*?(decreased|declined|fell)', result, re.IGNORECASE):
            if not re.search(r'(but|however|although|while)', result, re.IGNORECASE):
                consistency_issues.append("Potential contradictory growth statements")
        
        # Check for impossible values (basic sanity checks)
        percentages = re.findall(r'(\d+\.?\d*)%', result)
        for pct in percentages:
            if float(pct) > 1000:  # More than 1000% might be suspicious
                consistency_issues.append("Extremely high percentage values")
                break
        
        if consistency_issues:
            return 0.4, f"Logical consistency issues: {'; '.join(consistency_issues)}"
        
        return 0.9, "No obvious logical consistency issues"
    
    def _find_field_in_data(self, data: Dict, field: str) -> bool:
        """
        Recursively search for a field in nested data structure.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if field.lower() in key.lower():
                    return True
                if isinstance(value, (dict, list)):
                    if self._find_field_in_data(value, field):
                        return True
        elif isinstance(data, list):
            for item in data:
                if self._find_field_in_data(item, field):
                    return True
        
        return False
    
    def _check_data_freshness(self, data: Dict) -> bool:
        """
        Check if the data appears to be recent/fresh.
        """
        current_year = datetime.now().year
        
        # Look for recent years in the data
        data_str = json.dumps(data, default=str)
        years = re.findall(r'\b(20\d{2})\b', data_str)
        
        if years:
            latest_year = max(int(year) for year in years)
            return (current_year - latest_year) <= 2  # Data should be within 2 years
        
        # If no years found, check for recent timestamps
        timestamps = re.findall(r'20\d{2}-\d{2}-\d{2}', data_str)
        if timestamps:
            return True  # Assume recent if timestamps are present
        
        return False  # Can't determine freshness
    
    def _record_validation(self, task_description: str, task_result: str, is_valid: bool, score: float, checks: List):
        """
        Record validation result for analysis and improvement.
        """
        validation_record = {
            "timestamp": datetime.now().isoformat(),
            "task_description": task_description[:200],  # Truncate for storage
            "result_length": len(task_result),
            "is_valid": is_valid,
            "overall_score": score,
            "detailed_checks": [
                {"name": name, "score": score, "reason": reason}
                for name, score, reason in checks
            ]
        }
        
        self.validation_history.append(validation_record)
        
        # Keep only last 100 validations
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about validation performance.
        """
        if not self.validation_history:
            return {"message": "No validation history available"}
        
        total_validations = len(self.validation_history)
        successful_validations = sum(1 for v in self.validation_history if v["is_valid"])
        
        avg_score = sum(v["overall_score"] for v in self.validation_history) / total_validations
        
        return {
            "total_validations": total_validations,
            "success_rate": successful_validations / total_validations,
            "average_score": avg_score,
            "recent_trend": self._calculate_recent_trend()
        }
    
    def _calculate_recent_trend(self) -> str:
        """
        Calculate trend in recent validation performance.
        """
        if len(self.validation_history) < 10:
            return "Insufficient data"
        
        recent_10 = self.validation_history[-10:]
        earlier_10 = self.validation_history[-20:-10] if len(self.validation_history) >= 20 else []
        
        if not earlier_10:
            return "Insufficient data for trend"
        
        recent_avg = sum(v["overall_score"] for v in recent_10) / len(recent_10)
        earlier_avg = sum(v["overall_score"] for v in earlier_10) / len(earlier_10)
        
        if recent_avg > earlier_avg + 0.05:
            return "Improving"
        elif recent_avg < earlier_avg - 0.05:
            return "Declining"
        else:
            return "Stable"

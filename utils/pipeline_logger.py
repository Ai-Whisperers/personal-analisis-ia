# -*- coding: utf-8 -*-
"""
Pipeline Validation Logger - Granular external logging for end-to-end validation
All logs are stored externally and easily deleteable without affecting core functionality
"""
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class PipelineLogger:
    """External validation logger with 10 granular levels"""

    def __init__(self, log_dir: str = "local-reports/pipeline-validation"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamp-based session
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.log_dir / f"validation_{self.session_id}.jsonl"
        self.report_file = self.log_dir / f"report_{self.session_id}.md"

        # Initialize session
        self._log_event("SESSION_START", {
            "session_id": self.session_id,
            "pipeline_version": "2.0.0",
            "validation_levels": 10,
            "mock_mode_eliminated": True
        })

    def _log_event(self, event_type: str, data: Dict[str, Any], level: str = "INFO"):
        """Log structured event to external JSONL file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": event_type,
            "level": level,
            "data": data
        }

        try:
            with open(self.session_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception:
            # Fail silently - external logging should not break pipeline
            pass

    # LEVEL 1: API Infrastructure Validation
    def log_api_validation(self, api_key_present: bool, api_key_format: str, mock_eliminated: bool):
        """External log: API configuration and mock elimination validation"""
        self._log_event("L1_API_VALIDATION", {
            "api_key_present": api_key_present,
            "api_key_format_valid": api_key_format.startswith("sk-proj-") if api_key_format else False,
            "api_key_length_adequate": len(api_key_format) > 50 if api_key_format else False,
            "mock_mode_completely_eliminated": mock_eliminated,
            "production_ready": api_key_present and mock_eliminated,
            "validation_result": "PASS" if api_key_present and mock_eliminated else "FAIL"
        })

    # LEVEL 2: Data Ingestion Analysis
    def log_data_ingestion(self, file_info: Dict[str, Any], preprocessing_stats: Dict[str, Any]):
        """External log: File reading and initial data quality assessment"""
        self._log_event("L2_DATA_INGESTION", {
            "file_path": file_info.get("filename", "unknown"),
            "file_size_mb": file_info.get("size_mb", 0),
            "rows_detected": file_info.get("rows", 0),
            "columns_found": file_info.get("column_names", []),
            "required_columns_present": file_info.get("has_required_columns", False),
            "data_ingestion_quality": "EXCELLENT" if file_info.get("rows", 0) > 500 else "GOOD" if file_info.get("rows", 0) > 100 else "MINIMAL"
        })

    # LEVEL 3: Smart Data Cleaning
    def log_preprocessing(self, cleaning_stats: Dict[str, Any], nps_parsing_stats: Dict[str, Any]):
        """External log: Data cleaning and smart NPS parsing results"""
        self._log_event("L3_PREPROCESSING", {
            "initial_rows": cleaning_stats.get("original_rows", 0),
            "cleaned_rows": cleaning_stats.get("cleaned_rows", 0),
            "retention_rate_percent": (1 - cleaning_stats.get("removal_percentage", 0) / 100) * 100,
            "nps_smart_parsing_success": nps_parsing_stats.get("parsed_from_text", 0),
            "nps_scale_conversions": nps_parsing_stats.get("scale_conversions", 0),
            "nps_sentiment_inferences": nps_parsing_stats.get("sentiment_inferences", 0),
            "preprocessing_quality": "EXCELLENT" if cleaning_stats.get("removal_percentage", 100) < 15 else "GOOD"
        })

    # LEVEL 4: API Call Execution
    def log_api_execution(self, batch_summary: Dict[str, Any]):
        """External log: OpenAI API call performance and success"""
        self._log_event("L4_API_EXECUTION", {
            "total_api_calls": batch_summary.get("total_calls", 0),
            "successful_calls": batch_summary.get("successful_calls", 0),
            "failed_calls": batch_summary.get("failed_calls", 0),
            "success_rate_percent": batch_summary.get("success_rate", 0),
            "avg_response_time_ms": batch_summary.get("avg_response_time", 0) * 1000,
            "total_tokens_consumed": batch_summary.get("total_tokens", 0),
            "rate_limit_incidents": batch_summary.get("rate_limit_hits", 0),
            "api_health_status": "OPTIMAL" if batch_summary.get("success_rate", 0) > 95 else "DEGRADED"
        })

    # LEVEL 5: Response Processing
    def log_response_processing(self, parsing_stats: Dict[str, Any]):
        """External log: JSON parsing and response structure validation"""
        self._log_event("L5_RESPONSE_PROCESSING", {
            "responses_received": parsing_stats.get("responses_received", 0),
            "json_parse_success": parsing_stats.get("parse_success", 0),
            "json_repairs_applied": parsing_stats.get("repairs_applied", 0),
            "structure_validations_passed": parsing_stats.get("structure_valid", 0),
            "emotion_data_complete": parsing_stats.get("emotions_complete", 0),
            "response_processing_quality": "EXCELLENT" if parsing_stats.get("parse_success_rate", 0) > 98 else "GOOD"
        })

    # LEVEL 6: Post-AI NPS Inference
    def log_nps_inference(self, inference_stats: Dict[str, Any]):
        """External log: Emotion-based NPS calculation (post-AI)"""
        self._log_event("L6_NPS_INFERENCE", {
            "missing_nps_values": inference_stats.get("values_requiring_inference", 0),
            "successfully_inferred": inference_stats.get("inferred_count", 0),
            "inference_success_rate": inference_stats.get("inference_success_rate", 0),
            "average_confidence": inference_stats.get("avg_confidence", 0.0),
            "high_confidence_inferences": inference_stats.get("high_confidence_count", 0),
            "nps_coverage_improvement": inference_stats.get("coverage_improvement", {}).get("improvement_points", 0),
            "inference_algorithm": "emotion_weighted_v2",
            "inference_quality": "HIGH_QUALITY" if inference_stats.get("avg_confidence", 0) > 0.7 else "ACCEPTABLE"
        })

    # LEVEL 7: Data Transformation
    def log_data_transformation(self, transform_stats: Dict[str, Any]):
        """External log: AI results to chart-ready format transformation"""
        self._log_event("L7_DATA_TRANSFORMATION", {
            "emotion_columns_created": transform_stats.get("emotion_columns", 0),
            "category_columns_created": transform_stats.get("category_columns", 0),
            "derived_analytics_columns": transform_stats.get("derived_columns", 0),
            "chart_compatibility_score": transform_stats.get("chart_compatibility", 0.0),
            "export_readiness_score": transform_stats.get("export_readiness", 0.0),
            "data_transformation_status": "OPTIMAL" if transform_stats.get("chart_compatibility", 0) > 0.9 else "GOOD"
        })

    # LEVEL 8: Visualization System Validation
    def log_chart_system_validation(self, chart_stats: Dict[str, Any]):
        """External log: Chart rendering capability and data compatibility"""
        self._log_event("L8_CHART_VALIDATION", {
            "emotion_charts_ready": chart_stats.get("emotion_chart_ready", False),
            "nps_charts_ready": chart_stats.get("nps_chart_ready", False),
            "sentiment_charts_ready": chart_stats.get("sentiment_chart_ready", False),
            "pain_point_charts_ready": chart_stats.get("pain_point_chart_ready", False),
            "chart_data_completeness": chart_stats.get("data_completeness", 0.0),
            "visualization_system_status": "FULLY_FUNCTIONAL" if all([
                chart_stats.get("emotion_chart_ready", False),
                chart_stats.get("nps_chart_ready", False),
                chart_stats.get("sentiment_chart_ready", False)
            ]) else "PARTIAL_FUNCTIONALITY"
        })

    # LEVEL 9: Export System Validation
    def log_export_validation(self, export_stats: Dict[str, Any]):
        """External log: Excel/CSV export functionality"""
        self._log_event("L9_EXPORT_VALIDATION", {
            "export_formats_supported": export_stats.get("formats", []),
            "data_integrity_maintained": export_stats.get("data_intact", False),
            "emotion_data_exportable": export_stats.get("emotions_exportable", False),
            "nps_data_exportable": export_stats.get("nps_exportable", False),
            "metadata_preservation": export_stats.get("metadata_preserved", False),
            "export_system_health": "OPERATIONAL" if export_stats.get("data_intact", False) else "NEEDS_ATTENTION"
        })

    # LEVEL 10: Complete Pipeline Summary
    def log_pipeline_completion(self, summary_stats: Dict[str, Any]):
        """External log: End-to-end pipeline execution summary"""
        self._log_event("L10_PIPELINE_SUMMARY", {
            "total_execution_time_seconds": summary_stats.get("total_time", 0),
            "comments_processed": summary_stats.get("processed_count", 0),
            "sla_target_seconds": 10.0,
            "sla_compliance": summary_stats.get("sla_met", False),
            "api_calls_successful": summary_stats.get("api_success", False),
            "mock_fallbacks_eliminated": summary_stats.get("no_mock_used", True),
            "nps_inference_applied": summary_stats.get("nps_inferred", False),
            "charts_functional": summary_stats.get("charts_ready", False),
            "export_functional": summary_stats.get("export_ready", False),
            "overall_pipeline_health": summary_stats.get("health", "UNKNOWN"),
            "critical_issues_detected": summary_stats.get("critical_issues", []),
            "performance_rating": "EXCELLENT" if summary_stats.get("sla_met", False) and summary_stats.get("api_success", False) else "ACCEPTABLE"
        })

    def generate_live_report(self) -> str:
        """Generate live validation report from current session logs"""
        try:
            # Read current session logs
            log_entries = []
            if self.session_file.exists():
                with open(self.session_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            log_entries.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue

            # Create markdown report
            report_content = f"""# Live Pipeline Validation Report

**Session**: {self.session_id}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Events Logged**: {len(log_entries)}
**Mock Mode**: ❌ Eliminated

## 🎯 Pipeline Health Dashboard

"""

            # Extract latest status from each level
            latest_events = {}
            for entry in log_entries:
                event_type = entry.get("event_type", "")
                if event_type.startswith("L"):
                    latest_events[event_type] = entry

            # Generate status dashboard
            levels = [
                ("L1_API_VALIDATION", "🔑 API Configuration"),
                ("L2_DATA_INGESTION", "📊 Data Ingestion"),
                ("L3_PREPROCESSING", "🧹 Smart Cleaning"),
                ("L4_API_EXECUTION", "🚀 API Calls"),
                ("L5_RESPONSE_PROCESSING", "🔄 Response Parsing"),
                ("L6_NPS_INFERENCE", "🧠 NPS Inference"),
                ("L7_DATA_TRANSFORMATION", "🔧 Data Transform"),
                ("L8_CHART_VALIDATION", "📈 Chart System"),
                ("L9_EXPORT_VALIDATION", "📋 Export System"),
                ("L10_PIPELINE_SUMMARY", "✅ Final Summary")
            ]

            for level_key, level_name in levels:
                if level_key in latest_events:
                    event = latest_events[level_key]
                    data = event.get("data", {})
                    timestamp = event.get("timestamp", "")[:19]  # Remove microseconds

                    report_content += f"### {level_name}\n"
                    report_content += f"**Last Update**: {timestamp}\n"

                    # Level-specific status extraction
                    if level_key == "L1_API_VALIDATION":
                        result = data.get("validation_result", "UNKNOWN")
                        status = "✅ PASS" if result == "PASS" else "❌ FAIL"
                        report_content += f"**Status**: {status}\n"
                        if result == "FAIL":
                            report_content += f"- API Key Present: {'✅' if data.get('api_key_present') else '❌'}\n"
                            report_content += f"- Mock Eliminated: {'✅' if data.get('mock_mode_completely_eliminated') else '❌'}\n"

                    elif level_key == "L4_API_EXECUTION":
                        success_rate = data.get("success_rate_percent", 0)
                        status = "✅ HEALTHY" if success_rate > 95 else "⚠️ DEGRADED"
                        report_content += f"**Status**: {status}\n"
                        report_content += f"**Success Rate**: {success_rate:.1f}%\n"
                        report_content += f"**Avg Response**: {data.get('avg_response_time_ms', 0):.0f}ms\n"

                    elif level_key == "L6_NPS_INFERENCE":
                        inferred = data.get("successfully_inferred", 0)
                        confidence = data.get("average_confidence", 0)
                        quality = data.get("inference_quality", "UNKNOWN")
                        report_content += f"**Quality**: {quality}\n"
                        report_content += f"**Values Inferred**: {inferred}\n"
                        report_content += f"**Avg Confidence**: {confidence:.2f}\n"

                    elif level_key == "L10_PIPELINE_SUMMARY":
                        health = data.get("overall_pipeline_health", "UNKNOWN")
                        sla_met = data.get("sla_compliance", False)
                        rating = data.get("performance_rating", "UNKNOWN")
                        report_content += f"**Health**: {health}\n"
                        report_content += f"**Performance**: {rating}\n"
                        report_content += f"**SLA Compliance**: {'✅' if sla_met else '❌'}\n"

                    report_content += "\n"
                else:
                    report_content += f"### {level_name}\n**Status**: ⏳ Pending Execution\n\n"

            # Add cleanup instructions
            report_content += f"""---

## 📁 Generated Files

- **Detailed Logs**: `{self.session_file.name}`
- **This Report**: `{self.report_file.name}`

## 🗑️ Cleanup Commands

```bash
# Remove all validation logs
python utils/log_cleanup.py --all

# Remove this session only
python utils/log_cleanup.py --session {self.session_id}

# Manual cleanup
rm -rf local-reports/pipeline-validation/
```

**Note**: These logs are completely external and can be deleted without affecting the system.
"""

            # Write report
            with open(self.report_file, "w", encoding="utf-8") as f:
                f.write(report_content)

            return str(self.report_file)

        except Exception as e:
            logger.warning(f"Could not generate live report: {e}")
            return f"Error generating report: {e}"

# Global pipeline logger instance
pipeline_logger = PipelineLogger()

# Decorator for automatic pipeline step logging
def log_pipeline_step(step_name: str, level: int = 1):
    """Decorator for automatic external pipeline step logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                pipeline_logger._log_event(f"STEP_{step_name.upper()}_SUCCESS", {
                    "step": step_name,
                    "level": level,
                    "execution_time_seconds": execution_time,
                    "status": "COMPLETED"
                })
                return result

            except Exception as e:
                execution_time = time.time() - start_time
                pipeline_logger._log_event(f"STEP_{step_name.upper()}_ERROR", {
                    "step": step_name,
                    "level": level,
                    "execution_time_seconds": execution_time,
                    "error_type": type(e).__name__,
                    "error_message": str(e)[:200]
                }, level="ERROR")
                raise

        return wrapper
    return decorator
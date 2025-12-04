"""OpenAI API usage tracking service.

Tracks token usage, costs, and API call statistics.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta


# Pricing per 1M tokens (as of Dec 2024)
# Update these if OpenAI changes pricing
PRICING = {
    "gpt-4o-mini": {
        "input": 0.150,   # $0.150 per 1M input tokens
        "output": 0.600,  # $0.600 per 1M output tokens
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00,
    }
}

STORAGE_DIR = os.getenv("USAGE_LOGS_DIR", "usage_logs")


class OpenAIUsageTracker:
    """Track OpenAI API usage and costs."""

    def __init__(self, storage_dir: str = STORAGE_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.current_file = self.storage_dir / f"usage_{datetime.now().strftime('%Y%m')}.json"

    def _load_current_data(self) -> dict:
        """Load current month's usage data."""
        if self.current_file.exists():
            with open(self.current_file, 'r') as f:
                return json.load(f)
        return {"calls": [], "summary": {}}

    def _save_data(self, data: dict):
        """Save usage data to file."""
        with open(self.current_file, 'w') as f:
            json.dump(data, f, indent=2)

    def log_api_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        session_id: Optional[str] = None,
        response_time: Optional[float] = None
    ):
        """Log an OpenAI API call.

        Args:
            model: Model name (e.g., 'gpt-4o-mini')
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            total_tokens: Total tokens used
            session_id: Optional session ID to link with conversation logs
            response_time: API response time in seconds
        """
        # Calculate cost
        pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        # Create call record
        call_record = {
            "timestamp": time.time(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "session_id": session_id,
            "response_time": response_time
        }

        # Load and update data
        data = self._load_current_data()
        data["calls"].append(call_record)

        # Update summary
        summary = data.get("summary", {})
        summary["total_calls"] = summary.get("total_calls", 0) + 1
        summary["total_tokens"] = summary.get("total_tokens", 0) + total_tokens
        summary["total_prompt_tokens"] = summary.get("total_prompt_tokens", 0) + prompt_tokens
        summary["total_completion_tokens"] = summary.get("total_completion_tokens", 0) + completion_tokens
        summary["total_cost"] = round(summary.get("total_cost", 0) + total_cost, 6)
        summary["last_updated"] = time.time()

        # Track by model
        model_stats = summary.get("by_model", {})
        if model not in model_stats:
            model_stats[model] = {
                "calls": 0,
                "tokens": 0,
                "cost": 0
            }
        model_stats[model]["calls"] += 1
        model_stats[model]["tokens"] += total_tokens
        model_stats[model]["cost"] = round(model_stats[model]["cost"] + total_cost, 6)
        summary["by_model"] = model_stats

        data["summary"] = summary
        self._save_data(data)

    def get_summary(self, days: Optional[int] = None) -> dict:
        """Get usage summary.

        Args:
            days: Optional number of days to look back. If None, returns current month.

        Returns:
            Usage summary with totals and breakdowns
        """
        if days is None:
            # Return current month
            data = self._load_current_data()
            return data.get("summary", {})

        # Aggregate data from multiple months if needed
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        all_calls = []

        # Check all month files
        for file in sorted(self.storage_dir.glob("usage_*.json")):
            with open(file, 'r') as f:
                data = json.load(f)
                calls = [c for c in data.get("calls", []) if c["timestamp"] >= cutoff_time]
                all_calls.extend(calls)

        # Calculate aggregate summary
        if not all_calls:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "period_days": days
            }

        total_tokens = sum(c["total_tokens"] for c in all_calls)
        total_cost = sum(c["total_cost"] for c in all_calls)
        total_prompt = sum(c["prompt_tokens"] for c in all_calls)
        total_completion = sum(c["completion_tokens"] for c in all_calls)

        # Group by model
        by_model = {}
        for call in all_calls:
            model = call["model"]
            if model not in by_model:
                by_model[model] = {"calls": 0, "tokens": 0, "cost": 0}
            by_model[model]["calls"] += 1
            by_model[model]["tokens"] += call["total_tokens"]
            by_model[model]["cost"] = round(by_model[model]["cost"] + call["total_cost"], 6)

        return {
            "total_calls": len(all_calls),
            "total_tokens": total_tokens,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_cost": round(total_cost, 6),
            "by_model": by_model,
            "period_days": days,
            "first_call": min(c["timestamp"] for c in all_calls),
            "last_call": max(c["timestamp"] for c in all_calls)
        }

    def get_recent_calls(self, limit: int = 50) -> List[dict]:
        """Get recent API calls.

        Args:
            limit: Maximum number of calls to return

        Returns:
            List of recent API calls
        """
        data = self._load_current_data()
        calls = data.get("calls", [])
        return sorted(calls, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_daily_stats(self, days: int = 7) -> List[dict]:
        """Get daily usage statistics.

        Args:
            days: Number of days to include

        Returns:
            List of daily stats
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        all_calls = []

        # Collect calls from all relevant files
        for file in sorted(self.storage_dir.glob("usage_*.json")):
            with open(file, 'r') as f:
                data = json.load(f)
                calls = [c for c in data.get("calls", []) if c["timestamp"] >= cutoff_time]
                all_calls.extend(calls)

        # Group by day
        daily_stats = {}
        for call in all_calls:
            day = datetime.fromtimestamp(call["timestamp"]).strftime("%Y-%m-%d")
            if day not in daily_stats:
                daily_stats[day] = {
                    "date": day,
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0
                }
            daily_stats[day]["calls"] += 1
            daily_stats[day]["tokens"] += call["total_tokens"]
            daily_stats[day]["cost"] = round(daily_stats[day]["cost"] + call["total_cost"], 6)

        return sorted(daily_stats.values(), key=lambda x: x["date"])


# Global tracker instance
tracker = OpenAIUsageTracker()

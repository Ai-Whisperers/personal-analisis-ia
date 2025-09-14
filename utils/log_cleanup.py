# -*- coding: utf-8 -*-
"""
External Pipeline Log Cleanup - Zero impact on core system
Easy cleanup of validation logs without affecting pipeline functionality
"""
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class LogCleaner:
    """Manages external validation log cleanup"""

    def __init__(self):
        self.log_dir = Path("local-reports/pipeline-validation")

    def clean_all(self):
        """Remove ALL pipeline validation logs"""
        if self.log_dir.exists():
            shutil.rmtree(self.log_dir)
            print(f"🗑️ Removed all validation logs: {self.log_dir}")
            return True
        print("ℹ️ No validation logs found")
        return False

    def clean_session(self, session_id: str):
        """Remove specific session logs"""
        if not self.log_dir.exists():
            print("ℹ️ No validation logs directory found")
            return False

        removed = 0
        for file in self.log_dir.glob(f"*{session_id}*"):
            file.unlink()
            removed += 1

        print(f"🗑️ Removed {removed} files for session {session_id}")
        return removed > 0

    def clean_older_than(self, hours: int = 24):
        """Remove logs older than specified hours"""
        if not self.log_dir.exists():
            return 0

        cutoff = datetime.now() - timedelta(hours=hours)
        removed = 0

        for file in self.log_dir.glob("*.jsonl"):
            try:
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                    file.unlink()
                    removed += 1
            except (OSError, ValueError):
                continue

        for file in self.log_dir.glob("*.md"):
            try:
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                    file.unlink()
                    removed += 1
            except (OSError, ValueError):
                continue

        print(f"🗑️ Removed {removed} old validation logs (>{hours}h old)")
        return removed

    def list_sessions(self):
        """List all available validation sessions"""
        if not self.log_dir.exists():
            print("ℹ️ No validation logs found")
            return []

        sessions = set()
        for file in self.log_dir.glob("validation_*.jsonl"):
            try:
                session_id = file.stem.split("_", 1)[1]
                sessions.add(session_id)
            except IndexError:
                continue

        print(f"📊 Found {len(sessions)} validation sessions:")
        for session in sorted(sessions):
            session_file = self.log_dir / f"validation_{session}.jsonl"
            report_file = self.log_dir / f"report_{session}.md"

            size_info = ""
            if session_file.exists():
                size_kb = session_file.stat().st_size / 1024
                size_info = f" ({size_kb:.1f}KB)"

            files_info = []
            if session_file.exists():
                files_info.append("JSONL")
            if report_file.exists():
                files_info.append("Report")

            print(f"  - {session}{size_info} [{', '.join(files_info)}]")

        return list(sessions)

    def get_latest_report(self) -> Optional[str]:
        """Get path to the most recent validation report"""
        if not self.log_dir.exists():
            return None

        report_files = list(self.log_dir.glob("report_*.md"))
        if not report_files:
            return None

        # Get most recent report
        latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
        return str(latest_report)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of specific session"""
        session_file = self.log_dir / f"validation_{session_id}.jsonl"

        if not session_file.exists():
            return {"error": "Session not found"}

        try:
            events = []
            with open(session_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        events.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue

            # Extract key metrics
            summary = {
                "session_id": session_id,
                "total_events": len(events),
                "levels_completed": len(set(e.get("event_type", "") for e in events if e.get("event_type", "").startswith("L"))),
                "errors_detected": len([e for e in events if e.get("level") == "ERROR"]),
                "session_duration": "unknown"
            }

            # Find session start and end
            start_events = [e for e in events if e.get("event_type") == "SESSION_START"]
            end_events = [e for e in events if e.get("event_type") == "L10_PIPELINE_SUMMARY"]

            if start_events and end_events:
                start_time = datetime.fromisoformat(start_events[0].get("timestamp"))
                end_time = datetime.fromisoformat(end_events[-1].get("timestamp"))
                duration = end_time - start_time
                summary["session_duration"] = str(duration)

            return summary

        except Exception as e:
            return {"error": f"Could not read session: {e}"}

# CLI interface
if __name__ == "__main__":
    import sys
    import json
    cleaner = LogCleaner()

    if len(sys.argv) == 1:
        print("📊 Pipeline Log Cleanup Utility")
        print("\nAvailable Commands:")
        print("  python log_cleanup.py              # List sessions")
        print("  python log_cleanup.py --all        # Remove all logs")
        print("  python log_cleanup.py --old [hours] # Remove old logs")
        print("  python log_cleanup.py --session ID  # Remove specific session")
        print("  python log_cleanup.py --latest      # Show latest report")
        print()
        cleaner.list_sessions()

    elif sys.argv[1] == "--all":
        cleaner.clean_all()

    elif sys.argv[1] == "--old":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        cleaner.clean_older_than(hours)

    elif sys.argv[1] == "--session":
        if len(sys.argv) > 2:
            cleaner.clean_session(sys.argv[2])
        else:
            print("❌ Session ID required: python log_cleanup.py --session SESSION_ID")

    elif sys.argv[1] == "--latest":
        latest = cleaner.get_latest_report()
        if latest:
            print(f"📄 Latest report: {latest}")
            with open(latest, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print("ℹ️ No reports found")

    elif sys.argv[1] == "--summary":
        if len(sys.argv) > 2:
            summary = cleaner.get_session_summary(sys.argv[2])
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            print("❌ Session ID required: python log_cleanup.py --summary SESSION_ID")
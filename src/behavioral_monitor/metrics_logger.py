from datetime import datetime, timezone
import json
from pathlib import Path
import time


class MinuteMetricsLogger:
    METRIC_KEYS = {
        "ear": "EAR",
        "mar": "MAR",
        "blinks_per_minute": "BLINKS_PER_MINUTE",
        "perclos_percent": "PERCLOS",
        "yawns_per_minute": "YAWNS_PER_MINUTE",
        "avg_yawn_duration_seconds": "AVG_YAWN_DURATION",
        "avg_eyes_open_seconds": "AVG_EYES_OPEN_SECONDS"
    }

    def __init__(
        self,
        output_path,
        interval_seconds=60.0,
        max_observation_gap_seconds=0.5,
        min_yawn_duration=1.1,
        clock=time.monotonic,
        utcnow=lambda: datetime.now(timezone.utc)
    ):
        self.output_path = Path(output_path)
        self.interval_seconds = interval_seconds
        self.max_observation_gap_seconds = max_observation_gap_seconds
        self.min_yawn_duration = min_yawn_duration
        self._clock = clock
        self._utcnow = utcnow
        self._window_started_at = clock()
        self._window_started_utc = utcnow()
        self._last_observation_at = None
        self._reset_metrics()

    def clear(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text("", encoding="utf-8")

    def _reset_metrics(self):
        self._sample_count = 0
        self._metric_totals = {name: 0.0 for name in self.METRIC_KEYS}
        self._completed_yawn_count = 0
        self._completed_yawn_duration_total = 0.0
        self._observed_seconds = 0.0

    def add(self, features, timestamp=None):
        if features is None:
            return

        timestamp = self._clock() if timestamp is None else timestamp
        if self._last_observation_at is not None:
            elapsed = timestamp - self._last_observation_at
            if 0 < elapsed <= self.max_observation_gap_seconds:
                self._observed_seconds += elapsed
        self._last_observation_at = timestamp

        for name, key in self.METRIC_KEYS.items():
            value = features.get(key)
            if value is not None:
                self._metric_totals[name] += float(value)

        self._sample_count += 1
        if features.get("YAWN_ENDED"):
            duration = float(features["YAWN_DURATION_SECONDS"])
            if duration >= self.min_yawn_duration:
                self._completed_yawn_count += 1
                self._completed_yawn_duration_total += duration

    def flush_if_due(self, timestamp=None):
        timestamp = self._clock() if timestamp is None else timestamp
        elapsed = timestamp - self._window_started_at
        if elapsed < self.interval_seconds:
            return False

        window_end_utc = self._utcnow()
        record = {
            "window_start": self._window_started_utc.isoformat(),
            "window_end": window_end_utc.isoformat(),
            "window_seconds": round(elapsed, 3),
            "observed_frames": self._sample_count,
            "face_tracking_seconds": round(self._observed_seconds, 3),
            "face_tracking_coverage_percent": round(
                min(100.0, 100.0 * self._observed_seconds / elapsed), 1
            ) if elapsed > 0 else 0.0,
            "completed_yawns": self._completed_yawn_count,
            "completed_yawn_avg_duration_seconds": (
                round(
                    self._completed_yawn_duration_total
                    / self._completed_yawn_count,
                    3
                )
                if self._completed_yawn_count else None
            )
        }

        for name, total in self._metric_totals.items():
            record[f"mean_{name}"] = (
                round(total / self._sample_count, 4)
                if self._sample_count else None
            )

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a", encoding="utf-8") as output_file:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")

        self._window_started_at = timestamp
        self._window_started_utc = window_end_utc
        self._last_observation_at = None
        self._reset_metrics()
        return True

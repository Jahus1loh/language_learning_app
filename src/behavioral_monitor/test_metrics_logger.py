from datetime import datetime, timezone
import json

from metrics_logger import MinuteMetricsLogger


def test_clear_removes_previous_log_contents(tmp_path):
    log_path = tmp_path / "metrics.jsonl"
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"old": true}\n', encoding="utf-8")
    logger = MinuteMetricsLogger(log_path)

    logger.clear()

    assert log_path.read_text(encoding="utf-8") == ""


def test_writes_minute_summary_as_json_lines(tmp_path):
    current_time = [100.0]
    logger = MinuteMetricsLogger(
        tmp_path / "metrics.jsonl",
        interval_seconds=60,
        clock=lambda: current_time[0],
        utcnow=lambda: datetime(
            2026, 11, 12, 13, 0, tzinfo=timezone.utc
        )
    )
    features = {
        "EAR": 0.3,
        "MAR": 0.2,
        "BLINKS_PER_MINUTE": 12,
        "PERCLOS": 4,
        "YAWNS_PER_MINUTE": 1,
        "AVG_YAWN_DURATION": 2.0,
        "AVG_EYES_OPEN_SECONDS": 5.0,
        "YAWN_ENDED": True,
        "YAWN_DURATION_SECONDS": 2.0
    }

    logger.add(features, timestamp=100.0)
    logger.add(features, timestamp=100.2)
    current_time[0] = 159.0
    assert logger.flush_if_due() is False

    current_time[0] = 160.0
    assert logger.flush_if_due() is True

    records = [
        json.loads(line)
        for line in (tmp_path / "metrics.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert len(records) == 1
    assert records[0]["mean_ear"] == 0.3
    assert records[0]["completed_yawns"] == 2
    assert records[0]["face_tracking_seconds"] == 0.2
    assert records[0]["face_tracking_coverage_percent"] == 0.3


def test_writes_null_metrics_when_no_face_was_observed(tmp_path):
    current_time = [0.0]
    logger = MinuteMetricsLogger(
        tmp_path / "metrics.jsonl",
        interval_seconds=60,
        clock=lambda: current_time[0],
        utcnow=lambda: datetime(
            2026, 11, 12, 13, 0, tzinfo=timezone.utc
        )
    )

    current_time[0] = 60.0
    assert logger.flush_if_due() is True
    record = json.loads(
        (tmp_path / "metrics.jsonl").read_text(encoding="utf-8")
    )
    assert record["observed_frames"] == 0
    assert record["mean_ear"] is None
    assert record["face_tracking_coverage_percent"] == 0

from feature_extractor import FeatureExtractor


def test_counts_closed_to_open_transition_as_blink():
    extractor = FeatureExtractor()

    assert extractor._update_blink_rate(0.1, 0.0) == 0
    assert extractor._update_blink_rate(0.3, 0.1) == 1


def test_ignores_long_eye_closure():
    extractor = FeatureExtractor()

    extractor._update_blink_rate(0.1, 0.0)

    assert extractor._update_blink_rate(0.3, 1.1) == 0


def test_expires_blinks_outside_the_rolling_minute():
    extractor = FeatureExtractor()
    extractor._update_blink_rate(0.1, 0.0)
    extractor._update_blink_rate(0.3, 0.1)

    assert extractor._update_blink_rate(0.3, 60.2) == 0


def test_perclos_uses_closed_time_in_the_rolling_window():
    extractor = FeatureExtractor(
        perclos_window_seconds=2.0,
        max_observation_gap_seconds=1.1
    )

    assert extractor._update_perclos(0.1, 0.0) == 0
    assert extractor._update_perclos(0.1, 1.0) == 100
    assert extractor._update_perclos(0.3, 2.0) == 100
    assert extractor._update_perclos(0.3, 3.0) == 50
    assert extractor._update_perclos(0.3, 4.0) == 0


def test_perclos_ignores_gaps_without_face_observations():
    extractor = FeatureExtractor(
        perclos_window_seconds=2.0,
        max_observation_gap_seconds=0.5
    )

    extractor._update_perclos(0.1, 0.0)

    assert extractor._update_perclos(0.3, 1.0) == 0


def test_counts_yawn_only_after_minimum_duration():
    extractor = FeatureExtractor(
        max_observation_gap_seconds=1.1,
        min_yawn_duration=1.5,
        metric_window_seconds=60.0
    )

    assert extractor._update_duration_metrics(0.3, 0.3, 0.0)[0] == 0
    assert extractor._update_duration_metrics(0.3, 0.7, 0.2)[0] == 0
    assert extractor._yawn_started_this_frame is True
    assert extractor._update_duration_metrics(0.3, 0.7, 1.0)[0] == 0
    assert extractor._update_duration_metrics(0.3, 0.3, 2.0)[0] == 1
    assert extractor._yawn_ended_this_frame is True
    assert extractor._last_yawn_duration == 1.8


def test_reports_live_yawn_start_and_end_transitions():
    extractor = FeatureExtractor(
        max_observation_gap_seconds=1.1,
        min_yawn_duration=1.5
    )

    extractor._update_duration_metrics(0.3, 0.3, 0.0)
    extractor._update_duration_metrics(0.3, 0.7, 0.2)
    assert extractor._yawn_started_this_frame is True
    assert extractor._last_yawning is True

    extractor._update_duration_metrics(0.3, 0.7, 0.8)
    assert extractor._yawn_started_this_frame is False
    assert extractor._last_yawning is True

    extractor._update_duration_metrics(0.3, 0.3, 1.0)
    assert extractor._yawn_ended_this_frame is True
    assert extractor._last_yawn_duration == 0.8


def test_tracking_gap_does_not_report_yawn_end():
    extractor = FeatureExtractor(max_observation_gap_seconds=0.5)

    extractor._update_duration_metrics(0.3, 0.3, 0.0)
    extractor._update_duration_metrics(0.3, 0.7, 0.2)
    extractor._update_duration_metrics(0.3, 0.3, 2.0)

    assert extractor._yawn_ended_this_frame is False


def test_does_not_count_yawn_across_face_tracking_gap():
    extractor = FeatureExtractor(
        max_observation_gap_seconds=0.5,
        min_yawn_duration=1.5
    )

    extractor._update_duration_metrics(0.3, 0.7, 0.0)
    extractor._update_duration_metrics(0.3, 0.7, 0.2)

    assert extractor._update_duration_metrics(0.3, 0.3, 2.0)[0] == 0
    assert extractor._update_duration_metrics(0.3, 0.3, 2.2)[0] == 0


def test_calculates_average_completed_eye_open_duration():
    extractor = FeatureExtractor(
        max_observation_gap_seconds=1.1,
        metric_window_seconds=60.0
    )

    extractor._update_duration_metrics(0.3, 0.3, 0.0)
    extractor._update_duration_metrics(0.3, 0.3, 1.0)
    result = extractor._update_duration_metrics(0.1, 0.3, 2.0)

    assert result[2] == 2.0

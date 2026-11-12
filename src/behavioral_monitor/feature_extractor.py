
from collections import deque
import time

import numpy as np


class FeatureExtractor:
    def __init__(
        self,
        ear_threshold=0.21,
        blink_window_seconds=60.0,
        max_blink_duration=1.0,
        min_blink_duration=0.05,
        perclos_window_seconds=60.0,
        perclos_threshold=None,
        max_observation_gap_seconds=0.5,
        yawn_threshold=0.6,
        min_yawn_duration=0.8,
        metric_window_seconds=60.0
    ):
        self.ear_threshold = ear_threshold
        self.blink_window_seconds = blink_window_seconds
        self.max_blink_duration = max_blink_duration
        self.min_blink_duration = min_blink_duration
        self.perclos_window_seconds = perclos_window_seconds
        self.perclos_threshold = (
            ear_threshold if perclos_threshold is None else perclos_threshold
        )
        self.max_observation_gap_seconds = max_observation_gap_seconds
        self.yawn_threshold = yawn_threshold
        self.min_yawn_duration = min_yawn_duration
        self.metric_window_seconds = metric_window_seconds
        self._eyes_closed = False
        self._eyes_closed_at = None
        self._blink_times = deque()
        self._perclos_intervals = deque()
        self._last_perclos_observation = None
        self._last_perclos_closed = False
        self._last_metric_observation = None
        self._last_yawning = False
        self._yawn_started_at = None
        self._last_eyes_open = False
        self._eyes_open_since = None
        self._yawn_events = deque()
        self._eyes_open_durations = deque()
        self._yawn_started_this_frame = False
        self._yawn_ended_this_frame = False
        self._last_yawn_duration = 0.0

    def _update_blink_rate(self, ear, timestamp):
        if ear < self.ear_threshold:
            if not self._eyes_closed:
                self._eyes_closed = True
                self._eyes_closed_at = timestamp
        elif self._eyes_closed:
            duration = timestamp - self._eyes_closed_at
            if self.min_blink_duration <= duration <= self.max_blink_duration:
                self._blink_times.append(timestamp)
            self._eyes_closed = False
            self._eyes_closed_at = None

        cutoff = timestamp - self.blink_window_seconds
        while self._blink_times and self._blink_times[0] < cutoff:
            self._blink_times.popleft()

        return len(self._blink_times) * (60.0 / self.blink_window_seconds)

    def _update_perclos(self, ear, timestamp):
        eyes_closed = ear < self.perclos_threshold

        if self._last_perclos_observation is not None:
            elapsed = timestamp - self._last_perclos_observation
            if 0 < elapsed <= self.max_observation_gap_seconds:
                self._perclos_intervals.append((
                    self._last_perclos_observation,
                    timestamp,
                    self._last_perclos_closed
                ))

        self._last_perclos_observation = timestamp
        self._last_perclos_closed = eyes_closed

        cutoff = timestamp - self.perclos_window_seconds
        while (
            self._perclos_intervals
            and self._perclos_intervals[0][1] <= cutoff
        ):
            self._perclos_intervals.popleft()

        observed_duration = 0.0
        closed_duration = 0.0
        for start, end, was_closed in self._perclos_intervals:
            duration = max(0.0, min(end, timestamp) - max(start, cutoff))
            observed_duration += duration
            if was_closed:
                closed_duration += duration

        if observed_duration == 0:
            return 0.0

        return 100.0 * closed_duration / observed_duration

    def _update_duration_metrics(self, ear, mar, timestamp):
        eyes_open = ear >= self.perclos_threshold
        yawning = mar >= self.yawn_threshold
        self._yawn_started_this_frame = False
        self._yawn_ended_this_frame = False
        self._last_yawn_duration = 0.0

        if self._last_metric_observation is not None:
            elapsed = timestamp - self._last_metric_observation
            if 0 < elapsed <= self.max_observation_gap_seconds:
                if self._last_yawning and not yawning:
                    duration = timestamp - self._yawn_started_at
                    self._yawn_ended_this_frame = True
                    self._last_yawn_duration = duration
                    if duration >= self.min_yawn_duration:
                        self._yawn_events.append((timestamp, duration))

                if self._last_eyes_open and not eyes_open:
                    duration = timestamp - self._eyes_open_since
                    self._eyes_open_durations.append((timestamp, duration))
            else:
                self._yawn_started_at = None
                self._eyes_open_since = None
                self._last_yawning = False
                self._last_eyes_open = False

        if yawning and not self._last_yawning:
            self._yawn_started_at = timestamp
            self._yawn_started_this_frame = True
        elif not yawning:
            self._yawn_started_at = None

        if eyes_open and not self._last_eyes_open:
            self._eyes_open_since = timestamp
        elif not eyes_open:
            self._eyes_open_since = None

        self._last_metric_observation = timestamp
        self._last_yawning = yawning
        self._last_eyes_open = eyes_open

        cutoff = timestamp - self.metric_window_seconds
        while self._yawn_events and self._yawn_events[0][0] < cutoff:
            self._yawn_events.popleft()
        while (
            self._eyes_open_durations
            and self._eyes_open_durations[0][0] < cutoff
        ):
            self._eyes_open_durations.popleft()

        yawns_per_minute = (
            len(self._yawn_events) * (60.0 / self.metric_window_seconds)
        )
        average_yawn_duration = (
            sum(duration for _, duration in self._yawn_events)
            / len(self._yawn_events)
            if self._yawn_events else 0.0
        )
        average_eyes_open = (
            sum(duration for _, duration in self._eyes_open_durations)
            / len(self._eyes_open_durations)
            if self._eyes_open_durations else 0.0
        )

        return yawns_per_minute, average_yawn_duration, average_eyes_open

    # Punkty charakterystyczne oczu MediaPipe
    LEFT_EYE = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    # Punkty charakterystyczne ust
    MOUTH_VERTICAL = [
        (13, 14),
        (82, 87),
        (312, 317)
    ]

    MOUTH_HORIZONTAL = (78, 308)

    def _get_point(self, landmarks, index, width, height):
        point = landmarks.landmark[index]

        return np.array([
            point.x * width,
            point.y * height
        ])

    def _distance(self, p1, p2):
        return np.linalg.norm(p1 - p2)

    def calculate_ear(self, landmarks, eye_indices,
                      width, height):

        points = [
            self._get_point(landmarks, i, width, height)
            for i in eye_indices
        ]

        vertical_1 = self._distance(points[1], points[5])
        vertical_2 = self._distance(points[2], points[4])
        horizontal = self._distance(points[0], points[3])

        if horizontal == 0:
            return None

        ear = (vertical_1 + vertical_2) / (2 * horizontal)

        return float(ear)

    def calculate_mar(self, landmarks, width, height):

        vertical_distances = []

        for i, j in self.MOUTH_VERTICAL:
            p1 = self._get_point(landmarks, i, width, height)
            p2 = self._get_point(landmarks, j, width, height)

            vertical_distances.append(
                self._distance(p1, p2)
            )

        p_left = self._get_point(
            landmarks, self.MOUTH_HORIZONTAL[0], width, height
        )

        p_right = self._get_point(
            landmarks, self.MOUTH_HORIZONTAL[1], width, height
        )

        horizontal = self._distance(p_left, p_right)

        if horizontal == 0:
            return None

        mar = sum(vertical_distances) / (3 * horizontal)

        return float(mar)

    def extract(self, landmarks, frame_shape):

        height, width = frame_shape[:2]

        left_ear = self.calculate_ear(
            landmarks, self.LEFT_EYE, width, height
        )

        right_ear = self.calculate_ear(
            landmarks, self.RIGHT_EYE, width, height
        )

        mar = self.calculate_mar(
            landmarks, width, height
        )

        if left_ear is None or right_ear is None or mar is None:
            return None

        ear = (left_ear + right_ear) / 2
        timestamp = time.monotonic()
        blinks_per_minute = self._update_blink_rate(ear, timestamp)
        perclos = self._update_perclos(ear, timestamp)
        (
            yawns_per_minute,
            average_yawn_duration,
            average_eyes_open
        ) = self._update_duration_metrics(ear, mar, timestamp)

        return {
            "EAR": ear,
            "MAR": mar,
            "left_EAR": left_ear,
            "right_EAR": right_ear,
            "BLINKS_PER_MINUTE": blinks_per_minute,
            "PERCLOS": perclos,
            "YAWNS_PER_MINUTE": yawns_per_minute,
            "AVG_YAWN_DURATION": average_yawn_duration,
            "AVG_EYES_OPEN_SECONDS": average_eyes_open,
            "YAWNING": self._last_yawning,
            "YAWN_STARTED": self._yawn_started_this_frame,
            "YAWN_ENDED": self._yawn_ended_this_frame,
            "YAWN_DURATION_SECONDS": self._last_yawn_duration
        }

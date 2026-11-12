from datetime import datetime
from pathlib import Path
import time

import cv2

from camera import Camera
from face_detector import FaceDetector
from feature_extractor import FeatureExtractor
from metrics_logger import MinuteMetricsLogger


def main():
    extractor = FeatureExtractor()
    metrics_logger = MinuteMetricsLogger(
        Path(__file__).resolve().parent / "data" / "behavior_metrics.jsonl",
        max_observation_gap_seconds=extractor.max_observation_gap_seconds,
        min_yawn_duration=extractor.min_yawn_duration
    )
    metrics_logger.clear()

    camera = Camera(0)
    detector = FaceDetector()
    is_yawning = False
    yawn_notice = ""
    yawn_notice_until = 0.0

    try:
        while True:
            metrics_logger.flush_if_due()

            frame = camera.get_frame()
            if frame is None:
                continue

            current_time = datetime.now().strftime("%H:%M:%S")
            cv2.putText(
                frame,
                current_time,
                (frame.shape[1] - 150, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            landmarks = detector.detect(frame)
            if landmarks:
                features = extractor.extract(landmarks, frame.shape)
                metrics_logger.add(features)

                if features:
                    ear = features["EAR"]
                    mar = features["MAR"]
                    blinks_per_minute = features["BLINKS_PER_MINUTE"]
                    perclos = features["PERCLOS"]
                    yawns_per_minute = features["YAWNS_PER_MINUTE"]
                    average_yawn_duration = features["AVG_YAWN_DURATION"]
                    average_eyes_open = features["AVG_EYES_OPEN_SECONDS"]
                    is_yawning = features["YAWNING"]

                    if features["YAWN_STARTED"]:
                        yawn_notice = "YAWN STARTED"
                        yawn_notice_until = time.monotonic() + 2.0
                    elif features["YAWN_ENDED"]:
                        duration = features["YAWN_DURATION_SECONDS"]
                        yawn_notice = f"YAWN ENDED ({duration:.1f}s)"
                        yawn_notice_until = time.monotonic() + 2.0

                    metrics = [
                        f"EAR: {ear:.3f}",
                        f"MAR: {mar:.3f}",
                        f"Blinks/min: {blinks_per_minute:.0f}",
                        f"PERCLOS: {perclos:.1f}%",
                        f"Yawns/min: {yawns_per_minute:.0f}",
                        f"Avg yawn: {average_yawn_duration:.1f}s",
                        f"Avg eyes open: {average_eyes_open:.1f}s"
                    ]
                    for line_index, text in enumerate(metrics):
                        cv2.putText(
                            frame,
                            text,
                            (20, 40 + line_index * 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2
                        )
            else:
                is_yawning = False

            if is_yawning:
                yawn_status = "YAWNING - MAR above threshold"
                yawn_color = (0, 0, 255)
            elif time.monotonic() < yawn_notice_until:
                yawn_status = yawn_notice
                yawn_color = (0, 255, 255)
            else:
                yawn_status = ""
                yawn_color = (0, 255, 0)

            if yawn_status:
                cv2.putText(
                    frame,
                    yawn_status,
                    (20, frame.shape[0] - 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    yawn_color,
                    2
                )

            cv2.imshow("Behavioral Monitor", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        camera.release()
        detector.close()


if __name__ == "__main__":
    main()

import mediapipe as mp
import os

path = os.path.join(
    os.path.dirname(mp.__file__),
    "modules",
    "face_landmark",
    "face_landmark_front_cpu.binarypb"
)

print("Ścieżka:", path)
print("Istnieje:", os.path.exists(path))
print("Plik:", os.path.isfile(path))

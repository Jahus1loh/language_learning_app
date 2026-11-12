
import cv2


class Camera:
    def __init__(self, camera_id=0):
        self.camera = cv2.VideoCapture(camera_id)

        if not self.camera.isOpened():
            raise RuntimeError("Nie można uruchomić kamery")

    def get_frame(self):
        success, frame = self.camera.read()

        if not success:
            return None

        # Odbicie obrazu jak w lustrze
        frame = cv2.flip(frame, 1)

        return frame

    def release(self):
        self.camera.release()
        cv2.destroyAllWindows()

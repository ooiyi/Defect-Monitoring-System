import cv2
from PIL import Image, ImageTk
import mediapipe as mp

class CameraModule_checkstep:
    def __init__(self):
        self.cap = None  # Camera capture object
        self.running = False  # To track if the camera is running
        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,                # Detect up to 2 hands
            min_detection_confidence=0.5    # Adjust confidence as needed
        )
        self.zoom_factor = 1.0  # Default zoom factor

    def start_feed(self, video_label):
        if not self.running:
            self.cap = cv2.VideoCapture(1)  # Open the default camera
            if not self.cap.isOpened():
                print("Error: Unable to access the camera.")
                return
            self.running = True
            self._update_frame(video_label)

    def stop_feed(self):
        if self.running and self.cap is not None:
            self.running = False
            self.cap.release()  # Release the camera

    def _update_frame(self, video_label):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if ret:
            # Apply zoom
            frame = self._apply_zoom(frame)

            # Resize the frame to a larger resolution (e.g., 640x480)
            frame = cv2.resize(frame, (480, 360))

            # Convert frame to a format compatible with Tkinter
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            # Update the video label
            video_label.imgtk = imgtk  # Keep a reference to avoid garbage collection
            video_label.config(image=imgtk)

        # Schedule the next frame update
        video_label.after(10, lambda: self._update_frame(video_label))

    def _apply_zoom(self, frame):
        """Apply zoom to the given frame based on the zoom factor."""
        if self.zoom_factor == 1.0:
            return frame

        h, w, _ = frame.shape
        center_x, center_y = w // 2, h // 2

        # Calculate the new width and height based on zoom factor
        new_w = int(w / self.zoom_factor)
        new_h = int(h / self.zoom_factor)

        # Ensure the dimensions are within bounds
        if new_w <= 0 or new_h <= 0:
            return frame

        # Calculate the cropping box
        x1 = max(0, center_x - new_w // 2)
        x2 = min(w, center_x + new_w // 2)
        y1 = max(0, center_y - new_h // 2)
        y2 = min(h, center_y + new_h // 2)

        # Crop and resize the frame back to original dimensions
        cropped_frame = frame[y1:y2, x1:x2]
        return cv2.resize(cropped_frame, (w, h))

    def set_zoom_factor(self, zoom_factor):
        """Set the zoom factor for the camera module."""
        if zoom_factor > 0:
            self.zoom_factor = zoom_factor
        else:
            print("Invalid zoom factor. It must be greater than 0.")

    def get_current_frame(self):
        """Retrieve the current frame from the video feed."""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

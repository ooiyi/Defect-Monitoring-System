import cv2
from PIL import Image, ImageTk

class CameraModule2:
    def __init__(self):
        self.cap = None  # Camera capture object
        self.running = False  # To track if the camera is running
        self.video_label = None  # Tkinter video label
        self.zoom_factor = 1.0  # Initial zoom factor
        self.zoom_step = 0.1  # Step size for zoom in/out
        self.min_zoom = 1.0  # Minimum zoom (default frame)
        self.max_zoom = 2.0  # Maximum zoom level

    def start_feed(self, video_label):
        """Start the video feed."""
        if not self.running:
            self.cap = cv2.VideoCapture(3)  # Open the default camera
            if not self.cap.isOpened():
                print("Error: Unable to access the camera.")
                return
            self.running = True
            self.video_label = video_label
            self._update_frame()

    def stop_feed(self):
        """Stop the video feed."""
        if self.running and self.cap is not None:
            self.running = False
            self.cap.release()  # Release the camera
            self.video_label.config(image="")  # Clear the video feed label

    def _update_frame(self):
        """Update the video feed frame."""
        if not self.running:
            return

        ret, frame = self.cap.read()
        if ret:
            # Apply zoom by cropping and resizing
            frame = self._apply_zoom(frame)

            # Convert frame to a format compatible with Tkinter
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            # Update the video label
            self.video_label.imgtk = imgtk  # Keep a reference to avoid garbage collection
            self.video_label.config(image=imgtk)

        # Schedule the next frame update
        self.video_label.after(10, self._update_frame)

    def zoom_in(self):
        """Zoom in by increasing the zoom factor."""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor += self.zoom_step
            print(f"Zoomed In: Zoom factor is now {self.zoom_factor:.1f}")

    def zoom_out(self):
        """Zoom out by decreasing the zoom factor."""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor -= self.zoom_step
            print(f"Zoomed Out: Zoom factor is now {self.zoom_factor:.1f}")

    def _apply_zoom(self, frame):
        """Apply zoom by cropping and resizing the frame."""
        if self.zoom_factor == 1.0:
            return frame  # No zoom

        height, width, _ = frame.shape
        center_x, center_y = width // 2, height // 2

        # Calculate cropping dimensions
        new_width = int(width / self.zoom_factor)
        new_height = int(height / self.zoom_factor)

        x1 = max(0, center_x - new_width // 2)
        y1 = max(0, center_y - new_height // 2)
        x2 = min(width, center_x + new_width // 2)
        y2 = min(height, center_y + new_height // 2)

        # Crop and resize frame
        cropped_frame = frame[y1:y2, x1:x2]
        resized_frame = cv2.resize(cropped_frame, (width, height), interpolation=cv2.INTER_LINEAR)

        return resized_frame

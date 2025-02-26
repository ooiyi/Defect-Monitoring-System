import cv2
from PIL import Image, ImageTk

class CameraModule:
    def __init__(self):
        self.cap = None  # Camera capture object
        self.running = False  # To track if the camera is running

    def start_feed(self, video_label):
        if not self.running:
            self.cap = cv2.VideoCapture(0)  # Open the default camera
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

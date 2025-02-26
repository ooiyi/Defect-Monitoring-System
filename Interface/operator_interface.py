import tkinter as tk
import pandas as pd
import time
from check_step_cam import CameraModule_checkstep
import socket
import cv2

class OperatorInterface:
    def __init__(self, selected_process, parent_interface, detection_interface=None):
        self.window = tk.Toplevel()
        self.window.title('Operator Interface')
        self.parent_interface = parent_interface  # Reference to the RotatableCameraInterface
        self.detection_interface = detection_interface  # Reference to the OpenDetectionInterface
        
        # Load steps from supervisor based on selected process
        try:
            df = pd.read_csv("assembly_steps.csv")
            self.steps = df[df['process'] == selected_process].to_dict('records')
        except FileNotFoundError:
            tk.Label(self.window, text="Error: No Steps Defined!", fg="red").grid(row=0, column=0, columnspan=2, pady=10)
            return

        if not self.steps:
            tk.Label(self.window, text="Error: No Steps for Selected Process!", fg="red").grid(row=0, column=0, columnspan=2, pady=10)
            return

        self.current_step = 0
        self.step_h_angle = 90
        self.step_v_angle = 90
        self.step_time = 0
        self.step_zoom_factor = 1.0

        # Initialize socket connection to RPi
        self.rpi_host = "192.168.137.121"  # Replace with your RPi's IP address
        self.rpi_port = 5000
        self.socket = None

        # Camera feed setup
        self.camera_module = CameraModule_checkstep()
        self.video_label = tk.Label(self.window, bg="black")
        self.video_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        # Start the camera feed
        self.camera_module.start_feed(self.video_label)

        # Step display
        self.step_label = tk.Label(self.window, text="Current Step: ", font=("Arial", 14))
        self.step_label.grid(row=1, column=0, columnspan=2, pady=10)

        # Correctness display
        self.correctness_display = tk.Text(self.window, height=10, width=50, font=("Arial", 12))
        self.correctness_display.grid(row=2, column=0, columnspan=2, pady=10)

        # Alert display
        self.alert_label = tk.Label(self.window, text="", font=("Arial", 14), fg="red")
        self.alert_label.grid(row=3, column=0, columnspan=2, pady=10)

        # Start processing steps
        self.start_step()

        # Add a "Back to Supervisor Interface" button
        tk.Button(self.window, text="Finish Process", command=self.navigate_back).grid(row=4, column=0, columnspan=2, pady=10)

        # Bind cleanup function to close window
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_step(self):
        if self.current_step >= len(self.steps):
            self.step_label.config(text="All steps completed!")
            self.correctness_display.insert(tk.END, "Process completed successfully!\n", "blue")
            self.correctness_display.tag_configure("blue", foreground="blue")
            return

        # Get step details from the CSV
        step_details = self.steps[self.current_step]
        self.step_h_angle = step_details["h_angle"]
        self.step_v_angle = step_details["v_angle"]
        self.step_time = step_details["time"]
        self.step_zoom_factor = step_details["zoom_factor"]  # Default zoom factor is 1.0

        # Apply zoom factor to the camera
        self.camera_module.set_zoom_factor(self.step_zoom_factor)

        # Send angles to RPi
        self.send_angles_to_rpi()

        # Update UI with current step
        step_number = step_details["step_number"]
        self.step_label.config(text=f"Current Step: {step_number}")

        # Start step processing
        if self.current_step == 0:
            self.first_step_hand_detected_time = 0
            self.first_step_detection_start = None
            self.process_first_step()
        else:
            self.process_step()

    def process_first_step(self):
        frame = self.camera_module.get_current_frame()
        if frame is not None:
            # Convert frame to RGB for MediaPipe processing
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.camera_module.mp_hands.process(frame_rgb)

            if results.multi_hand_landmarks:
                if self.first_step_detection_start is None:
                    self.first_step_detection_start = time.time()
                else:
                    self.first_step_hand_detected_time += time.time() - self.first_step_detection_start
                    self.first_step_detection_start = time.time()

            else:
                self.first_step_detection_start = None

            if self.first_step_hand_detected_time >= self.step_time:
                self.correctness_display.insert(
                    tk.END,
                    f"Step {self.current_step + 1}: Correct!\n",
                    "green",
                )
                self.correctness_display.tag_configure("green", foreground="green")
                self.current_step += 1
                self.window.after(1000, self.start_step)
                return

        # Schedule the next check
        self.window.after(100, self.process_first_step)

    def process_step(self):
        start_time = time.time()
        hand_detected_time = 0
        detection_start = None

        def check_hand_detection():
            nonlocal hand_detected_time, detection_start
            frame = self.camera_module.get_current_frame()
            if frame is not None:
                # Convert frame to RGB for MediaPipe processing
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.camera_module.mp_hands.process(frame_rgb)

                if results.multi_hand_landmarks:
                    if detection_start is None:
                        detection_start = time.time()
                    else:
                        hand_detected_time += time.time() - detection_start
                        detection_start = time.time()
                else:
                    detection_start = None

                if hand_detected_time >= self.step_time:
                    self.correctness_display.insert(
                        tk.END,
                        f"Step {self.current_step + 1}: Correct!\n",
                        "green",
                    )
                    self.correctness_display.tag_configure("green", foreground="green")
                    self.current_step += 1
                    self.window.after(1000, self.start_step)
                    return

            if time.time() - start_time < 2 * self.step_time:
                self.window.after(100, check_hand_detection)
            else:
                self.correctness_display.insert(
                    tk.END,
                    f"Step {self.current_step + 1}: Incorrect! Timeout exceeded.\n",
                    "red",
                )
                self.correctness_display.tag_configure("red", foreground="red")
                self.alert_label.config(text=f"ALERT: Step {self.current_step + 1} failed! Stopping process.")
                self.beep_rpi()

        check_hand_detection()

    def send_angles_to_rpi(self):
        try:
            if self.socket is None:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.rpi_host, self.rpi_port))

            data = f"1,{self.step_h_angle},{self.step_v_angle}"  # 1 for cam1
            self.socket.sendall(data.encode('utf-8'))
            print(f"Sent angles to RPi: {data}")
        except Exception as e:
            print(f"Error sending angles to RPi: {e}")
            self.socket = None

    def beep_rpi(self):
        try:
            if self.socket is None:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.rpi_host, self.rpi_port))
            
            data = f"BEEP,1,3"  # 1 for cam1, 3 for 3sec
            self.socket.sendall(data.encode('utf-8'))
            print(f"Sent angles to RPi: {data}")
        except Exception as e:
            print(f"Error sending beep to RPi: {e}")
            self.socket = None

    def navigate_back(self):
        """Navigate back to the parent interface."""
        self.camera_module.stop_feed()
        if self.detection_interface:
            self.detection_interface.stop_detection()
        self.window.destroy()
        self.parent_interface.window.deiconify()

    def on_close(self):
        """Handle cleanup when the window is closed."""
        self.navigate_back()

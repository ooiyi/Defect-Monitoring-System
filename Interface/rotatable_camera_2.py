import tkinter as tk
import pandas as pd
from cam2 import CameraModule2
import socket

class RotatableCameraInterface_2:
    def __init__(self, return_to_main_callback=None, refresh_processes_callback=None):
        # Store the callback functions
        self.return_to_main_callback = return_to_main_callback
        self.refresh_processes_callback = refresh_processes_callback

        # Create a new Toplevel window
        self.window = tk.Toplevel()
        self.window.title("Rotatable Camera Interface")

        self.steps = []
        self.step_number = 1
        self.is_visualizing = False
        self.process_name_set = False  # Track if the process name is set initially

        # Create an instance of camera module
        self.camera_module = CameraModule2()

        # Initialize socket connection to RPi
        self.rpi_host = "192.168.137.121"  # Replace with your RPi's IP address
        self.rpi_port = 5000
        self.socket = None
        
        # Initialize camera angles
        self.horizontal_angle = 90
        self.vertical_angle = 90
        self.send_angles_to_rpi()

        # Initialize zoom
        self.zoom_factor = 1.0  # Initial zoom factor
        self.zoom_step = 0.1  # Step size for zoom in/out
        self.min_zoom = 1.0  # Minimum zoom (default frame)
        self.max_zoom = 2.0  # Maximum zoom level

        # Left Frame for controls
        left_frame = tk.Frame(self.window)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Video feed on the right
        self.video_label = tk.Label(self.window, bg="black")  # Keep black background
        self.video_label.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.video_label.grid_remove()  # Hide initially

        # Configure grid weights for resizing
        self.window.columnconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=3)  # Allocate more space for the video feed
        self.window.rowconfigure(0, weight=1)

        # Input fields
        tk.Label(left_frame, text="Process Name:").grid(row=0, column=0, sticky="e", padx=10, pady=5)
        self.process_name = tk.Entry(left_frame)
        self.process_name.grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="w")

        tk.Label(left_frame, text="Time Required (s):").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.time_required = tk.Entry(left_frame)
        self.time_required.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="w")

        # Adjust the angle section
        tk.Label(left_frame, text="Adjust Angle:").grid(row=2, column=0, sticky="e", padx=10, pady=5)

        angle_frame = tk.Frame(left_frame)
        angle_frame.grid(row=2, column=1, columnspan=2, pady=5)

        tk.Button(angle_frame, text="Up", width=10, command=self.move_up).grid(row=0, column=1, pady=5)
        tk.Button(angle_frame, text="Left", width=10, command=self.move_left).grid(row=1, column=0, padx=5)
        tk.Button(angle_frame, text="Right", width=10, command=self.move_right).grid(row=1, column=2, padx=5)
        tk.Button(angle_frame, text="Down", width=10, command=self.move_down).grid(row=2, column=1, pady=5)

        # Add Zoom In and Zoom Out buttons
        tk.Button(angle_frame, text="Zoom In", width=10, command=self.zoom_in).grid(row=0, column=3, padx=5)
        tk.Button(angle_frame, text="Zoom Out", width=10, command=self.zoom_out).grid(row=2, column=3, padx=5)

        # Visualization buttons in a labeled box
        visualization_frame = tk.LabelFrame(left_frame, text="Visualization Controls", padx=10, pady=10)
        visualization_frame.grid(row=3, column=0, columnspan=3, pady=10, padx=10)

        # Buttons inside the labeled box
        tk.Button(visualization_frame, text="Start Visualization", command=self.start_visualization).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(visualization_frame, text="Add Step", command=self.add_step).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(visualization_frame, text="Stop Visualization", command=self.stop_visualization).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(visualization_frame, text="Save Process", command=self.save_steps).grid(row=1, column=1, padx=5, pady=5)

        # Steps display
        tk.Label(left_frame, text="Steps:").grid(row=7, column=0, columnspan=3, padx=10, pady=5)
        self.step_display = tk.Text(left_frame, height=20, width=65)
        self.step_display.grid(row=8, column=0, columnspan=3, padx=10, pady=5)

        # Add a button to return to the main interface
        tk.Button(self.window, text="Return to Main", command=self.return_to_main).grid(row=9, column=0, columnspan=3, pady=10)

    def start_visualization(self):
        # Show the video label when visualization starts
        self.video_label.grid()  # Make the video_label visible
    
        # Start the camera feed
        self.camera_module.start_feed(self.video_label)

        if not self.is_visualizing:
            process = self.process_name.get().strip()
            if not self.process_name_set:
                if process:
                    self.step_display.insert(tk.END, f"\nProcess Name: {process}\n")
                    self.process_name_set = True
                    self.process_name.config(state='disabled')  # Disable input for process name
                
                    # Reset step number for the new process
                    self.step_number = 1  
                else:
                    tk.Label(self.window, text="Please enter a process name before starting!", fg="red").grid(row=11, column=0, columnspan=2)
                    return

            self.is_visualizing = True
            print("Starting video visualization...")

    def add_step(self):
        if not self.is_visualizing:
            tk.Label(self.window, text="Start visualization before adding steps", fg="red").grid(row=11, column=0, columnspan=2)
            return

        time = self.time_required.get().strip()
        dummy_angle = 45

        if time.isdigit():
            self.steps.append({"step_number": self.step_number, "process": self.process_name.get().strip(), "h_angle": self.horizontal_angle, "v_angle": self.vertical_angle, "time": int(time), "zoom_factor": self.zoom_factor})
            self.step_display.insert(tk.END, f"Step: {self.step_number}: Horizontal angle: {self.horizontal_angle}, Vertical Angle: {self.vertical_angle}, Time: {time}s, Zoom Factor: {self.zoom_factor}\n")
            self.step_number += 1

            # Clear input fields
            self.time_required.delete(0, tk.END)
        else:
            tk.Label(self.window, text="Invalid input. Please try again!", fg="red").grid(row=11, column=0, columnspan=2)

    def stop_visualization(self):
        # Hide initially
        self.video_label.grid_remove() 
        # Stop the camera feed
        self.camera_module.stop_feed()
        self.video_label.config(image="")  # Clear the video feed

        if self.is_visualizing:
            self.is_visualizing = False
            print("Stopping video visualization...")
            self.process_name_set = False  # Allow setting a new process name after stopping
            self.process_name.config(state='normal')  # Enable input for process name
            self.process_name.delete(0, tk.END)  # Clear the process name field

    def save_steps(self):
        if not self.steps:
            tk.Label(self.window, text="No steps to save!", fg="red").grid(row=11, column=0, columnspan=2)
            return

        # Convert the steps to a DataFrame
        new_steps_df = pd.DataFrame(self.steps)
        new_steps_df['step_number'] = new_steps_df.groupby('process').cumcount() + 1
        new_steps_df = new_steps_df[['process', 'step_number', 'h_angle', 'v_angle', 'time', 'zoom_factor']]

        try:
            existing_steps_df = pd.read_csv("assembly_steps.csv")
            combined_steps_df = pd.concat([existing_steps_df, new_steps_df], ignore_index=True)
        except FileNotFoundError:
            combined_steps_df = new_steps_df

        combined_steps_df.to_csv("assembly_steps.csv", index=False)
        tk.Label(self.window, text="Steps Saved!", fg="green").grid(row=11, column=0, columnspan=2)

        if self.refresh_processes_callback:
            self.refresh_processes_callback()

    def return_to_main(self):
        if self.return_to_main_callback:
            self.window.destroy()
            self.return_to_main_callback()

    def send_angles_to_rpi(self):
        try:
            if self.socket is None:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.rpi_host, self.rpi_port))

            data = f"{2},{self.horizontal_angle},{self.vertical_angle}" # 1 for cam1
            self.socket.sendall(data.encode('utf-8'))
            print(f"Sent angles to RPi: {data}")
        except Exception as e:
            print(f"Error sending angles to RPi: {e}")
            self.socket = None  # Reset the socket if an error occurs

    def move_up(self):
        self.vertical_angle = min(180, self.vertical_angle + 1)
        self.send_angles_to_rpi()

    def move_down(self):
        self.vertical_angle = max(0, self.vertical_angle - 1)
        self.send_angles_to_rpi()

    def move_left(self):
        self.horizontal_angle = max(0, self.horizontal_angle + 1)
        self.send_angles_to_rpi()

    def move_right(self):
        self.horizontal_angle = min(180, self.horizontal_angle - 1)
        self.send_angles_to_rpi()

    def zoom_in(self):
        try:
            self.camera_module.zoom_in()  # Assume CameraModule1 has this method
            if self.zoom_factor < self.max_zoom:
                self.zoom_factor += self.zoom_step
                print("Zoomed In")
        except Exception as e:
            print(f"Error zooming in: {e}")

    def zoom_out(self):
        try:
            self.camera_module.zoom_out()  # Assume CameraModule1 has this method
            if self.zoom_factor > self.min_zoom:
                self.zoom_factor -= self.zoom_step
                print("Zoomed Out")
        except Exception as e:
            print(f"Error zooming out: {e}")

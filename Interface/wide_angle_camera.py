import tkinter as tk
from tkinter import messagebox
import pandas as pd
from roi_selector import select_roi


class WideAngleCameraInterface:
    def __init__(self, root, return_to_main_callback):
        """
        Initialize the Wide-Angle Camera Interface.

        :param root: The root Tkinter window.
        :param return_to_main_callback: A callback function to navigate back to the main interface.
        """
        self.root = root  # Reference to the root window
        self.return_to_main_callback = return_to_main_callback  # Callback for navigation back to main
        self.window = tk.Toplevel(root)
        self.window.title("Wide-Angle Camera Interface")

        # Initialize attributes
        self.roi_coordinates = None
        self.roi_file = "roi_coordinates.csv"  # File to save ROI

        # Create video feed frame
        self.video_frame = tk.Frame(self.window, bg="black", bd=2, relief="ridge")
        self.video_frame.pack(pady=10)
        self.video_label = tk.Label(self.video_frame, text="Video Feed", font=("Arial", 14), fg="white", bg="black")
        self.video_label.pack()

        # Button frame
        self.button_frame = tk.Frame(self.window)
        self.button_frame.pack(pady=10, fill="x")

        # ROI selection button
        self.roi_button = tk.Button(self.button_frame, text="Select ROI", command=self.select_roi)
        self.roi_button.pack(side="left", padx=10)

        # Back button
        self.back_button = tk.Button(self.button_frame, text="Back to Main", command=self.navigate_to_main)
        self.back_button.pack(side="left", padx=10)

        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def select_roi(self):
        """Open the ROI selection tool, store the coordinates, and auto-save to CSV."""
        self.roi_coordinates = select_roi(camera_index=0, resolution=(1280, 720))
        if self.roi_coordinates and None not in self.roi_coordinates:
            messagebox.showinfo("ROI Selection", f"ROI selected: {self.roi_coordinates}")
            self.auto_save_roi()
        else:
            messagebox.showerror("ROI Selection", "No valid ROI selected.")

    def auto_save_roi(self):
        """Automatically save the selected ROI to a CSV file."""
        if self.roi_coordinates:
            try:
                # Prepare the ROI data for saving
                roi_data = {
                    "x1": [self.roi_coordinates[0]],
                    "y1": [self.roi_coordinates[1]],
                    "x2": [self.roi_coordinates[2]],
                    "y2": [self.roi_coordinates[3]],
                }

                # Write the data to a CSV file
                df = pd.DataFrame(roi_data)
                df.to_csv(self.roi_file, index=False)
                messagebox.showinfo("Auto Save ROI", f"ROI coordinates automatically saved to {self.roi_file}")
            except Exception as e:
                messagebox.showerror("Auto Save ROI", f"Error saving ROI: {e}")

    def navigate_to_main(self):
        """Navigate back to the main interface."""
        self.window.destroy()  # Close this interface
        self.return_to_main_callback()  # Call the main interface callback

    def on_closing(self):
        """Handle the closing event."""
        self.window.destroy()
        self.return_to_main_callback()

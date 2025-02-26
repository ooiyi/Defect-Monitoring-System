import tkinter as tk
from rotatable_camera import RotatableCameraInterface
from rotatable_camera_2 import RotatableCameraInterface_2
from wide_angle_camera import WideAngleCameraInterface
import pandas as pd
from operator_interface import OperatorInterface
from open_detection import OpenDetectionInterface

# Function to open wide-angle camera interface
def open_wide_camera():
    WideAngleCameraInterface(root, return_to_main)

# Function to open rotatable camera interface
def open_rotatable_camera():
    # Create the interface and pass the necessary callbacks
    RotatableCameraInterface(
        return_to_main_callback=return_to_main,
        refresh_processes_callback=load_available_processes
    )

def open_rotatable_camera_2():
    # Create the interface and pass the necessary callbacks
    RotatableCameraInterface_2(
        return_to_main_callback=return_to_main,
        refresh_processes_callback=load_available_processes
    )

def return_to_main():
    # If necessary, perform any cleanup actions here
    print("Returning to the main interface.")
    
# Function to load available processes from CSV
def load_available_processes():
    try:
        # Read the CSV file
        df = pd.read_csv("assembly_steps.csv")
        # Get unique process names
        processes = df['process'].unique()
        # Clear the current display
        process_list_display.config(state='normal')
        process_list_display.delete(1.0, tk.END)
        # Insert the process names into the text box
        for process in processes:
            process_list_display.insert(tk.END, f"{process}\n")
        process_list_display.config(state='disabled')  # Prevent editing
    except FileNotFoundError:
        # If the file doesn't exist, show a default message
        process_list_display.config(state='normal')
        process_list_display.delete(1.0, tk.END)
        process_list_display.insert(tk.END, "No processes available.\n")
        process_list_display.config(state='disabled')

# Function to start operator interface
def start_operator_interface():
    selected_process = current_process_entry.get().strip()
    detection_window = None
    try:
        # Validate and start the operator interface
        df = pd.read_csv("assembly_steps.csv")
        if selected_process not in df['process'].unique():
            tk.Label(root, text="Invalid process selected!", fg="red").pack(pady=5)
            return
        
        detection_window = OpenDetectionInterface()
        detection_window.window.geometry(f"700x700+560+100")
        
        operator_window = OperatorInterface(selected_process, root, detection_interface=detection_window)
        operator_window.window.geometry(f"500x700+50+100")
        
    except FileNotFoundError:
        tk.Label(root, text="No processes saved!", fg="red").pack(pady=5)
        
# Main GUI
root = tk.Tk()
root.title("Assembly Monitoring System")

label = tk.Label(root, text="Select The Camera", font=("Arial", 16))
label.pack(pady=20)

# Button for wide-angle camera
btn_wide_camera = tk.Button(root, text="Wide-Angle Camera", command=open_wide_camera, width=20, height=2)
btn_wide_camera.pack(pady=10)

# Button for rotatable camera 1
btn_rotatable1 = tk.Button(root, text="Rotatable Camera 1", command=open_rotatable_camera, width=20, height=2)
btn_rotatable1.pack(pady=10)

# Button for rotatable camera 2
btn_rotatable2 = tk.Button(root, text="Rotatable Camera 2", command=open_rotatable_camera_2, width=20, height=2)
btn_rotatable2.pack(pady=10)

# Section for processes
process_label = tk.Label(root, text="Available Processes:", font=("Arial", 12))
process_label.pack(pady=10)

process_list_display = tk.Text(root, height=5, width=40, state='disabled')
process_list_display.pack(pady=5)

tk.Label(root, text="Type Current Process:").pack(pady=5)
current_process_entry = tk.Entry(root)
current_process_entry.pack(pady=5)

start_process_button = tk.Button(root, text="Start Current Process", command=start_operator_interface)
start_process_button.pack(pady=5)

# Load the available processes at startup
load_available_processes()

root.mainloop()

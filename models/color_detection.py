from ultralytics import YOLO
import cv2
import math
import time
from datetime import datetime
import pandas as pd
import numpy as np
from roi_selector import select_roi  # Import the ROI selection function
from collections import Counter

# Initialize the camera and YOLO model
cap = cv2.VideoCapture(0)
model = YOLO("models/weights/best.pt")

# Set camera resolution to 1920x1080
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Define class names
classNames = ["backpack", "bench", "handbag", "person", "refrigerator", "product"]

# Use the ROI selector to define the region of interest
roi_x1, roi_y1, roi_x2, roi_y2 = select_roi(camera_index=0, resolution=(1920, 1080))

# Ensure valid ROI selection
if None in (roi_x1, roi_y1, roi_x2, roi_y2):
    print("No valid ROI selected. Exiting...")
    cap.release()
    cv2.destroyAllWindows()
    exit()

# Tracking objects
tracked_objects = {}
next_object_id = 1
buffer_time = 1  # Buffer for maintaining stability
iou_threshold = 0.2  # Minimum IoU for considering as the same object
distance_threshold = 150  # Euclidean distance threshold
min_duration = 10  # Minimum duration (in seconds) for logging

# Data logging
logged_data = []

# Helper function to calculate IoU
def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

# Function to detect the dominant color in an image
def detect_color(roi):
    """
    Detect the dominant color in the given region of interest (ROI).
    """
    # Resize ROI for faster processing
    resized_roi = cv2.resize(roi, (50, 50))
    # Blur to smooth out noise
    blurred_roi = cv2.GaussianBlur(resized_roi, (15, 15), 0)
    # Compute the average color
    avg_color = blurred_roi.mean(axis=0).mean(axis=0)  # BGR format
    return avg_color

# Function to map RGB color to a color name
def map_color_to_name(bgr_color):
    """
    Map a BGR color to a predefined color name based on proximity.
    """
    # Basic color mapping
    color_names = {
        (255, 0, 0): "Red",
        (0, 255, 0): "Green",
        (0, 0, 255): "Blue",
        (255, 255, 0): "Yellow",
        (255, 165, 0): "Orange",
        (128, 0, 128): "Purple",
        (0, 255, 255): "Cyan",
        (255, 192, 203): "Pink",
        (0, 0, 0): "Black",
        (255, 255, 255): "White",
        (128, 128, 128): "Gray",
        (165, 42, 42): "Brown"
    }

    # Convert BGR to RGB
    rgb_color = (bgr_color[2], bgr_color[1], bgr_color[0])

    # Find the closest color by Euclidean distance
    closest_color = min(color_names.keys(),
                        key=lambda c: math.sqrt((c[0] - rgb_color[0])**2 +
                                                (c[1] - rgb_color[1])**2 +
                                                (c[2] - rgb_color[2])**2))
    return color_names[closest_color]

# Function to detect upper clothing color
def detect_upper_clothing_color(bbox, image):
    """
    Extracts the upper body area (T-shirt area) from the bounding box
    and detects the dominant color in the region.
    """
    x1, y1, x2, y2 = bbox
    # Define the upper body region as the top 40% of the bounding box
    upper_y2 = y1 + int((y2 - y1) * 0.4)  # Only the top 40%
    upper_roi = image[y1:upper_y2, x1:x2]  # Extract the upper ROI

    if upper_roi.size > 0:  # Ensure ROI is valid
        # Detect the dominant color in the ROI
        bgr_color = detect_color(upper_roi)
        color_name = map_color_to_name(bgr_color)
    else:
        color_name = "Unknown"  # Fallback if ROI is invalid

    return color_name

# Main loop
while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture frame. Exiting...")
        break

    results = model(img, stream=True, conf=0.7)

    # Draw the ROI rectangle on the frame
    cv2.rectangle(img, (roi_x1, roi_y1), (roi_x2, roi_y2), (0, 255, 0), 2)  # Green ROI border

    detected_objects = []

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            class_id = int(box.cls[0])
            class_name = classNames[class_id]

            if class_name == "person":
                # Detect upper body (T-shirt area) color
                color_name = detect_upper_clothing_color((x1, y1, x2, y2), img)

                detected_objects.append({
                    'bbox': (x1, y1, x2, y2),
                    'class_name': class_name,
                    'color': color_name
                })

            elif class_name == "product":
                if x1 >= roi_x1 and y1 >= roi_y1 and x2 <= roi_x2 and y2 <= roi_y2:
                    detected_objects.append({'bbox': (x1, y1, x2, y2), 'class_name': class_name})

    current_time = time.time()
    new_tracked_objects = {}

    for detected in detected_objects:
        bbox = detected['bbox']
        class_name = detected['class_name']
        color_name = detected.get('color', 'N/A')  # Get color for "person" class

        # Assign a unique ID to each object
        best_match_id = None
        best_iou = 0

        # Match with existing tracked objects
        for obj_id, tracked in tracked_objects.items():
            if tracked['class_name'] != class_name:
                continue

            iou = calculate_iou(bbox, tracked['bbox'])
            if iou > best_iou and iou > iou_threshold:
                best_match_id = obj_id
                best_iou = iou

        if best_match_id is not None:
            # Update existing object
            new_tracked_objects[best_match_id] = {
                'bbox': bbox,
                'start_time': tracked_objects[best_match_id]['start_time'],
                'last_seen': current_time,
                'class_name': class_name,
                'color': color_name
            }
        else:
            # Create a new object
            new_tracked_objects[next_object_id] = {
                'bbox': bbox,
                'start_time': current_time,
                'last_seen': current_time,
                'class_name': class_name,
                'color': color_name
            }
            next_object_id += 1

    tracked_objects = new_tracked_objects

    # Draw bounding boxes and labels
    for obj_id, tracked in tracked_objects.items():
        bbox = tracked['bbox']
        elapsed_time = current_time - tracked['start_time']

        label = f"{tracked['class_name']} {obj_id}"
        if tracked['class_name'] == "person":
            label += f" ({tracked['color']})"  # Add color to the label

        cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 255), 3)
        cv2.putText(img, label, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Display the frame
    cv2.imshow('Webcam', img)

    # Exit the loop when 'q' is pressed
    if cv2.waitKey(1) == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

# Save logged data to a CSV
df = pd.DataFrame(logged_data)
df.to_csv("Time_data.csv", index=False)
print("ROI data saved to Time_data.csv")
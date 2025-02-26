import cv2

# Initialize the camera
cap = cv2.VideoCapture(0)  # Change '0' to your camera index if using multiple cameras

# Get the camera resolution
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Camera resolution: {width}x{height}")

# Display the camera feed to confirm
while True:
    success, frame = cap.read()
    if not success:
        break

    # Show the resolution on the frame
    cv2.putText(frame, f"Resolution: {width}x{height}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Camera Feed", frame)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

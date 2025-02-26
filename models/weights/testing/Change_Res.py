import cv2

# Initialize the camera
cap = cv2.VideoCapture(0)  # Change '0' to your camera index if needed

# Set the resolution to 1920x1080
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Get the resolution to verify
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Resolution set to: {width}x{height}")

# Display the camera feed
while True:
    success, frame = cap.read()
    if not success:
        break

    cv2.putText(frame, f"Resolution: {width}x{height}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Camera Feed", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

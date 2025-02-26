import cv2
import mediapipe as mp
import time

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands

# Set up video capture
cap = cv2.VideoCapture(1)

# Variables to track hand detection and timer
hand_detected = False
start_time = None

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,                # Detect up to 2 hands
    min_detection_confidence=0.5    # Adjust confidence as needed
) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame to detect hands
        results = hands.process(frame_rgb)

        # Check if hands are detected
        if results.multi_hand_landmarks: # if detected
            if not hand_detected:  # Timer flag
                hand_detected = True
                start_time = time.time() 

            # Calculate elapsed time
            elapsed_time = time.time() - start_time if start_time else 0
            cv2.putText(frame, f"Time: {elapsed_time:.2f}s", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            hand_detected = False  # Reset if no hands are detected
            start_time = None

        # Display the frame
        cv2.imshow('Hand Detection with Timer', frame)

        # Exit on pressing 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

# Release resources
cap.release()
cv2.destroyAllWindows()

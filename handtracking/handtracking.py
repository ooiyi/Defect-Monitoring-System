import cv2
import mediapipe as mp

# Initialize MediaPipe Hands and drawing utilities
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Set up video capture
cap = cv2.VideoCapture(1)

# Configure the MediaPipe Hands model
with mp_hands.Hands(
    static_image_mode=False,         # False for live detection
    max_num_hands=1,                 # Detect up to 2 hands
    min_detection_confidence=0.5,    # Minimum confidence for detection
    min_tracking_confidence=0.5,      # Minimum confidence for tracking
    model_complexity=1
) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Ignoring empty frame.")
            continue

        # Convert the frame to RGB as MediaPipe requires
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame with MediaPipe
        results = hands.process(frame_rgb)

        # Draw hand annotations on the frame
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Display the annotated frame
        cv2.imshow('Hand Tracking', frame)

        # Break the loop on pressing 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

# Release resources
cap.release()
cv2.destroyAllWindows()

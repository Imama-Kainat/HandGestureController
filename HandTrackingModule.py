import cv2  # Import the OpenCV library for image processing
import mediapipe as mp  # Import the Mediapipe library for hand detection
import time  # Import the time module to measure time intervals
import math  # Import the math module for mathematical calculations

class HandDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        # Initialize the hand detector with parameters
        self.mode = mode  # Set to True for static image mode (only one frame), False for video mode
        self.maxHands = int(maxHands)  # Maximum number of hands to detect (default is 2)
        self.detectionCon = float(detectionCon)  # Confidence level for detecting hands
        self.trackCon = float(trackCon)  # Confidence level for tracking hands

        # Set up the Mediapipe Hands module
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,  # Use static or video mode
            max_num_hands=self.maxHands,  # Maximum number of hands to detect
            min_detection_confidence=self.detectionCon,  # Minimum confidence for detection
            min_tracking_confidence=self.trackCon  # Minimum confidence for tracking
        )
        
        # Set up drawing utilities for hand landmarks
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]  # List of IDs for fingertip landmarks

    def findHands(self, img, draw=True):
        # Convert the image from BGR to RGB format for Mediapipe processing
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Process the RGB image to find hands
        self.results = self.hands.process(imgRGB)

        # If hands are detected, draw landmarks on the image
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    # Draw hand landmarks and connections on the image
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img  # Return the image with drawn landmarks

    def findPosition(self, img, handNo=0, draw=True):
        # Initialize lists to hold landmark positions
        xList = []
        yList = []
        bbox = []  # Bounding box for the hand
        self.lmList = []  # List of landmarks for the hand
        
        # Check if hands were detected
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]  # Get the landmarks of the specified hand
            for id, lm in enumerate(myHand.landmark):  # Loop through each landmark
                h, w, c = img.shape  # Get the dimensions of the image
                cx, cy = int(lm.x * w), int(lm.y * h)  # Convert normalized coordinates to pixel coordinates
                xList.append(cx)  # Add x coordinate to list
                yList.append(cy)  # Add y coordinate to list
                self.lmList.append([id, cx, cy])  # Add landmark ID and coordinates to the list
                if draw:
                    # Draw a circle at the landmark position
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                    
            # Calculate the bounding box for the hand
            xmin, xmax = min(xList), max(xList)  # Minimum and maximum x coordinates
            ymin, ymax = min(yList), max(yList)  # Minimum and maximum y coordinates
            bbox = xmin, ymin, xmax, ymax  # Create bounding box tuple

            if draw:
                # Draw a rectangle around the bounding box
                cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20), (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)
        
        return self.lmList, bbox  # Return the list of landmarks and bounding box

    def fingersUp(self):
        # Check which fingers are up (extended) and return their state
        fingers = []
        # Check the thumb (ID 4)
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)  # Thumb is up
        else:
            fingers.append(0)  # Thumb is down
        
        # Check the four fingers (IDs 8, 12, 16, 20)
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)  # Finger is up
            else:
                fingers.append(0)  # Finger is down
        
        return fingers  # Return the list of fingers (1 for up, 0 for down)

    def findDistance(self, p1, p2, img, draw=True):
        # Calculate the distance between two specified landmarks (p1 and p2)
        x1, y1 = self.lmList[p1][1], self.lmList[p1][2]  # Get coordinates of the first landmark
        x2, y2 = self.lmList[p2][1], self.lmList[p2][2]  # Get coordinates of the second landmark
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Calculate midpoint between the two landmarks
        
        if draw:
            # Draw circles at the positions of the landmarks
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            # Draw a line between the two landmarks
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            # Draw a circle at the midpoint
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)
        
        # Calculate the distance using the Pythagorean theorem
        length = math.hypot(x2 - x1, y2 - y1)
        return length, img, [x1, y1, x2, y2, cx, cy]  # Return the distance, updated image, and coordinates

def main():
    pTime = 0  # Initialize previous time variable for FPS calculation
    cap = cv2.VideoCapture(0)  # Start capturing video from the default camera (0)
    detector = HandDetector()  # Create an instance of the HandDetector class

    while True:
        success, img = cap.read()  # Read a frame from the video
        if not success:  # Check if the frame was read successfully
            print("Error: Failed to read frame.")
            break  # Exit if frame read fails

        if img is None or img.size == 0:  # Check if the image is empty
            print("Error: Empty frame received.")
            continue  # Skip to the next iteration if empty

        img = detector.findHands(img)  # Detect hands in the image
        lmList, bbox = detector.findPosition(img)  # Get landmark positions and bounding box
        if lmList:  # If landmarks are found
            print(lmList[4])  # Print the coordinates of the tip of the thumb (landmark ID 4)

        cTime = time.time()  # Get the current time
        fps = 1 / (cTime - pTime)  # Calculate the frames per second (FPS)
        pTime = cTime  # Update the previous time for the next calculation

        # Display the FPS on the image
        cv2.putText(img, f"FPS: {int(fps)}", (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
        cv2.imshow("Image", img)  # Show the image in a window

        if cv2.waitKey(1) & 0xFF == ord('q'):  # If 'q' is pressed, exit the loop
            break

    cap.release()  # Release the camera when done
    cv2.destroyAllWindows()  # Close all OpenCV windows

if __name__ == "__main__":
    main()  # Run the main function

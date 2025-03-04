import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
import numpy as np
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import time
import pandas as pd

MARGIN = 10  # pixels for text margin
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54)

# Initialize storage for finger landmarks and movement timing
finger_data = []
start_time = None   # Global timer variable
movement_data = []
overlay = None

# Excel file name
excel_file = "hand_movement_times.xlsx"

def frame_zones(frame):
    #creates overlay to visualize start and end zones
    overlay_img = np.zeros_like(frame)
    height, width,_ = frame.shape
    start_x = int(0.2 * width)
    end_x = int(0.8 * width)
    cv2.rectangle(overlay_img,(start_x,0),(start_x,height),(0,255,0),5) #starting line
    cv2.rectangle(overlay_img,(end_x,0),(end_x,height),(255,0,0),5) #ending line
    cv2.putText(overlay_img,'START ZONE',(5,int(height*0.1)),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)#start text
    cv2.putText(overlay_img,'END ZONE',(end_x+5,int(height*0.1)),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,0,0),2)#end text
    
    return overlay_img

def draw_landmarks_on_frame(rgb_frame, detection_result):
    global start_time, movement_data
    hand_landmarks_list = detection_result.hand_landmarks
    handedness_list = detection_result.handedness
    annotated_frame = np.copy(rgb_frame)
    frame_data = []

    for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]
        handedness_obj = handedness_list[idx]
        # Extract label string
        hand_label = handedness_obj[0].category_name if hasattr(handedness_obj, "__getitem__") else handedness_obj.category_name
       
        hand_data = {
            "Thumb": [],
            "Index": [],
            "Middle": [],
            "Ring": [],
            "Pinky": [],
            "Hand": hand_label
        }
       
        # Collect landmarks for each finger (using indices for thumb, index, etc.)
        for i, landmark in enumerate(hand_landmarks):
            if i in [1, 2, 3, 4]:
                hand_data["Thumb"].append((landmark.x, landmark.y))
            elif i in [5, 6, 7, 8]:
                hand_data["Index"].append((landmark.x, landmark.y))
            elif i in [9, 10, 11, 12]:
                hand_data["Middle"].append((landmark.x, landmark.y))
            elif i in [13, 14, 15, 16]:
                hand_data["Ring"].append((landmark.x, landmark.y))
            elif i in [17, 18, 19, 20]:
                hand_data["Pinky"].append((landmark.x, landmark.y))
               
        frame_data.append(hand_data)
       
        #START TIMER
        for thumb_x, thumb_y in hand_data["Thumb"]:
            if hand_label == "Right" and thumb_x < 0.25:
                if start_time is None:
                    start_time = time.time()
                    print("Right thumb detected on left side. Timer started.")
       
        #STOP TIMER
        for thumb_x, thumb_y in hand_data["Thumb"]:
            if hand_label == "Left" and thumb_x > 0.8:
                if start_time is not None:
                    end_time = time.time()
                    completion_time = end_time - start_time
                    print(f"Left thumb reached right side. Total time: {completion_time:.2f} seconds")
                    movement_data.append({
                        "Start Time": start_time,
                        "End Time": end_time,
                        "Duration (s)": completion_time
                    })
                    save_to_excel(movement_data)
                    start_time = None  # reset the timer after recording
       
        # -- Draw landmarks on frame --
        hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        hand_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) 
            for landmark in hand_landmarks
        ])
        solutions.drawing_utils.draw_landmarks(
            annotated_frame,
            hand_landmarks_proto,
            solutions.hands.HAND_CONNECTIONS,
            solutions.drawing_styles.get_default_hand_landmarks_style(),
            solutions.drawing_styles.get_default_hand_connections_style()
        )

        # -- Draw the hand label on the frame --
        height, width, _ = annotated_frame.shape
        x_coordinates = [landmark.x for landmark in hand_landmarks]
        y_coordinates = [landmark.y for landmark in hand_landmarks]
        text_x = int(min(x_coordinates) * width)
        text_y = int(min(y_coordinates) * height) - MARGIN
        cv2.putText(annotated_frame, hand_label,
                    (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                    FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)
               
    finger_data.append(frame_data)
    return annotated_frame

def save_to_excel(data):
    """Save recorded times to an Excel file."""
    df = pd.DataFrame(data)
    df.to_excel(excel_file, index=False)
    print(f"Data saved to {excel_file}")

# ------------------ Setup HandLandmarker ------------------
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2)
detector = vision.HandLandmarker.create_from_options(options)

# ------------------ Start Video Capture ------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

ret, startup = cap.read()
if overlay is None:
    overlay = frame_zones(startup)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Frame capture failed.")
        break

    # create frame overlay

    # Convert frame to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    # Detect hand landmarks
    detection_result = detector.detect(mp_frame)
    
    # Annotate frame and track timing
    annotated_frame = draw_landmarks_on_frame(rgb_frame, detection_result)
    # adds precomputed overlay
    final_frame = cv2.addWeighted(annotated_frame,1,overlay,1,0)
    
    # Display the annotated frame
    cv2.imshow('Hand Landmark Detection', cv2.cvtColor(final_frame, cv2.COLOR_RGB2BGR))
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Save finger data to file
np.save("finger_data.npy", np.array(finger_data, dtype=object))
print("Finger data saved successfully as 'finger_data.npy'")

cap.release()
cv2.destroyAllWindows()

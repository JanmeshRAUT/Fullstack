import cv2
import mediapipe as mp
import math

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=5,
    refine_landmarks=True,
    min_detection_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
MOUTH = [61, 291, 13, 14]

def eye_aspect_ratio(eye):
    A = math.dist(eye[1], eye[5])
    B = math.dist(eye[2], eye[4])
    C = math.dist(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def mouth_aspect_ratio(mouth):
    X = math.dist(mouth[0], mouth[1])  
    Y = math.dist(mouth[2], mouth[3]) 
    return Y / X

EYE_AR_THRESH = 0.25
MOU_AR_THRESH = 0.6
EYE_AR_CONSEC_FRAMES = 48
MOU_AR_CONSEC_FRAMES = 15

COUNTERS = []
yawns_list = []
yawnStatus_list = []
mouth_counters = []

SURVEILLANCE_STREAM = 0
cap = cv2.VideoCapture(SURVEILLANCE_STREAM)

while True:
    ret, frame = cap.read()
    if not ret:
        key = cv2.waitKey(100)
        if key & 0xFF == ord("q"):
            break
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    annotated_frame = frame.copy()

    if results.multi_face_landmarks:
        num_faces = len(results.multi_face_landmarks)

        while len(COUNTERS) < num_faces:
            COUNTERS.append(0)
            yawns_list.append(0)
            yawnStatus_list.append(False)
            mouth_counters.append(0)

        while len(COUNTERS) > num_faces:
            COUNTERS.pop()
            yawns_list.pop()
            yawnStatus_list.pop()
            mouth_counters.pop()

        for idx, face_landmarks in enumerate(results.multi_face_landmarks):
            mp_drawing.draw_landmarks(
                image=annotated_frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
            )
            mp_drawing.draw_landmarks(
                image=annotated_frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
            )

            leftEye = [(face_landmarks.landmark[i].x * frame.shape[1],
                        face_landmarks.landmark[i].y * frame.shape[0]) for i in LEFT_EYE]
            rightEye = [(face_landmarks.landmark[i].x * frame.shape[1],
                         face_landmarks.landmark[i].y * frame.shape[0]) for i in RIGHT_EYE]
            mouth = [(face_landmarks.landmark[i].x * frame.shape[1],
                      face_landmarks.landmark[i].y * frame.shape[0]) for i in MOUTH]

            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0
            mar = mouth_aspect_ratio(mouth)

            if ear < EYE_AR_THRESH:
                COUNTERS[idx] += 1
                cv2.putText(frame, f"Face {idx+1}: Eyes Closed", (10, 30 + idx * 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                if COUNTERS[idx] >= EYE_AR_CONSEC_FRAMES:
                    cv2.putText(frame, f"Face {idx+1}: DROWSINESS ALERT!", (10, 55 + idx * 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                COUNTERS[idx] = 0
                cv2.putText(frame, f"Face {idx+1}: Eyes Open", (10, 30 + idx * 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if mar > MOU_AR_THRESH:
                mouth_counters[idx] += 1
                cv2.putText(frame, f"Face {idx+1}: Mouth Open", (10, 80 + idx * 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                if mouth_counters[idx] >= MOU_AR_CONSEC_FRAMES and not yawnStatus_list[idx]:
                    yawns_list[idx] += 1
                    yawnStatus_list[idx] = True
                    cv2.putText(frame, f"Face {idx+1}: YAWN DETECTED!", (10, 105 + idx * 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                mouth_counters[idx] = 0
                yawnStatus_list[idx] = False

            cv2.putText(frame,
                        f"Face {idx+1}: EAR={ear:.2f} | MAR={mar:.2f} | Yawns={yawns_list[idx]}",
                        (10, 135 + idx * 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Driver Monitoring", frame)
    cv2.imshow("Annotated Face Mesh", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

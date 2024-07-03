import cv2
import numpy as np

mv = cv2.VideoCapture(r"C:\Users\kazum\Videos\Replay 2024-07-03 02-02-54.mp4")

width = mv.get(cv2.CAP_PROP_FRAME_WIDTH)
height = mv.get(cv2.CAP_PROP_FRAME_HEIGHT)

while (mv.isOpened()):
    ret, frame = mv.read()
    cv2.imshow("Movie",frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

mv.release()
cv2.destroyAllWindows()
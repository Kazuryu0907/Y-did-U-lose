from obs import OBS
from cam import DeathMonitor, Queue
import cv2
import time

o = OBS("localhost",4455,"uc70NkXRBNvMzWSW")
o.init_cam_replay()

capture = cv2.VideoCapture(1)
monitor = DeathMonitor(capture)

def show_movie(path:str,speed_ratio=1.):
    mv = cv2.VideoCapture(path)
    height = mv.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = mv.get(cv2.CAP_PROP_FRAME_WIDTH)
    fps = mv.get(cv2.CAP_PROP_FPS)
    wait_time = (1/fps)*(1./speed_ratio)
    print(f"{wait_time=}")
    while (mv.isOpened()):
        start = time.time()
        ret, frame = mv.read()
        if frame is None:
            break
        resized_frame = cv2.resize(frame,(int(width/2),int(height/2)))
        cv2.imshow("Movie",resized_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        # FPS調整
        while time.time() - start < wait_time:
            pass
        
    mv.release()
    cv2.destroyAllWindows()

def callback():
    path = o.save_replay()
    print(f"{path=}")
    show_movie(path,speed_ratio=0.5)
try:
    monitor.run(callback)
except KeyboardInterrupt:
    # 終了時リプレイ削除
    print("Deleting replay")
    o.delete_replay()
    print("Stopping VirtualCam & ReplayBuffer")
    o.stop_cam_replay()
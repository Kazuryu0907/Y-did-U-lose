import cv2
import time
import numpy as np
from typing import Callable,Dict


def get_available_cameras(max_cameras=10):
    available_cameras = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

# # 最大10台のカメラをチェック
# cameras = list_cameras()
# print(f"Available cameras: {cameras}")

def test_camera(camera_index:int,capture_sec:int=5):
    cap = cv2.VideoCapture(camera_index)
    start = time.time()
    while time.time() - start < capture_sec:
        ret, frame = cap.read()
        cv2.imshow("Camera_test",frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()

class Queue:
    def __init__(self,size:int):
        self.size = size
        self.queue = np.array([])
    def add_data(self,data:float):
        if len(self.queue) == self.size:
            self.pop()
        self.queue = np.append(self.queue,data)
        
    def pop(self):
        self.queue = self.queue[1:]
    
    def get_mean(self):
        return np.mean(self.queue)

class DeathMonitor:
    def __init__(self,camera_index:int,height=480,width=640):
        self.HEIGHT = height
        self.WIDTH = width
        self.capture = cv2.VideoCapture(camera_index)
        # self.original_w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        # self.original_h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.original_w = 1920
        self.original_h = 1080
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.HEIGHT)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.WIDTH)
        self.queue = Queue(10)
        self.prev_black_flag = False
        # fpsとblack_ratioのlogging
        self.logger = {}
    
    def set_logger(self,logger:Dict):
        self.logger = logger

    def run(self,callback:Callable,threshold=0.6):
        iter = 0
        self.threshold = threshold
        dummy_frame = np.zeros((self.original_h//2,self.original_w//2,3),dtype=np.uint8)
        while True:
            start = time.time()
            ret, frame = self.capture.read()
            cv2.imshow("Death Monitor",dummy_frame)
            gray_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            # black検知
            black_count = np.count_nonzero(gray_frame == 0)
            black_ratio = black_count / (self.HEIGHT * self.WIDTH)
            self.queue.add_data(black_ratio)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            elapsed = time.time() - start
            # if iter == 100:
            #     print(f"fps: {1/elapsed: .3f}")
            #     iter = 0
            mean_black_ratio = self.queue.get_mean()

            # * 0.6はHyperParameter
            black_flag = mean_black_ratio > self.threshold
            if black_flag and not self.prev_black_flag:
                callback()
                print("Black frame detected")

            # * logging
            self.logger["fps"] = 1/elapsed
            self.logger["black_ratio"] = mean_black_ratio

            self.prev_black_flag = black_flag
            iter += 1
    def show_movie(self,path:str,speed_ratio=1.):
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
            cv2.imshow("Death Monitor",resized_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            # FPS調整
            while time.time() - start < wait_time:
                pass
            
        mv.release()
        cv2.destroyAllWindows()
if __name__ == "__main__":
    # capture = cv2.VideoCapture(1)
    test_camera(1)
    # monitor = Death_Monitor(capture)
    # monitor.run(lambda:print("b"))
    # capture.release()
    cv2.destroyAllWindows()

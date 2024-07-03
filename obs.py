import obsws_python as obs
from typing import List
import time
import os

class OBS:
    cl:obs.ReqClient
    replay_paths: List[str]

    def __init__(self,host:str,port:int,password:str):
        self.replay_paths = []
        try:
            self.cl = obs.ReqClient(host=host,port=port,password=password)
        except:
            raise ValueError("Failed to connect to OBS")
        

    def ping(self) -> str:
        return self.cl.get_version().obs_version

    def init_cam_replay(self):
        # resp = cl.send("SaveReplayBuffer",raw=True)
        # resp = cl.send("GetLastReplayBufferReplay",raw=True)
        #* VirtualCam立ち上げ
        if not self.cl.send("GetVirtualCamStatus").output_active:
            print("Stating VirtualCam")
            self.cl.send("StartVirtualCam")

        # * ReplayBuffer立ち上げ
        if not self.cl.send("GetReplayBufferStatus").output_active:
            print("Starting ReplayBuffer")
            self.cl.send("StartReplayBuffer")
    
    def stop_cam_replay(self):
        # * VirtualCam停止
        self.cl.send("StopVirtualCam")
        # * ReplayBuffer停止
        self.cl.send("StopReplayBuffer")

        # print(f"{resp.output_active=}")
    
    def save_replay(self) -> str:
        """
        Save replay buffer and return the video path
        """
        self.cl.send("SaveReplayBuffer")
        time.sleep(1)
        resp = self.cl.send("GetLastReplayBufferReplay")
        path = resp.saved_replay_path
        self.replay_paths.append(path)
        return path
    
    def delete_replay(self):
        for path in self.replay_paths:
            os.remove(path)
            

o = OBS("localhost",4455,"uc70NkXRBNvMzWSW")
o.init_cam_replay()
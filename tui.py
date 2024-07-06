from rich import print
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.spinner import Spinner
from prompt_toolkit import PromptSession,prompt
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.output.win32 import Win32Output
from prompt_toolkit.output import create_output
from prompt_toolkit.validation import Validator
import pyfiglet
import time
from enum import Enum,auto
import queue
import threading
from obs import OBS
from cam import get_available_cameras,test_camera,DeathMonitor
import subprocess

from typing import Callable,List,Self

# ?==========GLOBALS========== 
obs = None
death_monitor = None
camera_indexes = []
death_monitor_threshold = 0.6
death_monitor_logger = {}
# ?===========================
session = PromptSession(output=Win32Output(create_output()))

title = pyfiglet.figlet_format("Y did U lose?",font="isometric1")

layout_texts = Align.center(Text(title,style="bold blink2 green",justify="center"),vertical="middle")
layout = Layout(Panel(layout_texts,style="green"))
print(layout)

time.sleep(3)
layout = Layout()
layout.split_column(
    Layout(name="upper"),
    Layout(name="lower")
)
# layout["upper"].split_row(Layout(name="left"),Layout(name="right"))
# layout["upper"]["left"].ratio = 2
# layout["upper"]["right"].update(Panel(Text("FPS")))
layout["lower"].ratio = 2
logo = pyfiglet.figlet_format("Y did U lose?",font="banner")
logo_text = Text(logo,style="bold green blink2",justify="center")
logo_text.append(Text("===Death Monitor for Valorant===\n",justify="center",style="cyan3"))
logo_text.append(Text("Developed by Kazuryu\n",justify="center",style="cyan3 link https://x.com/kazuryu_RL"))
# layout["upper"].update(Text(logo_text,style="bold green blink2",justify="center"))
layout["upper"].update(logo_text)

layout["lower"].update(Text("Nice to meet you!",style="bold green"))
layout["lower"].update(Text("1st. Connect to OBS websocket",style="bold green"))
# user_input = prompt("Enter the host name: ")
# layout["lower"].update(Panel(f"Enter the host name: {user_input}"))
# name = Prompt.ask("Enter ", default="kazuryu")
print(layout)

class CheckPoint:
    def __init__(self,name:str):
        self.name = name

class CheckPointRegister:
    def __init__(self):
        self.check_points = {}
        for checkpoint in CheckPoints:
            self.register(checkpoint.name)
    def register(self,checkpoint_name:str):
        checkpoint = CheckPoint(checkpoint_name)
        self.check_points[checkpoint_name] = checkpoint
    def get(self,checkpoint:Enum) -> CheckPoint:
        return self.check_points.get(checkpoint.name)

# promptの入力を保存する辞書
user_inputs = {}
class PromptMessage:
    def __init__(self,prompt:str,prompt_name:str,**kwargs):
        self.prompt = prompt
        self.prompt_name = prompt_name
        self.kwargs = kwargs

    def ask(self):
        # Validatorが次のSessionに引き継がれるので対策
        if self.kwargs.get("validator") is None:
            session.validator = None

        msg = session.prompt(self.prompt,**self.kwargs)
        # msg = prompt(self.prompt,**self.kwargs)
        user_inputs[self.prompt_name] = msg
        msg = f"{self.prompt_name}: {msg}"
        return msg

class RenderableSpinner:
    def __init__(self,spinner:Spinner):
        self.spinner = spinner
    def update(self,):
        return self.spinner.render(time.time())

class CallAPI:
    def __init__(self,spinner:Spinner,func:Callable[[],str|Text],check_point:CheckPoint=None):
        self.renderable_spinner = RenderableSpinner(spinner)
        self.return_value = None
        self._func = func
        self.error_queue = queue.Queue()
        self.check_point = check_point
    # 返り値がほしいのでワンクッション
    # Error handlingもここで
    def func(self):
        try:
            self.return_value = self._func()
        except Exception as e:
            self.error_queue.put(e)
    def call(self):
        self.thread = threading.Thread(target=self.func)
        self.thread.start()
    def is_successful(self):
        return self.error_queue.empty()
    def get_error(self):
        """
        is_successfulがFalseの時のみ呼んで
        """
        return self.error_queue.get()
    def get_check_point(self) -> CheckPoint:
        return self.check_point
    def get_value(self):
        return self.return_value
    def is_running(self):
        return self.thread.is_alive()


def connect_to_obs():
    global obs
    time.sleep(2)
    hostname = user_inputs.get("hostname")
    port = user_inputs.get("port")
    password = user_inputs.get("password")
    _obs = OBS(hostname,port,password)
    version = _obs.ping()
    obs = _obs
    return f"Connected! OBS Version: {version}"

def cameras_api_func():
    global camera_indexes
    # time.sleep(2)
    camera_indexes = get_available_cameras()
    if len(camera_indexes) == 0:
        raise Exception("No camera is available")
    return f"Available camera indexes: {camera_indexes}"

def is_there_only_camera_api_func():
    global camera_indexes
    if len(camera_indexes) == 1:
        user_inputs["camera_index"] = str(camera_indexes[0])
        raise Exception("Camera is only one. Skip selecting camera.")

def obs_init_api_func():
    global obs
    time.sleep(2)
    obs.init_cam_replay()
    return "Initialized OBS VirtualCam & ReplayBuffer!"

def test_camera_api_func():
    # TODO Validate 
    camera_index = int(user_inputs.get("camera_index"))
    test_camera(camera_index)
    return None

# TODO o.delete_replay()実装しといて
def death_monitor_api_func():
    global obs,death_monitor_logger,death_monitor_threshold,death_monitor
    camera_index = int(user_inputs.get("camera_index"))
    death_monitor = DeathMonitor(camera_index)
    death_monitor.set_logger(death_monitor_logger)
    def callback():
        path = obs.save_replay()
        print(f"{path=}")
        death_monitor.show_movie(path,speed_ratio=0.5)
    death_monitor.run(callback,death_monitor_threshold)

def determine_camera_api_func():
    ans = user_inputs.get("determine_camera")
    if ans == "y":
        return None
    elif ans == "n":
        raise Exception("Reselect another camera")

is_y_or_n_validator = Validator.from_callable(lambda s: s.lower() in ["y","n"],error_message="Please enter y or n",move_cursor_to_end=True)
camera_indexes_validator = Validator.from_callable(lambda s: s.isdigit() and int(s) in camera_indexes,error_message=f"Please enter the camera index from the options in [].Please enter the camera index from the options in [].",move_cursor_to_end=True)

class CheckPoints(Enum):
    OBS = auto()
    SKIP_SELECT_CAMERA = auto()
    RESELECT_CAMERA = auto()
    EXIT = auto()


checkpoint_register = CheckPointRegister()

connect_obs_api = CallAPI(Spinner("dots",text="Connecting..."),connect_to_obs,checkpoint_register.get(CheckPoints.OBS))
obs_init_api = CallAPI(Spinner("dots",text="Setting up your OBS VirtualCam & ReplayBuffer..."),obs_init_api_func)
# カメラが1つしかないときはcheckpointまで飛ばす
cameras_api = CallAPI(Spinner("dots",text="Getting Camera Indexes..."),cameras_api_func,checkpoint_register.get(CheckPoints.EXIT))
is_there_only_camera_api = CallAPI(Spinner("dots"),is_there_only_camera_api_func,checkpoint_register.get(CheckPoints.SKIP_SELECT_CAMERA))
test_camera_api = CallAPI(Spinner("dots",text="Testing Camera..."),test_camera_api_func)
determine_camera_api = CallAPI(Spinner("dots"),determine_camera_api_func,checkpoint_register.get(CheckPoints.RESELECT_CAMERA))
death_monitor_api = CallAPI(Spinner("dots",text="Waiting for your death..."),death_monitor_api_func)

exit_api = CallAPI(Spinner("dots",text="Exiting..."),lambda: subprocess.call("PAUSE",shell=True))

commands = [
    "Hello!", 
    "First, Connect to OBS websocket", 
    checkpoint_register.get(CheckPoints.OBS),
    PromptMessage("Enter the hostname> ","hostname",default="localhost"),
    PromptMessage("Enter the port> ","port",default="4455"),
    PromptMessage("Enter the password> ","password"),
    connect_obs_api,
    obs_init_api,
    "Next, Select Your OBS VirtualCam",
    checkpoint_register.get(CheckPoints.RESELECT_CAMERA),
    cameras_api,
    is_there_only_camera_api,
    PromptMessage("Enter the camera index> ","camera_index",validator=camera_indexes_validator),
    test_camera_api,
    # カメラがokか確認
    PromptMessage("Was this camera OK? (y/n)> ","determine_camera",validator=is_y_or_n_validator),
    determine_camera_api,
    # カメラ1つしかないときはここまでskip
    checkpoint_register.get(CheckPoints.SKIP_SELECT_CAMERA),
    "Camera Selected!",
    CallAPI(Spinner("dots",text="Launch Death Monitor..."),lambda:time.sleep(2)),
    # death_monitor_api,
    # # CallAPI(Spinner("dots",text="Selecting camera..."),lambda: input()),
    # checkpoint_register.get(CheckPoints.EXIT),
    # exit_api
    ]

def display_message(message:str|PromptMessage):
    # log的なmessage
    if isinstance(message,str):
        message = "> " + message
        message += "\n"
        return message
    if isinstance(message,PromptMessage):
        text = "< "
        with patch_stdout():
            text += message.ask()
        text += "\n"
        return Text(text,style="red")


layout_texts = Text()
rps = 8
with Live(layout,refresh_per_second=rps,screen=True) as live:
    # checkpointを戻すため，indexを導入
    cmd_index = 0
    n_commands = len(commands)
    while cmd_index < n_commands:
        cmd = commands[cmd_index]
        # * Messageを表示させるものはこっち
        if isinstance(cmd,(str,PromptMessage)):
            time.sleep(1./rps)
            text = display_message(cmd)
            layout_texts.append(text)
            layout["lower"].update(Panel(layout_texts,style="bold green"))
            time.sleep(2)
        # * Spinnerを表示させるものはこっち 
        if isinstance(cmd,(CallAPI,)):
            api = cmd
            api.call()
            # スピン回す処理
            while api.is_running():
                spinner_text = api.renderable_spinner.update()
                _text = layout_texts.copy()
                _text.append(spinner_text)
                layout["lower"].update(Panel(_text,style="bold green"))
                live.update(layout) 
            # 成功時はreturn valueをdisplay
            if api.is_successful():
                resp = api.get_value()
                # print用returnがあればdisplay
                if resp is not None:
                    layout_texts.append(Text(display_message(resp),style="cyan2"))
                    layout["lower"].update(Panel(layout_texts,style="bold green"))
                    live.update(layout)
            # 失敗時はエラーメッセージを表示し，checkpointまで戻る
            else:
                error_msg = str(api.get_error()) + "\n"
                layout_texts.append(Text(error_msg,style="red underline"))
                layout["lower"].update(Panel(layout_texts,style="bold green"))
                # 1/refresh_per_second < sleep_timeならちゃんと更新されそう
                time.sleep(2./rps)
                # checkpointまで戻る
                checkpoint = api.get_check_point()
                # 下で+1されるので-1
                cmd_index = commands.index(checkpoint) - 1
            
            layout["lower"].update(Panel(layout_texts,style="bold green"))
        
        cmd_index += 1
    # Death Monitor Loop
    death_monitor_api.call()
    while 1:
        panel_color = "green"
        if not death_monitor_api.is_running():
            if not death_monitor_api.is_successful():
                a = death_monitor_api.get_error()
            break
        text = Text()
        # TODO mp4再生時にfpsとblack_ratio更新されないから，threadingとかで退避させて
        fps = death_monitor_logger.get("fps",None)
        if fps is not None:
            fps = f"{fps: .1f}"
        black_ratio = death_monitor_logger.get("black_ratio",None)
        if (black_ratio is not None) and (black_ratio > death_monitor_threshold):
            panel_color = "red"
        text.append(f"fps:{fps}\n",style="bold green")
        text.append(f"black_ratio:{black_ratio}\n",style="bold green")
        layout["lower"].update(Panel(text,style=f"bold {panel_color}"))
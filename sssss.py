from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.output.win32 import Win32Output
from prompt_toolkit.output import create_output

console = Console()
session = PromptSession(output=Win32Output(create_output()))

# 初期のTextオブジェクトを作成
text = Text()

def update_panel():
    return Panel(text, title="User Inputs")

def main():
    with Live(update_panel(), refresh_per_second=10, screen=True) as live:
        while True:
            with patch_stdout():
                user_input = session.prompt("Enter something: ")
            text.append(f"{user_input}\n")
            live.update(update_panel())

if __name__ == "__main__":
    main()
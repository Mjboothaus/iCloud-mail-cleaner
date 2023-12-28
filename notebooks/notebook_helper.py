import sys
from pathlib import Path
import datetime as dt
from IPython.display import display, Markdown


def notebook_add_parent_dir_to_path():
    module_path = Path.cwd().parent.as_posix()
    if module_path not in sys.path:
        sys.path.append(module_path)
        print(f"Added parent directory {module_path} to PYTHONPATH")


def start_execution_time():
    start_time = dt.datetime.now()
    disp_md(f"Notebook execution start time: {start_time.strftime('%d-%m-%Y %H:%M:%S')}")
    return start_time


def execution_time(start_time):
    exec_time = (dt.datetime.now() - start_time).seconds
    disp_md(f"Notebook execution finished --- Elapsed time {exec_time} seconds ---")
    return exec_time


def disp_md(md_str):
    display(Markdown(f"##### {md_str}"))

"""
Monitors filesystem status in realtime.
"""
import logging
import pathlib
import subprocess
from distutils.spawn import find_executable

from PySide2.QtCore import QThread, Signal

from ziton.config import included_directories

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class Worker(QThread):
    "Represents an async worker thread."
    fileDeleted = Signal(str)
    fileCreated = Signal(str)

    def __init__(self, parent=None):
        "inits the inotify worker thread."
        super().__init__(parent)
        self.cmd = [
            "inotifywait",
            "-r",
            "-m",
            "-e",
            "create",
            "-e",
            "delete",
            "-e",
            "moved_to",
            "-e",
            "moved_from",
        ] + included_directories()

    def inotify_process(self):
        "Start inotify process and yield filesystem changes as they come in."
        popen = subprocess.Popen(
            self.cmd, stdout=subprocess.PIPE, universal_newlines=True
        )
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        popen.stdout.close()
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, self.cmd)

    def run(self):
        "Start the Qthread."
        for event in self.inotify_process():
            try:
                folder, command, filename = event.split()
                full_path = str(pathlib.Path(folder).joinpath(filename))
                if command in ("CREATE", "MOVED_TO"):
                    self.fileCreated.emit(full_path)
                elif command in ("DELETE", "MOVED_FROM"):
                    self.fileDeleted.emit(full_path)
            except ValueError as err:
                LOGGER.error(f"error: {err}")


def check_dependencies():
    """
    Searches user path for inotify-wait.
    If it doesn't exist inotify-tools or a similar package may provide it.
    """
    return find_executable("inotifywait")

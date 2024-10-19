from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from threading import Event
import time


class LogChangedHandler(FileSystemEventHandler):
    event = Event()

    def on_modified(self, event: FileModifiedEvent) -> None:
        """
        Set event when file is changed
        """
        if "logs.log" in event.src_path:
            self.event.set()
            time.sleep(0.2)

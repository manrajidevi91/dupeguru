import os
import sys
import time
import subprocess
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("Watcher")

class RestartHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.restart_scheduled = False
        self.last_restart = 0
        self.debounce_seconds = 1  # Prevent rapid restarts
        self.start_process()

    def start_process(self):
        if self.process:
            logger.info("Terminating existing process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        logger.info(f"Starting application: {self.command}")
        self.process = subprocess.Popen(self.command, shell=True)

    def on_any_event(self, event):
        if event.is_directory:
            return
        
        # Define files to watch
        watched_extensions = ('.py', '.html', '.css', '.js', '.json')
        filename = event.src_path
        
        # Ignore common noise
        ignored_patterns = ['venv', '__pycache__', '.git', '.pytest_cache', 'cached_pictures.db']
        if any(pattern in filename for pattern in ignored_patterns):
            return

        if filename.endswith(watched_extensions):
            current_time = time.time()
            if current_time - self.last_restart > self.debounce_seconds:
                logger.info(f"File change detected: {os.path.basename(filename)}")
                self.start_process()
                self.last_restart = current_time

if __name__ == "__main__":
    # Ensure app.py exists
    if not os.path.exists("app.py"):
        logger.error("app.py not found in the current directory!")
        sys.exit(1)

    command = f"\"{sys.executable}\" app.py"
    
    event_handler = RestartHandler(command)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    
    logger.info("dupeGuru Watcher started. Monitoring code changes...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Watcher stopping...")
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    
    observer.join()

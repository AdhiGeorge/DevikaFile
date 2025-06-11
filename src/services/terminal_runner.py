import subprocess
import tempfile
import os
import shutil
import threading
import time
import logging
from typing import List, Optional

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger("terminal_runner")

class TerminalRunner:
    def __init__(self, timeout: int = 30, memory_limit_mb: int = 256):
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb

    def run(self, command: List[str], input_text: Optional[str] = None) -> dict:
        """
        Run a command in a temporary directory with resource limits.
        Returns a dict with stdout, stderr, exit_code, and duration.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            logger.info(f"Running command: {' '.join(command)} in {tmpdir}")
            start_time = time.time()
            try:
                if os.name == 'nt':
                    # Windows: no preexec_fn, but can use psutil for monitoring
                    proc = subprocess.Popen(
                        command,
                        cwd=tmpdir,
                        stdin=subprocess.PIPE if input_text else None,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=False,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    # Unix: set resource limits in preexec_fn
                    import resource
                    def set_limits():
                        resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit_mb * 1024 * 1024, self.memory_limit_mb * 1024 * 1024))
                        resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
                    proc = subprocess.Popen(
                        command,
                        cwd=tmpdir,
                        stdin=subprocess.PIPE if input_text else None,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=False,
                        preexec_fn=set_limits
                    )
                # Monitor process for timeout and memory
                timer = threading.Timer(self.timeout, proc.kill)
                timer.start()
                try:
                    stdout, stderr = proc.communicate(input=input_text.encode() if input_text else None)
                finally:
                    timer.cancel()
                duration = time.time() - start_time
                exit_code = proc.returncode
                # Optionally check memory usage with psutil
                if psutil and proc.pid:
                    try:
                        p = psutil.Process(proc.pid)
                        mem = p.memory_info().rss // (1024 * 1024)
                        logger.info(f"Process memory usage: {mem} MB")
                    except Exception:
                        pass
                logger.info(f"Command finished with exit code {exit_code} in {duration:.2f}s")
                return {
                    "stdout": stdout.decode(errors="replace"),
                    "stderr": stderr.decode(errors="replace"),
                    "exit_code": exit_code,
                    "duration": duration,
                }
            except Exception as e:
                logger.error(f"Error running command: {e}")
                return {
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                    "duration": time.time() - start_time,
                } 
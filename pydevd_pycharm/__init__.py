import logging
import os
import socket
import time

HOST = os.environ.get("PYDEVD_PYCHARM_HOST", "host.docker.internal")
PORT = int(os.environ.get("PYDEVD_PYCHARM_PORT", 21000))
RETRY_SECONDS = int(os.environ.get("PYDEVD_PYCHARM_RETRY_SECONDS", 3))
RETRY_ATTEMPTS = int(os.environ.get("PYDEVD_PYCHARM_RETRY_ATTEMPTS", 10))
DOCKER_WORKAROUND_TRY_SUBNETS = int(os.environ.get("PYDEVD_PYCHARM_DOCKER_WORKAROUND_TRY_SUBNETS", 0))

logger = logging.getLogger(__name__)


class PydevdPyCharm:
    @staticmethod
    def _get_gateway_address(address):
        parts = address.split(".")
        parts[-1] = "1"
        return ".".join(parts)

    def __init__(
            self,
            host=HOST,
            port=PORT,
            retry_seconds=RETRY_SECONDS,
            retry_attempts=RETRY_ATTEMPTS,
            docker_workaround_try_subnets=DOCKER_WORKAROUND_TRY_SUBNETS,
    ):
        try:
            import pydevd_pycharm as pydevd_pycharm_module
            self.debugger = pydevd_pycharm_module
            logger.info(f"Found pydevd_pycharm version {self.debugger.__version__}")
            self.installed = True
        except ModuleNotFoundError:
            logger.warning("ENABLE_PYDEVD_PYCHARM set but pydevd_pycharm not installed")
            self.installed = False
        self.hosts = [host]
        if docker_workaround_try_subnets:
            subnets = socket.gethostbyname_ex(socket.gethostname())[-1]
            self.hosts += [self._get_gateway_address(subnet) for subnet in subnets]
        self.port = port
        self.retry_seconds = retry_seconds
        self.retry_attempts = retry_attempts

    def connect(self):
        for host in self.hosts:
            logger.info(f"Looking for Python Debug Server at {host}:{self.port}...")
            attempts_left = self.retry_attempts + 1
            while attempts_left:
                try:
                    self.debugger.settrace(
                        host,
                        port=self.port,
                        stdoutToServer=True,
                        stderrToServer=True,
                        suspend=False,
                    )
                except ConnectionError:
                    attempts_left -= 1
                    if attempts_left == 0:
                        logger.error(f"Could not connect to Debug Server {host} - is it running?")
                    else:
                        logger.warning(
                            f"No answer... will try again in {self.retry_seconds} "
                            f"seconds ({attempts_left} attempts left)"
                        )
                        time.sleep(self.retry_seconds)
                except OSError:
                    logger.error(f"Could not reach Debug Server {host} - is the address correct?")
                    attempts_left = 0
                else:
                    logger.info("PyDev.Debugger connected")
                    return


if os.environ.get("ENABLE_PYDEVD_PYCHARM") == "1":
    logger.info("Debugging with pydevd_pycharm enabled")
    pydevd_pycharm = PydevdPyCharm()
    if pydevd_pycharm.installed:
        pydevd_pycharm.connect()

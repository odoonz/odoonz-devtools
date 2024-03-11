import logging
import os
import socket
import time

HOST = os.environ.get("PYDEVD_PYCHARM_HOST", "host.docker.internal")
PORT = int(os.environ.get("PYDEVD_PYCHARM_PORT", 21000))
RETRY_SECONDS = int(os.environ.get("PYDEVD_PYCHARM_RETRY_SECONDS", 3))
RETRY_ATTEMPTS = int(os.environ.get("PYDEVD_PYCHARM_RETRY_ATTEMPTS", 10))
DOCKER_WORKAROUND_TRY_SUBNETS = int(os.environ.get("PYDEVD_PYCHARM_DOCKER_WORKAROUND_TRY_SUBNETS", 0))
DOCKER_WORKAROUND_RETRY_SECONDS = int(os.environ.get("PYDEVD_PYCHARM_DOCKER_WORKAROUND_RETRY_SECONDS", 0))

logger = logging.getLogger(__name__)


def _get_gateway_address(subnet):
    parts = subnet.split(".")
    parts[-1] = "1"
    return ".".join(parts)


if os.environ.get("ENABLE_PYDEVD_PYCHARM") == "1":
    logger.info("Debugging with pydevd_pycharm enabled")
    try:
        import pydevd_pycharm
        PYDEVD_PYCHARM_INSTALLED = True
    except ModuleNotFoundError:
        PYDEVD_PYCHARM_INSTALLED = False

    if PYDEVD_PYCHARM_INSTALLED:
        version = pydevd_pycharm.__version__
        logger.info(f"Found pydevd_pycharm version {version}")
        logger.info(f"Looking for Python Debug Server at {HOST}:{PORT}...")
        attempts_left = RETRY_ATTEMPTS + 1
        host = HOST
        subnets = socket.gethostbyname_ex(socket.gethostname())[-1]
        while attempts_left:
            try:
                pydevd_pycharm.settrace(
                    host,
                    port=PORT,
                    stdoutToServer=True,
                    stderrToServer=True,
                    suspend=False,
                )
            except ConnectionError:
                attempts_left -= 1
                if attempts_left == 0:
                    logger.error("Could not connect to Debug Server - is it running?")
                else:
                    logger.warning(
                        f"No answer... will try again in {RETRY_SECONDS} "
                        f"seconds ({attempts_left} attempts left)"
                    )
                    time.sleep(RETRY_SECONDS)
            except OSError:
                if DOCKER_WORKAROUND_TRY_SUBNETS and subnets:
                    subnet = subnets.pop(0)
                    logger.info(f"Trying to connect on subnet of {subnet}")
                    host = _get_gateway_address(subnet)
                else:
                    if attempts_left == 0:
                        logger.error("Could not resolve Debug Server host - is the address correct?")
                    else:
                        attempts_left -= 1
                        logger.warning(
                            f"Could not resolve {HOST}... will try again in {RETRY_SECONDS} "
                            f"seconds ({attempts_left} attempts left)"
                        )
                        if DOCKER_WORKAROUND_TRY_SUBNETS:
                            time.sleep(DOCKER_WORKAROUND_RETRY_SECONDS)
                        else:
                            time.sleep(RETRY_SECONDS)
            else:
                logger.info("PyDev.Debugger connected")
                attempts_left = 0

    else:
        logger.warning("ENABLE_PYDEVD_PYCHARM set but pydevd_pycharm not installed")

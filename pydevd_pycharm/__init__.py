import logging
import os
import socket
import time

HOST = os.environ.get("PYDEVD_PYCHARM_HOST", "host.docker.internal")
PORT = int(os.environ.get("PYDEVD_PYCHARM_PORT", 21000))
RETRY_SECONDS = int(os.environ.get("PYDEVD_PYCHARM_RETRY_SECONDS", 3))
RETRY_ATTEMPTS = int(os.environ.get("PYDEVD_PYCHARM_RETRY_ATTEMPTS", 10))
DOCKER_WORKAROUND_TRY_SUBNETS = bool(os.environ.get("PYDEVD_PYCHARM_DOCKER_WORKAROUND_TRY_SUBNETS", False))

logger = logging.getLogger(__name__)


def _get_subnet_addresses():
    return socket.gethostbyname_ex(socket.gethostname())[-1]


def _get_gateway_address(subnet):
    parts = subnet.split(".")
    return f"{parts[0]}.{parts[1]}.{parts[2]}.1"


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
        while attempts_left:
            attempts_left -= 1
            try:
                pydevd_pycharm.settrace(
                    HOST,
                    port=PORT,
                    stdoutToServer=True,
                    stderrToServer=True,
                    suspend=False,
                )
            except ConnectionError:
                if attempts_left == 0:
                    logger.error("Could not connect to Debug Server - is it running?")
                else:
                    logger.warning(
                        f"No answer... will try again in {RETRY_SECONDS} "
                        f"seconds ({attempts_left} attempts left)"
                    )
                    time.sleep(RETRY_SECONDS)
            except OSError:
                if DOCKER_WORKAROUND_TRY_SUBNETS:
                    if attempts_left == 0:
                        logger.error("Could not resolve Debug Server host - is the address correct?")
                    for subnet in _get_subnet_addresses():
                        logger.info(f"Trying to connect on subnet {subnet}")
                        gateway_address = _get_gateway_address(subnet)
                        try:
                            pydevd_pycharm.settrace(
                                gateway_address,
                                port=PORT,
                                stdoutToServer=True,
                                stderrToServer=True,
                                suspend=False,
                            )
                        except ConnectionError:
                            logger.warning(f"Could not connect to {gateway_address}")
                    time.sleep(RETRY_SECONDS)
                else:
                    logger.warning(
                        f"Could not resolve {HOST}... will try again in {RETRY_SECONDS} "
                        f"seconds ({attempts_left} attempts left)"
                    )
                    time.sleep(RETRY_SECONDS)
            else:
                logger.info("PyDev.Debugger connected")
                attempts_left = 0

    else:
        logger.warning("ENABLE_PYDEVD_PYCHARM set but pydevd_pycharm not installed")

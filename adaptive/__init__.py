import logging
from subprocess import Popen, PIPE
from adaptive.constants import LOG_FORMAT

def init_console_logger(lvl):
    """
    Parameters
    ----------
    lvl [int] : Integer of level of logging desired 0,1,2,3
    Returns
    -------
    logging object
    """
    logging_levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    report_lvl = logging_levels[lvl]

    logging.basicConfig(format=LOG_FORMAT, level=report_lvl)
    return logging


def run_command(command):
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    return stdout, stderr

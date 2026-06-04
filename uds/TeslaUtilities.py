"""
Created on Apr 14, 2015

@author: kthode

@description: TeslaUtilities contains functions that are used in multiple classes.
"""
import os
import sys
import json
import signal
import base64
import logging
import smtplib

from traceback import format_exception

# Constants
TESLA_SMTP = 'tslaonly-smtp.teslamotors.com'
TESLA_SMTP_PORT = 25


class SignalDirection(int):
    SOURCE = 0
    DESTINATION = 1
    INPUT = 2
    OUTPUT = 3
    INVALID = -1


# TODO: Remove once all BC Python Modules are moved over to the new logging method
class Master_Log_Entry_Type(int):
    info = 0
    warning = 1
    error = 2
    debug = 3


class LoggingLevel(int):
    DEBUG = 0  # Detailed information of interest when diagnosing problems
    INFO = 1  # Confirmation that things are working as expected
    WARNING = 2  # Indication of unexpected behavior or potential problem in near future; software works as expected
    ERROR = 3  # Due to a more serial problem, the software was unable to perform a function
    CRITICAL = 4  # A serious error indicating that the program may be unable to continue running
    DISABLED = 5  # No logging


class LoggingHandler(int):
    STREAM_HANDLER = 0
    FILE_HANDLER = 1
    NULL_HANDLER = 2


class HandlerStream(int):
    STDERR = 0
    STDOUT = 1


def get_hmac_key(key, message):
    """
    Get HMAC Key is used when setting up Python Remote Objects.  The
    parameters are concatenated to generate the final key value.
    :param key: <String> The key value
    :param message: <String> The message value
    :return hmac_key: <String> The generated HMAC key
    """
    hmac_key = str(key) + str(message)
    return hmac_key


def load_json_file(filename):
    """
    Load JSON File loads a supplied JSON file.
    :param filename: <String> The full path to the file
    :return jsonDict: <dict> the dictionary in the file
    """
    jsonDict = dict()
    with open(filename, 'rb') as J:
        jsonDict = json.load(J)
    return jsonDict


def write_json_file(filepath, data):
    """
    Write JSON File writes a supplied dictionary to the specified filepath.
    :param filepath: <string> Full file path to the JSON file to write
    :param data: <dictionary> JSON data to write to file
    :return success: <boolean> True on success, False on failure
    """
    success = False
    # Including separators allows for extra pretty print (no trailing white space)
    outString = json.dumps(data, sort_keys=True, indent=4, separators=(',', ':'))
    if filepath.endswith('.json'):
        with open(filepath, 'w') as outputFile:
            outputFile.write(outString)
            success = True
    else:
        success = False
    return success


def get_smtp(smtpHost=TESLA_SMTP, smtpPort=TESLA_SMTP_PORT):
    """
    Get SMTP attempts to set up an SMTP connected.
    :param smtpHost: <string> The name of the host
    :param smtpPort: <int> The port number
    :return smtpObj: <smtplib.STMP> The created smtp object, or None on failure
    """
    smtpObj = None
    try:
        smtpObj = smtplib.SMTP(smtpHost, smtpPort)
    except:
        smtpObj = None

    return smtpObj


# Remove once all BC Python Modules are moved to the logging method
def setup_master_log(log_path, log_filename, logger='Master', log_format='%(asctime)s: %(levelname)s: %(message)s'):
    """
    Setup Master Log sets up the master log.
    :param log_path: <String> The path to the directory containing the master log file
    :param log_filename: <String> The filename of the master log file
    :param logger: <String> The name (unique ID) of the logger, defaulted to 'Master' (Optional)
    :param log_format: <String> The formatting for the master log (default: '%(asctime)s: %(levelname)s: %(message)s')
    :return MLOG: <Logger> the master log, or None if failed
    """
    full_filename = os.path.join(log_path, log_filename)
    success = False
    try:
        hndl = logging.FileHandler(full_filename)
        success = True
    except IOError:
        os.mkdir(log_path)
        try:
            hndl = logging.FileHandler(full_filename)
            success = True
        except:
            print "Could not create log files."
            success = False

    if success:
        frm = logging.Formatter(log_format)
        hndl.setLevel(logging.INFO)
        hndl.setFormatter(frm)

        MLOG = logging.getLogger(logger)
        MLOG.setLevel(logging.INFO)
        MLOG.addHandler(hndl)
    else:
        MLOG = None

    return MLOG


# TODO: Remove once all BC Python Modules are moved to the new logging method
def master_log(entry_type, entry_text, master_log, log_entry=True):
    """
    Master Log logs entries into the specified master log that was setup using setup_master_log.
    :param entry_type: <Master_Log_Entry_Type> The type of entry for the master log
    :param entry_text: <String> The message to be written to the log
    :param master_log: <Logger> master log, set up using setup_master_log
    :param log_entry: <boolean> True if the logger should log this entry, False otherwise
    """
    if log_entry:
        if entry_type == Master_Log_Entry_Type.info:
            master_log.info(str(entry_text))
        elif entry_type == Master_Log_Entry_Type.warning:
            master_log.warning(str(entry_text))
        elif entry_type == Master_Log_Entry_Type.error:
            master_log.error(str(entry_text))
        elif entry_type == Master_Log_Entry_Type.debug:
            master_log.debug(str(entry_text))


def get_logger(loggingLevel=None, logFile=None, fileAppend=True, handler=None, handlerStreamType=None,
               formatter='%(asctime)s: %(levelname)s: %(message)s'):
    """
    Get Logger returns the requested logger.  If the handler is a file handler, then logFile must be input into
      get logger.  If the handler is a stream handler, then handlerStreamType must be input into get logger.

    :param loggingLevel: <LoggingLevel> The level that the log should log do; defaults to the root log
    :param logFile: <string> The full file path to the log; defaults to None; should only be used for root logs
    :param fileAppend: <boolean> True if the log file should be appended to, False for overwrite; defaults to True
    :param handler: <LoggingHandler> The type of logging handler to use; defaults to None
    :param handlerStreamType: <HandlerStream> The type of handler stream the handler should log to; defaults to None
    :param formatter: <string> format the log entires should take; defaults to '%(asctime)s: %(levelname)s: %(message)s'
    :return logger: <Logger> the requested log, or None on failure
    """
    # Get logger
    logger = logging.getLogger(__name__)

    def except_handler(ty, value, tb):
        logger.exception("Uncaught exception: {0}: ".format(str(value)), exc_info=(ty, value, tb))
        sys.stdout.write(''.join(format_exception(ty, value, tb)))

    # setup excepthook
    sys.excepthook = except_handler

    # Get the handler
    logHandler = None
    # File Handler
    if handler == LoggingHandler.FILE_HANDLER:
        try:
            if logFile and fileAppend:
                # Append to existing log
                logHandler = logging.FileHandler(logFile)
            elif logFile:
                # Overwrite log
                logHandler = logging.FileHandler(logFile, mode='w')
            else:
                logger.error("To create a log file, must pass in a log file path.")
                logger = None
        except IOError:
            os.makedirs(os.path.dirname(logFile))
            try:
                if fileAppend:
                    # Append to existing log
                    logHandler = logging.FileHandler(logFile)
                else:
                    # Overwrite log
                    logHandler = logging.FileHandler(logFile, mode='w')
            except:
                logger.error("Failed to create log file {0}.".format(logFile))
                logger = None

    # Stream Handler
    elif handler == LoggingHandler.STREAM_HANDLER:
        if handlerStreamType:
            if handlerStreamType == HandlerStream.STDERR:
                # default
                logHandler = logging.StreamHandler()
            elif handlerStreamType == HandlerStream.STDOUT:
                logHandler = logging.StreamHandler(sys.stdout)
            else:
                logger.warning("Unknown Stream Handler Type {0}.  Defaulting to STDERR.".format(handler))
                logHandler = logging.StreamHandler()
        else:
            logger.error("Handler Stream Type required to set up a handler stream.")
            logger = None

    # NULL Handler
    elif handler == LoggingHandler.NULL_HANDLER:
        logHandler = logging.NullHandler()

    # No Handler
    else:
        logHandler = None

    # Set the format, if applicable
    if formatter and logHandler:
        fmt = logging.Formatter(formatter)
        logHandler.setFormatter(fmt)

    # Add the handler
    if logHandler:
        logger.addHandler(logHandler)

        # Set logging level
        if loggingLevel == LoggingLevel.DISABLED:
            logger.disabled = True
        elif loggingLevel == LoggingLevel.DEBUG:
            logger.setLevel(logging.DEBUG)
        elif loggingLevel == LoggingLevel.INFO:
            logger.setLevel(logging.INFO)
        elif loggingLevel == LoggingLevel.WARNING:
            logger.setLevel(logging.WARNING)
        elif loggingLevel == LoggingLevel.ERROR:
            logger.setLevel(logging.ERROR)
        elif loggingLevel == LoggingLevel.CRITICAL:
            logger.setLevel(logging.CRITICAL)
        else:
            # Defaults to NOTSET (causes all messages to be processed when logger is root logger,
            #                     or delegation to the parent when the logger is a non-root logger)
            pass

    return logger


def get_credentials(filename):
    """
    Get Credentials opens the creds file and decodes the credentials.
    :param filename: <String> The full path to the credentials file
    :return credsDict: <Dictionary> 'user', 'pw' keys that decoded contain the user name and password
    """
    credsDict = dict()
    with open(filename, "r") as credsFile:
        usernameLine = credsFile.readline()
        passwordLine = credsFile.readline()

    credsDict["user"] = base64.b64decode(usernameLine)
    credsDict["pw"] = base64.b64decode(passwordLine)

    return credsDict


def kill_process_by_name(targetProcessName, verbose=True):
    """
    Kill Process By Name kills all instances of processes with a specified name
    NOTE: No Mac support!
    :param targetProcessName: <String> The name of the process to be killed
    :param verbose: <boolean> flag that determines whether error messages are printed
    :return success: <boolean> True if processes were killed or none to be killed, False on error
    """

    # ignore first 3 lines because they're part of the header
    taskList = os.popen('tasklist').readlines()[3:]
    procInstances = [task for task in taskList if targetProcessName == task.split()[0]]
    success = True
    for instance in procInstances:
        # parse out the pid and kill
        try:
            os.kill(int(instance.split()[1]), signal.SIGTERM)
        except OSError as e:
            if verbose:
                print "Failed to kill {0} with pid {1}".format(targetProcessName, instance.split()[1])
                print e
            success = False
    return success

# coding=utf-8
# from coloredlogs
import datetime
import logging
import copy
import sys
import time
import json

BLACK = 10001
RED = 10002
GREEN = 10003
YELLOW = 10004
BLUE = 10005
MAGENTA = 10006
CYAN = 10007
WHITE = 10008
HTTP_RESP = 20000



if sys.version >= (3, 0, 0):
    def _log_patch(self, level, msg, args, exc_info=None, extra=None, stack_info=False, **kwargs):
        from logging import _srcfile
        sinfo = None
        if _srcfile:
            try:
                fn, lno, func, sinfo = self.findCaller(stack_info)
            except ValueError:  # pragma: no cover
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else:  # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        record = self.makeRecord(self.name, level, fn, lno, msg, args,
                                 exc_info, func, extra, sinfo)

        record.fields = kwargs
        self.handle(record)
else:
    def _log_patch(self, level, msg, args, exc_info=None, extra=None, **kwargs):
        from logging import _srcfile
        if _srcfile:
            #IronPython doesn't track Python frames, so findCaller raises an
            #exception on some versions of IronPython. We trap it here so that
            #IronPython can use logging.
            try:
                fn, lno, func = self.findCaller()
            except ValueError:
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else:
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        record = self.makeRecord(self.name, level, fn, lno, msg, args, exc_info, func, extra)

        record.fields = kwargs
        self.handle(record)


logging.Logger._log = _log_patch


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.log_black = lambda x: logger.log(BLACK, x)
    logger.log_red = lambda x: logger.log(RED, x)
    logger.log_green = lambda x: logger.log(GREEN, x)
    logger.log_yellow = lambda x: logger.log(YELLOW, x)
    logger.log_blue = lambda x: logger.log(BLUE, x)
    logger.log_magenta = lambda x: logger.log(MAGENTA, x)
    logger.log_cyan = lambda x: logger.log(CYAN, x)
    logger.log_white = lambda x: logger.log(WHITE, x)
    logger.log_http = lambda x: logger.log(HTTP_RESP, x)

    return logger


root_handler = None
# Portable color codes from http://en.wikipedia.org/wiki/ANSI_escape_code#Colors.
ansi_color_codes = dict(black=0, red=1, green=2, yellow=3, blue=4, magenta=5, cyan=6, white=7)


def ansi_text(text, color=None, bold=False, faint=False, underline=False, inverse=False, strike_through=False):
    """
    Wrap text in ANSI escape sequences for the given color and/or style(s).
    :param text: The text to wrap in ANSI escape sequences (a string).
    :param color: The name of a color (one of the strings ``black``, ``red``,
                  ``green``, ``yellow``, ``blue``, ``magenta``, ``cyan`` or
                  ``white``) or ``None`` (the default) which means no escape
                  sequence to switch color will be emitted.
    :param bold: ``True`` enables bold font (the default is ``False``).
    :param faint: ``True`` enables faint font (the default is ``False``).
    :param underline: ``True`` enables underline font (the default is ``False``).
    :param inverse: ``True`` enables inverse font (the default is ``False``).
    :param strike_through: ``True`` enables crossed-out / strike-through font
                           (the default is ``False``).
    :returns: The text message wrapped in ANSI escape sequences (a string).
    :raises: :py:exc:`Exception` when an invalid color name is given.
    """
    sequences = []
    if bold:
        sequences.append('1')
    if faint:
        sequences.append('2')
    if underline:
        sequences.append('4')
    if inverse:
        sequences.append('7')
    if strike_through:
        sequences.append('9')
    if color:
        try:
            sequences.append('3%i' % ansi_color_codes[color])
        except KeyError:
            msg = "Invalid color name %r! (expected one of %s)"
            raise Exception(msg % (color, ', '.join(sorted(ansi_color_codes))))
    if sequences:
        return '\x1b[%sm%s\x1b[0m' % (';'.join(sequences), text)
    else:
        return text


class ColoredStreamHandler(logging.StreamHandler):
    """
    The :py:class:`ColoredStreamHandler` class enables colored terminal output
    for a logger created with Python's :py:mod:`logging` module. The log
    handler formats log messages including timestamps, logger names and
    severity levels. It uses `ANSI escape sequences`_ to highlight timestamps
    and debug messages in green and error and warning messages in red. The
    handler does not use ANSI escape sequences when output redirection applies,
    for example when the standard error stream is being redirected to a file.
    Here's an example of its use::
        # Create a logger object.
        import logging
        logger = logging.getLogger('your-module')
        # Initialize coloredlogs.
        import coloredlogs
        coloredlogs.install()
        coloredlogs.set_level(logging.DEBUG)
        # Some examples.
        logger.debug("this is a debugging message")
        logger.info("this is an informational message")
        logger.warn("this is a warning message")
        logger.error("this is an error message")
        logger.fatal("this is a fatal message")
        logger.critical("this is a critical message")
    .. _ANSI escape sequences: http://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    """

    default_severity_to_style = {
        'DEBUG': dict(color='green'),
        'INFO': dict(),
        'VERBOSE': dict(color='blue'),
        'WARNING': dict(color='yellow'),
        'ERROR': dict(color='red'),
        'CRITICAL': dict(color='red', bold=True),
    }

    user_defined_seversity = {
        'Level 10001': dict(color='black'),
        'Level 10002': dict(color='red'),
        'Level 10003': dict(color='green'),
        'Level 10004': dict(color='yellow'),
        'Level 10005': dict(color='blue'),
        'Level 10006': dict(color='magenta'),
        'Level 10007': dict(color='cyan'),
        'Level 10008': dict(color='white'),
    }

    default_severity_to_style.update(user_defined_seversity)

    def __init__(self, stream=sys.stderr, level=logging.NOTSET, isatty=None,
                 show_name=True, show_severity=True, show_timestamps=True,
                 show_hostname=True, use_chroot=True, severity_to_style=None, no_color=False):
        logging.StreamHandler.__init__(self, stream)
        self.level = level
        self.show_timestamps = show_timestamps
        self.show_hostname = show_hostname
        self.show_name = show_name
        self.show_severity = show_severity
        self.severity_to_style = self.default_severity_to_style.copy()
        if severity_to_style:
            self.severity_to_style.update(severity_to_style)
        if isatty is not None:
            self.isatty = isatty
        else:
            # Protect against sys.stderr.isatty() not being defined (e.g. in
            # the Python Interface to Vim).
            try:
                self.isatty = stream.isatty()
            except Exception:
                self.isatty = False

        self._no_color = no_color
        
        if sys.version < (3, 0, 0):
            self.terminator = '\n'
            
    def emit(self, record):
        """
        Called by the :py:mod:`logging` module for each log record. Formats the
        log message and passes it onto :py:func:`logging.StreamHandler.emit()`.
        """
        # If the message doesn't need to be rendered we take a shortcut.
        if record.levelno < self.level:
            return
        # Make sure the message is a string.
        message = record.msg
        try:
            if not isinstance(message, str):
                message = message.__repr__()
        except NameError:
            if not isinstance(message, str):
                message = str(message)

        if not self._no_color:
            # Colorize the log message text.
            severity = record.levelname

            if severity in self.severity_to_style:
                message = self.wrap_style(text=message, **self.severity_to_style[severity])

            # Compose the formatted log message as:
            #   timestamp hostname name severity message
            # Everything except the message text is optional.
            parts = []
            if self.show_timestamps:
                parts.append(self.wrap_style(
                    text='[%s] %s:%s' % (self.render_timestamp(record.created),
                                         record.filename, record.lineno),
                    color='green'))
            parts.append(self.wrap_style(text=record.name, color='cyan'))
        else:
            # message = '[%s] %s' % (record.levelname, message)
            parts = []
            # if self.show_timestamps:
            #    parts.append(self.render_timestamp(record.created))

        parts.append(message)
        message = ' '.join(parts)
        # Copy the original record so we don't break other handlers.
        record = copy.copy(record)
        record.msg = message
        # Use the built-in stream handler to handle output.
        self._emit(record)

    def _emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            msg = self.format(record)

            if self._no_color:
                # 生产环境 无颜色
                foo = {"message": msg, "level": record.levelname, "timestamp": datetime.datetime.now().isoformat()}
                if hasattr(record, 'fields') and isinstance(record.fields, dict):
                    foo['fields'] = record.fields

                msg = json.dumps(foo, default=str)

            else:
                if hasattr(record, 'fields') and isinstance(record.fields, dict):
                    msg += '\t'
                    msg += ' '.join(
                        map(lambda x: '%s=%s' % (self.wrap_style(x[0], color='blue'), x[1]), record.fields.items()))

                    msg = '[%s] ' % record.levelname + msg

            stream = self.stream
            stream.write(msg)
            stream.write(self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

    def render_timestamp(self, created):
        """
        Format the time stamp of the log record. Receives the time when the
        LogRecord was created (as returned by :py:func:`time.time()`). By
        default this returns a string in the format ``YYYY-MM-DD HH:MM:SS``.
        Subclasses can override this method to customize date/time formatting.
        """
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created))

    def render_name(self, name):
        """
        Format the name of the logger. Receives the name of the logger used to
        log the call. By default this returns a string in the format
        ``NAME[PID]`` (where PID is the process ID reported by
        :py:func:`os.getpid()`).
        Subclasses can override this method to customize logger name formatting.
        """
        return '%s[%s]' % (name, self.pid)

    def wrap_style(self, text, **kw):
        """
        Wrapper for :py:func:`ansi_text()` that's disabled when ``isatty=False``.
        """
        return ansi_text(text, **kw) if self.isatty else text


def install(level=logging.FATAL, no_color=False, **kw):
    """
    Install a :py:class:`ColoredStreamHandler` for the root logger. Calling
    this function multiple times will never install more than one handler.
    :param level: The logging level to filter on (defaults to :py:data:`logging.INFO`).
    :param kw: Optional keyword arguments for :py:class:`ColoredStreamHandler`.
    """
    global root_handler
    if not root_handler:
        # Create the root handler.
        root_handler = ColoredStreamHandler(level=level, no_color=no_color, **kw)
        # Install the root handler.
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.NOTSET)
        root_logger.addHandler(root_handler)


# Initialize coloredlogs.

# print json log if no_color = 0 else colored logs
install(level=logging.INFO, show_hostname=False, show_name=False, no_color=0)


if __name__ == '__main__':
    logger = get_logger('Test')
    logger.info("test %d", 123, name="hi", age=771)

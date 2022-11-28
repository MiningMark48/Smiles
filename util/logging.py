import logging
import typing

log = logging.getLogger("smiles")


class Colors:
    """
    Colors used for logging.
    """

    reset = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strike_through = '\033[09m'
    invisible = '\033[08m'

    class FG:
        """
        Foreground colors
        """

        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        light_grey = '\033[37m'
        dark_grey = '\033[90m'
        light_red = '\033[91m'
        light_green = '\033[92m'
        yellow = '\033[93m'
        light_blue = '\033[94m'
        pink = '\033[95m'
        light_cyan = '\033[96m'

    class BG:
        """
        Background colors
        """

        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        light_grey = '\033[47m'


class ConsoleColorFormatter(logging.Formatter):
    """Logging formatter to add colors"""

    def __init__(self, format: str, date_format: str, style: str, colored=True):
        self.fmt = format
        self.date_format = date_format
        self.style = style
        self.colored = colored

        def f(c):
            return c + format + Colors.reset

        self.formats = {
            logging.DEBUG: f(Colors.FG.purple),
            logging.INFO: f(Colors.FG.light_grey),
            logging.WARNING: f(Colors.FG.orange),
            logging.ERROR: f(Colors.FG.red),
            logging.CRITICAL: f(Colors.FG.pink),
            CustomLogLevels.LOG_LEVELS["success"]: f(Colors.FG.light_green),
            CustomLogLevels.LINEBREAK_LEVELS["lnbrk"]["level"]: f(Colors.FG.light_cyan)
        }

    def format(self, record):
        log_fmt = self.formats.get(record.levelno) if self.colored else self.fmt
        formatter = logging.Formatter(log_fmt, self.date_format, self.style)
        return formatter.format(record)


class CustomLogLevels:
    LOG_LEVELS = {
        "success": 21
    }

    LINEBREAK_LEVELS = {
        "lnbrk": {
            "level": 22,
            "char": "- ",
            "char_amt": 20
        }
    }

    @staticmethod
    def add_log_levels():
        """
        Add the log levels to the logging module
        """

        log.info("Adding log levels")

        for level_name in CustomLogLevels.LOG_LEVELS:
            CustomLogLevels.add_log_level(level_name, CustomLogLevels.LOG_LEVELS[level_name])

        linebreak_levels = CustomLogLevels.LINEBREAK_LEVELS
        for level_name in linebreak_levels:
            CustomLogLevels.add_linebreak_level(
                level_name, linebreak_levels[level_name]["level"], char=linebreak_levels[level_name]["char"],
                char_amt=linebreak_levels[level_name]["char_amt"])

        log.info("Log levels added")

    @staticmethod
    def add_log_level(level_name: str, level_num: int):
        """Add a custom log level to the logging module.

        Args:
            level_name (str): Log level name
            level_num (int): Log level number
        """

        logging.addLevelName(level_num, level_name.upper())

        def cstm_level(self, message, *args, **kwargs):
            self._log(level_num, message, args, **kwargs)

        setattr(logging.Logger, level_name.lower(), cstm_level)

        log.debug(f"Added log level {level_name} ({level_num})")

    @staticmethod
    def add_linebreak_level(level_name: str, level_num: int, char="-", char_amt=10):
        """Add a custom linebreak log level to the logging module.

        Args:
            level_name (str): Log level name
            level_num (int): Log level number
            char (str): Character used to break the log level
            char_amt (int): Number of characters to use for the log level
        """

        logging.addLevelName(level_num, level_name.upper())

        def cstm_level(self, message: typing.Optional[str] = None, *args, **kwargs):
            log_message = char * (int(char_amt / 2)) + message + char * (
                int(char_amt / 2)) if message else char * char_amt
            self._log(level_num, str(log_message).upper() + ' ', args, **kwargs)

        setattr(logging.Logger, level_name.lower(), cstm_level)

        log.debug(f"Added linebreak log level {level_name} ({level_num}) (Char: '{char}' [{char_amt}])")

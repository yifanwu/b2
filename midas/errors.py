from typing import Any, Optional

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class NullValueError(Exception):
    def __init__(self, message):
        super().__init__(message)


class WrongTypeError(Exception):
    def __init__(self, message):
        super().__init__(message)


class DfNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InternalLogicalError(Exception):
    def __init__(self, message):
        super().__init__(message)


class UserError(Exception):
    def __init__(self, message):
        super().__init__(message)

        
def check_not_null(val: Any, err_msg: Optional[str]=None):
    if (val == None):
        raise NullValueError(err_msg)


def type_check_with_warning(val: Any, t: Any):
    if not (isinstance(val, t)):
        err_msg = f"expected variable to be {t} but got {val} instead"
        raise WrongTypeError(err_msg)


def report_error_to_user(msg: str):
    print(bcolors.WARNING + "[Warning] " + msg + bcolors.ENDC)


def logging(function: str, msg: str):
    print(bcolors.GREEN + f"[{function}]\t\t" + msg + bcolors.ENDC)


def debug_log(msg: str):
    print(bcolors.WARNING + msg + bcolors.ENDC)
    
from typing import Any, Optional

class NullValueError(Exception):
    def __init__(self, message):
        super().__init__(message)


class WrongTypeError(Exception):
    def __init__(self, message):
        super().__init__(message)


class DfNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)


def check_not_null(val: Any, err_msg: Optional[str]=None):
    if (val == None):
        raise NullValueError(err_msg)


def type_check_with_warning(val: Any, t: Any):
    if not (isinstance(val, t)):
        err_msg = f"expected variable to be {t} but got {val} instead"
        raise WrongTypeError(err_msg)

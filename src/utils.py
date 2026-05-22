# -------------------------------------------------------------------------- #
#                                  Packages                                  #
# -------------------------------------------------------------------------- #
import datetime
import pathlib


# -------------------------------------------------------------------------- #
#                                  Classes                                   #
# -------------------------------------------------------------------------- #
class CheckType:
    """Functions that raises an error if the type is unexpected."""

    def __init__(self):
        return None

    @staticmethod
    def _check_type(var, expected_type):
        if not isinstance(var, expected_type):
            raise TypeError(f"Expected {expected_type}, recieved {type(var)}")
        return None

    @staticmethod
    def is_bool(var):
        """Raise a TypeError if the input is not a boolean."""
        return CheckType._check_type(var, bool)

    @staticmethod
    def is_int(var):
        """Raise a TypeError if the input is not an integer."""
        return CheckType._check_type(var, int)

    @staticmethod
    def is_float(var):
        """Raise a TypeError if the input is not a float."""
        return CheckType._check_type(var, float)

    @staticmethod
    def is_str(var):
        """Raise a TypeError if the input is not a string."""
        return CheckType._check_type(var, str)

    @staticmethod
    def is_string(var):
        """Raise a TypeError if the input is not a string."""
        return CheckType.is_str(var)

    @staticmethod
    def is_dict(var):
        """Raise a TypeError if the input is not a dictionary."""
        return CheckType._check_type(var, dict)

    @staticmethod
    def is_list(var):
        """Raise a TypeError if the input is not a list."""
        return CheckType._check_type(var, list)

    @staticmethod
    def is_datetime(var):
        """Raise a TypeError if the input is not a datetime."""
        return CheckType._check_type(var, datetime.datetime)

    @staticmethod
    def is_date(var):
        """Raise a TypeError if the input is not a date."""
        return CheckType._check_type(var, datetime.date)

    @staticmethod
    def is_path(var):
        """Raise a TypeError if the input is not a path from the Path libary."""
        return CheckType._check_type(var, type(pathlib.Path.home()))


# -------------------------------------------------------------------------- #
#                                    Main                                    #
# -------------------------------------------------------------------------- #
if __name__ == "__main__":
    pass

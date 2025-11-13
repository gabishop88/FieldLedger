from enum import StrEnum


class ExeMsg(StrEnum):
    """## Provides literals to maintain consistent error messages.
    If a literal contains a format string (like the `{0}` in `ExeMsg.NF_USER`), use `.format()`:
    `ExeMsg.NF_USER.format(missing_user.id)`

    See https://docs.python.org/3/library/stdtypes.html#str.format for more information.
    """

    # HTTP_400_BAD_REQUEST
    BAD_PWD = "Incorrect Password."
    BAD_EMPTY_SEARCH = "Provide A Search Option"
    # NOTE: `crud_base.py`  current has the only exception that doesn't use ExeMsg since it passes the exception detail directly up from the database.

    # HTTP_403_FORBIDDEN
    FBDN_CRED = "Unable To Validate Credentials."
    FBDN_PRIV = "User Missing Priveleges."
    FBDN_DEL_1SU = "YOU ARE NEEDED, ADMINISTRATOR."
    FBDN_REM_1SU = "Cannot Delete First Superuser."

    # HTTP_404_NOT_FOUND
    NF_USER = "<User {0}> Not Found."
    NF_FARM = "<Farm {0}> Not Found."
    NF_EMAIL = "<Email {0}> Not Found."
    NF_TABLE = "<Table {0}> Not Found."
    NF_TABLE_KEY = "<{0} {1}> Not Found."

    # HTTP_409_CONFLICT
    CONFLICT_EMAIL = "<Email {0}> Already In Use."

from enum import StrEnum


class ExeMsg(StrEnum):
    """### Provides literals to maintain consistent error messages.
    Use `.format()` to replace placeholers (like the `{0}` in `ExeMsg.NF`):
    > `ExeMsg.NF.format("User", missing_user_id)`

    > `<{0} {1}> Not Found.` -> `<User 123e4567-e89b-12d3-a456-426614174000> Not Found.`

    See https://docs.python.org/3/library/stdtypes.html#str.format for more information.
    """

    # HTTP_400_BAD_REQUEST
    BAD_PWD = "Incorrect Password."
    BAD_EMPTY_SEARCH = "Provide A Search Option"

    # HTTP_403_FORBIDDEN
    FBDN_CRED = "Unable To Validate Credentials."
    FBDN_PRIV = "User Missing Priveleges."
    FBDN_DEL_1SU = "YOU ARE NEEDED, ADMINISTRATOR."
    FBDN_REM_1SU = "Cannot Delete First Superuser."

    # HTTP_404_NOT_FOUND
    NF = "<{0} {1}> Not Found."

    # HTTP_409_CONFLICT (Matches the detail sent by the DB when violating constraints)
    KEY_EXISTS = "Key ({0})=({1}) already exists."

    # HTTP_422_UNPROCESSABLE_ENTITY
    INVALID_WKT = "'geom' is not valid WKT."
    INVALID_TOPO = "'geom' has invalid topology."

def test_current_user(db) -> None:
    ...

# TODO: Add tests that make sure "app.current_user" is set properly for each Session dep
# I used these endpoints to test manually, figure out the best way to do unit testing.

# @router.get("/session-variable/read")
# def debug_session_var_readonly(db: ReadSession) -> str:
#     return str(db.exec(text('SHOW "app.current_user";')).first()[0])  # type: ignore


# @router.get("/session-variable/write")
# def debug_session_var_write(db: WriteSession) -> str:
#     return str(db.exec(text('SHOW "app.current_user";')).first()[0])  # type: ignore


# @router.get("/session-variable/user")
# def debug_session_var_user(db: UserSession) -> str:
#     return str(db.exec(text('SHOW "app.current_user";')).first()[0])  # type: ignore

from contextvars import ContextVar

_request_id_context: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(value: str) -> None:
    _request_id_context.set(value)


def get_request_id() -> str:
    return _request_id_context.get()

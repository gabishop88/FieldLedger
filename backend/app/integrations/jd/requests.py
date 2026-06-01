import logging
from typing import Literal
from urllib.parse import urlparse

from requests import Response
from requests.api import request
from rich.logging import RichHandler

log_handler = RichHandler(rich_tracebacks=True, show_time=False)
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[log_handler])
log = logging.getLogger(__name__)

Method = Literal["get", "post", "put", "patch", "delete"]


def rq(m: Method, url: str, pram=None, head=None, json=None, data=None) -> Response:
    """Make and print request, return response."""
    res = request(m, url, params=pram, headers=head, data=data, json=json)
    u, status = urlparse(res.request.url), res.status_code
    log.info(f'{u.hostname} "{m.upper()} {u.path}?{u.query} HTTP/1.1" {status} -')
    assert status in (200, 304, 404, 409), f"{status}: {res.text}"
    return res

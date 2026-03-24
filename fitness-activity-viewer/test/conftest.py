"""
Pytest configuration for Playwright tests.
"""
import pytest
import time
from subprocess import Popen
from http.client import HTTPConnection
from contextlib import contextmanager
from typing import Callable
from playwright.sync_api import Browser, BrowserContext, Page


def gen_background_server_ctxmanager(
    cmd: list | None = None,
    cwd: str = "/",
    port: int = 8000,
    healthendpoint: str = "/",
    wait_seconds: int = 5,
    **kwargs,
) -> Callable:
    if cmd is None:
        cmd = ["python", "-m", "http.server"]

    @contextmanager
    def server():
        print(f"opening server {cmd=} at {cwd=}")
        retries = 10
        process = Popen(cmd, cwd=cwd, **kwargs)
        # give it 1 second right off the bat
        time.sleep(1)
        while retries > 0:
            conn = HTTPConnection(f"localhost:{port}")
            try:
                conn.request("HEAD", healthendpoint)
                response = conn.getresponse()
                if response is not None:
                    print(f"health check for {cmd=} got a response")
                    yield process
                    break
            except ConnectionRefusedError:
                print(f"failed health check for {cmd=}, waiting {wait_seconds=}")
                time.sleep(wait_seconds)
                retries -= 1

        if not retries:
            raise RuntimeError(f"Failed to start server at {port=}")
        else:
            print(f"terminating process after {retries}")
            # do it twice for good measure
            process.terminate()
            time.sleep(1)
            process.terminate()
            time.sleep(1)

    return server


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Override browser context arguments."""
    return {
        **browser_context_args,
        "viewport": {"width": 1400, "height": 900},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="function")
def context(browser: Browser):
    """Create a new browser context for each test."""
    context = browser.new_context(
        viewport={"width": 1400, "height": 900},
        ignore_https_errors=True,
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """Create a new page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session")
def background_server():
    """Start background HTTP server for tests."""
    import os
    # Run server from project root, not test directory
    cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_ctx = gen_background_server_ctxmanager(
        cmd=["python", "-m", "http.server", "8000"],
        cwd=cwd,
        port=8000,
        healthendpoint="/",
        wait_seconds=2,
    )
    with server_ctx():
        yield "http://localhost:8000"


@pytest.fixture(scope="session")
def base_url(background_server):
    """Provide base URL for tests."""
    return background_server

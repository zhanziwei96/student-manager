import pytest
import re
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, playwright):
    return {"viewport": {"width":1280,"height":720}}


def test_example(page: Page) -> None:
    page.goto("http://localhost:3000/")

"""Playwright browser session helpers for apply automation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from job_agent.config import Settings
from job_agent.constants.apply import CAPTCHA_SELECTORS, TWO_FA_SELECTORS
from job_agent.logging_setup import get_logger

pclog = get_logger(__name__)


class BrowserSession:
    """Thin wrapper around a persistent Playwright browser context."""

    def __init__(self, settings: Settings, portal: str) -> None:
        """Prepare session paths for a portal.

        Args:
            settings: App settings (headless, slow_mo, sessions dir).
            portal: Portal id used as the session folder name.
        """
        self.settings = settings
        self.portal = portal
        self.user_data_dir = Path(settings.sessions_dir) / portal
        self._playwright: Any = None
        self._context: Any = None
        self._page: Any = None

    def __enter__(self) -> BrowserSession:
        """Start Playwright with a persistent context for cookie reuse."""
        from playwright.sync_api import sync_playwright

        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        # Persistent context keeps logged-in cookies between runs.
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=self.settings.apply_headless,
            slow_mo=self.settings.apply_slow_mo_ms,
        )
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        pclog.info(
            "Started browser portal=%s headless=%s slow_mo_ms=%s",
            self.portal,
            self.settings.apply_headless,
            self.settings.apply_slow_mo_ms,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        """Close context and stop Playwright."""
        del exc_type, exc, tb
        if self._context is not None:
            self._context.close()
        if self._playwright is not None:
            self._playwright.stop()
        pclog.info("Closed browser portal=%s", self.portal)

    @property
    def page(self) -> Any:
        """Return the active Playwright page."""
        if self._page is None:
            raise RuntimeError("BrowserSession not started")
        return self._page

    def goto(self, url: str) -> None:
        """Navigate to a URL with a generous wait for network idle.

        Args:
            url: Absolute URL.
        """
        pclog.debug("Navigate portal=%s url=%s", self.portal, url)
        self.page.goto(url, wait_until="domcontentloaded")

    def fill_if_present(self, selector: str, value: str) -> bool:
        """Fill an input when the selector exists.

        Args:
            selector: CSS selector.
            value: Value to type.

        Returns:
            ``True`` if the element was found and filled.
        """
        locator = self.page.locator(selector)
        if locator.count() == 0:
            return False
        locator.first.fill(value)
        return True

    def click_if_present(self, selector: str) -> bool:
        """Click the first matching element when present.

        Args:
            selector: CSS selector.

        Returns:
            ``True`` if clicked.
        """
        locator = self.page.locator(selector)
        if locator.count() == 0:
            return False
        locator.first.click()
        return True

    def detect_captcha(self) -> bool:
        """Return True if a known CAPTCHA selector is visible."""
        for selector in CAPTCHA_SELECTORS:
            locator = self.page.locator(selector)
            if locator.count() > 0:
                pclog.warning("CAPTCHA detected portal=%s selector=%s", self.portal, selector)
                return True
        return False

    def detect_2fa(self) -> bool:
        """Return True if a known OTP/2FA input is visible."""
        for selector in TWO_FA_SELECTORS:
            locator = self.page.locator(selector)
            if locator.count() > 0:
                pclog.warning("2FA detected portal=%s selector=%s", self.portal, selector)
                return True
        return False

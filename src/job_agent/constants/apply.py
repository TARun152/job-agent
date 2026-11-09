"""Apply automation and safety defaults."""

DEFAULT_APPLY_SLOW_MO_MS = 120
DEFAULT_MAX_DAILY_APPLIES = 10
DEFAULT_MAX_DAILY_DISCOVERIES = 50
DEFAULT_NOTICE_PERIOD_DAYS = 30

APPLY_STATUS_PENDING = "pending"
APPLY_STATUS_APPLIED = "applied"
APPLY_STATUS_FAILED = "failed"
APPLY_STATUS_SKIPPED = "skipped"
APPLY_STATUS_PAUSED_CAPTCHA = "paused_captcha"
APPLY_STATUS_PAUSED_2FA = "paused_2fa"

CAPTCHA_SELECTORS = (
    "iframe[src*='recaptcha']",
    ".g-recaptcha",
    "#captcha",
    "[data-testid='captcha']",
)

TWO_FA_SELECTORS = (
    "input[name*='otp']",
    "input[name*='2fa']",
    "input[autocomplete='one-time-code']",
    "#otp",
)

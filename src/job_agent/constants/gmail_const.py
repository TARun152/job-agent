"""Gmail OAuth scopes and OTP patterns."""

GMAIL_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
)

OTP_PATTERN = r"\b(\d{4,8})\b"
OTP_CONTEXT_PATTERN = r"(?:otp|code|verification|passcode)[^\d]{0,20}(\d{4,8})"

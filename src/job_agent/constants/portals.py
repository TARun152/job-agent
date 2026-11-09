"""Portal identifiers used across discovery and apply adapters."""

PORTAL_NAUKRI = "naukri"
PORTAL_INSTAHYRE = "instahyre"
PORTAL_LINKEDIN = "linkedin"
PORTAL_WORKDAY = "workday"

SUPPORTED_PORTALS = (
    PORTAL_NAUKRI,
    PORTAL_INSTAHYRE,
    PORTAL_LINKEDIN,
    PORTAL_WORKDAY,
)

# Public search / login entry URLs (not secrets).
NAUKRI_BASE_URL = "https://www.naukri.com"
NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_SEARCH_URL = "https://www.naukri.com/{query}-jobs"

INSTAHYRE_BASE_URL = "https://www.instahyre.com"
INSTAHYRE_LOGIN_URL = "https://www.instahyre.com/login/"
INSTAHYRE_SEARCH_URL = "https://www.instahyre.com/search-jobs"

LINKEDIN_BASE_URL = "https://www.linkedin.com"
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_JOBS_SEARCH_URL = "https://www.linkedin.com/jobs/search/"

WORKDAY_JOBS_PATH = "/wday/cxs/{tenant}/{site}/jobs"

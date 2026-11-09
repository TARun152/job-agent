"""Lifecycle statuses for jobs and queued applications."""

JOB_STATUS_DISCOVERED = "discovered"
JOB_STATUS_MATCHED = "matched"
JOB_STATUS_SKIPPED_LOW_SCORE = "skipped_low_score"
JOB_STATUS_TAILORED = "tailored"

APP_STATUS_QUEUED = "queued"
APP_STATUS_APPROVED = "approved"
APP_STATUS_SKIPPED = "skipped"
APP_STATUS_REJECTED_BY_USER = "rejected_by_user"

QUEUE_HOST_DEFAULT = "127.0.0.1"
QUEUE_PORT_DEFAULT = 8080

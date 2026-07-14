import json
import os
from datetime import datetime, timezone


def append_to_email_log(to_email: str, subject: str, body: str) -> None:
    """
    Appends a mock email notification as a single line JSON entry in mock_emails.log.
    Creates the log file if it does not exist.
    """
    # Write to mock_emails.log at workspace root or container root
    log_path = "mock_emails.log"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "to": to_email,
        "subject": subject,
        "body": body
    }

    # Ensure single-line JSONL format by appending with line breaks
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

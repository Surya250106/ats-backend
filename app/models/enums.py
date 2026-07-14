import enum


class UserRole(str, enum.Enum):
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"


class JobStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"

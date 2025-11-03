from enum import StrEnum

DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000000"


class UserRole(StrEnum):
    """User roles for route planning service"""

    OWNER = "owner"
    ADMIN = "admin"
    DISPATCHER = "dispatcher"
    COURIER = "courier"

"""Exceptions for Hypontech Cloud API."""


class HyponCloudError(Exception):
    """Base exception for Hypontech Cloud API."""


class AuthenticationError(HyponCloudError):
    """Exception raised when authentication fails."""


class ConnectionError(HyponCloudError):
    """Exception raised when connection to API fails."""


class RateLimitError(HyponCloudError):
    """Exception raised when API rate limit is exceeded."""

"""Exceptions for Hypontech Cloud API."""


class HyponCloudError(Exception):
    """Base exception for Hypontech Cloud API."""


class AuthenticationError(HyponCloudError):
    """Exception raised when authentication fails."""


class RequestError(HyponCloudError):
    """Exception raised when API request fails."""


class RateLimitError(HyponCloudError):
    """Exception raised when API rate limit is exceeded."""

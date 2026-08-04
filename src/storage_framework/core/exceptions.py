class StorageFrameworkError(RuntimeError):
    """Base framework exception."""


class ResourceNotFound(StorageFrameworkError):
    """Requested storage resource does not exist."""


class ResourceConflict(StorageFrameworkError):
    """Requested operation conflicts with current state."""


class ValidationError(StorageFrameworkError):
    """Input or postcondition validation failed."""


class OperationTimeout(StorageFrameworkError):
    """Asynchronous operation did not finish before timeout."""

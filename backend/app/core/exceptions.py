class DocWatcherError(Exception):
    """Base exception for DocWatcher."""


class ProjectNotFoundError(DocWatcherError):
    """Project not found."""


class ProjectConnectionError(DocWatcherError):
    """Failed to connect to project repository."""


class CommitNotFoundError(DocWatcherError):
    """Commit not found."""


class GitProviderError(DocWatcherError):
    """Git provider operation failed."""


class LLMError(DocWatcherError):
    """LLM API call failed."""


class PatchGenerationError(DocWatcherError):
    """Patch generation failed."""


class PRCreationError(DocWatcherError):
    """PR creation failed."""


class ConfigParseError(DocWatcherError):
    """docops.yml parsing failed."""

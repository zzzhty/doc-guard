class DocGuardError(Exception):
    """Base exception for DocGuard."""


class ProjectNotFoundError(DocGuardError):
    """Project not found."""


class ProjectConnectionError(DocGuardError):
    """Failed to connect to project repository."""


class CommitNotFoundError(DocGuardError):
    """Commit not found."""


class GitProviderError(DocGuardError):
    """Git provider operation failed."""


class LLMError(DocGuardError):
    """LLM API call failed."""


class PatchGenerationError(DocGuardError):
    """Patch generation failed."""


class PRCreationError(DocGuardError):
    """PR creation failed."""


class ConfigParseError(DocGuardError):
    """docops.yml parsing failed."""

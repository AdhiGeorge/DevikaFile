"""Convenience wrapper that exposes the Reporter class at the
src.agents.reporter module path expected by other parts of the codebase.

The implementation lives in `src.agents.researcher.reporter.reporter.Reporter`.
Importing it here avoids changing all existing import statements.
"""

from .researcher.reporter.reporter import Reporter  # type: ignore  # noqa: F401

__all__ = ["Reporter"]

"""exhibitkit — sell-side-style research documents from Markdown.

Public surface: build(), check(), load_theme(), validate_palette(), and the mpl helper module.
Units and conventions: colours are sRGB hex strings; lengths in the LaTeX templates are in
points or fractions of the text width; dates are ISO in front matter and rendered as
"Month D, YYYY".
"""
from .build import BuildResult, build
from .check import CheckResult, check
from .palette import validate_palette
from .themes import Theme, load_theme

__version__ = "0.1.2"
__all__ = ["build", "BuildResult", "check", "CheckResult", "load_theme", "Theme", "validate_palette", "__version__"]

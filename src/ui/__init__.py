"""
CodeAtlas UI Module

Gradio-based user interface components.
"""

from .app import create_app
from .components import make_nav_bar, make_loading_html, make_stats_bar
from .styles import CUSTOM_CSS

__all__ = [
    "create_app",
    "make_nav_bar",
    "make_loading_html",
    "make_stats_bar",
    "CUSTOM_CSS",
]

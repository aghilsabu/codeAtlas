"""CodeAtlas - AI-Powered Codebase Visualization Tool"""

from src.ui import create_app, CUSTOM_CSS
from src.config import AUDIOS_DIR
import gradio as gr


def main():
    """Launch the CodeAtlas application."""
    app, custom_css = create_app()
    
    # Use Soft theme with orange accent
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.orange,
        secondary_hue=gr.themes.colors.orange,
        neutral_hue=gr.themes.colors.gray,
    )
    
    app.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860,
        mcp_server=True,
        theme=theme,
        css=custom_css,
        allowed_paths=[str(AUDIOS_DIR)],
    )


if __name__ == "__main__":
    main()

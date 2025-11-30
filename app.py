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
    
    # Force light theme CSS
    light_theme_css = """
    .dark {
        --body-background-fill: white !important;
        --background-fill-primary: white !important;
        --background-fill-secondary: #f7f7f7 !important;
        --block-background-fill: white !important;
        --body-text-color: #374151 !important;
        --block-label-text-color: #374151 !important;
        --block-title-text-color: #374151 !important;
        --input-background-fill: white !important;
        --input-background-fill-focus: white !important;
        --border-color-primary: #e5e7eb !important;
        --link-text-color: #ea580c !important;
        --link-text-color-hover: #c2410c !important;
        --button-primary-background-fill: #ea580c !important;
        --button-primary-text-color: white !important;
    }
    """
    combined_css = light_theme_css + (custom_css or "")
    
    app.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860,
        mcp_server=True,
        theme=theme,
        css=combined_css,
        allowed_paths=[str(AUDIOS_DIR)],
    )


if __name__ == "__main__":
    main()

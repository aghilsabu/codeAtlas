"""
CodeAtlas UI Application

Main Gradio application with multi-page routing.
Implements the three-page layout: Generate, Explore, Settings.
"""

import os
import json
import time
import logging
import gradio as gr
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from ..config import get_config, Config, SESSION_FILE, AUDIOS_DIR
from ..core.repository import RepositoryLoader
from ..core.analyzer import CodeAnalyzer
from ..core.diagram import DiagramGenerator, LayoutOptions
from ..integrations.voice import generate_audio_summary
from .components import (
    make_nav_bar,
    make_loading_html,
    make_stats_bar,
    make_error_html,
    make_empty_state_html,
    make_hero_section,
    make_footer,
)
from .styles import CUSTOM_CSS

logger = logging.getLogger("codeatlas.ui")

# Global instances
_repository_loader: Optional[RepositoryLoader] = None
_diagram_generator: Optional[DiagramGenerator] = None


def get_repository_loader() -> RepositoryLoader:
    """Get or create repository loader instance."""
    global _repository_loader
    if _repository_loader is None:
        _repository_loader = RepositoryLoader()
    return _repository_loader


def get_diagram_generator() -> DiagramGenerator:
    """Get or create diagram generator instance."""
    global _diagram_generator
    if _diagram_generator is None:
        _diagram_generator = DiagramGenerator()
    return _diagram_generator


# Session state management
def load_session_state() -> Dict[str, Any]:
    """Load session state from file."""
    try:
        if SESSION_FILE.exists():
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load session: {e}")
    return {
        "dot_source": None,
        "repo_name": "",
        "stats": {},
        "api_key": "",
        "openai_api_key": "",
        "elevenlabs_api_key": "",
        "model": "Gemini 2.5 Pro",
        "pending_request": None,
    }


def save_session_state(data: Dict[str, Any]) -> bool:
    """Save session state to file."""
    try:
        existing = load_session_state()
        existing.update(data)
        with open(SESSION_FILE, "w") as f:
            json.dump(existing, f)
        return True
    except Exception as e:
        logger.warning(f"Failed to save session: {e}")
        return False


def get_current_model() -> str:
    """Get the current model from session state."""
    config = get_config()
    return config.current_model


def get_model_choices() -> List[str]:
    """Get available model choices."""
    config = get_config()
    return list(config.models.all_models.keys())


def create_app():
    """Create the Gradio application with multi-page routing."""
    config = get_config()
    
    # ==================== MAIN PAGE (Generate) ====================
    with gr.Blocks(title="CodeAtlas - AI Codebase Visualizer", fill_height=True) as app:
        gr.Navbar(visible=False)
        
        # State
        file_input = gr.State(value=None)
        
        # Top nav bar
        with gr.Row(elem_classes="nav-bar-row"):
            nav_bar = gr.HTML(make_nav_bar("generate"))
            model_selector = gr.Dropdown(
                choices=get_model_choices(),
                value=get_current_model(),
                show_label=False,
                container=False,
                scale=0,
                min_width=180,
                elem_classes="model-dropdown-nav"
            )
        
        # Hero section
        gr.HTML(make_hero_section())
        
        # Input section
        with gr.Row():
            gr.Column(scale=1, min_width=50)
            with gr.Column(scale=3, min_width=400):
                github_input = gr.Textbox(
                    placeholder="github.com/owner/repo or paste a GitHub URL",
                    label="GitHub Repository",
                    lines=1,
                )
                with gr.Row():
                    analyze_btn = gr.Button("🚀 Generate Diagram", variant="primary", scale=2)
                    upload_btn = gr.UploadButton("📁 Upload ZIP", file_types=[".zip"], scale=1, variant="secondary")
                
                error_msg = gr.HTML(visible=False)
            gr.Column(scale=1, min_width=50)
        
        # Footer
        gr.HTML(make_footer())
        
        # Event handlers
        def start_analysis(file_path, github_url, selected_model):
            """Validate input and prepare for analysis."""
            logger.info(f"start_analysis: file={file_path}, url={github_url}, model={selected_model}")
            
            if not file_path and (not github_url or not github_url.strip()):
                raise gr.Error("Please enter a GitHub URL or upload a ZIP file")
            
            session = load_session_state()
            if not session.get("api_key"):
                raise gr.Error("API Key not configured. Please go to Settings first.")
            
            # Save model selection and pending request
            save_session_state({
                "model": selected_model,
                "pending_request": {
                    "github_url": github_url.strip() if github_url else None,
                    "file_path": file_path,
                },
                "dot_source": None,
                "repo_name": "",
                "stats": {},
            })
            
            return gr.update(visible=False), None, True
        
        do_redirect = gr.State(False)
        
        # Wire up events
        for trigger in [analyze_btn.click, github_input.submit]:
            trigger(
                fn=start_analysis,
                inputs=[file_input, github_input, model_selector],
                outputs=[error_msg, file_input, do_redirect]
            ).success(
                fn=None,
                js="() => { window.location.href = '/explore'; }"
            )
        
        upload_btn.upload(
            fn=lambda f, m: start_analysis(f, "", m),
            inputs=[upload_btn, model_selector],
            outputs=[error_msg, file_input, do_redirect]
        ).success(
            fn=None,
            js="() => { window.location.href = '/explore'; }"
        )
        
        # Model change handler
        def on_model_change(model):
            save_session_state({"model": model})
            config.current_model = model
            config.save_to_session()
        
        model_selector.change(fn=on_model_change, inputs=[model_selector])
        app.load(fn=get_current_model, outputs=[model_selector])
    
    # ==================== EXPLORE PAGE ====================
    with app.route("explore") as explore_page:
        current_dot = gr.State(value=None)
        chat_history = gr.State(value=[])
        
        # Nav bar
        with gr.Row(elem_classes="nav-bar-row"):
            explore_nav = gr.HTML(make_nav_bar("explore"))
            explore_model = gr.Dropdown(
                choices=get_model_choices(),
                value=get_current_model(),
                show_label=False,
                container=False,
                scale=0,
                min_width=180,
                elem_classes="model-dropdown-nav"
            )
        
        # Left sidebar - History & Layout
        with gr.Sidebar(position="left", open=False):
            gr.Markdown("#### 📜 History")
            history_dropdown = gr.Dropdown(
                choices=[],
                label="Saved Diagrams",
                interactive=True,
            )
            with gr.Row():
                load_history_btn = gr.Button("Load", variant="primary", size="sm", scale=2)
                refresh_history_btn = gr.Button("🔄", variant="secondary", size="sm", scale=1, min_width=40)
            
            gr.Markdown("---")
            gr.Markdown("#### 📐 Layout")
            layout_direction = gr.Dropdown(
                choices=["Top → Down", "Left → Right", "Bottom → Up", "Right → Left"],
                value="Top → Down",
                label="Direction",
            )
            layout_splines = gr.Dropdown(
                choices=["polyline", "ortho", "spline", "line"],
                value="polyline",
                label="Edge Style",
            )
            layout_nodesep = gr.Slider(0.1, 2.0, 0.5, step=0.1, label="Node Spacing")
            layout_ranksep = gr.Slider(0.25, 3.0, 0.75, step=0.25, label="Layer Spacing")
            zoom_slider = gr.Slider(0.25, 3.0, 1.0, step=0.1, label="Zoom")
            apply_layout_btn = gr.Button("Apply Changes", variant="primary")
        
        # Right sidebar - Audio & Chat
        with gr.Sidebar(position="right", open=False, width=400, elem_classes="sidebar-right"):
            with gr.Row(elem_classes="audio-row"):
                audio_gen_btn = gr.Button("🔊 Generate Audio", variant="primary", size="sm", elem_classes="audio-gen-btn")
            audio_status = gr.HTML("", elem_classes="audio-status")
            audio_player = gr.Audio(
                label=None,
                show_label=False,
                type="filepath",
                sources=[],
                interactive=False,
                elem_classes="audio-player-compact"
            )
            
            gr.HTML('<div style="font-size: 0.85rem; font-weight: 600; color: #374151; padding: 0.5rem 0;">💬 Ask About Code</div>')
            
            chatbot = gr.Chatbot(
                show_label=False,
                placeholder="Ask questions about the architecture...",
                elem_id="codeatlas-chat",
                avatar_images=(None, "https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg"),
                layout="panel",
                autoscroll=True
            )
            
            with gr.Column(elem_classes="chat-input-container"):
                with gr.Row(elem_classes="chat-input-row"):
                    chat_input = gr.Textbox(
                        placeholder="Ask about the architecture...",
                        show_label=False,
                        scale=6,
                        container=False,
                        lines=1,
                    )
                    chat_send_btn = gr.Button("➤", variant="primary", size="sm", scale=1, min_width=40)
        
        # Main content
        stats_output = gr.HTML("")
        diagram_output = gr.HTML(make_loading_html("⏳", "Loading..."))
        
        # Process function with progress updates
        def process_pending_request():
            """Process a pending analysis request with streaming updates."""
            session = load_session_state()
            pending = session.get("pending_request")
            
            # No pending request - show existing or empty
            if not pending or not (pending.get("github_url") or pending.get("file_path")):
                dot_source = session.get("dot_source")
                if dot_source:
                    generator = get_diagram_generator()
                    diagram = generator.render(dot_source, repo_name=session.get("repo_name", ""))
                    
                    # Count nodes/edges for existing diagram
                    node_count, edge_count = generator._count_nodes_edges(dot_source)
                    
                    stats = make_stats_bar(
                        repo_name=session.get("repo_name", ""),
                        files_processed=session.get("stats", {}).get("files_processed", 0),
                        total_characters=session.get("stats", {}).get("total_characters", 0),
                        model_name=session.get("model", ""),
                        node_count=node_count,
                        edge_count=edge_count,
                    )
                    return diagram, stats, dot_source
                else:
                    return make_empty_state_html(), "", None
            
            # Get request details
            github_url = pending.get("github_url")
            file_path = pending.get("file_path")
            model_choice = session.get("model", "Gemini 2.5 Pro")
            
            config = get_config()
            model_name = config.models.get_model_id(model_choice)
            
            # Get API key
            if config.models.is_openai_model(model_name):
                api_key = session.get("openai_api_key", "")
                if not api_key:
                    yield make_error_html("OpenAI API key required", "🔑", "/settings", "Add Key →"), "", None
                    return
            else:
                api_key = session.get("api_key", "")
                if not api_key:
                    yield make_error_html("Gemini API key required", "🔑", "/settings", "Add Key →"), "", None
                    return
            
            # Clear pending request
            save_session_state({"pending_request": None})
            
            # Step 1: Download/Process
            display_name = ""
            yield make_loading_html("📥", "Downloading repository..." if github_url else "Processing file..."), "", None
            time.sleep(0.1)  # Allow UI to update
            
            loader = get_repository_loader()
            if github_url:
                result = loader.load_from_github(github_url)
                parts = github_url.rstrip("/").split("/")
                display_name = "/".join(parts[-2:]) if len(parts) >= 2 else github_url
            else:
                result = loader.load_from_file(file_path)
                display_name = Path(file_path).stem if file_path else "upload"
            
            if result.error:
                yield make_error_html(result.error), "", None
                return
            
            # Step 2: Show files found (display briefly)
            yield make_loading_html(
                "🔍", 
                f"Extracted {result.stats.files_processed} files",
                f"{result.stats.total_characters:,} characters • Preparing AI analysis..."
            ), "", None
            time.sleep(0.5)  # Brief pause to show extraction results
            
            # Step 3: AI Analysis - this step shows while actual analysis happens
            yield make_loading_html(
                "🧠",
                "AI analyzing code structure...",
                f"Using {model_choice}"
            ), "", None
            time.sleep(0.3)  # Brief pause to render before heavy work
            
            # Step 4: Generate diagram
            try:
                yield make_loading_html("🗺️", "Generating architecture diagram...", f"{model_choice} • This may take a moment..."), "", None
                time.sleep(0.1)  # Allow UI to update
                
                analyzer = CodeAnalyzer(api_key=api_key, model_name=model_name)
                analysis = analyzer.generate_diagram(result.context)
                
                if not analysis.success:
                    yield make_error_html(analysis.error), "", None
                    return
                
                # Prepare metadata for saving
                diagram_metadata = {
                    "model_name": model_choice,
                    "files_processed": result.stats.files_processed,
                    "total_characters": result.stats.total_characters,
                }
                
                # Save results
                save_session_state({
                    "dot_source": analysis.content,
                    "repo_name": display_name,
                    "stats": result.stats.as_dict,
                    "model": model_choice,
                })
                
                # Render diagram with metadata
                generator = get_diagram_generator()
                diagram = generator.render(
                    analysis.content, 
                    repo_name=display_name, 
                    save_to_history=True,
                    metadata=diagram_metadata
                )
                
                # Count nodes/edges for stats bar
                node_count, edge_count = generator._count_nodes_edges(analysis.content)
                
                stats = make_stats_bar(
                    repo_name=display_name,
                    files_processed=result.stats.files_processed,
                    total_characters=result.stats.total_characters,
                    model_name=model_choice,
                    node_count=node_count,
                    edge_count=edge_count,
                )
                
                yield diagram, stats, analysis.content
                
            except Exception as e:
                logger.exception("Analysis failed")
                yield make_error_html(str(e)), "", None
        
        def apply_layout(dot_source, direction, splines, nodesep, ranksep, zoom):
            """Apply layout changes to the diagram."""
            if not dot_source:
                return make_empty_state_html("No diagram to adjust.")
            
            layout = LayoutOptions.from_ui(direction, splines, nodesep, ranksep, zoom)
            generator = get_diagram_generator()
            return generator.render(dot_source, layout)
        
        def load_from_history(selected):
            """Load a diagram from history with metadata."""
            if not selected:
                return make_empty_state_html("Select a diagram."), "", None, [], []
            
            generator = get_diagram_generator()
            dot_source, metadata = generator.load_from_history_with_metadata(selected)
            
            if not dot_source:
                return make_error_html("Diagram not found"), "", None, [], []
            
            # Extract repo name from filename or metadata
            name = selected.replace("raw_", "").replace(".dot", "")
            parts = name.split("_")
            repo_name = metadata.get("repo_name") if metadata else None
            if not repo_name:
                repo_name = "_".join(parts[:-2]) if len(parts) > 2 else parts[0] if parts else "local"
            
            diagram = generator.render(dot_source, repo_name=repo_name)
            
            # Always count nodes/edges from DOT source for accurate stats
            node_count, edge_count = generator._count_nodes_edges(dot_source)
            
            # Build stats bar with all available metadata
            stats = make_stats_bar(
                repo_name=repo_name,
                files_processed=metadata.get("files_processed", 0) if metadata else 0,
                total_characters=metadata.get("total_characters", 0) if metadata else 0,
                model_name=metadata.get("model_name", "") if metadata else "",
                node_count=node_count,
                edge_count=edge_count,
                extra_info="📂 From history",
            )
            
            return diagram, stats, dot_source, [], []
        
        def chat_about_diagram(message, history, dot_source):
            """Chat about the loaded diagram."""
            if not message or not message.strip():
                return history, ""
            
            message = message.strip()
            history = history or []
            
            if not dot_source:
                history = history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "⚠️ No diagram loaded. Please generate or load one first."}
                ]
                return history, ""
            
            session = load_session_state()
            api_key = session.get("api_key", "")
            model_choice = session.get("model", "Gemini 2.5 Pro")
            
            if not api_key:
                history = history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "⚠️ API key not configured. Go to Settings."}
                ]
                return history, ""
            
            try:
                config = get_config()
                model_name = config.models.get_model_id(model_choice)
                analyzer = CodeAnalyzer(api_key=api_key, model_name=model_name)
                
                result = analyzer.chat(message, dot_source, history)
                
                response = result.content if result.success else f"❌ {result.error}"
                history = history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response}
                ]
                
            except Exception as e:
                logger.exception("Chat error")
                history = history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": f"❌ Error: {str(e)}"}
                ]
            
            return history, ""
        
        def handle_audio_gen(dot_source):
            """Generate audio summary."""
            audio_path, status = generate_audio_summary(dot_source)
            if audio_path and audio_path.exists():
                return status, str(audio_path)
            return status, None
        
        def refresh_history_choices():
            """Refresh the history dropdown with latest diagrams."""
            choices = get_diagram_generator().get_history_choices()
            return gr.update(choices=choices, value=None)
        
        # Event wiring
        explore_page.load(fn=process_pending_request, outputs=[diagram_output, stats_output, current_dot])
        explore_page.load(fn=lambda: [], outputs=[chat_history])
        explore_page.load(fn=refresh_history_choices, outputs=[history_dropdown])
        explore_page.load(fn=get_current_model, outputs=[explore_model])
        
        apply_layout_btn.click(
            fn=apply_layout,
            inputs=[current_dot, layout_direction, layout_splines, layout_nodesep, layout_ranksep, zoom_slider],
            outputs=[diagram_output]
        )
        
        refresh_history_btn.click(
            fn=refresh_history_choices,
            outputs=[history_dropdown]
        )
        
        load_history_btn.click(
            fn=load_from_history,
            inputs=[history_dropdown],
            outputs=[diagram_output, stats_output, current_dot, chat_history, chatbot]
        )
        
        chat_send_btn.click(
            fn=chat_about_diagram,
            inputs=[chat_input, chatbot, current_dot],
            outputs=[chatbot, chat_input]
        )
        
        chat_input.submit(
            fn=chat_about_diagram,
            inputs=[chat_input, chatbot, current_dot],
            outputs=[chatbot, chat_input]
        )
        
        audio_gen_btn.click(
            fn=handle_audio_gen,
            inputs=[current_dot],
            outputs=[audio_status, audio_player]
        )
        
        explore_model.change(
            fn=lambda m: save_session_state({"model": m}),
            inputs=[explore_model]
        )
    
    # ==================== SETTINGS PAGE ====================
    with app.route("settings") as settings_page:
        with gr.Row(elem_classes="nav-bar-row"):
            settings_nav = gr.HTML(make_nav_bar("settings"))
            settings_model = gr.Dropdown(
                choices=get_model_choices(),
                value=get_current_model(),
                show_label=False,
                container=False,
                scale=0,
                min_width=180,
                elem_classes="model-dropdown-nav"
            )
        
        gr.HTML('''
            <div style="text-align: center; padding: 2rem 1rem 1.5rem;">
                <h1 style="font-size: 1.75rem; font-weight: 700; color: #111827;">⚙️ API Keys</h1>
                <p style="color: #6b7280; margin-top: 0.5rem;">Configure your API keys to enable all features</p>
            </div>
        ''')
        
        with gr.Row():
            gr.Column(scale=1, min_width=50)
            with gr.Column(scale=2, min_width=400):
                settings_gemini = gr.Textbox(
                    label="Google Gemini API Key (required)",
                    placeholder="Get from aistudio.google.com/apikey",
                    type="password",
                    interactive=True
                )
                settings_openai = gr.Textbox(
                    label="OpenAI API Key (optional)",
                    placeholder="Get from platform.openai.com/api-keys",
                    type="password",
                    interactive=True
                )
                settings_elevenlabs = gr.Textbox(
                    label="ElevenLabs API Key (optional, for audio)",
                    placeholder="Get from elevenlabs.io/app/developers/api-keys",
                    type="password",
                    interactive=True
                )
                
                save_btn = gr.Button("💾 Save Settings", variant="primary")
                settings_status = gr.HTML("")
            gr.Column(scale=1, min_width=50)
        
        # Settings events
        def load_settings():
            session = load_session_state()
            return (
                session.get("api_key", ""),
                session.get("openai_api_key", ""),
                session.get("elevenlabs_api_key", "")
            )
        
        def save_settings(gemini_key, openai_key, elevenlabs_key):
            if save_session_state({
                "api_key": gemini_key,
                "openai_api_key": openai_key,
                "elevenlabs_api_key": elevenlabs_key,
            }):
                # Update config
                config = get_config()
                config.gemini_api_key = gemini_key
                config.openai_api_key = openai_key
                config.elevenlabs_api_key = elevenlabs_key
                return '<p style="color: #059669; text-align: center;">✅ Settings saved!</p>'
            return '<p style="color: #dc2626; text-align: center;">❌ Failed to save</p>'
        
        settings_page.load(fn=load_settings, outputs=[settings_gemini, settings_openai, settings_elevenlabs])
        settings_page.load(fn=get_current_model, outputs=[settings_model])
        
        save_btn.click(
            fn=save_settings,
            inputs=[settings_gemini, settings_openai, settings_elevenlabs],
            outputs=[settings_status]
        )
        
        settings_model.change(
            fn=lambda m: save_session_state({"model": m}),
            inputs=[settings_model]
        )
    
    return app, CUSTOM_CSS

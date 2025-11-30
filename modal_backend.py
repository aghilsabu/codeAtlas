"""
CodeAtlas Modal Backend - HTTP API Endpoints

This file provides Modal web endpoints that can be called from the HF Space frontend.
Deploy with: modal deploy modal_backend.py

The HF Space Gradio app calls these endpoints for heavy compute operations.
This qualifies for the Modal Innovation Award ($2,500).
"""

import modal
import json

# Create Modal app
app = modal.App(name="codeatlas-backend")

# Container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("graphviz", "fonts-liberation", "git")
    .pip_install(
        "google-genai>=1.0.0",
        "llama-index-core>=0.11.0",
        "llama-index-llms-gemini>=0.4.0",
        "llama-index-llms-openai>=0.3.0",
        "openai>=1.0.0",
        "elevenlabs>=1.0.0",
        "graphviz>=0.20.0",
        "requests>=2.31.0",
    )
)

# Mount source code (excluding data and cache)
local_files = modal.Mount.from_local_dir(
    ".",
    remote_path="/app",
    condition=lambda path: not any(x in path for x in [
        "__pycache__", ".git", ".venv", "node_modules",
        "data/", ".session_state.json", ".env",
    ])
)


# ============================================================================
# Diagram Generation Endpoint
# ============================================================================

@app.function(
    image=image,
    mounts=[local_files],
    cpu=2.0,
    memory=4096,
    timeout=300,
    secrets=[modal.Secret.from_name("codeatlas-secrets", required_keys=[])],
)
@modal.web_endpoint(method="POST", docs=True)
def generate_diagram(request: dict) -> dict:
    """
    Generate architecture diagram from GitHub repository.
    
    POST /generate_diagram
    {
        "github_url": "https://github.com/owner/repo",
        "api_key": "your-gemini-api-key",
        "model_name": "gemini-2.5-flash",
        "focus_area": "optional focus area"
    }
    
    Returns:
    {
        "success": true,
        "dot_source": "digraph {...}",
        "summary": "Architecture summary...",
        "filename": "raw_owner_repo_timestamp.dot",
        "stats": {"nodes": 10, "edges": 15}
    }
    """
    import sys
    import os
    
    sys.path.insert(0, "/app")
    os.chdir("/app")
    os.makedirs("/app/data/diagrams", exist_ok=True)
    
    try:
        github_url = request.get("github_url", "")
        api_key = request.get("api_key", "")
        model_name = request.get("model_name", "gemini-2.5-flash")
        focus_area = request.get("focus_area", "")
        
        if not github_url:
            return {"success": False, "error": "github_url is required"}
        if not api_key:
            return {"success": False, "error": "api_key is required"}
        
        from src.core.diagram import DiagramGenerator
        from src.core.github_client import GitHubClient
        
        # Fetch code from GitHub
        client = GitHubClient()
        code_context = client.fetch_repo_content(github_url)
        
        if not code_context:
            return {"success": False, "error": "Failed to fetch repository content"}
        
        # Generate diagram
        generator = DiagramGenerator(api_key=api_key, model_name=model_name)
        dot_source, summary = generator.generate(code_context, focus_area=focus_area)
        
        if not dot_source:
            return {"success": False, "error": "Failed to generate diagram"}
        
        # Save and get filename
        filename = generator.save_diagram(dot_source, github_url)
        
        # Count nodes and edges
        node_count, edge_count = generator._count_nodes_edges(dot_source)
        
        return {
            "success": True,
            "dot_source": dot_source,
            "summary": summary,
            "filename": filename,
            "stats": {
                "nodes": node_count,
                "edges": edge_count,
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# Voice Narration Endpoint
# ============================================================================

@app.function(
    image=image,
    mounts=[local_files],
    cpu=1.0,
    memory=2048,
    timeout=120,
    secrets=[modal.Secret.from_name("codeatlas-secrets", required_keys=[])],
)
@modal.web_endpoint(method="POST", docs=True)
def generate_voice(request: dict) -> dict:
    """
    Generate voice narration for diagram summary.
    
    POST /generate_voice
    {
        "text": "Text to convert to speech",
        "api_key": "your-elevenlabs-api-key",
        "voice_id": "optional-voice-id"
    }
    
    Returns:
    {
        "success": true,
        "audio_base64": "base64-encoded-audio",
        "duration_seconds": 30
    }
    """
    import sys
    import os
    import base64
    
    sys.path.insert(0, "/app")
    os.chdir("/app")
    
    try:
        text = request.get("text", "")
        api_key = request.get("api_key", "")
        voice_id = request.get("voice_id", "JBFqnCBsd6RMkjVDRZzb")
        
        if not text:
            return {"success": False, "error": "text is required"}
        if not api_key:
            return {"success": False, "error": "api_key is required"}
        
        from elevenlabs import ElevenLabs
        
        client = ElevenLabs(api_key=api_key)
        
        audio_generator = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        
        # Collect audio bytes
        audio_bytes = b"".join(audio_generator)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # Estimate duration (rough: ~16KB per second for mp3)
        duration_estimate = len(audio_bytes) / (16 * 1024)
        
        return {
            "success": True,
            "audio_base64": audio_base64,
            "duration_seconds": round(duration_estimate, 1),
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# Codebase Analysis Endpoint (MCP Tool)
# ============================================================================

@app.function(
    image=image,
    mounts=[local_files],
    cpu=2.0,
    memory=4096,
    timeout=300,
    secrets=[modal.Secret.from_name("codeatlas-secrets", required_keys=[])],
)
@modal.web_endpoint(method="POST", docs=True)
def analyze_codebase(request: dict) -> dict:
    """
    Analyze codebase architecture using AI.
    
    POST /analyze_codebase
    {
        "github_url": "https://github.com/owner/repo",
        "api_key": "your-api-key",
        "model_name": "gemini-2.5-flash",
        "question": "optional specific question"
    }
    
    Returns:
    {
        "success": true,
        "analysis": "Detailed architecture analysis..."
    }
    """
    import sys
    import os
    
    sys.path.insert(0, "/app")
    os.chdir("/app")
    
    try:
        github_url = request.get("github_url", "")
        api_key = request.get("api_key", "")
        model_name = request.get("model_name", "gemini-2.5-flash")
        question = request.get("question", "")
        
        if not github_url:
            return {"success": False, "error": "github_url is required"}
        if not api_key:
            return {"success": False, "error": "api_key is required"}
        
        from src.mcp.tools import analyze_codebase as mcp_analyze
        
        result = mcp_analyze(
            api_key=api_key,
            github_url=github_url,
            model_name=model_name,
        )
        
        return {
            "success": True,
            "analysis": result,
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.function(image=image, cpu=0.25, memory=256)
@modal.web_endpoint(method="GET", docs=True)
def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "codeatlas-backend",
        "version": "1.0.0",
    }


# ============================================================================
# Local Entrypoint
# ============================================================================

@app.local_entrypoint()
def main():
    """Print deployment instructions."""
    print("=" * 60)
    print("🚀 CodeAtlas Modal Backend")
    print("=" * 60)
    print()
    print("Commands:")
    print("  modal serve modal_backend.py   # Test locally")
    print("  modal deploy modal_backend.py  # Deploy to production")
    print()
    print("After deployment, you'll get URLs like:")
    print("  https://YOUR_USERNAME--codeatlas-backend-generate-diagram.modal.run")
    print("  https://YOUR_USERNAME--codeatlas-backend-generate-voice.modal.run")
    print("  https://YOUR_USERNAME--codeatlas-backend-analyze-codebase.modal.run")
    print()
    print("Set MODAL_BACKEND_URL in your HF Space secrets!")
    print("=" * 60)

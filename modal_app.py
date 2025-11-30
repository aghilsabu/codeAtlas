"""CodeAtlas - Modal Cloud Deployment"""

import modal

app = modal.App(name="codeatlas")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("graphviz", "fonts-liberation")
    .pip_install(
        "gradio>=5.0.0",
        "fastapi[standard]",
        "uvicorn>=0.20.0",
        "google-genai>=1.0.0",
        "llama-index-core>=0.11.0",
        "llama-index-llms-gemini>=0.4.0",
        "llama-index-llms-openai>=0.3.0",
        "elevenlabs>=1.0.0",
        "fastmcp>=0.1.0",
        "requests>=2.31.0",
        "graphviz>=0.20.0",
    )
)

local_files = modal.Mount.from_local_dir(
    ".",
    remote_path="/app",
    condition=lambda path: not any(x in path for x in [
        "__pycache__", ".git", ".venv", "node_modules",
        "data/", ".session_state.json", ".env",
    ])
)


@app.function(
    image=image,
    mounts=[local_files],
    cpu=2.0,
    memory=4096,
    min_containers=0,
    max_containers=10,
    scaledown_window=300,
    timeout=600,
    secrets=[modal.Secret.from_name("codeatlas-secrets", required_keys=[])],
)
@modal.concurrent(max_inputs=50)
@modal.asgi_app()
def serve():
    """Serve the CodeAtlas Gradio application."""
    import os
    import sys
    
    sys.path.insert(0, "/app")
    os.chdir("/app")
    
    os.makedirs("/app/data/diagrams", exist_ok=True)
    os.makedirs("/app/data/audios", exist_ok=True)
    os.makedirs("/app/data/logs", exist_ok=True)
    
    from fastapi import FastAPI
    from gradio.routes import mount_gradio_app
    from src.ui import create_app, CUSTOM_CSS
    import gradio as gr
    
    gradio_app, _ = create_app()
    
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.orange,
        secondary_hue=gr.themes.colors.orange,
        neutral_hue=gr.themes.colors.gray,
    )
    
    fastapi_app = FastAPI(title="CodeAtlas", version="1.0.0")
    
    @fastapi_app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return mount_gradio_app(app=fastapi_app, blocks=gradio_app, path="/")


@app.function(image=image, mounts=[local_files], cpu=1.0, memory=2048, timeout=300)
def analyze_codebase_remote(github_url: str, api_key: str, model_name: str = "gemini-2.5-flash") -> str:
    """Remote function to analyze a codebase."""
    import sys
    import os
    
    sys.path.insert(0, "/app")
    os.chdir("/app")
    
    from src.mcp.tools import analyze_codebase
    return analyze_codebase(api_key=api_key, github_url=github_url, model_name=model_name)


@app.local_entrypoint()
def main():
    print("🚀 Use 'modal serve modal_app.py' to test locally")
    print("   Use 'modal deploy modal_app.py' to deploy")

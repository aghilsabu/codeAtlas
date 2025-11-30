"""MCP Tools - CodeAtlas functions exposed via MCP protocol"""

import logging
from typing import Optional

from .server import mcp
from ..core.repository import RepositoryLoader
from ..core.analyzer import CodeAnalyzer
from ..core.diagram import DiagramGenerator

logger = logging.getLogger("codeatlas.mcp.tools")


@mcp.tool()
def analyze_codebase(api_key: str, github_url: Optional[str] = None, file_path: Optional[str] = None, model_name: str = "gemini-2.5-flash") -> str:
    """Analyze a codebase and generate a Graphviz DOT architecture diagram."""
    logger.info(f"analyze_codebase: url={github_url}, file={file_path}, model={model_name}")
    
    if not github_url and not file_path:
        return "Error: Please provide either a GitHub URL or a file path."
    if not api_key:
        return "Error: API key is required."
    
    loader = RepositoryLoader()
    result = loader.load_from_file(file_path) if file_path else loader.load_from_github(github_url)
    
    if result.error:
        return f"Error: {result.error}"
    
    logger.info(f"Loaded: {result.stats.files_processed} files, {result.stats.total_characters:,} chars")
    
    analyzer = CodeAnalyzer(api_key=api_key, model_name=model_name)
    analysis = analyzer.generate_diagram(result.context)
    
    if not analysis.success:
        return f"Error: {analysis.error}"
    
    DiagramGenerator()._save_diagram(analysis.content, "raw", result.repo_name)
    return analysis.content


@mcp.tool()
def get_architecture_summary(api_key: str, github_url: Optional[str] = None, file_path: Optional[str] = None, model_name: str = "gemini-2.5-flash") -> str:
    """Generate a text summary of a codebase's architecture."""
    logger.info(f"get_architecture_summary: url={github_url}, file={file_path}")
    
    if not github_url and not file_path:
        return "Error: Please provide either a GitHub URL or a file path."
    if not api_key:
        return "Error: API key is required."
    
    loader = RepositoryLoader()
    result = loader.load_from_file(file_path) if file_path else loader.load_from_github(github_url)
    
    if result.error:
        return f"Error: {result.error}"
    
    analyzer = CodeAnalyzer(api_key=api_key, model_name=model_name)
    analysis = analyzer.generate_summary(result.context)
    
    return analysis.content if analysis.success else f"Error: {analysis.error}"


@mcp.tool()
def chat_with_codebase(api_key: str, question: str, github_url: Optional[str] = None, file_path: Optional[str] = None, model_name: str = "gemini-2.5-flash") -> str:
    """Ask questions about a codebase and get AI-powered answers."""
    logger.info(f"chat_with_codebase: question={question[:50]}...")
    
    if not github_url and not file_path:
        return "Error: Please provide either a GitHub URL or a file path."
    if not api_key:
        return "Error: API key is required."
    if not question or not question.strip():
        return "Error: Please provide a question."
    
    loader = RepositoryLoader()
    result = loader.load_from_file(file_path) if file_path else loader.load_from_github(github_url)
    
    if result.error:
        return f"Error: {result.error}"
    
    analyzer = CodeAnalyzer(api_key=api_key, model_name=model_name)
    response = analyzer.chat(question, result.context)
    
    return response.content if response.success else f"Error: {response.error}"


@mcp.tool()
def list_recent_analyses() -> str:
    """List recently analyzed codebases."""
    history = DiagramGenerator().get_history(limit=10)
    
    if not history:
        return "No recent analyses found."
    
    lines = ["Recent Analyses:"]
    for i, d in enumerate(history, 1):
        lines.append(f"{i}. {d.repo_name} — {d.formatted_timestamp}")
    return "\n".join(lines)

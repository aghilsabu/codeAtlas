"""
UI Components

Reusable UI components for the Gradio interface.
"""

from typing import Optional, Dict


def make_nav_bar(active_page: str) -> str:
    """Generate the top navigation bar HTML.
    
    Args:
        active_page: One of 'generate', 'explore', or 'settings'
        
    Returns:
        HTML string for the navigation bar
    """
    links = [
        ("generate", "/", "🚀 Generate"),
        ("explore", "/explore", "🔍 Explore"),
        ("settings", "/settings", "⚙️ Settings"),
    ]
    
    nav_links = ""
    for page_id, href, label in links:
        active_class = "active" if page_id == active_page else ""
        nav_links += f'<a href="{href}" class="{active_class}">{label}</a>'
    
    return f'''
        <div class="top-nav-bar">
            <div class="nav-links">
                {nav_links}
            </div>
        </div>
    '''


def make_loading_html(emoji: str, message: str, submessage: str = "") -> str:
    """Generate a loading animation HTML.
    
    Args:
        emoji: Emoji to display with animation
        message: Main loading message
        submessage: Optional sub-message
        
    Returns:
        HTML string for loading state
    """
    sub_html = f'<p class="loading-submessage">{submessage}</p>' if submessage else ""
    return f'''
        <div class="loading-container">
            <div class="loading-emoji">{emoji}</div>
            <p class="loading-message">{message}</p>
            {sub_html}
        </div>
    '''


def make_stats_bar(
    repo_name: str = "",
    files_processed: int = 0,
    total_characters: int = 0,
    model_name: str = "",
    node_count: int = 0,
    edge_count: int = 0,
    extra_info: str = ""
) -> str:
    """Generate the stats bar HTML.
    
    Args:
        repo_name: Repository name
        files_processed: Number of files processed
        total_characters: Total characters analyzed
        model_name: AI model used
        node_count: Number of nodes in diagram
        edge_count: Number of edges in diagram
        extra_info: Additional information to display
        
    Returns:
        HTML string for stats bar
    """
    parts = []
    
    if repo_name:
        parts.append(f'<span>📦 <strong>{repo_name}</strong></span>')
    if files_processed:
        parts.append(f'<span>📁 <strong>{files_processed}</strong> files</span>')
    if total_characters:
        parts.append(f'<span>📊 <strong>{total_characters:,}</strong> chars</span>')
    if node_count:
        parts.append(f'<span>🔵 <strong>{node_count}</strong> nodes</span>')
    if edge_count:
        parts.append(f'<span>🔗 <strong>{edge_count}</strong> edges</span>')
    if model_name:
        parts.append(f'<span>🤖 <strong>{model_name}</strong></span>')
    if extra_info:
        parts.append(f'<span>{extra_info}</span>')
    
    return f'<div class="stats-bar">{"".join(parts)}</div>'


def make_error_html(message: str, emoji: str = "❌", link_href: str = "/", link_text: str = "← Try Again") -> str:
    """Generate error display HTML.
    
    Args:
        message: Error message to display
        emoji: Emoji to show
        link_href: Link destination
        link_text: Link text
        
    Returns:
        HTML string for error display
    """
    return f'''
        <div class="error-container">
            <div class="error-emoji">{emoji}</div>
            <p class="error-message">{message}</p>
            <a href="{link_href}" class="error-link">{link_text}</a>
        </div>
    '''


def make_empty_state_html(message: str = "No diagram yet.", link_href: str = "/", link_text: str = "Generate one →") -> str:
    """Generate empty state HTML.
    
    Args:
        message: Message to display
        link_href: Link destination
        link_text: Link text
        
    Returns:
        HTML string for empty state
    """
    return f'''
        <div style="display: flex; align-items: center; justify-content: center; 
                    min-height: 500px; color: #9ca3af; font-size: 1.1rem;">
            {message} <a href="{link_href}" style="margin-left: 0.5rem; color: #f97316;">{link_text}</a>
        </div>
    '''


def make_hero_section(
    emoji: str = "🏗️",
    title: str = "CodeAtlas",
    subtitle: str = "Visualize any codebase architecture with AI"
) -> str:
    """Generate hero section HTML.
    
    Args:
        emoji: Main emoji
        title: Title text
        subtitle: Subtitle text
        
    Returns:
        HTML string for hero section
    """
    return f'''
        <div class="hero-section">
            <div class="hero-emoji">{emoji}</div>
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">{subtitle}</p>
        </div>
    '''


def make_footer() -> str:
    """Generate footer HTML.
    
    Returns:
        HTML string for footer
    """
    return '''
        <div class="footer">
            Built for MCP's 1st Birthday Hackathon 🎂 · 
            <a href="https://github.com/aghilsabu/codeAtlas" target="_blank">GitHub</a> · 
            <a href="https://x.com/aghilsabu" target="_blank">@aghilsabu</a>
        </div>
    '''

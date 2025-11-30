"""
Diagram Generator Module

Handles Graphviz rendering, sanitization, and diagram management.
"""

import os
import re
import json
import logging
import tempfile
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple, Dict

from ..config import get_config, DIAGRAMS_DIR

logger = logging.getLogger("codeatlas.diagram")

# Try to import graphviz
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False
    logger.warning("Graphviz not available")


@dataclass
class LayoutOptions:
    """Options for diagram layout."""
    direction: str = "TB"  # TB, LR, BT, RL
    splines: str = "polyline"  # polyline, ortho, spline, line
    nodesep: float = 0.5
    ranksep: float = 0.75
    zoom: float = 1.0
    
    DIRECTION_MAP = {
        "Top → Down": "TB",
        "Left → Right": "LR", 
        "Bottom → Up": "BT",
        "Right → Left": "RL",
    }
    
    @classmethod
    def from_ui(cls, direction: str, splines: str, nodesep: float, ranksep: float, zoom: float = 1.0):
        """Create from UI values."""
        return cls(
            direction=cls.DIRECTION_MAP.get(direction, "TB"),
            splines=splines,
            nodesep=nodesep,
            ranksep=ranksep,
            zoom=zoom,
        )


@dataclass
class DiagramInfo:
    """Information about a saved diagram."""
    filename: str
    repo_name: str
    timestamp: str
    formatted_timestamp: str
    file_path: Path
    # Metadata fields (loaded from JSON if available)
    model_name: str = ""
    files_processed: int = 0
    total_characters: int = 0
    node_count: int = 0
    edge_count: int = 0


class DiagramGenerator:
    """Generates and manages architecture diagrams."""
    
    def __init__(self):
        self.config = get_config()
        self.diagrams_dir = self.config.diagrams_dir
    
    def render(
        self, 
        dot_source: str, 
        layout: Optional[LayoutOptions] = None,
        repo_name: str = "",
        save_to_history: bool = False,
        metadata: Optional[Dict] = None
    ) -> str:
        """Render DOT source to HTML with embedded SVG.
        
        Args:
            dot_source: Graphviz DOT source code
            layout: Layout options
            repo_name: Repository name for saving
            save_to_history: Whether to save to history
            metadata: Optional metadata dict (model, files, chars) to save with diagram
            
        Returns:
            HTML string with SVG diagram
        """
        if dot_source.startswith("Error:"):
            return self._error_html(dot_source)
        
        if not GRAPHVIZ_AVAILABLE:
            return self._fallback_html(dot_source)
        
        if layout is None:
            layout = LayoutOptions()
        
        try:
            # Clean and prepare DOT source
            dot_source = self._prepare_dot(dot_source)
            
            # Save raw diagram if requested
            if save_to_history:
                self._save_diagram(dot_source, "raw", repo_name, metadata)
            
            # Sanitize DOT code
            dot_source = self._sanitize_dot(dot_source)
            
            # Apply layout settings
            dot_source = self._apply_layout(dot_source, layout)
            
            # Render to SVG
            svg_content = self._render_svg(dot_source)
            
            # Wrap in HTML
            return self._wrap_svg(svg_content, layout.zoom)
            
        except Exception as e:
            logger.exception("Rendering failed")
            return self._fallback_html(dot_source, error=str(e))
    
    def _prepare_dot(self, dot_source: str) -> str:
        """Prepare DOT source by removing markdown and ensuring structure."""
        dot_source = dot_source.strip()
        
        # Remove markdown code fences
        if dot_source.startswith("```"):
            lines = dot_source.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            dot_source = "\n".join(lines)
        
        # Ensure digraph wrapper
        if "digraph" not in dot_source and "graph" not in dot_source:
            dot_source = f"digraph G {{\n{dot_source}\n}}"
        
        return dot_source
    
    def _sanitize_dot(self, dot_source: str) -> str:
        """Sanitize DOT source to fix common LLM output issues."""
        # Check for error responses
        if "Error" in dot_source and any(x in dot_source for x in ["429", "RESOURCE_EXHAUSTED", "quota"]):
            raise ValueError("Rate limited - received error instead of diagram")
        
        lines = dot_source.split("\n")
        sanitized = []
        brace_count = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("#"):
                sanitized.append(line)
                continue
            
            brace_count += line.count("{") - line.count("}")
            
            # Remove HTML-like tags that Graphviz doesn't support
            line = re.sub(r"<[^>]+>", "", line)
            
            # Fix incomplete edges at end of file
            is_last_few = i >= len(lines) - 3
            if is_last_few:
                if stripped.endswith("->") or re.match(r".*->\s*$", stripped):
                    continue
                if "->" in stripped and not stripped.endswith(";") and "[" not in stripped:
                    parts = stripped.split("->")
                    if len(parts) == 2 and not parts[1].strip():
                        continue
                # Fix unclosed quotes
                if stripped.count('"') % 2 == 1:
                    line = line.rstrip() + '"];'
            
            sanitized.append(line)
        
        result = "\n".join(sanitized)
        
        # Balance braces
        if brace_count > 0:
            result += "\n" + "}" * brace_count
        
        return result
    
    def _apply_layout(self, dot_source: str, layout: LayoutOptions) -> str:
        """Apply layout settings to DOT source."""
        # Remove existing layout attributes
        dot_source = re.sub(r"rankdir\s*=\s*\w+\s*;?", "", dot_source)
        dot_source = re.sub(r"splines\s*=\s*\w+\s*;?", "", dot_source)
        dot_source = re.sub(r"nodesep\s*=\s*[\d.]+\s*;?", "", dot_source)
        dot_source = re.sub(r"ranksep\s*=\s*[\d.]+\s*;?", "", dot_source)
        
        # Add new layout settings
        layout_settings = f"""
    rankdir={layout.direction};
    splines={layout.splines};
    nodesep={layout.nodesep};
    ranksep={layout.ranksep};
    pad=0.5;
    node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12, width=2.0, height=0.6, margin="0.2,0.1"];
    edge [fontname="Helvetica", fontsize=10, arrowsize=0.8];
"""
        dot_source = dot_source.replace("{", "{" + layout_settings, 1)
        
        # For ortho splines, convert label to xlabel
        if layout.splines == "ortho":
            lines = dot_source.split("\n")
            converted = []
            for line in lines:
                if "->" in line and "label=" in line and "xlabel=" not in line:
                    line = line.replace("label=", "xlabel=")
                converted.append(line)
            dot_source = "\n".join(converted)
        
        return dot_source
    
    def _render_svg(self, dot_source: str) -> str:
        """Render DOT to SVG using Graphviz."""
        graph = graphviz.Source(dot_source)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "diagram")
            graph.render(output_path, format="svg", cleanup=True)
            
            with open(output_path + ".svg", "r", encoding="utf-8") as f:
                return f.read()
    
    def _wrap_svg(self, svg_content: str, zoom: float = 1.0) -> str:
        """Wrap SVG in responsive HTML container."""
        # Make SVG responsive
        svg_content = re.sub(r'<svg([^>]*?)width="[^"]*"', r'<svg\1width="100%"', svg_content)
        svg_content = re.sub(r'height="[^"]*"', 'height="auto"', svg_content, count=1)
        
        # Apply zoom
        transform = f'style="transform: scale({zoom}); transform-origin: top left;"' if zoom != 1.0 else ""
        
        return f'''<div class="diagram-box">
            <div class="diagram-inner" {transform}>
                {svg_content}
            </div>
        </div>'''
    
    def _save_diagram(
        self, 
        dot_content: str, 
        prefix: str, 
        repo_name: str = "",
        metadata: Optional[Dict] = None
    ) -> Path:
        """Save DOT content to history with optional metadata."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize repo name
        safe_repo = repo_name.replace("/", "_").replace(" ", "_") if repo_name else ""
        safe_repo = "".join(c for c in safe_repo if c.isalnum() or c in "_-")[:50]
        
        filename = f"{prefix}_{safe_repo}_{timestamp}.dot" if safe_repo else f"{prefix}_{timestamp}.dot"
        filepath = self.diagrams_dir / filename
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(dot_content)
            logger.info(f"Saved diagram: {filepath}")
            
            # Save metadata as JSON if provided
            if metadata:
                # Add node/edge counts from DOT content
                node_count, edge_count = self._count_nodes_edges(dot_content)
                metadata["node_count"] = node_count
                metadata["edge_count"] = edge_count
                metadata["repo_name"] = repo_name
                metadata["timestamp"] = timestamp
                
                meta_filepath = filepath.with_suffix(".json")
                with open(meta_filepath, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
                logger.info(f"Saved metadata: {meta_filepath}")
            
            return filepath
        except Exception as e:
            logger.warning(f"Failed to save diagram: {e}")
            return None
    
    def _count_nodes_edges(self, dot_content: str) -> Tuple[int, int]:
        """Count nodes and edges in DOT source."""
        # Count edges (lines with ->), handling quoted node names
        edge_pattern = r'(?:"[^"]+"|[\w]+)\s*->\s*(?:"[^"]+"|[\w]+)'
        edges = len(re.findall(edge_pattern, dot_content))
        
        # Count unique node names (excluding keywords)
        keywords = {'digraph', 'graph', 'subgraph', 'node', 'edge', 'rankdir', 'splines', 'nodesep', 'ranksep', 'label', 'style', 'shape', 'color', 'fillcolor', 'fontname', 'fontsize', 'margin', 'pad', 'width', 'height', 'arrowsize', 'cluster', 'tb', 'lr', 'bt', 'rl'}
        
        nodes = set()
        
        # Match quoted node names in definitions: "Node Name" [...]
        quoted_defs = re.findall(r'^\s*"([^"]+)"\s*\[', dot_content, re.MULTILINE)
        for node in quoted_defs:
            nodes.add(node)
        
        # Match unquoted node definitions: NodeName [...]  
        unquoted_defs = re.findall(r'^\s*(\w+)\s*\[', dot_content, re.MULTILINE)
        for node in unquoted_defs:
            if node.lower() not in keywords and not node.isdigit():
                nodes.add(node)
        
        # Match nodes in edges (both quoted and unquoted)
        edge_nodes = re.findall(r'(?:"([^"]+)"|(\w+))\s*->\s*(?:"([^"]+)"|(\w+))', dot_content)
        for match in edge_nodes:
            # Each match is (quoted_src, unquoted_src, quoted_dst, unquoted_dst)
            src = match[0] or match[1]
            dst = match[2] or match[3]
            if src and src.lower() not in keywords and not src.isdigit():
                nodes.add(src)
            if dst and dst.lower() not in keywords and not dst.isdigit():
                nodes.add(dst)
        
        return len(nodes), edges
    
    def get_history(self, limit: int = 50) -> List[DiagramInfo]:
        """Get list of saved diagrams.
        
        Args:
            limit: Maximum number of diagrams to return
            
        Returns:
            List of DiagramInfo objects
        """
        if not self.diagrams_dir.exists():
            return []
        
        files = [f for f in self.diagrams_dir.iterdir() if f.name.startswith("raw_") and f.suffix == ".dot"]
        
        # Sort by timestamp (newest first)
        def extract_timestamp(path: Path) -> str:
            name = path.stem.replace("raw_", "")
            parts = name.split("_")
            if len(parts) >= 2:
                return parts[-2] + parts[-1]
            return "0"
        
        files.sort(key=extract_timestamp, reverse=True)
        
        # Build DiagramInfo list (no deduplication - show all history)
        diagrams = []
        for f in files[:limit]:
            name = f.stem.replace("raw_", "")
            parts = name.split("_")
            
            if len(parts) >= 2 and len(parts[-2]) == 8 and len(parts[-1]) == 6:
                repo_parts = parts[:-2]
                repo_name = repo_parts[-1] if repo_parts else "local"
                date_part = parts[-2]
                time_part = parts[-1]
                
                try:
                    formatted_ts = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}"
                except:
                    formatted_ts = f"{date_part}_{time_part}"
                
                # Load metadata if available
                metadata = self._load_metadata(f)
                
                diagrams.append(DiagramInfo(
                    filename=f.name,
                    repo_name=metadata.get("repo_name", repo_name) if metadata else repo_name,
                    timestamp=f"{date_part}_{time_part}",
                    formatted_timestamp=formatted_ts,
                    file_path=f,
                    model_name=metadata.get("model_name", "") if metadata else "",
                    files_processed=metadata.get("files_processed", 0) if metadata else 0,
                    total_characters=metadata.get("total_characters", 0) if metadata else 0,
                    node_count=metadata.get("node_count", 0) if metadata else 0,
                    edge_count=metadata.get("edge_count", 0) if metadata else 0,
                ))
        
        return diagrams
    
    def _load_metadata(self, dot_filepath: Path) -> Optional[Dict]:
        """Load metadata JSON for a diagram file."""
        meta_filepath = dot_filepath.with_suffix(".json")
        if not meta_filepath.exists():
            return None
        try:
            with open(meta_filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            return None
    
    def get_history_choices(self) -> List[Tuple[str, str]]:
        """Get history as choices for Gradio dropdown."""
        diagrams = self.get_history()
        return [(f"{d.repo_name} — {d.formatted_timestamp}", d.filename) for d in diagrams]
    
    def load_from_history(self, filename: str) -> Optional[str]:
        """Load a diagram from history.
        
        Args:
            filename: Name of the diagram file
            
        Returns:
            DOT source or None if not found
        """
        filepath = self.diagrams_dir / filename
        if not filepath.exists():
            return None
        
        try:
            return filepath.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to load diagram: {e}")
            return None
    
    def load_from_history_with_metadata(self, filename: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Load a diagram and its metadata from history.
        
        Args:
            filename: Name of the diagram file
            
        Returns:
            Tuple of (DOT source, metadata dict) or (None, None) if not found
        """
        filepath = self.diagrams_dir / filename
        if not filepath.exists():
            return None, None
        
        try:
            dot_source = filepath.read_text(encoding="utf-8")
            metadata = self._load_metadata(filepath)
            
            # If no metadata file, compute node/edge counts from DOT
            if metadata is None:
                node_count, edge_count = self._count_nodes_edges(dot_source)
                metadata = {
                    "node_count": node_count,
                    "edge_count": edge_count,
                }
            
            return dot_source, metadata
        except Exception as e:
            logger.warning(f"Failed to load diagram: {e}")
            return None, None
    
    def _error_html(self, message: str) -> str:
        """Generate error display HTML."""
        return f'''<div style="color:#dc2626; padding:20px; text-align:center;">
            <strong>⚠️ {message}</strong>
        </div>'''
    
    def _fallback_html(self, content: str, error: str = None) -> str:
        """Generate fallback HTML when Graphviz is unavailable."""
        error_msg = f"<p style='color: #dc2626;'>Rendering error: {error}</p>" if error else ""
        return f'''<div style="background: #f9fafb; padding: 1.5rem; border-radius: 12px;">
            <strong>📊 Architecture (Text View)</strong>
            {error_msg}
            <pre style="background: #fff; padding: 1rem; border-radius: 8px; overflow-x: auto;">{content[:2000]}</pre>
        </div>'''

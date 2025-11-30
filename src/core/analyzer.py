"""
Code Analyzer Module

Uses LlamaIndex + AI models for intelligent code analysis.
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict

from ..config import get_config

logger = logging.getLogger("codeatlas.analyzer")

# LlamaIndex imports
try:
    from llama_index.core.llms import ChatMessage
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    logger.warning("LlamaIndex core not available")

try:
    from llama_index.llms.gemini import Gemini
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("LlamaIndex Gemini not available")

try:
    from llama_index.llms.openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("LlamaIndex OpenAI not available")

# Fallback to google-genai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# System prompts for different analysis tasks
ARCHITECT_PROMPT = """You are CodeAtlas, an expert software architect. Generate a Graphviz DOT diagram showing code architecture with RELATIONSHIPS.

CRITICAL CONSTRAINTS:
- Maximum 15-20 nodes (focus on KEY architectural components)
- Maximum 25-30 edges (most important relationships)
- Group related components into subgraphs
- Omit trivial files (tests, configs, utilities)

WHAT TO SHOW:
- Main entry points and core modules
- Key classes/services with clear responsibilities  
- Important data flow and dependencies
- Layer boundaries (API, Business Logic, Data)

RULES:
1. Start with: digraph CodeArchitecture {
2. Every diagram MUST have arrows showing component connections
3. Use actual class/file names from the code
4. Group related items in clusters with descriptive labels
5. Use colors to distinguish layers/types

EXAMPLE:
```dot
digraph CodeArchitecture {
    rankdir=TB;
    node [shape=box, style="rounded,filled", fontname="Helvetica"];
    
    subgraph cluster_api {
        label="API Layer";
        style="rounded,filled";
        fillcolor="#e8f5e9";
        Routes; Handlers;
    }
    
    subgraph cluster_services {
        label="Business Logic";
        style="rounded,filled";
        fillcolor="#e3f2fd";
        UserService; DataProcessor;
    }
    
    Routes -> Handlers;
    Handlers -> UserService;
    Handlers -> DataProcessor;
}
```

Generate ONLY valid DOT code. Focus on architectural clarity."""

SUMMARY_PROMPT = """You are CodeAtlas. Analyze the codebase and provide a concise summary.

Include:
1. **Project Overview**: What does this codebase do?
2. **Technology Stack**: Languages, frameworks, key dependencies
3. **Architecture Pattern**: MVC, microservices, monolith, etc.
4. **Key Components**: Main modules and their responsibilities
5. **Entry Points**: Where does execution start?

Keep it concise (200-300 words). Be specific about actual file/class names."""

CHAT_PROMPT = """You are CodeAtlas, an expert software architect assistant.

You're analyzing a codebase and helping answer questions about its architecture.
Use the provided code context to give accurate, specific answers.
Reference actual file names, class names, and code patterns when relevant.

Be helpful, concise, and technical. If you're unsure about something, say so."""


@dataclass
class AnalysisResult:
    """Result of code analysis."""
    content: str
    success: bool = True
    error: Optional[str] = None


class CodeAnalyzer:
    """Analyzes code using LlamaIndex and AI models."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.config = get_config()
        self.api_key = api_key or self.config.gemini_api_key
        self.model_name = model_name or self.config.models.get_model_id(self.config.current_model)
        self._llm = None
    
    @property
    def llm(self):
        """Get or create the LLM instance."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm
    
    def _create_llm(self):
        """Create appropriate LLM based on model name."""
        is_openai = self.config.models.is_openai_model(self.model_name)
        
        if is_openai:
            if not OPENAI_AVAILABLE:
                raise ValueError("OpenAI support not available. Install llama-index-llms-openai")
            api_key = self.config.openai_api_key or self.api_key
            return OpenAI(api_key=api_key, model=self.model_name, temperature=0.7, max_tokens=4096)
        else:
            if GEMINI_AVAILABLE:
                return Gemini(
                    api_key=self.api_key,
                    model=f"models/{self.model_name}",
                    temperature=0.7,
                    max_tokens=4096,
                )
            elif GENAI_AVAILABLE:
                return None  # Will use fallback
            else:
                raise ValueError("No AI backend available")
    
    def _generate_with_llamaindex(self, system_prompt: str, user_prompt: str) -> str:
        """Generate content using LlamaIndex."""
        if self.llm is None:
            return self._generate_with_genai(system_prompt, user_prompt)
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]
        response = self.llm.chat(messages)
        return response.message.content
    
    def _generate_with_genai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate content using google-genai directly (fallback)."""
        if not GENAI_AVAILABLE:
            raise ValueError("No AI backend available")
        
        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model_name,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=4096,
            )
        )
        return response.text or ""
    
    def generate_diagram(self, code_context: str) -> AnalysisResult:
        """Generate an architecture diagram from code context.
        
        Args:
            code_context: Formatted code content
            
        Returns:
            AnalysisResult with DOT diagram or error
        """
        user_prompt = f"""Analyze this codebase and generate an architecture diagram:

{code_context}

Generate a Graphviz DOT diagram showing the main components and their relationships."""
        
        try:
            logger.info(f"Generating diagram with {self.model_name}")
            content = self._generate_with_llamaindex(ARCHITECT_PROMPT, user_prompt)
            
            if not content.strip():
                return AnalysisResult(content="", success=False, error="Empty response from AI")
            
            # Extract DOT content
            import re
            match = re.search(r"```(?:dot|graphviz)?\s*(.*?)\s*```", content, re.DOTALL)
            dot_content = match.group(1).strip() if match else content.strip()
            
            # Validate DOT code
            if "digraph" not in dot_content and "graph" not in dot_content:
                return AnalysisResult(
                    content="", 
                    success=False, 
                    error=f"Invalid DOT code: {dot_content[:200]}"
                )
            
            return AnalysisResult(content=dot_content)
            
        except Exception as e:
            logger.exception("Diagram generation failed")
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                return AnalysisResult(content="", success=False, error="Rate limited. Please wait and try again.")
            elif "401" in error_str or "403" in error_str:
                return AnalysisResult(content="", success=False, error="Invalid API key.")
            return AnalysisResult(content="", success=False, error=str(e))
    
    def generate_summary(self, code_context: str) -> AnalysisResult:
        """Generate a summary of the codebase.
        
        Args:
            code_context: Formatted code content
            
        Returns:
            AnalysisResult with summary or error
        """
        user_prompt = f"""Analyze this codebase:

{code_context}

Provide a concise summary."""
        
        try:
            logger.info(f"Generating summary with {self.model_name}")
            content = self._generate_with_llamaindex(SUMMARY_PROMPT, user_prompt)
            return AnalysisResult(content=content.strip())
        except Exception as e:
            logger.exception("Summary generation failed")
            return AnalysisResult(content="", success=False, error=str(e))
    
    def chat(self, message: str, code_context: str, history: Optional[List[Dict]] = None) -> AnalysisResult:
        """Chat about the codebase.
        
        Args:
            message: User's question
            code_context: Formatted code content (or DOT diagram)
            history: Previous chat messages
            
        Returns:
            AnalysisResult with response or error
        """
        # Build context from history
        history_text = ""
        if history:
            for msg in history[-6:]:  # Last 3 exchanges
                if isinstance(msg, dict):
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    content = msg.get("content", "")
                    if content:
                        history_text += f"{role}: {content}\n"
        
        user_prompt = f"""Code context:
{code_context}

{history_text}
Current question: {message}"""
        
        try:
            content = self._generate_with_llamaindex(CHAT_PROMPT, user_prompt)
            return AnalysisResult(content=content.strip())
        except Exception as e:
            logger.exception("Chat failed")
            return AnalysisResult(content="", success=False, error=str(e))

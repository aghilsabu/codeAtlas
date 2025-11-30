"""CodeAtlas Configuration"""

import os
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DIAGRAMS_DIR = DATA_DIR / "diagrams"
AUDIOS_DIR = DATA_DIR / "audios"
LOGS_DIR = DATA_DIR / "logs"
SESSION_FILE = BASE_DIR / ".session_state.json"

for dir_path in [DATA_DIR, DIAGRAMS_DIR, AUDIOS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Logging
LOG_FILE = LOGS_DIR / "codeatlas.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("codeatlas")


@dataclass
class ModelConfig:
    """Configuration for AI models."""
    
    # Gemini Models (latest first)
    GEMINI_MODELS: Dict[str, str] = field(default_factory=lambda: {
        "Gemini 3.0 Pro": "gemini-3.0-pro",
        "Gemini 2.5 Pro": "gemini-2.5-pro",
        "Gemini 2.5 Flash": "gemini-2.5-flash",
        "Gemini 2.5 Flash Lite": "gemini-2.5-flash-lite",
        "Gemini 2.0 Flash": "gemini-2.0-flash",
        "Gemini 2.0 Flash Lite": "gemini-2.0-flash-lite",
    })
    
    # OpenAI Models (latest first)
    OPENAI_MODELS: Dict[str, str] = field(default_factory=lambda: {
        "GPT-5.1": "gpt-5.1",
        "GPT-5 Mini": "gpt-5-mini",
        "GPT-5 Nano": "gpt-5-nano",
    })
    
    DEFAULT_MODEL: str = "Gemini 2.5 Pro"
    
    @property
    def all_models(self) -> Dict[str, str]:
        """Get all available models."""
        return {**self.GEMINI_MODELS, **self.OPENAI_MODELS}
    
    def is_openai_model(self, model_name: str) -> bool:
        """Check if a model is from OpenAI."""
        return model_name.startswith(("gpt-", "o1", "o3"))
    
    def get_model_id(self, display_name: str) -> str:
        """Get model ID from display name."""
        return self.all_models.get(display_name, self.GEMINI_MODELS[self.DEFAULT_MODEL])


@dataclass
class ProcessingConfig:
    """Configuration for code processing."""
    
    # File extensions to process
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
        ".cs", ".go", ".rs", ".php", ".rb", ".sql", ".yaml", ".yml",
        ".json", ".md", ".txt", ".sh", ".bash", ".zsh"
    })
    
    # Special files to include regardless of extension
    ALLOWED_FILES: set = field(default_factory=lambda: {
        "Dockerfile", "Makefile", "README", "LICENSE", ".gitignore"
    })
    
    # Directories to ignore
    BLOCKED_DIRS: set = field(default_factory=lambda: {
        "node_modules", "__pycache__", ".git", "dist", "build", "venv",
        ".venv", "env", ".env", ".idea", ".vscode", "coverage", ".next",
        "target", "bin", "obj", ".gradle", ".m2", "vendor", "Pods",
        "test", "tests", "__tests__", "spec", "specs", "testing",
        "test_data", "testdata", "fixtures", "mocks", "mock",
        "e2e", "integration", "unit", "cypress", "playwright"
    })
    
    # Files to ignore
    BLOCKED_PATTERNS: set = field(default_factory=lambda: {
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "composer.lock",
        "Gemfile.lock", "Cargo.lock", "poetry.lock", ".DS_Store",
        ".eslintrc", ".prettierrc", "tsconfig.json", "jest.config.js",
        "babel.config.js", ".babelrc", "webpack.config.js", "vite.config.js",
        "setup.cfg", "pyproject.toml", "tox.ini", ".coveragerc"
    })
    
    # Test file patterns
    TEST_FILE_PATTERNS: set = field(default_factory=lambda: {
        "test_", "_test.", ".test.", ".spec.", "_spec.",
        "conftest.py", "pytest.ini", "setup.py"
    })
    
    # Size limits
    MAX_FILE_SIZE: int = 50 * 1024  # 50KB
    MAX_CONTEXT_SIZE: int = 3_500_000  # ~1M tokens
    LARGE_REPO_THRESHOLD: int = 10_000_000  # 10MB


@dataclass  
class Config:
    """Main configuration class."""
    
    # API Keys (from environment or session)
    gemini_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("GEMINI_API_KEY", "")
    )
    openai_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", "")
    )
    elevenlabs_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("ELEVENLABS_API_KEY", "")
    )
    
    # Model configuration
    models: ModelConfig = field(default_factory=ModelConfig)
    
    # Processing configuration  
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    
    # Current model selection
    current_model: str = "Gemini 2.5 Pro"
    
    # Paths
    diagrams_dir: Path = DIAGRAMS_DIR
    audios_dir: Path = AUDIOS_DIR
    session_file: Path = SESSION_FILE
    
    # Server settings
    server_host: str = "0.0.0.0"
    server_port: int = 7860
    
    def save_to_session(self) -> bool:
        """Save current config to session file."""
        try:
            data = {
                "api_key": self.gemini_api_key,
                "openai_api_key": self.openai_api_key,
                "elevenlabs_api_key": self.elevenlabs_api_key,
                "model": self.current_model,
            }
            with open(self.session_file, "w") as f:
                json.dump(data, f)
            return True
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
            return False
    
    def load_from_session(self) -> "Config":
        """Load config from session file."""
        try:
            if self.session_file.exists():
                with open(self.session_file, "r") as f:
                    data = json.load(f)
                self.gemini_api_key = data.get("api_key", self.gemini_api_key)
                self.openai_api_key = data.get("openai_api_key", self.openai_api_key)
                self.elevenlabs_api_key = data.get("elevenlabs_api_key", self.elevenlabs_api_key)
                self.current_model = data.get("model", self.current_model)
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
        return self
    
    def get_api_key_for_model(self, model_name: str) -> str:
        """Get the appropriate API key for a model."""
        if self.models.is_openai_model(model_name):
            return self.openai_api_key or ""
        return self.gemini_api_key or ""


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config().load_from_session()
    return _config

"""
Repository Loader Module

Handles downloading and processing GitHub repositories and ZIP files.
"""

import io
import re
import zipfile
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List
import requests

from ..config import get_config

logger = logging.getLogger("codeatlas.repository")


@dataclass
class ProcessingStats:
    """Statistics from processing a repository."""
    files_processed: int = 0
    files_skipped: int = 0
    total_characters: int = 0
    estimated_tokens: int = 0
    
    @property
    def as_dict(self) -> dict:
        return {
            "files_processed": self.files_processed,
            "files_skipped": self.files_skipped,
            "total_characters": self.total_characters,
            "estimated_tokens": self.estimated_tokens,
        }


@dataclass
class ProcessingResult:
    """Result of processing a repository."""
    context: Optional[str] = None
    error: Optional[str] = None
    stats: Optional[ProcessingStats] = None
    repo_name: str = ""


class RepositoryLoader:
    """Loads and processes code repositories."""
    
    def __init__(self):
        self.config = get_config()
        self.processing = self.config.processing
    
    def load_from_github(self, url: str) -> ProcessingResult:
        """Download and process a GitHub repository.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            ProcessingResult with context or error
        """
        zip_file, error = self._download_github_repo(url)
        if error:
            return ProcessingResult(error=error)
        
        # Extract repo name
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        repo_name = f"{match.group(1)}/{match.group(2)}" if match else url
        
        try:
            context, stats = self._process_zip(zip_file)
            if not context:
                return ProcessingResult(error="No valid code files found in repository.")
            return ProcessingResult(context=context, stats=stats, repo_name=repo_name)
        finally:
            zip_file.close()
    
    def load_from_file(self, file_path: str) -> ProcessingResult:
        """Process an uploaded ZIP file.
        
        Args:
            file_path: Path to the uploaded file
            
        Returns:
            ProcessingResult with context or error
        """
        try:
            with zipfile.ZipFile(file_path, "r") as zip_file:
                context, stats = self._process_zip(zip_file)
                if not context:
                    return ProcessingResult(error="No valid code files found in ZIP.")
                repo_name = Path(file_path).stem
                return ProcessingResult(context=context, stats=stats, repo_name=repo_name)
        except zipfile.BadZipFile:
            return ProcessingResult(error="Invalid ZIP archive.")
        except Exception as e:
            logger.exception("Error processing file")
            return ProcessingResult(error=f"Error: {str(e)}")
    
    def _download_github_repo(self, url: str) -> Tuple[Optional[zipfile.ZipFile], Optional[str]]:
        """Download a GitHub repository as a ZIP file."""
        try:
            # Normalize URL
            url = url.strip().rstrip("/")
            if url.endswith(".git"):
                url = url[:-4]
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            # Validate GitHub URL
            if "github.com" not in url:
                return None, "Please provide a valid GitHub URL"
            
            # Extract owner/repo
            match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
            if not match:
                return None, "Invalid GitHub URL format"
            
            owner, repo = match.groups()
            repo = repo.split(".")[0] if "." in repo and not repo.endswith(".js") else repo
            clean_url = f"https://github.com/{owner}/{repo}"
            
            # Try downloading from different branches
            for branch in ["HEAD", "main", "master"]:
                archive_url = f"{clean_url}/archive/{branch}.zip"
                logger.info(f"Trying: {archive_url}")
                
                response = requests.get(archive_url, stream=True, timeout=60, allow_redirects=True)
                if response.status_code == 200:
                    buffer = io.BytesIO()
                    for chunk in response.iter_content(chunk_size=8192):
                        buffer.write(chunk)
                    buffer.seek(0)
                    return zipfile.ZipFile(buffer, "r"), None
            
            return None, f"Repository not found: {owner}/{repo}"
            
        except requests.exceptions.Timeout:
            return None, "Request timed out"
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)}"
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def _is_allowed_file(self, file_path: str, aggressive: bool = False) -> bool:
        """Check if a file should be processed."""
        filename = file_path.split("/")[-1]
        filename_lower = filename.lower()
        
        # Check blocked patterns
        if filename in self.processing.BLOCKED_PATTERNS:
            return False
        
        # Check blocked directories
        path_parts = file_path.split("/")
        for part in path_parts[:-1]:
            if part in self.processing.BLOCKED_DIRS:
                return False
        
        # Check test file patterns
        for pattern in self.processing.TEST_FILE_PATTERNS:
            if pattern in filename_lower:
                return False
        
        # Aggressive filtering for large repos
        if aggressive:
            path_lower = file_path.lower()
            skip_patterns = ["example", "demo", "sample", "doc/", "docs/", 
                          "tutorial", "benchmark", "contrib/", "scripts/"]
            for pattern in skip_patterns:
                if pattern in path_lower:
                    return False
            
            # Only core code extensions
            core_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs"}
            ext = "." + filename.split(".")[-1] if "." in filename else ""
            if ext and ext not in core_extensions:
                return False
        
        # Check allowed files
        if filename in self.processing.ALLOWED_FILES:
            return True
        
        # Check extensions
        for ext in self.processing.ALLOWED_EXTENSIONS:
            if filename.endswith(ext):
                return True
        
        return False
    
    def _clean_code(self, content: str) -> str:
        """Clean code content."""
        # Remove excessive blank lines
        content = re.sub(r"\n{4,}", "\n\n\n", content)
        # Remove trailing whitespace
        lines = [line.rstrip() for line in content.split("\n")]
        return "\n".join(lines).strip()
    
    def _process_zip(self, zip_file: zipfile.ZipFile) -> Tuple[str, ProcessingStats]:
        """Process a ZIP file and extract code content."""
        stats = ProcessingStats()
        file_contents = []
        
        # Calculate total size for aggressive filtering
        file_list = zip_file.namelist()
        total_size = sum(
            zip_file.getinfo(f).file_size 
            for f in file_list 
            if not f.endswith("/")
        )
        aggressive = total_size > self.processing.LARGE_REPO_THRESHOLD
        
        if aggressive:
            logger.info(f"Large repo ({total_size:,} bytes), using aggressive filtering")
        
        # Sort by priority (shallow = more important)
        def file_priority(path):
            depth = path.count("/")
            priority_dirs = ["src/", "lib/", "core/", "app/", "pkg/"]
            for pd in priority_dirs:
                if pd in path.lower():
                    return (0, depth, path)
            return (1, depth, path)
        
        sorted_files = sorted(file_list, key=file_priority)
        
        for file_path in sorted_files:
            if file_path.endswith("/"):
                continue
            
            if not self._is_allowed_file(file_path, aggressive):
                stats.files_skipped += 1
                continue
            
            try:
                file_info = zip_file.getinfo(file_path)
                if file_info.file_size > self.processing.MAX_FILE_SIZE:
                    stats.files_skipped += 1
                    continue
                
                with zip_file.open(file_path) as f:
                    content = f.read().decode("utf-8", errors="ignore")
                
                content = self._clean_code(content)
                if not content.strip():
                    stats.files_skipped += 1
                    continue
                
                file_entry = f'<file name="{file_path}">\n{content}\n</file>\n\n'
                
                if stats.total_characters + len(file_entry) > self.processing.MAX_CONTEXT_SIZE:
                    break
                
                file_contents.append(file_entry)
                stats.total_characters += len(file_entry)
                stats.files_processed += 1
                
            except Exception as e:
                stats.files_skipped += 1
                logger.debug(f"Error processing {file_path}: {e}")
        
        stats.estimated_tokens = stats.total_characters // 4
        context = "".join(file_contents)
        
        logger.info(f"Processed {stats.files_processed} files, {stats.total_characters:,} chars")
        return context, stats

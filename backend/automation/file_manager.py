import os
import glob
import shutil
import platform
from pathlib import Path

class FileManager:
    """
    Cross-platform file management and search module.
    Supports voice-driven search, folder creation, organization, and safe file operations.
    """

    @classmethod
    def get_search_roots(cls) -> list[str]:
        """Get common user directories for fast prioritized searching."""
        home = str(Path.home())
        roots = [
            os.path.join(home, "Desktop"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Pictures"),
            os.path.join(home, "Music")
        ]
        return [r for r in roots if os.path.exists(r)]

    @classmethod
    def search_files(cls, query: str, max_results: int = 5, extension: str = None) -> dict:
        """
        Fast prioritized search for files across Desktop, Downloads, and Documents.
        """
        query_clean = query.lower().strip()
        matched = []

        roots = cls.get_search_roots()
        for root in roots:
            for dirpath, _, filenames in os.walk(root):
                # Skip hidden directories like .git, .cache
                if "/." in dirpath or "\\." in dirpath:
                    continue
                for fname in filenames:
                    if fname.startswith("."):
                        continue
                    
                    fname_lower = fname.lower()
                    if query_clean in fname_lower:
                        if extension and not fname_lower.endswith(extension.lower()):
                            continue
                        
                        full_path = os.path.join(dirpath, fname)
                        size_kb = round(os.path.getsize(full_path) / 1024, 1)
                        matched.append({
                            "name": fname,
                            "path": full_path,
                            "size_kb": size_kb,
                            "directory": dirpath
                        })

                        if len(matched) >= max_results:
                            break
                if len(matched) >= max_results:
                    break

        return {
            "success": True,
            "query": query,
            "count": len(matched),
            "files": matched
        }

    @classmethod
    def create_file(cls, filename: str, content: str = "", directory: str = None) -> dict:
        """Create a new file with optional content in specified directory (defaults to Desktop)."""
        target_dir = directory or os.path.join(str(Path.home()), "Desktop")
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "message": f"Created file {filename}",
                "path": file_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def create_folder(cls, folder_name: str, parent_directory: str = None) -> dict:
        """Create a new folder."""
        target_dir = parent_directory or os.path.join(str(Path.home()), "Desktop")
        folder_path = os.path.join(target_dir, folder_name)
        try:
            os.makedirs(folder_path, exist_ok=True)
            return {
                "success": True,
                "message": f"Created folder {folder_name}",
                "path": folder_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def read_recent_downloads(cls, count: int = 5) -> dict:
        """Get the most recently modified or downloaded files."""
        downloads_dir = os.path.join(str(Path.home()), "Downloads")
        if not os.path.exists(downloads_dir):
            return {"success": False, "error": "Downloads folder not found"}

        files = []
        for entry in os.scandir(downloads_dir):
            if entry.is_file() and not entry.name.startswith("."):
                files.append({
                    "name": entry.name,
                    "path": entry.path,
                    "modified_time": entry.stat().st_mtime,
                    "size_kb": round(entry.stat().st_size / 1024, 1)
                })

        # Sort by latest modified
        files.sort(key=lambda x: x["modified_time"], reverse=True)
        return {
            "success": True,
            "recent_files": files[:count]
        }

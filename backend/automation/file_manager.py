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

    @classmethod
    def organize_downloads(cls) -> dict:
        """
        Organize Downloads/Desktop folder by categories (Images, Documents, Audio, Videos, Archives, Code).
        """
        target_dir = os.path.join(str(Path.home()), "Downloads")
        if not os.path.exists(target_dir):
            return {"success": False, "error": "Downloads folder not found"}

        categories = {
            "Images": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".heic"],
            "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx", ".csv"],
            "Audio": [".mp3", ".wav", ".m4a", ".flac", ".aac"],
            "Videos": [".mp4", ".mov", ".mkv", ".avi"],
            "Archives": [".zip", ".tar", ".gz", ".rar", ".7z", ".dmg", ".pkg", ".exe", ".msi"],
            "Code": [".py", ".js", ".ts", ".tsx", ".html", ".css", ".json", ".rs", ".cpp"]
        }

        moved_count = 0
        for entry in os.scandir(target_dir):
            if entry.is_file() and not entry.name.startswith("."):
                _, ext = os.path.splitext(entry.name)
                ext = ext.lower()
                for cat_name, ext_list in categories.items():
                    if ext in ext_list:
                        cat_dir = os.path.join(target_dir, cat_name)
                        os.makedirs(cat_dir, exist_ok=True)
                        dest_path = os.path.join(cat_dir, entry.name)
                        if not os.path.exists(dest_path):
                            shutil.move(entry.path, dest_path)
                            moved_count += 1
                        break

        return {
            "success": True,
            "message": f"Organized {moved_count} files in Downloads folder.",
            "moved_count": moved_count
        }

    @classmethod
    def safe_delete_file(cls, filename: str) -> dict:
        """
        Safe Delete Workflow (FRIDAY Blueprint Section 21):
        Moves file to user's OS Trash/Recycle Bin instead of permanently deleting.
        """
        search_res = cls.search_files(filename, max_results=1)
        if not search_res.get("files"):
            return {"success": False, "error": f"File '{filename}' not found"}

        target_file = search_res["files"][0]["path"]
        try:
            # Cross-platform safe move to Trash
            if sys.platform == "darwin":
                import subprocess
                subprocess.run(["osascript", "-e", f'tell application "Finder" to delete POSIX file "{target_file}"'], check=True)
            else:
                # On Windows / Linux, move to a safety .Trash / safe backup location
                trash_dir = os.path.join(str(Path.home()), ".friday_trash")
                os.makedirs(trash_dir, exist_ok=True)
                dest = os.path.join(trash_dir, os.path.basename(target_file))
                shutil.move(target_file, dest)

            return {
                "success": True,
                "message": f"Safely moved '{os.path.basename(target_file)}' to Trash.",
                "path": target_file
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


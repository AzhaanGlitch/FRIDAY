import uvicorn
import os
import sys

if __name__ == "__main__":
    # Add project root to sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    os.environ["PYTHONPATH"] = project_root + os.pathsep + os.environ.get("PYTHONPATH", "")
    
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, reload=True)


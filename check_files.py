import os
import random

def get_project_files():
    base_dir = '/home/noogh/projects/noogh_unified_system/src'
    ignore_dirs = {'.venv', '.noogh_venv', '__pycache__', 'venv', 'mcp_server', 'training', 'system-prompts-and-models-of-ai-tools-main', '.git', '.gemini'}
    py_files = []
    
    for root, dirs, files in os.walk(base_dir):
        # modify dirs in-place to prune ignore_dirs
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.venv')]
        
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    
    return py_files

if __name__ == '__main__':
    files = get_project_files()
    print(f"Total internal Python files: {len(files)}")
    dirs = {}
    for f in files:
        d = os.path.dirname(f).replace('/home/noogh/projects/noogh_unified_system/src', '')
        if d == '': d = '/'
        dirs[d] = dirs.get(d, 0) + 1
    
    for d, c in sorted(dirs.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {d}: {c} files")

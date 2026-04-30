import os
from pathlib import Path

def generate_tree(root_dir: Path, exclude_dirs: set) -> str:
    tree_str = "dir tree:\n\n"
    # Walk the directory
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip excluded
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        level = root.replace(str(root_dir), '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree_str += f"{indent}{os.path.basename(root)}/\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f.endswith(('.pyc', '.git')) or f.startswith('.'):
                continue
            tree_str += f"{subindent}{f}\n"
    return tree_str

def dump_codebase(root_path: str, output_file: str = "codebase_structure.txt"):
    root_dir = Path(root_path).resolve()
    exclude_dirs = {'.venv', 'env', '__pycache__', '.git', 'node_modules', '.idea', '.vscode'}
    exclude_extensions = {'.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.exe', '.bin', '.db', '.sqlite','.docx','.doc','.json'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 1. Write Directory Tree
        try:
            tree = generate_tree(root_dir, exclude_dirs)
            outfile.write(tree)
            outfile.write("\n" + "="*80 + "\n\n")
        except Exception as e:
            outfile.write(f"Error generating tree: {e}\n\n")

        # 2. Write File Contents
        for root, dirs, files in os.walk(root_dir):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                if file.startswith('.') or file == output_file:
                    continue
                
                file_path = Path(root) / file
                if file_path.suffix in exclude_extensions:
                    continue

                relative_path = file_path.relative_to(root_dir)
                
                outfile.write(f"\nSTART OF FILE: {relative_path}\n")
                outfile.write(f"PATH: {relative_path}\n")
                outfile.write("-" * 80 + "\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        outfile.write(f.read())
                except UnicodeDecodeError:
                    outfile.write("[Binary or non-UTF-8 file content skipped]")
                except Exception as e:
                    outfile.write(f"[Error reading file: {e}]")
                
                outfile.write("\n\n" + "="*80 + "\n")

    print(f"Codebase dumped to {output_file}")

if __name__ == "__main__":
    # Default to current directory
    target_dir = input("Enter folder path (press Enter for current directory): ").strip()
    if not target_dir:
        target_dir = "."
    
    output_name = input("Enter output filename (default: codebase_context.txt): ").strip()
    if not output_name:
        output_name = "codebase_context.txt"
        
    dump_codebase(target_dir, output_name)



import os
import sys
import fnmatch
import datetime

def main():
    # Parse root directory from arguments
    root_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
    
    # Validate root directory
    if not os.path.isdir(root_dir):
        print(f"Error: '{root_dir}' is not a valid directory")
        return

    # Handle .codeignore file
    codeignore_path = os.path.join(root_dir, '.codeignore')
    default_ignore = [
        '.git/',
        '__pycache__/',
        'venv/',
        'node_modules/',
        '*.bin',
        '*.png',
        '*.jpg',
    ]
    ignore_patterns = []
    using_codeignore = True

    if os.path.exists(codeignore_path):
        try:
            with open(codeignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.append(line)
        except Exception as e:
            print(f"Warning: Could not read .codeignore file: {e}")
            ignore_patterns = default_ignore.copy()
            using_codeignore = False
    else:
        ignore_patterns = default_ignore.copy()
        using_codeignore = False
        print("Notice: .codeignore file not found, using default ignore patterns")

    # Split patterns into directory and file patterns
    dir_patterns = set()
    file_patterns = set()
    
    for pattern in ignore_patterns:
        if pattern.endswith('/'):
            dir_patterns.add(pattern.rstrip('/'))
        else:
            file_patterns.add(pattern)

    # Prepare output content
    output_content = []
    file_count = 0
    error_count = 0

    # Traverse directory tree
    for root, dirs, files in os.walk(root_dir, topdown=True):
        # Filter directories
        dirs[:] = [d for d in dirs if not any(
            fnmatch.fnmatch(d, pattern) for pattern in dir_patterns
        )]

        # Process files
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, root_dir)

            # Skip files matching file patterns
            if any(fnmatch.fnmatch(filename, pattern) for pattern in file_patterns):
                continue

            # Try to read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                print(f"Warning: Skipping binary file: {rel_path}")
                error_count += 1
                continue
            except PermissionError:
                print(f"Warning: Permission denied for: {rel_path}")
                error_count += 1
                continue
            except Exception as e:
                print(f"Warning: Could not read {rel_path}: {e}")
                error_count += 1
                continue

            # Add to output
            output_content.append(f"# FILE: {rel_path}\n{content}\n")
            file_count += 1

    # Prepare metadata header
    generated_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    header = [
        f"# Generated: {generated_time}",
        f"# Root Directory: {os.path.abspath(root_dir)}",
        f"# Ignored Patterns: {ignore_patterns}\n"
    ]

    # Write output file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'combined_code.txt')
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header))
            f.write('\n'.join(output_content))
    except Exception as e:
        print(f"Error: Failed to write output file: {e}")
        return

    # Print summary
    print(f"Successfully processed {file_count} files")
    print(f"Skipped {error_count} files due to errors or ignores")
    if not using_codeignore:
        print("Note: Used default ignore patterns")

if __name__ == "__main__":
    main()
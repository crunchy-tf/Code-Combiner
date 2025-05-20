import os
import sys
import fnmatch
import datetime

def main():
    # --- Determine script directory early for .codeignore and output ---
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Parse root directory to scan from arguments ---
    # This is the directory whose contents will be combined
    root_dir_to_scan = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()

    # Validate root directory to scan
    if not os.path.isdir(root_dir_to_scan):
        print(f"Error: '{root_dir_to_scan}' is not a valid directory to scan.")
        return

    # --- Handle .codeignore file (from script's directory) ---
    codeignore_path = os.path.join(script_dir, '.codeignore')

    # Default patterns (excluding .git/ as it's always ignored)
    # These are used if .codeignore is not found or is unreadable.
    default_ignore_rules = [
        '__pycache__/',
        'venv/',
        '*.venv/', # Common for project-specific venvs
        '.env',
        'node_modules/',
        'dist/',
        'build/',
        '*.pyc',
        '*.o',
        '*.so',
        '*.dll',
        '*.exe',
        '*.bin',
        '.DS_Store', # macOS specific
        '*.log',
        '*.tmp',
        '*.swp',
        '*.swo',
        '*.bak',
        '*.class', # Java
        '*.jar',   # Java
        '*.war',   # Java
        '*.ear',   # Java
        # Common media/binary files often not wanted in combined code
        '*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.tiff', '*.ico',
        '*.pdf',
        '*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt', '*.pptx',
        '*.zip', '*.tar', '*.gz', '*.rar', '*.7z',
        '*.mp3', '*.mp4', '*.avi', '*.mov', '*.webm',
        'package-lock.json',
        'yarn.lock',
        'Pipfile.lock',
        'poetry.lock',
        'target/', # Rust, Java (Maven/Gradle)
        '.idea/', # JetBrains IDEs
        '.vscode/', # VS Code
        'nbproject/', # NetBeans
        '*.sublime-project', '*.sublime-workspace', # Sublime Text
    ]
    ignore_patterns_from_file_or_default = []
    using_codeignore_file = True # Assume we'll use it

    if os.path.exists(codeignore_path):
        try:
            with open(codeignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns_from_file_or_default.append(line)
            print(f"Notice: Using .codeignore file found at '{codeignore_path}'")
        except Exception as e:
            print(f"Warning: Could not read .codeignore file at '{codeignore_path}': {e}")
            print("Notice: Falling back to default ignore patterns (plus always-ignored .git/).")
            ignore_patterns_from_file_or_default = default_ignore_rules.copy()
            using_codeignore_file = False
    else:
        print(f"Notice: .codeignore file not found at '{codeignore_path}'.")
        print("Notice: Using default ignore patterns (plus always-ignored .git/).")
        ignore_patterns_from_file_or_default = default_ignore_rules.copy()
        using_codeignore_file = False

    # --- Combine all ignore patterns ---
    # Start with '.git/' (always ignored) and add patterns from file/defaults.
    # Use a set to avoid duplicates if '.git/' was also in .codeignore
    final_effective_ignore_patterns = list(set(['.git/'] + ignore_patterns_from_file_or_default))

    # Split effective patterns into directory and file patterns
    dir_ignore_patterns = set()  # Patterns for directory names, e.g., "node_modules"
    file_ignore_patterns = set() # Patterns for filenames or relative paths, e.g., "*.log" or "src/*.tmp"

    for pattern in final_effective_ignore_patterns:
        if pattern.endswith('/'):
            # For directory patterns like "venv/", store "venv"
            dir_ignore_patterns.add(pattern.rstrip('/'))
        else:
            file_ignore_patterns.add(pattern)

    # Prepare output content
    output_content_parts = []
    processed_file_count = 0
    skipped_due_to_error_count = 0

    # --- Traverse directory tree of the target project ---
    print(f"\nScanning directory: {root_dir_to_scan}")
    for current_dir_path, subdir_names, file_names in os.walk(root_dir_to_scan, topdown=True):
        # Filter directories to prevent descending into them
        # A directory 'd_name' is ignored if its name matches any pattern in dir_ignore_patterns
        subdir_names[:] = [
            d_name for d_name in subdir_names
            if not any(fnmatch.fnmatch(d_name, dir_pat) for dir_pat in dir_ignore_patterns)
        ]

        # Process files in the current directory
        for f_name in file_names:
            full_file_path = os.path.join(current_dir_path, f_name)
            # Relative path from the scanned root, e.g., 'src/main.py' or 'README.md'
            relative_file_path = os.path.relpath(full_file_path, root_dir_to_scan)
            # Normalize path separators for consistent fnmatch (Unix-style)
            normalized_relative_path = relative_file_path.replace(os.sep, '/')

            is_ignored_by_file_pattern = False
            for file_pat in file_ignore_patterns:
                # Match pattern against the full relative path OR just the filename
                if fnmatch.fnmatch(normalized_relative_path, file_pat) or \
                   fnmatch.fnmatch(f_name, file_pat):
                    is_ignored_by_file_pattern = True
                    break
            
            if is_ignored_by_file_pattern:
                continue # Skip this file

            # Try to read file content
            try:
                with open(full_file_path, 'r', encoding='utf-8') as f_obj:
                    content = f_obj.read()
            except UnicodeDecodeError:
                # This often indicates a binary file not caught by extension-based ignores
                # print(f"Warning: Skipping binary or non-UTF-8 file: {relative_file_path}") # Can be noisy
                skipped_due_to_error_count += 1
                continue
            except PermissionError:
                print(f"Warning: Permission denied for: {relative_file_path}")
                skipped_due_to_error_count += 1
                continue
            except Exception as e:
                print(f"Warning: Could not read {relative_file_path}: {e}")
                skipped_due_to_error_count += 1
                continue

            # Add to output
            output_content_parts.append(f"# FILE: {normalized_relative_path}\n{content}\n")
            processed_file_count += 1

    # --- Prepare metadata header for the output file ---
    generation_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    header_lines = [
        f"# Combined Code Generated: {generation_time_str}",
        f"# Scanned Root Directory: {os.path.abspath(root_dir_to_scan)}",
        f"# .codeignore File Source: {'Used: ' + codeignore_path if using_codeignore_file else 'Not found/used; defaults applied.'}",
        f"# Effective Ignored Patterns (includes always-ignored '.git/'): {sorted(list(final_effective_ignore_patterns))}\n"
    ]

    # --- Write output file (in script's directory, fixed filename) ---
    # CHANGED: Fixed output filename to 'combined_code.txt'
    output_filename = 'combined_code.txt'
    output_file_path = os.path.join(script_dir, output_filename)

    try:
        # 'w' mode will overwrite the file if it exists
        with open(output_file_path, 'w', encoding='utf-8') as f_out:
            f_out.write('\n'.join(header_lines))
            f_out.write('\n'.join(output_content_parts)) # Join all collected file contents
        print(f"\nSuccessfully processed {processed_file_count} files.")
        print(f"Output written to: {output_file_path} (overwritten if existed).") # Clarify overwrite
    except Exception as e:
        print(f"Error: Failed to write output file '{output_file_path}': {e}")
        return

    if skipped_due_to_error_count > 0:
        print(f"Skipped {skipped_due_to_error_count} files due to reading errors or being binary/non-UTF-8.")
    if not using_codeignore_file:
        print("Reminder: Default ignore patterns were used because .codeignore was not found or was unreadable.")
    print("Reminder: The '.git/' directory and its contents are always ignored.")

if __name__ == "__main__":
    main()
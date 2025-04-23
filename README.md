# Code-Combiner

Features ✨

✅ Recursive directory scanning – Processes all files in a directory and its subdirectories.

✅ Ignore file support – Uses .codeignore (like .gitignore) to exclude files/directories.

✅ Binary file detection – Automatically skips non-text files (images, executables, etc.).

✅ Formatted output – Clearly marks each file’s path and content for easy parsing.

✅ Error handling – Skips unreadable files and logs warnings.

✅ Metadata header – Includes timestamps, root directory, and ignored patterns.

Installation ⚙️
Prerequisites

    Python 3.6+

Setup

    Clone the repo (or download the script):
    bash

git clone https://github.com/yourusername/code-combiner.git

cd code-combiner

Run the script:
bash

    python code_combiner.py [optional/path/to/directory]

        If no path is given, it scans the current directory.

Usage 📖
Basic Command
bash

python code_combiner.py

    Scans the current directory.

    Outputs to combined_code.txt in the script’s folder.

Scan a Specific Directory
bash

python code_combiner.py ~/projects/my_app

Custom Exclusions (.codeignore)

Create a .codeignore file in the target directory to exclude files/directories.

Example .codeignore:
text

# Ignore directories
venv/
node_modules/
tmp/

# Ignore file types
*.log
*.pdf
*.jpg

Default Ignored Patterns

If .codeignore doesn’t exist, the script skips:

    .git/, __pycache__/, venv/, node_modules/

    *.bin, *.png, *.jpg

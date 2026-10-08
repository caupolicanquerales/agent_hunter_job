#!/usr/bin/env python3
"""Delete generated files inside a project folder, filtered by optional glob patterns."""
import fnmatch
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OPENCODE_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
PROJECT_DIR = os.path.realpath(os.path.dirname(OPENCODE_DIR))

USAGE = "Usage: python3 delete_all_files_in_folder.py <folder> [--pattern <glob>]... [--exclude <glob>]..."


def parse_arguments(argv):
    if not argv:
        raise ValueError(USAGE)
    folder = argv[0]
    patterns = []
    excludes = []
    index = 1
    while index < len(argv):
        flag = argv[index]
        if flag not in ("--pattern", "--exclude") or index + 1 >= len(argv):
            raise ValueError(USAGE)
        values = patterns if flag == "--pattern" else excludes
        values.append(argv[index + 1])
        index += 2
    return folder, patterns, excludes


def resolve_folder(name):
    """Resolve the folder against the project root and refuse protected/outside paths."""
    if not name or not name.strip():
        raise ValueError("Folder is required, example: reports")
    candidate = name.strip()
    folder = os.path.realpath(candidate if os.path.isabs(candidate) else os.path.join(PROJECT_DIR, candidate))
    protected = {PROJECT_DIR, os.path.realpath(os.path.expanduser("~")), "/"}
    if folder in protected:
        raise ValueError(f"Refusing to clean a protected folder: {folder}")
    if os.path.commonpath([PROJECT_DIR, folder]) != PROJECT_DIR:
        raise ValueError(f"Refusing to clean a folder outside the project: {folder}")
    return folder


def matches(file_name, patterns):
    return not patterns or any(fnmatch.fnmatch(file_name, pattern) for pattern in patterns)


def delete_files(folder, patterns, excludes):
    """Remove files (never subdirectories) matching the patterns and not the excludes."""
    if not os.path.isdir(folder):
        print(f"Folder not found (nothing to remove): {folder}")
        return None
    removed = []
    for entry in sorted(os.listdir(folder)):
        path = os.path.join(folder, entry)
        if not os.path.isfile(path):
            continue
        if not matches(entry, patterns):
            continue
        if any(fnmatch.fnmatch(entry, exclude) for exclude in excludes):
            continue
        os.remove(path)
        removed.append(entry)
    return removed


def main():
    try:
        folder_arg, patterns, excludes = parse_arguments(sys.argv[1:])
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
    try:
        folder = resolve_folder(folder_arg)
        removed = delete_files(folder, patterns, excludes)
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    if removed is None:
        return
    print(f"Removed {len(removed)} files from {folder}")
    if removed:
        print(f"Removed: {', '.join(removed)}")


if __name__ == "__main__":
    main()

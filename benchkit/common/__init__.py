from pathlib import Path

from .dbgen import DbGenPipe as DbGenPipe
from .file_management import DataFormat as DataFormat
from .file_management import download_file_to_storage as download_file_to_storage
from .markers import exclude_from_package as exclude_from_package
from .markup import strip_markup as strip_markup

# Capture original working directory at module load time.
# This is critical for thread-safety: os.chdir() in one thread affects all threads,
# so we need a stable reference point for resolving paths to project root.
# Used by: InfraManager (terraform paths), SuiteRunner (log paths)
PROJECT_ROOT = Path.cwd()

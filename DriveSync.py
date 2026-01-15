# --------------------------------------------------------------------------
# DriveSync.py - Robust, Multi-Threaded Directory Copier
#
# Features:
# - Multi-threaded copying using ThreadPoolExecutor.
# - Smart Sync: Skips files if they exist match size and modification time.
# - Robust: Retries on network errors (e.g., Semaphore Timeout).
# - Logging: Detailed logs to file and console.
# - Dry-Run Mode: Simulate operations without changes.
# - Statistics: Summary report at the end.
#
# Author: Alejandro Pedro Ayala
# --------------------------------------------------------------------------

import argparse
import shutil
import sys
import time
import glob
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

try:
    from tqdm import tqdm
except ImportError:
    print("Error: 'tqdm' library not found. Please install it using 'pip install tqdm'", file=sys.stderr)
    sys.exit(1)

# --- Constants ---
SEMAPHORE_TIMEOUT_ERROR_CODE = 121
LOG_FILENAME = f"DriveSync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def setup_logging(verbose: bool):
    """Configures logging to file and console."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File Handler (Detailed)
    file_handler = logging.FileHandler(LOG_FILENAME, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console Handler (Less verbose unless requested)
    # We use tqdm.write for console output to avoid interfering with progress bars,
    # so we might not attach a standard StreamHandler to root if using tqdm.
    # Instead, we'll use a custom handler or just rely on tqdm.write in logic.
    # For simplicity, we strictly use our own print/write wrappers for console.

def log_message(message: str, level: str = "INFO", console: bool = True):
    """Logs a message to file and optionally prints it to console via tqdm."""
    logger = logging.getLogger()
    if level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    
    if console:
        # If verbose or level is high, print. 
        # But here we let the caller decide visibility.
        tqdm.write(f"[{level}] {message}")

def should_skip_file(source: Path, dest: Path) -> bool:
    """
    Smart Sync Logic:
    Returns True if destination exists and matches source size and mtime.
    """
    if not dest.exists():
        return False
    
    try:
        s_stat = source.stat()
        d_stat = dest.stat()
        
        # Check size
        if s_stat.st_size != d_stat.st_size:
            return False
            
        # Check modification time (allow for small precision differences, e.g., 2 seconds)
        if abs(s_stat.st_mtime - d_stat.st_mtime) > 2.0:
            return False
            
        return True
    except OSError:
        return False # If we can't accept files, retry or re-copy is safer

def copy_task(source: Path, dest: Path, args: argparse.Namespace, pbar: tqdm) -> str:
    """
    Worker function to copy a single file.
    Returns a status string: 'copied', 'skipped', 'error'
    """
    try:
        if args.dry_run:
            if should_skip_file(source, dest) and not args.overwrite:
                 return 'skipped'
            return 'copied'

        if not args.overwrite and should_skip_file(source, dest):
            if args.verbose:
                log_message(f"Skipping identical file: {source.name}", level="INFO", console=False)
            pbar.update(source.stat().st_size)
            return 'skipped'
        
        # Create parent dir if it doesn't exist (race condition safe)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Retry loop
        for attempt in range(args.retries + 1):
            try:
                shutil.copy2(source, dest)
                break
            except OSError as e:
                if e.winerror == SEMAPHORE_TIMEOUT_ERROR_CODE and attempt < args.retries:
                    log_message(f"Timeout on '{source.name}'. Retrying ({attempt+1}/{args.retries})...", level="WARNING")
                    time.sleep(args.retry_delay)
                else:
                    raise
        
        pbar.update(source.stat().st_size)
        return 'copied'

    except Exception as e:
        log_message(f"Failed to copy {source}: {e}", level="ERROR")
        return 'error'

def scan_for_files(source_dir: Path, dest_dir: Path) -> List[Tuple[Path, Path, int]]:
    """
    Recursively scans source_dir and returns a list of (source, dest, size) tuples.
    """
    file_list = []
    try:
        # Using rglob for simpler recursion, though iterdir is sometimes faster for huge trees.
        # Standard rglob is fine for most 'user' folder sizes.
        for source_path in source_dir.rglob('*'):
            if source_path.is_file():
                rel_path = source_path.relative_to(source_dir)
                dest_path = dest_dir / rel_path
                try:
                    size = source_path.stat().st_size
                    file_list.append((source_path, dest_path, size))
                except OSError as e:
                    log_message(f"Skipping inaccessible file {source_path}: {e}", level="WARNING")
    except OSError as e:
        log_message(f"Error accessing directory {source_dir}: {e}", level="ERROR")
    return file_list

def main():
    parser = argparse.ArgumentParser(
        description="DriveSync: Robust directory synchronization tool.",
        epilog="Examples:\n"
               '  DriveSync.exe "G:\\My Drive" "D:\\Backup" --threads 20 --dry-run\n'
               '  DriveSync.exe .\\Project* D:\\Archives',
        formatter_class=argparse.RawTextHelpFormatter
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("sources", nargs='*', type=Path, help="Source directories (supports wildcards).")
    source_group.add_argument("-f", "--from-file", dest="source_file", type=Path, help="File containing list of source directories.")

    parser.add_argument("destination", type=Path, help="Destination parent directory.")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Max concurrent threads (default: 10).")
    parser.add_argument("--retries", type=int, default=3, help="Retries on timeout (default: 3).")
    parser.add_argument("--retry-delay", type=int, default=5, help="Retry delay in seconds.")
    parser.add_argument("--overwrite", action="store_true", help="Force overwrite existing files (disables Smart Sync).")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without copying.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed logs to console.")
    parser.add_argument("--no-verify", action="store_true", help="Skip size/time check (just check existence). Unsafe.")

    args = parser.parse_args()
    setup_logging(args.verbose)
    
    log_message("--- DriveSync Started ---", console=True)
    if args.dry_run:
        log_message("!!! DRY RUN MODE - No files will be copied !!!", console=True)

    # --- Source Expansion ---
    sources_to_process = []
    initial_sources = []
    
    if args.source_file:
        if args.source_file.exists():
            with args.source_file.open('r', encoding='utf-8') as f:
                initial_sources = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            log_message(f"Source file not found: {args.source_file}", level="ERROR")
            sys.exit(1)
    else:
        initial_sources = args.sources

    for src_str in initial_sources:
        src_str = str(src_str)
        matched = False
        for path in glob.glob(src_str):
            matched = True
            p = Path(path).resolve()
            if p.is_dir():
                sources_to_process.append(p)
            else:
                log_message(f"Skipping non-directory source: {p}", level="WARNING")
        if not matched:
            log_message(f"No match found for pattern: {src_str}", level="WARNING")

    if not sources_to_process:
        log_message("No valid source directories found.", level="ERROR")
        sys.exit(1)

    dest_root = args.destination.resolve()
    dest_root.mkdir(parents=True, exist_ok=True)

    # --- Scaning Phase ---
    all_files_to_copy: List[Tuple[Path, Path, int]] = []
    total_batch_size = 0
    
    log_message("Scanning source directories...", console=True)
    for source in sources_to_process:
        # Destination for this source folder
        # If source is C:\Data, and dest is D:\Backup, we copy to D:\Backup\Data
        final_dest = dest_root / source.name
        
        # Guard against recursive copy
        try:
            if final_dest.resolve() == source or source in final_dest.resolve().parents:
                 log_message(f"Skipping recursive copy: {source} -> {final_dest}", level="ERROR")
                 continue
        except Exception:
            pass # Path resolution issues

        files = scan_for_files(source, final_dest)
        all_files_to_copy.extend(files)
        total_batch_size += sum(f[2] for f in files)

    file_count = len(all_files_to_copy)
    log_message(f"Found {file_count} files. Total size: {total_batch_size / (1024**2):.2f} MB", console=True)
    
    if file_count == 0:
        log_message("Nothing to copy.", console=True)
        sys.exit(0)

    # --- Execution Phase ---
    stats = {'copied': 0, 'skipped': 0, 'error': 0}
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        with tqdm(total=total_batch_size, unit='B', unit_scale=True, unit_divisor=1024, desc="Syncing") as pbar:
            futures = {
                executor.submit(copy_task, src, dst, args, pbar): (src, dst)
                for src, dst, size in all_files_to_copy
            }

            for future in as_completed(futures):
                result = future.result()
                stats[result] += 1

    duration = time.time() - start_time
    
    # --- Summary ---
    summary = (
        f"\n--- Sync Complete ---\n"
        f"Time Taken: {duration:.2f}s\n"
        f"Files Copied: {stats['copied']}\n"
        f"Files Skipped: {stats['skipped']}\n"
        f"Errors: {stats['error']}\n"
        f"Log File: {LOG_FILENAME}\n"
    )
    log_message(summary, console=True)

if __name__ == "__main__":
    main()
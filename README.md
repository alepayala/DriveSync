# DriveSync

**DriveSync** is a robust, multi-threaded directory synchronization tool written in Python. It is designed to efficiently copy files from multiple source directories to a destination, skipping files that are already identical (Smart Sync) and handling network flakiness with automatic retries.

## Features

-   **Multi-Threaded**: Uses `ThreadPoolExecutor` for high-speed parallel copying.
-   **Smart Sync**: Skips files if they already exist at the destination with the same size and modification time.
-   **Robust**: Automatically retries on network errors (e.g., Semaphore Timeout).
-   **Dry-Run Mode**: Simulate the operation to see what would be copied without making changes.
-   **Detailed Logging**: Logs operations to both a file and the console.
-   **Wildcard Support**: Accepts glob patterns for source directories.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/DriveSync.git
    cd DriveSync
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script from the command line:

```bash
python DriveSync.py "Source_Path" "Destination_Path" [options]
```

### Examples

**Basic Copy:**
```bash
python DriveSync.py "C:\MyDocuments" "D:\Backup"
```

**Using Wildcards:**
```bash
python DriveSync.py "C:\Projects\*" "D:\Backups\Projects"
```

**Dry Run (Simulation):**
```bash
python DriveSync.py "C:\Data" "D:\Backup" --dry-run
```

**High Performance (20 threads):**
```bash
python DriveSync.py "C:\Data" "D:\Backup" --threads 20
```

### Options

| Option | Description |
| :--- | :--- |
| `sources` | Source directories (supports wildcards). Mutually exclusive with `-f`. |
| `-f`, `--from-file` | Read list of source directories from a file. |
| `destination` | Destination parent directory. |
| `-t`, `--threads` | Max concurrent threads (default: 10). |
| `--retries` | Number of retries on timeout (default: 3). |
| `--retry-delay` | Seconds to wait between retries. |
| `--overwrite` | Force overwrite existing files (disables Smart Sync). |
| `--dry-run` | Simulate without copying. |
| `--verbose` | Print detailed logs to console. |
| `--no-verify` | Skip size/time check (unsafe, checks existence only). |

## Building a Standalone Executable

You can use PyInstaller to build a standalone `.exe`:

```bash
pyinstaller DriveSync.spec
```
(Or run `build_DriveSync.bat` if available)

## Author

Alejandro Pedro Ayala

## License

[MIT License](LICENSE)

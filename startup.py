"""
Startup script to ensure data directory exists on Railway
Note: Data is now stored in Firebase Firestore, only local files are needed
"""
import os

def get_data_dir():
    """Get the data directory path (same logic as config.py)"""
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY"):
        return "/app/data_files"
    else:
        return "data_files"

def ensure_data_directory():
    """Ensure the data directory and all required files exist"""
    data_dir = get_data_dir()

    # Create data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"Created data directory: {data_dir}")

    # Create subdirectories for local file storage (QR codes, etc.)
    subdirs = ["upi_qr_codes"]
    for subdir in subdirs:
        subdir_path = os.path.join(data_dir, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path, exist_ok=True)
            print(f"Created subdirectory: {subdir_path}")

    print("Data directory setup complete!")
    print("Note: Configuration data is stored in Firebase Firestore, not in local JSON files.")

if __name__ == "__main__":
    ensure_data_directory()

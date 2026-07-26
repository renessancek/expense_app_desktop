import glob
import os

from app_paths import documents_dir


class Scanner:
    def __init__(self, watch_path=None):
        self.watch_path = watch_path or str(documents_dir() / "BankStatements")
        os.makedirs(self.watch_path, exist_ok=True)

    def scan_for_csvs(self):
        pattern = os.path.join(self.watch_path, "*.csv")
        return glob.glob(pattern)

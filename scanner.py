import os
import glob

class Scanner:
    def __init__(self, watch_path=None):
        if watch_path is None:
            self.watch_path = os.path.expanduser('~/Documents/BankStatements')
        else:
            self.watch_path = watch_path
        
        if not os.path.exists(self.watch_path):
            os.makedirs(self.watch_path)

    def scan_for_csvs(self):
        pattern = os.path.join(self.watch_path, "*.csv")
        return glob.glob(pattern)

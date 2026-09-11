# Expense App Desktop

A local, browser-free desktop app for importing, categorizing, and reviewing bank-statement CSV files. The UI is native PySide6 — no browser and no local web server.

## Features

- Scan CSV files from `Documents/BankStatements` or import them manually
- Transaction table with sorting, pagination, and category, month, and live text filters
- Import, create, delete, and restore rules from backups
- Sum categories and export them as an Excel file

## Windows 10/11

### Set up and run

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\start_expense_app.ps1
```

For a Start menu entry:

```powershell
.\install_windows_app.ps1
```

To start the app at login:

```powershell
.\install_windows_app.ps1 -EnableAutostart
```

To remove the Start menu and autostart shortcuts:

```powershell
.\uninstall_windows_app.ps1
```

The app opens a native desktop window. No browser is started.

## Ubuntu/Linux

### Set up and run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
chmod +x start_expense_app.sh install_ubuntu_app.sh
./start_expense_app.sh
```

For an application-menu entry:

```bash
./install_ubuntu_app.sh
```

For autostart, add the absolute path to `start_expense_app.sh` under **Startup Applications** in system settings.

To remove the application-menu entry:

```bash
chmod +x uninstall_ubuntu_app.sh
./uninstall_ubuntu_app.sh
```

On Ubuntu the app also runs natively with PySide6 and does not need a browser or a local web server.

### Optional Tesseract (OCR)

Photos and scanned PDFs need the `tesseract` binary on `PATH` (languages `deu` and `eng`). Digital PDFs with a text layer work without Tesseract.

If the host should not or cannot install Tesseract itself (immutable distros, no `pacman`/`apt`), set it up with Distrobox: [install-tesseract-linux-distrobox.md](install-tesseract-linux-distrobox.md).

## Tests

Application code lives in [`src/`](src/). Unit tests live in [`tests/`](tests/). From the project root, with the virtualenv active:

```bash
python -m unittest discover -s tests -t .
```

On Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

## Build a Windows EXE

After installing dependencies:

```powershell
.\build_windows_exe.ps1
```

The result is `dist\Expense App Desktop\Expense App Desktop.exe`.

## Data

Rules and backups stay in the personal data directory. On Windows that is `%LOCALAPPDATA%\Expense App Desktop`; on Linux `~/.local/share/expense-app-desktop` (or the folder configured via `XDG_DATA_HOME`). The default folder for bank statements is `BankStatements` in the personal Documents folder — on Linux the XDG path is used (for example `~/Dokumente/BankStatements` on German systems, otherwise `~/Documents/BankStatements`).

The app still stores rules internally as `rules.json`. Import accepts JSON **and** CSV, for example a Google Sheets export (File → Download → CSV). A table with `category`/`kategorie` and `keywords`/`keyword` is enough.

Ready-to-import examples live in [`rules/`](rules/): [`rules/rules.json`](rules/rules.json) and [`rules/rules.csv`](rules/rules.csv).

JSON (`rules.json`):

```json
{
  "rules": [
    {
      "category": "Supermarkt",
      "keywords": ["rewe", "aldi", "lidl"]
    },
    {
      "category": "Amazon",
      "keywords": ["amazon"]
    },
    {
      "category": "Internet",
      "keywords": ["telekom", "vodafone"]
    }
  ]
}
```

CSV (`rules.csv`):

```csv
category,keywords
Supermarkt,"rewe, aldi, lidl"
Amazon,amazon
Internet,"telekom, vodafone"
```

Instead of a keywords column, keywords can sit in their own columns, or each row can hold a single keyword. Semicolon-separated German CSV exports work too.

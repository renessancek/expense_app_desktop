# Expense App Desktop

Eine browserfreie, lokale Desktop-Anwendung zum Einlesen, Kategorisieren und Auswerten von Kontoauszugs-CSV-Dateien. Die Oberfläche läuft nativ mit PySide6 – kein Browser und kein lokaler Webserver werden gestartet.

## Funktionen

- CSV-Dateien aus `Dokumente/BankStatements` scannen oder manuell importieren
- Transaktionstabelle mit Sortierung, Paginierung sowie Kategorie-, Monats- und Live-Textsuche
- Regeln importieren, anlegen, löschen und aus Sicherungen wiederherstellen
- Kategorien summieren und als Excel-Datei exportieren

## Windows 10/11

### Einrichten und starten

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\start_expense_app.ps1
```

Für einen Startmenü-Eintrag:

```powershell
.\install_windows_app.ps1
```

Für Autostart bei der Anmeldung:

```powershell
.\install_windows_app.ps1 -EnableAutostart
```

Zum Entfernen der Startmenü- und Autostart-Verknüpfung:

```powershell
.\uninstall_windows_app.ps1
```

Die Anwendung öffnet ein natives Desktop-Fenster. Es wird kein Browser gestartet.

## Ubuntu/Linux

### Einrichten und starten

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
chmod +x start_expense_app.sh install_ubuntu_app.sh
./start_expense_app.sh
```

Für einen Eintrag im Anwendungsmenü:

```bash
./install_ubuntu_app.sh
```

Für Autostart den absoluten Pfad zu `start_expense_app.sh` in den Systemeinstellungen unter **Startup Applications** hinterlegen.

Zum Entfernen des Anwendungsmenü-Eintrags:

```bash
chmod +x uninstall_ubuntu_app.sh
./uninstall_ubuntu_app.sh
```

Auch unter Ubuntu läuft die Anwendung nativ mit PySide6 und benötigt keinen Browser oder lokalen Webserver.

## EXE-Paket erstellen

Nach der Installation der Abhängigkeiten:

```powershell
.\build_windows_exe.ps1
```

Das Ergebnis liegt anschließend unter `dist\Expense App Desktop\Expense App Desktop.exe`.

## Daten

Regeln und Backups bleiben im persönlichen Datenordner. Unter Windows ist das `%LOCALAPPDATA%\Expense App Desktop`; unter Linux `~/.local/share/expense-app-desktop` (oder der über `XDG_DATA_HOME` konfigurierte Ordner). Der Standardordner für Kontoauszüge ist unter Windows `Dokumente/BankStatements`, unter Linux `~/Documents/BankStatements`.
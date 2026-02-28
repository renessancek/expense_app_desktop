# Ubuntu App + Startup Setup Guide

This project can be installed as a normal Ubuntu app entry so you can open and close it from the Applications menu.

## 1) Install dependencies

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Install the app launcher

```bash
chmod +x install_ubuntu_app.sh start_expense_app.sh
./install_ubuntu_app.sh
```

This creates:

`~/.local/share/applications/expense-app-desktop.desktop`

Now search for **Expense App Desktop** in Ubuntu Apps and launch it like any other app.

## 3) Optional: Start automatically on login

1. Open **Startup Applications**.
2. Click **Add**.
3. Name: `Expense App Desktop`
4. Command: `/absolute/path/to/your/project/start_expense_app.sh`
5. Click **Add**.

## 4) Uninstall app launcher

```bash
chmod +x uninstall_ubuntu_app.sh
./uninstall_ubuntu_app.sh
```

## 5) Logs and troubleshooting

Launcher and Streamlit runtime logs are written to:

```bash
~/.cache/expense-app-desktop/launcher.log
```

Log rotation is automatic (max ~5 MB per file, keeps 5 backups as `launcher.log.1` to `launcher.log.5`).

To watch logs live while launching the app:

```bash
tail -f ~/.cache/expense-app-desktop/launcher.log
```

Rules and learned mappings are stored at:

```bash
~/.local/share/expense-app-desktop/rules.json
```

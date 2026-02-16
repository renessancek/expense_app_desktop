# Ubuntu Startup Setup Guide

To have the Expense App Desktop open automatically when you log in to your Ubuntu machine, follow these steps:

## 1. Create a Startup Script
Create a file named `start_expense_app.sh` in the project directory:

```bash
#!/bin/bash
cd /home/ren/Documents/antigravity_projects/expense_app_desktop
streamlit run app.py --server.headless true
```
Make it executable:
`chmod +x /home/ren/Documents/antigravity_projects/expense_app_desktop/start_expense_app.sh`

## 2. Add to Startup Applications
1. Open the **Startup Applications** tool from the Ubuntu application menu.
2. Click **Add**.
3. Name: `Expense App Desktop`
4. Command: `/home/ren/Documents/antigravity_projects/expense_app_desktop/start_expense_app.sh`
5. Comment: `Starts the expense app scanner and UI`
6. Click **Add**.

## Alternative: Using a .desktop file
You can also create a file at `~/.config/autostart/expense_app.desktop`:

```ini
[Desktop Entry]
Type=Application
Exec=/home/ren/Documents/antigravity_projects/expense_app_desktop/start_expense_app.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name[en_US]=Expense App Desktop
Name=Expense App Desktop
Comment[en_US]=Starts the expense app scanner and UI
Comment=Starts the expense app scanner and UI
```

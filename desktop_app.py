"""Native, browser-free desktop entry point for Expense App Desktop."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QTimer, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFormLayout,
    QGridLayout, QGroupBox, QHeaderView, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox,
    QSplitter, QTabWidget, QTableView, QVBoxLayout, QWidget,
)

from categorizer import Categorizer
from expense_data import ExpenseDataStore
from parser import Parser
from scanner import Scanner


def statistics_for_categories(totals, categories):
    """Return the category totals selected for an export."""
    return totals[totals["Category"].isin(categories)].copy()


DEFAULT_UNSELECTED_EXPORT_CATEGORIES = {"Abhebung", "Investments", "Firma", "Privat", "Paypal"}


class DataFrameModel(QAbstractTableModel):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.frame = pd.DataFrame(columns=columns)

    def set_frame(self, frame):
        self.beginResetModel()
        self.frame = frame.reindex(columns=self.columns).reset_index(drop=True)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.frame)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.TextAlignmentRole):
            return None
        value = self.frame.iat[index.row(), index.column()]
        column = self.columns[index.column()]
        if role == Qt.TextAlignmentRole and column == "Amount":
            return Qt.AlignRight | Qt.AlignVCenter
        if pd.isna(value):
            return ""
        if column == "Amount":
            return f"{float(value):.2f} €"
        if column == "Date" and hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return str(value)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columns[section]
        return super().headerData(section, orientation, role)


class ExpenseWindow(QMainWindow):
    PAGE_SIZE = 20
    TABLE_COLUMNS = ["Date", "Description", "Amount", "Category", "Source", "File"]
    FRAME_COLUMNS = ["date", "description", "amount", "category", "source", "file"]
    TRANSACTION_COLUMN_LIMITS = {
        "Date": (105, 135),
        "Description": (230, 700),
        "Amount": (105, 135),
        "Category": (150, 260),
        "Source": (140, 240),
        "File": (170, 340),
    }

    def __init__(self):
        super().__init__()
        self.scanner, self.parser, self.categorizer = Scanner(), Parser(), Categorizer()
        self.store = ExpenseDataStore(self.scanner, self.parser, self.categorizer)
        self.page, self.sort_column, self.sort_descending = 1, "date", True
        self.setWindowTitle("Expense App Desktop")
        self.resize(1300, 820)
        self._build_ui()
        self.reload_transactions()

    def _build_ui(self):
        tabs = QTabWidget()
        tabs.addTab(self._transaction_tab(), "Transactions")
        tabs.addTab(self._category_tab(), "Categories")
        tabs.addTab(self._statistics_tab(), "Statistics")
        self.setCentralWidget(tabs)
        refresh = QAction("Scan for new CSVs", self)
        refresh.triggered.connect(self.reload_transactions)
        self.menuBar().addAction(refresh)

    def _transaction_tab(self):
        page = QWidget(); layout = QVBoxLayout(page)
        self.scan_label = QLabel(); layout.addWidget(self.scan_label)
        controls = QHBoxLayout()
        import_button = QPushButton("Import CSV files…"); import_button.clicked.connect(self.choose_csv_files)
        scan_button = QPushButton("Scan folder"); scan_button.clicked.connect(self.reload_transactions)
        self.category_filter, self.month_filter = QComboBox(), QComboBox()
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Search descriptions as you type")
        reset = QPushButton("Show all transactions"); reset.clicked.connect(self.reset_filters)
        for label, widget in (("Category", self.category_filter), ("Month", self.month_filter), ("Search", self.search_input)):
            controls.addWidget(QLabel(label)); controls.addWidget(widget, 1 if label == "Search" else 0)
        controls.addWidget(import_button); controls.addWidget(scan_button); controls.addWidget(reset); layout.addLayout(controls)
        self.category_filter.currentTextChanged.connect(self.filters_changed)
        self.month_filter.currentTextChanged.connect(self.filters_changed)
        self.search_input.textChanged.connect(self.filters_changed)
        metrics = QHBoxLayout(); self.total_label, self.spent_label, self.categorized_label = QLabel(), QLabel(), QLabel()
        for label in (self.total_label, self.spent_label, self.categorized_label): metrics.addWidget(label)
        layout.addLayout(metrics)
        self.result_label = QLabel(); layout.addWidget(self.result_label)
        self.transaction_model = DataFrameModel(self.TABLE_COLUMNS, self)
        self.transaction_table = QTableView(); self.transaction_table.setModel(self.transaction_model)
        self.transaction_table.setSelectionBehavior(QTableView.SelectRows); self.transaction_table.setEditTriggers(QTableView.NoEditTriggers)
        self.transaction_table.setTextElideMode(Qt.ElideRight)
        header = self.transaction_table.horizontalHeader()
        header.setStretchLastSection(False); header.setMinimumSectionSize(80)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.sectionClicked.connect(self.change_sort)
        self.transaction_table.doubleClicked.connect(self.show_transaction_details); layout.addWidget(self.transaction_table, 1)
        pagination = QHBoxLayout(); self.previous = QPushButton("Previous"); self.next = QPushButton("Next")
        self.page_spin = QSpinBox(); self.page_spin.setMinimum(1); self.page_label = QLabel()
        self.previous.clicked.connect(lambda: self.set_page(self.page - 1)); self.next.clicked.connect(lambda: self.set_page(self.page + 1)); self.page_spin.valueChanged.connect(self.set_page)
        for widget in (self.previous, QLabel("Page"), self.page_spin, self.page_label, self.next): pagination.addWidget(widget)
        pagination.addStretch(); layout.addLayout(pagination)
        self.report_model = DataFrameModel(["File", "status", "rows_read", "imported_expenses", "skipped_non_expenses", "details"], self)
        report_view = QTableView(); report_view.setModel(self.report_model); report_view.setMaximumHeight(155)
        group = QGroupBox("Import results"); group_layout = QVBoxLayout(group); group_layout.addWidget(report_view); layout.addWidget(group)
        return page

    def _category_tab(self):
        page = QWidget(); layout = QVBoxLayout(page)
        controls = QGridLayout(); self.rule_category, self.rule_keywords = QLineEdit(), QLineEdit()
        add = QPushButton("Add / merge rule"); delete = QPushButton("Delete selected rule"); restore = QPushButton("Restore latest backup"); import_rules = QPushButton("Import rules.json…")
        controls.addWidget(QLabel("Category"), 0, 0); controls.addWidget(self.rule_category, 0, 1); controls.addWidget(QLabel("Keywords (comma separated)"), 1, 0); controls.addWidget(self.rule_keywords, 1, 1)
        controls.addWidget(add, 2, 0); controls.addWidget(delete, 2, 1); controls.addWidget(restore, 2, 2); controls.addWidget(import_rules, 2, 3); layout.addLayout(controls)
        add.clicked.connect(self.add_rule); delete.clicked.connect(self.delete_rule); restore.clicked.connect(self.restore_rules); import_rules.clicked.connect(self.import_rules_file)
        self.rule_model = DataFrameModel(["Category", "Keywords"], self); self.rule_table = QTableView(); self.rule_table.setModel(self.rule_model); self.rule_table.clicked.connect(self.select_rule); layout.addWidget(self.rule_table)
        return page

    def _statistics_tab(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.addWidget(QLabel("Category totals for all imported expenses"))
        self.stats_model = DataFrameModel(["Category", "Total spent (€)"], self)
        self.statistics_table = QTableView(); self.statistics_table.setModel(self.stats_model); self.statistics_table.setMaximumHeight(240)
        layout.addWidget(self.statistics_table)
        export_selection = QGroupBox("Categories to export")
        export_selection_layout = QVBoxLayout(export_selection)
        export_selection_layout.setContentsMargins(9, 7, 9, 7); export_selection_layout.setSpacing(5)
        export_selection_layout.addWidget(QLabel("Select the category totals to include in the Excel file:"))
        self.export_category_checkboxes = []
        self.export_category_grid = QWidget(); self.export_category_grid_layout = QGridLayout(self.export_category_grid)
        self.export_category_grid_layout.setContentsMargins(4, 2, 4, 2); self.export_category_grid_layout.setHorizontalSpacing(18); self.export_category_grid_layout.setVerticalSpacing(2); self.export_category_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.export_category_scroll = QScrollArea(); self.export_category_scroll.setWidgetResizable(True); self.export_category_scroll.setWidget(self.export_category_grid)
        export_selection_layout.addWidget(self.export_category_scroll, 1)
        selection_controls = QHBoxLayout()
        select_all = QPushButton("Select all"); clear_all = QPushButton("Select none")
        select_all.clicked.connect(lambda: self._set_category_checks(Qt.Checked))
        clear_all.clicked.connect(lambda: self._set_category_checks(Qt.Unchecked))
        selection_controls.addWidget(select_all); selection_controls.addWidget(clear_all); selection_controls.addStretch()
        export_selection_layout.addLayout(selection_controls)
        layout.addWidget(export_selection, 1)
        export = QPushButton("Export selected category totals to Excel…"); export.clicked.connect(self.export_statistics); layout.addWidget(export); return page

    def choose_csv_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Import bank statements", "", "CSV files (*.csv)")
        if files: self.reload_transactions(files)

    def reload_transactions(self, selected_files=None):
        self.store.reload(selected_files); self.scan_label.setText(f"Scanning folder: {self.scanner.watch_path}")
        self._populate_filters(); self.page = 1; self.refresh_transactions(); self.refresh_rules(); self.refresh_statistics()

    def _populate_filters(self):
        category, month = self.category_filter.currentText() or "All", self.month_filter.currentText() or "All"
        self.category_filter.blockSignals(True); self.month_filter.blockSignals(True)
        self.category_filter.clear(); self.category_filter.addItems(["All"] + self.categorizer.get_all_categories())
        self.month_filter.clear(); self.month_filter.addItems(["All"] + self.store.months())
        self.category_filter.setCurrentText(category if category in [self.category_filter.itemText(i) for i in range(self.category_filter.count())] else "All")
        self.month_filter.setCurrentText(month if month in [self.month_filter.itemText(i) for i in range(self.month_filter.count())] else "All")
        self.category_filter.blockSignals(False); self.month_filter.blockSignals(False)

    def filters_changed(self, *_): self.page = 1; self.refresh_transactions()
    def reset_filters(self):
        self.category_filter.setCurrentText("All"); self.month_filter.setCurrentText("All"); self.search_input.clear(); self.filters_changed()
    def set_page(self, page): self.page = page; self.refresh_transactions()

    def change_sort(self, section):
        column = self.FRAME_COLUMNS[section]
        self.sort_descending = not self.sort_descending if column == self.sort_column else column in ("date", "amount")
        self.sort_column = column; self.page = 1; self.refresh_transactions()

    def refresh_transactions(self):
        frame = self.store.filtered(self.category_filter.currentText() or "All", self.month_filter.currentText() or "All", self.search_input.text())
        if not frame.empty: frame = frame.sort_values(self.sort_column, ascending=not self.sort_descending, kind="stable")
        total = len(frame); pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE); self.page = min(max(1, self.page), pages)
        self.page_spin.blockSignals(True); self.page_spin.setRange(1, pages); self.page_spin.setValue(self.page); self.page_spin.blockSignals(False)
        start = (self.page - 1) * self.PAGE_SIZE; display = frame.iloc[start:start + self.PAGE_SIZE]
        shown = display.rename(columns=dict(zip(self.FRAME_COLUMNS, self.TABLE_COLUMNS)))
        self.transaction_model.set_frame(shown); self._schedule_transaction_column_resize(); self.result_label.setText(f"Showing {start + 1 if total else 0}–{min(start + self.PAGE_SIZE, total)} of {total} transactions")
        self.page_label.setText(f"of {pages}"); self.previous.setEnabled(self.page > 1); self.next.setEnabled(self.page < pages)
        full = self.store.dataframe; self.total_label.setText(f"Total transactions: {len(full)}"); self.spent_label.setText(f"Total spent: {abs(full.loc[full['amount'] < 0, 'amount'].sum()):.2f} €")
        self.categorized_label.setText(f"Categorized: {(full['category'] != 'Sonstiges').sum()}")
        self.report_model.set_frame(self.store.reports_dataframe())

    def _schedule_transaction_column_resize(self):
        """Resize transaction columns after the table has applied its new data and layout."""
        QTimer.singleShot(0, self._resize_transaction_columns)

    def _resize_transaction_columns(self):
        """Fit visible content while bounding long text columns and using spare space."""
        table = self.transaction_table
        available_width = table.viewport().width()
        widths = []
        for index, column in enumerate(self.TABLE_COLUMNS):
            minimum, maximum = self.TRANSACTION_COLUMN_LIMITS[column]
            content_width = table.sizeHintForColumn(index) + 18
            widths.append(max(minimum, min(content_width, maximum)))

        remaining_width = max(0, available_width - sum(widths))
        for column in ("Description", "File", "Source"):
            if not remaining_width:
                break
            index = self.TABLE_COLUMNS.index(column)
            maximum = self.TRANSACTION_COLUMN_LIMITS[column][1]
            extra_width = min(remaining_width, maximum - widths[index])
            widths[index] += extra_width
            remaining_width -= extra_width

        for index, width in enumerate(widths):
            table.setColumnWidth(index, width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "transaction_table"):
            self._schedule_transaction_column_resize()
    def show_transaction_details(self, index):
        row = self.transaction_model.frame.iloc[index.row()]
        QMessageBox.information(self, "Transaction", f"Description: {row['Description']}\nCategory: {row['Category']}\nSource: {row['Source']} ({row['File']})")

    def refresh_rules(self):
        rules = pd.DataFrame([{"Category": r["category"], "Keywords": ", ".join(r["keywords"])} for r in self.categorizer.rules])
        self.rule_model.set_frame(rules)

    def select_rule(self, index):
        row = self.rule_model.frame.iloc[index.row()]; self.rule_category.setText(row["Category"]); self.rule_keywords.setText(row["Keywords"])

    def add_rule(self):
        category = self.rule_category.text().strip(); keywords = [k.strip().lower() for k in self.rule_keywords.text().split(",") if k.strip()]
        if not category or not keywords: return QMessageBox.warning(self, "Missing data", "Enter a category and at least one keyword.")
        self.categorizer.add_rule(keywords, category); self.reload_transactions()

    def delete_rule(self):
        category = self.rule_category.text().strip()
        if category: self.categorizer.delete_rule(category); self.reload_transactions()

    def restore_rules(self):
        success, message = self.categorizer.restore_latest_backup(); QMessageBox.information(self, "Restore rules", message)
        if success: self.reload_transactions()

    def import_rules_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import rules", "", "JSON files (*.json)")
        if not path: return
        try:
            self.categorizer.import_rules(json.loads(Path(path).read_text(encoding="utf-8"))); self.reload_transactions()
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error: QMessageBox.critical(self, "Import failed", str(error))

    def refresh_statistics(self):
        frame = self.store.dataframe
        if frame.empty:
            self.stats_model.set_frame(pd.DataFrame(columns=["Category", "Total spent (€)"]))
        else:
            expenses = frame[frame["amount"] < 0].copy(); expenses["amount"] = expenses["amount"].abs()
            totals = expenses.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False).rename(columns={"category": "Category", "amount": "Total spent (€)"})
            self.stats_model.set_frame(totals)
        self._refresh_export_category_selection()

    def _refresh_export_category_selection(self):
        """Keep existing export choices while selecting newly available categories by default."""
        previous_states = {checkbox.property("category_name"): checkbox.isChecked() for checkbox in self.export_category_checkboxes}
        while self.export_category_grid_layout.count():
            item = self.export_category_grid_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.export_category_checkboxes = []
        categories = sorted((str(category) for category in self.stats_model.frame["Category"]), key=str.casefold)
        columns = 3
        rows = max(1, (len(categories) + columns - 1) // columns)
        for index, category in enumerate(categories):
            checkbox = QCheckBox(category.replace("&", "&&"))
            checkbox.setProperty("category_name", category)
            checkbox.setChecked(previous_states.get(category, category not in DEFAULT_UNSELECTED_EXPORT_CATEGORIES))
            self.export_category_checkboxes.append(checkbox)
            self.export_category_grid_layout.addWidget(checkbox, index % rows, index // rows)
        for column in range(columns):
            self.export_category_grid_layout.setColumnStretch(column, 1)

    def _selected_export_categories(self):
        return [checkbox.property("category_name") for checkbox in self.export_category_checkboxes if checkbox.isChecked()]

    def export_statistics(self):
        categories = self._selected_export_categories()
        if not categories:
            QMessageBox.warning(self, "No categories selected", "Select at least one category to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export category totals", "expense_report.xlsx", "Excel files (*.xlsx)")
        if not path:
            return
        try:
            statistics_for_categories(self.stats_model.frame, categories).to_excel(path, index=False)
        except OSError as error:
            QMessageBox.critical(self, "Export failed", str(error))

    def _set_category_checks(self, check_state):
        for checkbox in self.export_category_checkboxes:
            checkbox.setChecked(check_state == Qt.Checked)


def main():
    app = QApplication(sys.argv); app.setApplicationName("Expense App Desktop")
    window = ExpenseWindow(); window.showMaximized(); return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

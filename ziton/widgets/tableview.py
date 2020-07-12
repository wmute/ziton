"""
Tableview Widget, represents all of our file data.
"""
import logging
import pathlib
import subprocess
from datetime import datetime

from PySide2.QtCore import QItemSelectionModel, Qt, Signal, Slot
from PySide2.QtSql import QSqlTableModel
from PySide2.QtWidgets import QAbstractItemView, QHeaderView, QTableView

from ziton.database import dbrecord_from_path
from ziton.widgets.contextmenu import RightClickMenu
from ziton.widgets.icon_provider import IconProvider

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class TableModel(QSqlTableModel):
    """Standard Sql model with custom icons for the filename column."""

    def __init__(self):
        QSqlTableModel.__init__(self)
        # initiate model
        self.setTable("files")
        self.select()
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.setHeaderData(0, Qt.Horizontal, "Filename")
        self.setHeaderData(1, Qt.Horizontal, "Filepath")
        self.setHeaderData(2, Qt.Horizontal, "Filesize")
        self.setHeaderData(3, Qt.Horizontal, "Last Modified")
        self.icon_provider = IconProvider()
        self.setEditStrategy(QSqlTableModel.OnFieldChange)

    def data(self, index, role=Qt.DisplayRole):
        "returns data for the given index."
        if index.column() == 0:
            if role == Qt.DisplayRole:
                return QSqlTableModel.data(self, index, role)
            if role == Qt.DecorationRole:
                idx = index.sibling(index.row(), 1)
                path = super(TableModel, self).data(idx)
                return self.icon_provider.icon(path)
        # filesize
        if index.column() == 2:
            if role == Qt.DisplayRole:
                value = QSqlTableModel.data(self, index, role)
                return "{:,} KB".format(int(value / 1000))
        # file modification date
        if index.column() == 3:
            if role == Qt.DisplayRole:
                value = QSqlTableModel.data(self, index, role)
                return datetime.fromtimestamp(value).strftime("%Y-%m-%d-%H:%M")
        return QSqlTableModel.data(self, index, role)


class Tableview(QTableView):
    """Subclass of QTableView to manage keyPressEvents."""

    tabPressed = Signal()

    def __init__(self):
        """initialises the Tableview class."""
        QTableView.__init__(self)
        # model
        self._model = TableModel()
        # set widget parameters
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setModel(self._model)
        self.setColumnHidden(4, True)
        self.show()

    @Slot(str)
    def update_filter(self, pattern):
        "updates regex filter when searchtext changes."
        self.model().setFilter("filename like '%{}%'".format(pattern))

    def update_model(self):
        "updates the entire model."
        self.setModel(TableModel())

    def selected_file_path(self):
        """Get path of currently selected file."""
        idx = self.selectionModel().currentIndex()
        fp_idx = idx.siblingAtColumn(1)
        fpath = self.model().data(fp_idx)
        return fpath

    def open_selected_file(self):
        """open file with default application."""
        fpath = self.selected_file_path()
        if fpath:
            subprocess.run(["xdg-open", fpath], check=False)

    def keyPressEvent(self, event):
        """custom key events, primarily to handle file execution"""
        key = event.key()
        if key == Qt.Key_Tab:
            self.tabPressed.emit()
        elif key == Qt.Key_Up:
            idx = self.selectionModel().currentIndex()
            new_idx = 0 if idx.row() == 0 else idx.siblingAtRow(idx.row() - 1)
            self.selectionModel().setCurrentIndex(
                new_idx, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
            )
        elif key == Qt.Key_Down:
            idx = self.selectionModel().currentIndex()
            new_idx = idx.siblingAtRow(idx.row() + 1)
            self.selectionModel().setCurrentIndex(
                new_idx, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
            )
        elif key == Qt.Key_Return:
            self.open_selected_file()

    def mouseDoubleClickEvent(self, event):
        "Handle doubleclick events."
        btn = event.button()
        pos = event.globalPos()
        if btn == Qt.MouseButton.LeftButton:
            self.open_selected_file()
        elif btn == Qt.MouseButton.RightButton:
            menu = RightClickMenu(self.selected_file_path(), pos)
            menu.exec_(pos)
            self.update_model()

    def mousePressEvent(self, event):
        "Handle single click events."
        btn = event.button()
        pos = event.globalPos()
        rel_pos = event.pos()
        if btn == Qt.MouseButton.LeftButton:
            idx = self.indexAt(rel_pos)
            self.selectRow(idx.row())
        elif btn == Qt.MouseButton.RightButton:
            menu = RightClickMenu(self.selected_file_path(), pos)
            menu.exec_(pos)
            self.update_model()

    @Slot(str)
    def insert_record(self, filepath):
        """insert new record in active DB."""
        # check if file exists
        if pathlib.Path(filepath).exists():
            new_db_entry = dbrecord_from_path(filepath)
            LOGGER.info(f"inserting new table row... {filepath}")
            new_record = self._model.record()
            new_record.setValue("filename", new_db_entry.filename)
            new_record.setValue("filepath", new_db_entry.filepath)
            new_record.setValue("size", new_db_entry.size)
            new_record.setValue("modified", new_db_entry.modified)
            self._model.insertRecord(-1, new_record)
            self.update_model()

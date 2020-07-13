"""
Central entry point for the application.
"""

import sys

from PySide2.QtCore import QCoreApplication, Qt, Signal, Slot
from PySide2.QtGui import QIcon
from PySide2.QtSql import QSqlDatabase
from PySide2.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget

import ziton.monitor as monitor
from ziton.config import database_path, included_directories, is_indexing_enabled
from ziton.widgets.entries_trayicon import TrayEntryInfo
from ziton.widgets.menubar import Menubar
from ziton.widgets.tableview import Tableview

from . import STYLESHEET_PATH, LOGO_PATH


# TODO: Iron out bugs in live file monitoring, implement file deletion signal


class Mainwindow(QWidget):
    """Central widget and entrypoint for the program."""

    selChanged = Signal(str)

    def __init__(self):
        QWidget.__init__(self)
        # connect to existing DB
        self.database = QSqlDatabase.addDatabase("QSQLITE")
        self.database.setDatabaseName(database_path())
        self.database.open()
        # start monitoring the filesystem for changes
        if is_indexing_enabled():
            self.watch = monitor.Worker(self)
            self.watch.fileCreated.connect(self.file_created)
            self.watch.start()
        # widgets
        self.searchbar = QLineEdit()
        self.menubar = Menubar()
        self.trayinfo = TrayEntryInfo()
        self.view = Tableview()

        # set layout
        self.central_layout = QVBoxLayout()
        self.central_layout.addWidget(self.menubar)
        self.central_layout.addWidget(self.searchbar)
        self.central_layout.addWidget(self.view)
        self.central_layout.addWidget(self.trayinfo)
        self.setLayout(self.central_layout)

        # signals
        self.searchbar.textChanged.connect(self.view.update_filter)
        self.view.selectionModel().selectionChanged.connect(self.update_tray)
        self.view.tabPressed.connect(self.focus_searchbar)
        self.selChanged.connect(self.trayinfo.update_selected_text)
        self.menubar.dbUpdated.connect(self.trayinfo.update_selected_text)
        self.menubar.dbUpdated.connect(self.trayinfo.update_filecount)
        self.menubar.dbUpdated.connect(self.reload_db_model_and_view)

    def update_tray(self, item):
        """Update the tray information when selection has changed."""
        indexes = item.indexes()
        # get first column that contains the file's name and update the tray
        name = self.view.model().data(indexes[0])
        self.selChanged.emit(name)

    @Slot()
    def focus_searchbar(self):
        "puts searchbar into focus."
        self.searchbar.setFocus()

    @Slot()
    def reload_db_model_and_view(self):
        "reloads entire database model and updates view."
        self.database.close()
        self.database.open()
        self.view.update_model()

    def file_created(self, filepath):
        "Consume inotify file creation event."
        self.view.insert_record(filepath)


def main():
    "program entrypoint."
    included_directories()
    with open(STYLESHEET_PATH, "r") as infile:
        stylesheet = infile.read()

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    app.setWindowIcon(QIcon(str(LOGO_PATH)))
    app.setApplicationDisplayName("Ziton")

    widget = Mainwindow()
    widget.resize(1200, 800)
    widget.show()

    sys.exit(app.exec_())

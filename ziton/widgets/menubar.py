"""
Widget that represents the menubar.
"""
import logging

from PySide2.QtCore import QCoreApplication, QThread, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMenu, QMenuBar

from .. import TRASH_ICON
from .. import database as db
from .icon_provider import IconProvider
from .preferences import PreferenceDialog

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


# TODO: find a better way to rebuild bookmarks widget on data change.


class Worker(QThread):
    """Qt Worker Thread, responsible for handling one inotify thread."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        db.build_database()
        self.parent().update_finished()
        LOGGER.info("db update finished!")


class Menubar(QMenuBar):
    """Menubar widget."""

    dbUpdated = Signal(str)

    def __init__(self):
        """Initialises the menu bar."""
        # data
        self.bookmarks = db.get_bookmarks()
        self.icon_provider = IconProvider()
        # widgets
        QMenuBar.__init__(self)
        self.file_menu = QMenu("File")
        self.edit_menu = QMenu("Edit")
        self.bookmark_menu = QMenu("Bookmarks")

        self.file_menu.addAction("Update Database", self.rebuild_btn_clicked)
        self.file_menu.addAction("Quit", QCoreApplication.quit)
        self.edit_menu.addAction("Preferences", self.preferences_action_clicked)

        self.addMenu(self.file_menu)
        self.addMenu(self.edit_menu)
        self.addMenu(self.bookmark_menu)

        self.populate_bookmark_menu()
        self.bookmark_menu.addSeparator()
        self.bookmark_menu.addAction(
            QIcon(TRASH_ICON),
            "Delete Bookmarks",
            self.delete_bookmarks_clicked,
        )

    def populate_bookmark_menu(self):
        """Populate the bookmark dropdown menu"""
        for name, path in self.bookmarks:
            icn = self.icon_provider.icon(path)
            self.bookmark_menu.addAction(icn, f"{name}")

    def update_finished(self):
        """Update finished signal."""
        self.dbUpdated.emit("Database updated")

    def rebuild_btn_clicked(self):
        """Update the entire database."""
        self.dbUpdated.emit("Updating DB...")
        self.thread = Worker(self)
        self.thread.start()

    def preferences_action_clicked(self):
        """Preference dialog button click event."""
        self.preferences = PreferenceDialog()

    def delete_bookmarks_clicked(self):
        """Deletes all bookmarks from the DB and clears the menu."""
        db.delete_bookmarks()

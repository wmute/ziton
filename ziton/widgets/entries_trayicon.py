"""
Widget that represents the main view's info tray.
"""

from PySide2.QtCore import Slot
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QSpacerItem,
                               QWidget)

from ziton.database import number_of_rows


class TrayEntryInfo(QWidget):
    """Represents the tray icon at the bottom that shows the number
     of entries in the database."""

    def __init__(self):
        QWidget.__init__(self)
        self.layout = QHBoxLayout()
        # DB icon
        self.db_icon_label = QLabel()
        self.db_icon_label.setMaximumSize(16, 16)
        self.db_icon_label.setText("")
        self.db_icon_label.setPixmap(QPixmap("resources/database.png"))
        self.db_icon_label.setScaledContents(True)
        # label for file count
        self.filecount = QLabel()
        self.update_filecount()
        self.spacer_item = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        # currently selected file
        self.selected = QLabel()
        self.selected.setText("")
        # set layout
        self.layout.addWidget(self.selected)
        self.layout.addItem(self.spacer_item)
        self.layout.addWidget(self.db_icon_label)
        self.layout.addWidget(self.filecount)
        self.setLayout(self.layout)

    @Slot(str)
    def update_selected_text(self, text):
        "Visually highlight currently selected row."
        self.selected.setText(text)

    @Slot()
    def update_filecount(self):
        "Updates filecount label in the main view."
        rows = number_of_rows()
        self.filecount.setText(f"{rows:,} Items")

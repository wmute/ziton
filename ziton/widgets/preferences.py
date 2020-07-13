"""
Widget that represents the preferences submenu.
"""
from PySide2.QtCore import QFile, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QCheckBox, QListWidget, QListWidgetItem, QPushButton

import ziton.config as cfg

from ziton import PREFERENCES_PATH


class PreferenceDialog:
    "Represents the settings dialog."

    def __init__(self):
        "inits the settingsd dialog."
        # load ui file
        ui_file = QFile(PREFERENCES_PATH)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        # widgets
        self.add_item_btn = self.window.findChild(QPushButton, "add_item")
        self.remove_item_btn = self.window.findChild(QPushButton, "remove_item")
        self.directory_list = self.window.findChild(QListWidget, "included_files")
        self.exluded_live_dirs = self.window.findChild(QListWidget, "excluded_dirs")
        self.update_startup_box = self.window.findChild(QCheckBox, "update_startup_box")
        self.live_indexing_box = self.window.findChild(QCheckBox, "live_indexing_box")
        self.hidden_indexing_box = self.window.findChild(
            QCheckBox, "hidden_indexing_box"
        )
        self.save_btn = self.window.findChild(QPushButton, "save_btn")
        self.close_btn = self.window.findChild(QPushButton, "close_btn")
        # signals
        self.add_item_btn.clicked.connect(self.insert_row)
        self.remove_item_btn.clicked.connect(self.remove_selected)
        self.save_btn.clicked.connect(self.save_configuration)
        self.close_btn.clicked.connect(self.window.accept)
        # load existing config
        for directory in cfg.included_directories():
            self.insert_row(directory)
        self.update_startup_box.setChecked(cfg.start_updated_enabled())
        self.live_indexing_box.setChecked(cfg.is_indexing_enabled())
        self.hidden_indexing_box.setChecked(cfg.hidden_files_enabled())

        self.window.exec_()

    def insert_row(self, path=False):
        "Insert a new row."
        path = "<new directory>" if not path else path
        new_item = QListWidgetItem()
        new_item.setText(path)
        new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
        i = self.directory_list.count()
        self.directory_list.insertItem(i, new_item)

    def remove_selected(self):
        "Removes a row."
        selected = self.directory_list.selectedItems()
        for sel in selected:
            self.directory_list.takeItem(self.directory_list.row(sel))

    def save_configuration(self):
        "writes configuraton changes to disk."
        dirs = [
            self.directory_list.item(i).text()
            for i in range(self.directory_list.count())
        ]
        current_config = {
            "included_directories": dirs,
            "index_on_startup": self.update_startup_box.isChecked(),
            "live_updates": self.live_indexing_box.isChecked(),
            "hidden_files": self.hidden_indexing_box.isChecked(),
            "database_path": cfg.database_path(),
            "excluded": cfg.excluded_files(),
        }
        cfg.save_configuration(current_config)
        # close the dialog
        self.window.accept()

    def close_dialog(self):
        "Closes the dialog popup."
        self.window.emit.accepted()

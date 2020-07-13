from pathlib import Path

# static resource filepaths
FILE_DIR = Path(__file__).parent.absolute()
RESOURCE_DIR = FILE_DIR.joinpath("resources")
STYLESHEET_PATH = str(RESOURCE_DIR.joinpath("stylesheet.qss"))
LOGO_PATH = str(RESOURCE_DIR.joinpath("logo.png"))
DATABASE_ICON = str(Path(RESOURCE_DIR).joinpath("icons", "database.png"))
TRASH_ICON = str(Path(RESOURCE_DIR).joinpath("icons", "trash.png"))
PREFERENCES_PATH = str(Path(RESOURCE_DIR).joinpath("ui", "preferences.ui"))
FOLDER_ICON_PATH = str(RESOURCE_DIR.joinpath("icons", "folder.png"))
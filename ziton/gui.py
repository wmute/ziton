def start():
    from . import config as cfg

    cfg.validate_config_file()
    from . import database as db

    db.validate_database()
    if cfg.start_updated_enabled():
        db.build_database()

    from .app import main

    main()

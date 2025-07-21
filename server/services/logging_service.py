from logging import getLogger, INFO, StreamHandler, FileHandler, Formatter

def get_main_logger():
    logger = getLogger("main")
    logger.setLevel(INFO)
    handler1 = StreamHandler()
    handler2 = FileHandler(filename="./log.log")
    formatter = Formatter(
        "%(levelname)s [main] %(module)s:%(lineno)d | %(message)s"
    )
    handler1.setFormatter(formatter)
    handler2.setFormatter(formatter)
    logger.addHandler(handler1)
    logger.addHandler(handler2)
    return logger

main_logger = get_main_logger()

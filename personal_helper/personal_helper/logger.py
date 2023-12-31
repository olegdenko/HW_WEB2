import logging

log_format = (
    "%(asctime)s [%(levelname)s] - %(name)s - %(funcName)s(%(lineno)d) - %(message)s"
)

file_handler = logging.FileHandler("helper.logs")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter(log_format))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.NOTSET)
stream_handler.setFormatter(logging.Formatter(log_format))


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    # logger.addHandler(stream_handler)
    return logger


if __name__ == "__maim__":
    ...
    # print(get_logger())

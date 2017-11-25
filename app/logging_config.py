import logging


def config_log_system(loggine_level, log_file_name):
    logging.basicConfig(level=loggine_level,
        format='%(asctime)s %(filename)s [line: %(lineno)d] %(levelname)s %(message)s',
        datefmt='%a, %d, %b %Y %H: %M: %S',
        filename=log_file_name)

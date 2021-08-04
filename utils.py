import logging

def get_logger(logger_name, logger_file, log_level=logging.INFO):
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=log_level, format=log_format, datefmt='%y-%m-%d_%H:%M', filename=logger_file, filemode='w')
    formatter = logging.Formatter(log_format)
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(formatter)
    logging.getLogger(logger_name).addHandler(console)

    return logging.getLogger(logger_name)
import logging
log_format = "%(name)s - %(asctime)s - %(levelname)s - %(filename)s at line %(lineno)s:\n%(message)s"
logging.basicConfig(filename="logs.log", filemode="w",
                    level="DEBUG", format=log_format)

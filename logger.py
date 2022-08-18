import logging

logging.basicConfig(format='%(asctime)s %(threadName)s %(levelname)s %(message)s', filemode='w', filename="logs.log")
logger = logging.getLogger()
logger.setLevel(logging.INFO)



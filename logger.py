import logging, watchtower, boto3
from credentials import accountid
from utils.auth import assume_role
from datetime import datetime

logging.basicConfig(format='%(asctime)s %(threadName)s %(levelname)s %(message)s', filemode='w', filename="logs.log")
logger = logging.getLogger()
credentials = assume_role()
logger.info("credentials")
logger.info(credentials)
opslyft_boto3_client = boto3.client(
    'logs',
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken'],
)
logger.addHandler(watchtower.CloudWatchLogHandler(boto3_client=opslyft_boto3_client,log_group_name=f"{accountid}-prometheus-logs",log_stream_name=f"{accountid}_prometheus_logs_{datetime.today().strftime('%Y-%m-%d')}"))
logger.setLevel(logging.INFO)



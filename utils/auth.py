import  boto3
from credentials import accountid, unique_id

master_account_id = '612488371952'

def assume_role():
    sts_client = boto3.client('sts')
    assumed_role_object=sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{master_account_id}:role/prometheus-roles-{accountid}/prometheus-{accountid}-{unique_id}",
        RoleSessionName="AssumeRoleSession1"
    )
    credentials=assumed_role_object['Credentials']
    return credentials;
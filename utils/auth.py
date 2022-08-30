import  boto3
from credentials import accountid

def assume_role():
    sts_client = boto3.client('sts')
    assumed_role_object=sts_client.assume_role(
        RoleArn=f"arn:aws:iam::544089724024:role/{accountid}-prometheus-role",
        RoleSessionName="AssumeRoleSession1"
    )
    credentials=assumed_role_object['Credentials']
    return credentials;
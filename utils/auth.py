import  boto3
from credentials import accountid, stackid

def assume_role():
    sts_client = boto3.client('sts')
    assumed_role_object=sts_client.assume_role(
        RoleArn=f"arn:aws:iam::612488371952:role/prometheus-roles-{accountid}/{stackid}",
        RoleSessionName="AssumeRoleSession1"
    )
    credentials=assumed_role_object['Credentials']
    return credentials;
import os, boto3, sys, requests, json, traceback, gzip
from datetime import datetime
from logger import logger
from utils.auth import assume_role
from getRequiredMetrics import getRequiredMetrics
from credentials import prometheus_credentials, accountid, unique_id

def GetMetricsNames(url,username=None,password=None):
    metrics = getRequiredMetrics()
    logger.info("Fetching metrics names")
    names=[]
    if username and password:
      try:
        response = requests.get('{0}/api/v1/label/__name__/values'.format(url),auth=requests.auth.HTTPBasicAuth(username, password))
        response.raise_for_status()
        names = response.json()['data']
      except Exception as e:
        logger.error(e)
        
        
    else:
      try:
        response = requests.get('{0}/api/v1/label/__name__/values'.format(url))
        response.raise_for_status()
        names = response.json()['data']
      except Exception as e:
        logger.error(e)
        
    return [x for x in names if x in metrics], names

def GetPrometheusData(metrixNames,username=None,password=None):
  metrixString = '|'.join(metrixNames)
  logger.info('Querying prometheus at {0}'.format(prometheus_credentials["url"]))
  logger.info('Query : ' + '{{__name__=~"{0}"}}'.format(metrixString) + '[1h]')
  try:
    if username and password:
      response = requests.get('{0}/api/v1/query'.format(prometheus_credentials["url"]),
      params={'query': '{{__name__=~"{0}"}}'.format(metrixString) + '[1h]'},auth=requests.auth.HTTPBasicAuth(username, password))
      response.raise_for_status()
    else:
      response = requests.get('{0}/api/v1/query'.format(prometheus_credentials["url"]),
      params={'query': '{{__name__=~"{0}"}}'.format(metrixString) + '[1h]'})
      response.raise_for_status()
    # logger.info('Query response')
    # logger.info(response)
    results = response.json()['data']['result']
    # logger.info('Resultant metrics')
    # logger.info(results)
    return results
  except Exception as e:
    logger.error(e)
    

def CompressData(results):
  logger.info("Zipping data")
  converted_results = map(lambda el: {
      "metric": {**el["metric"]},
      "values": list(map(lambda value: float(value[1]), el["values"])),
      "timestamps": list(map(lambda value: int(float(value[0])*1000), el["values"])),
    }, results)
  # Convert to JSON
  json_data = json.dumps(list(converted_results))
  # Convert to bytes
  encoded = json_data.encode('utf-8')
  # Compress
  compressed = gzip.compress(encoded)

  with open("metrics.zip", 'wb') as f: 
    f.write(compressed)

def UploadToS3(date, start_hour, end_hour):
  try:
    logger.info("Uploading to S3 bucket prometheus-bucket-{0}".format(accountid))
    credentials = assume_role()
    s3_resource=boto3.resource(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name='us-east-1'
    )
    object = s3_resource.Object(f'prometheus-bucket-{accountid}', f"{unique_id}/{date}_{start_hour}-{end_hour}_metrics.zip")
    result = object.put(Body=open("metrics.zip", 'rb'))
    logger.info(result)
    os.remove('metrics.zip')
  except Exception:
        logger.error(traceback.format_exc())

def main():
  logger.info(f"Importing prometheus data for account: {accountid}")
  if not prometheus_credentials or not accountid or not unique_id:
    logger.info('Credentials not found')
    sys.exit(1)
  username=''
  password=''
  try:
    username=prometheus_credentials['username']
    password=prometheus_credentials['password']
  except KeyError:
    pass
  url = prometheus_credentials["url"]
  if username and password:
    metrixNames, availableMetrics=GetMetricsNames(url,username,password)
  else:
    metrixNames, availableMetrics=GetMetricsNames(url)
  logger.info("Filtered metrics names")
  logger.info(metrixNames)
  if len(metrixNames) == 0:
    logger.info('Metrics not available')
    logger.info(f'Available Metrics: {availableMetrics}')
    sys.exit(1)
  date = datetime.now().strftime('%d-%m-%Y')
  start_hour = datetime.now().hour
  end_hour = (start_hour + 1) % 24
  if username and password:
    results = GetPrometheusData(metrixNames,username,password)
  else:
    results = GetPrometheusData(metrixNames)
  CompressData(results)
  UploadToS3(date, start_hour, end_hour)

if __name__ == '__main__':
  main()

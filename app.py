import os, boto3, sys, requests, json, traceback, gzip
from datetime import datetime
from logger import logger
from utils.auth import assume_role
from getRequiredMetrics import getRequiredMetrics
from credentials import prometheus_credentials, accountid

def GetMetricsNames(url):
    metrics = getRequiredMetrics()
    logger.info("Fetching metrics names")
    response = requests.get('{0}/api/v1/label/__name__/values'.format(url))
    names = response.json()['data']
    return [x for x in names if x in metrics]

def GetPrometheusData(metrixNames):
  metrixString = '|'.join(metrixNames)
  logger.info('Querying prometheus at {0}'.format(prometheus_credentials["url"]))
  logger.info('Query : ' + '{{__name__=~"{0}"}}'.format(metrixString) + '[1h]')
  response = requests.get('{0}/api/v1/query'.format(prometheus_credentials["url"]),
  params={'query': '{{__name__=~"{0}"}}'.format(metrixString) + '[1h]'})
  # logger.info('Query response')
  # logger.info(response)
  results = response.json()['data']['result']
  # logger.info('Resultant metrics')
  # logger.info(results)
  return results

def CompressData(results):
  logger.info("Zipping data")
  converted_results = map(lambda el: {
      "metric": {**el["metric"], 'accountid': accountid},
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

def UploadToS3():
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
    object = s3_resource.Object(f'prometheus-bucket-{accountid}', f"{datetime.now().strftime('%d-%m-%Y-%H:%M:%S')}_metrics.zip")
    result = object.put(Body=open("metrics.zip", 'rb'))
    logger.info(result)
    os.remove('metrics.zip')
  except Exception:
        logger.error(traceback.format_exc())

def main():
  logger.info(f"Importing prometheus data for account: {accountid}")
  if not prometheus_credentials or not accountid:
    logger.info('Credentials not found')
    sys.exit(1)
  metrixNames=GetMetricsNames(prometheus_credentials["url"])
  logger.info("Filtered metrics names")
  logger.info(metrixNames)
  if len(metrixNames) == 0:
    logger.info('Metrics not available')
    sys.exit(1)
  results = GetPrometheusData(metrixNames)
  CompressData(results)
  UploadToS3()

main()

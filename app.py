import os, boto3, sys, requests, csv, traceback
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
  logger.info('Query : ' + '{{__name__=~"{0}"}}'.format(metrixString) + '[1d]')
  response = requests.get('{0}/api/v1/query'.format(prometheus_credentials["url"]),
  params={'query': '{{__name__=~"{0}"}}'.format(metrixString) + '[1d]'})
  # logger.info('Query response')
  # logger.info(response)
  results = response.json()['data']['result']
  # logger.info('Resultant metrics')
  # logger.info(results)
  return results

def GetLabelNames(results):
  labelnames = set()
  for result in results:
    labelnames.update(result['metric'].keys())
  labelnames.discard('__name__')
  labelnames = sorted(labelnames)
  logger.info("Label names")
  logger.info(labelnames)
  return labelnames

def CompressData(labelnames, results):
  logger.info("Zipping data")
  # Write the samples.
  writer = csv.writer(sys.stdout)
  writer.writerow(['name', 'timestamp', 'value'] + labelnames + ['accountid'])
  for result in results:
      for value in result['values']:
          l = [result['metric'].get('__name__', '')] + value
          for label in labelnames:
              l.append(result['metric'].get(label, ''))
          l.append(accountid)
          writer.writerow(l)

def UploadToS3():
  try:
    logger.info("Uploading to S3 bucket {0}-prometheus-bucket".format(accountid))
    credentials = assume_role()
    s3_resource=boto3.resource(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )
    s3_resource.create_bucket(Bucket=f'{accountid}-prometheus-bucket')
    object = s3_resource.Object(f'{accountid}-prometheus-bucket', f"{datetime.today().strftime('%Y-%m-%d')}_metrics.gz")
    result = object.put(Body=open("metrics.gz", 'rb'))
    logger.info(result)
    os.remove('metrics.gz')
  except Exception:
        logger.error(traceback.format_exc())

def main():
  logger.info("Importing prometheus data for account{accountid}")
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
  labelnames = GetLabelNames(results)
  CompressData(labelnames, results)
  UploadToS3()

main()












# groupeddata = dict()
# for result in results:
#     for value in result["values"]:
#         if value[0] not in groupeddata:
#             groupeddata[value[0]] = {}
#         for metric in metrixNames:
#             if metric == result["metric"]["__name__"]:
#                 groupeddata[value[0]][metric] = value[1]
#         for labelname in labelnames:
#             if labelname in result['metric']:
#                 groupeddata[value[0]][labelname] = result["metric"][labelname]
        
# # print(groupeddata)

# csvstringformatarray = []
# for index, metric in enumerate(metrixNames):
#     csvstringformatarray.append(f"{index+1}:metric:{metric}")

# csvstringformatarray.append(f"{len(metrixNames)+1}:time:unix_ms")

# for index, labelname in enumerate(labelnames):
#     csvstringformatarray.append(f"{len(metrixNames)+ 2 + index}:label:{labelname}")

# csvstringformat = ','.join(csvstringformatarray)
# print(csvstringformatarray)
# print(csvstringformat)


# for timekey in groupeddata.keys():
#     csvstringvaluesarray=[]
#     for index, metric in enumerate(metrixNames):
#         if metric in groupeddata[timekey]:
#             csvstringvaluesarray.append(groupeddata[timekey][metric])
#         else:
#             csvstringvaluesarray.append(0)
#     csvstringvaluesarray.append(f"{str(int(timekey)*1000)}")
#     for index, labelname in enumerate(labelnames):
#         if labelname in groupeddata[timekey]:
#             csvstringvaluesarray.append(groupeddata[timekey][labelname])
#         else:
#             csvstringvaluesarray.append('')
#     csvstringvalues = ','.join(csvstringvaluesarray)
#     print(csvstringvaluesarray)
#     print(csvstringvalues)
#     params = (
#         ('format', csvstringformat),
#     )
#     response = requests.post('{0}/api/v1/import/csv'.format(victoriametrics_credentials["url"]), params=params, data=csvstringvalues)
#     print(response)

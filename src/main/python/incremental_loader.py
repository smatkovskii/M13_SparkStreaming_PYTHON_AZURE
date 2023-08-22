from pyspark.sql import SparkSession
import os


sourceStorageAccount = os.environ['SOURCE_AZURE_STORAGE_ACCOUNT_NAME']
sourceDataContainer = os.environ['SOURCE_AZURE_STORAGE_CONTAINER_NAME']

destStorageAccount = os.environ['DEST_AZURE_STORAGE_ACCOUNT_NAME']
destDataContainer = os.environ['DEST_AZURE_STORAGE_CONTAINER_NAME']

spark = SparkSession.Builder().getOrCreate()
spark.conf.set(f'fs.azure.account.key.{sourceStorageAccount}.dfs.core.windows.net', os.environ['SOURCE_AZURE_STORAGE_ACCOUNT_KEY'])
spark.conf.set(f'fs.azure.account.key.{destStorageAccount}.dfs.core.windows.net', os.environ['DEST_AZURE_STORAGE_ACCOUNT_KEY'])

source = spark.read.parquet(f'abfss://{sourceDataContainer}@{sourceStorageAccount}.dfs.core.windows.net/hotel-weather')

dateCol = 'wthr_date'
dateRows = (source.select(dateCol)
    .distinct().sort(dateCol).collect())
dates = list(map(lambda r: r.asDict()[dateCol], dateRows))
print(dates)

for date in dates:
    (source.where(f'{dateCol} = "{date}"')
        .write.partitionBy('year', 'month', 'day') \
        .parquet(f'abfss://{destDataContainer}@{destStorageAccount}.dfs.core.windows.net/hotel-weather', mode='append'))
    print(f'Processed date {date}')
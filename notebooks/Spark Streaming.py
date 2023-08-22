# Databricks notebook source
# DBTITLE 1,Specify names for the storage accounts and containers
sourceStorageAccount = 'm13sparkstreaming'
sourceDataContainer = 'sourcestore'

destStorageAccount = 'styasm13westeurope'
destDataContainer = 'data'

# COMMAND ----------

# DBTITLE 1,Set configuration
spark.conf.set(f'fs.azure.account.key.{sourceStorageAccount}.dfs.core.windows.net', dbutils.secrets.get(scope='sparkstream', key='source_storage_account_key'))

spark.conf.set(f'fs.azure.account.key.{destStorageAccount}.dfs.core.windows.net', dbutils.secrets.get(scope='sparkstream', key='dest_storage_account_key'))

username = spark.sql("SELECT regexp_replace(current_user(), '[^a-zA-Z0-9]', '_')").first()[0]
checkpointPath = f'/tmp/{username}/_checkpoint/m13sparkstreaming'

# COMMAND ----------

# DBTITLE 1,Copy the data to the destination container
(spark.read.parquet(f'abfss://{sourceDataContainer}@{sourceStorageAccount}.dfs.core.windows.net/hotel-weather')
    .write.partitionBy('year', 'month', 'day')
    .parquet(f'abfss://{destDataContainer}@{destStorageAccount}.dfs.core.windows.net/hotel-weather'))

# COMMAND ----------

# DBTITLE 1,Create and fill delta table
import pyspark.sql.functions as F


spark.sql('DROP TABLE IF EXISTS city_stats')
dbutils.fs.rm(checkpointPath, True)

(spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", checkpointPath)
    .load(f'abfss://{destDataContainer}@{destStorageAccount}.dfs.core.windows.net/hotel-weather')
    .groupBy(F.col('city'), F.col('wthr_date'))
    .agg(F.approx_count_distinct('id').alias('hotels_in_city'), 
         F.min('avg_tmpr_c').alias('min_tmpr_c'), F.max('avg_tmpr_c').alias('max_tmpr_c'), 
         F.first('avg_tmpr_c').alias('avg_tmpr_c'))
    .writeStream
    .outputMode('complete')
    .trigger(processingTime='30 seconds')
    .option("checkpointLocation", checkpointPath)
    .toTable('city_stats'))

# COMMAND ----------

# DBTITLE 1,Display the delta table with aggregations
display(spark.readStream.table('city_stats'))

# COMMAND ----------

# DBTITLE 1,Dynamically display top-10 cities by number of hotels
display(spark.readStream.table('city_stats')
    .groupBy('city', 'wthr_date', 'hotels_in_city', 'min_tmpr_c', 'max_tmpr_c', 'avg_tmpr_c').agg(F.lit(1))
    .sort(F.desc('hotels_in_city')).limit(10))

# COMMAND ----------

# DBTITLE 1,Display a snapshot of top-10 distinct cities
biggestCities = spark.sql('''
    select city, wthr_date, hotels_in_city, min_tmpr_c, max_tmpr_c, avg_tmpr_c
    from (
        select city, any_value(wthr_date) wthr_date, hotels_in_city,
        any_value(min_tmpr_c) min_tmpr_c, any_value(max_tmpr_c) max_tmpr_c, any_value(avg_tmpr_c) avg_tmpr_c,
        row_number() over (partition by city order by hotels_in_city desc) rn
        from city_stats
        group by city, hotels_in_city
    )
    where rn = 1
    order by hotels_in_city desc
    limit 10
''')

display(biggestCities)

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql.functions import *
from awsglue.dynamicframe import DynamicFrame

from pyspark.sql.window import Window
from pyspark.sql.functions import rank, max

from pyspark.conf import SparkConf

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'iceberg_job_catalog_warehouse', 'output_path'])
conf = SparkConf()

# S3 sink params

output_path = args['output_path']

s3_target = args['iceberg_job_catalog_warehouse']
checkpoint_location = output_path + "/cp/"
temp_path = output_path + "/tmp/"

# Glue Iceberg Connector Bioler Plate
## Please make sure to pass runtime argument --output_path with value as the S3 path "s3://<your-iceberg-blog-demo-bucket>"
## Please make sure to pass runtime argument --iceberg_job_catalog_warehouse "s3://skicebergdemo/iceberg_custdata/"
conf.set("spark.sql.catalog.glue_catalog.warehouse", args['iceberg_job_catalog_warehouse'])
conf.set("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
conf.set("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
conf.set("spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
conf.set("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
conf.set("spark.sql.iceberg.handle-timestamp-without-timezone","true")

sc = SparkContext(conf=conf)
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)


def processBatch(dataFrame, batchId):

    if not dataFrame.rdd.isEmpty():
        dynamic_frame = DynamicFrame.fromDF(dataFrame, glueContext, "from_data_frame")
        dynamic_frame.printSchema()
        apply_mapping = ApplyMapping.apply(frame = dynamic_frame, mappings = [ \
            ("year", "string", "year", "string"), \
            ("month", "string", "month", "string"), \
            ("day", "string", "day", "string"), \
            ("hour", "string", "hour", "string"), \
            ("minute", "string", "minute", "string"), \
            ("customerid", "string", "customerid", "int"), \
            ("firstname", "string", "firstname", "string"), \
            ("lastname", "string", "lastname", "string"), \
            ("dateofbirth", "string", "dateofbirth", "string"), \
            ("city", "string", "city", "string"), \
            ("buildingnumber", "string", "buildingnumber", "int"), \
            ("streetaddress", "string", "streetaddress", "string"), \
            ("state", "string", "state", "string"), \
            ("zipcode", "string", "zipcode", "string"), \
            ("country", "string", "country", "string"), \
            ("countrycode", "string", "countrycode", "string"), \
            ("phonenumber", "string", "phonenumber", "string"), \
            ("productname", "string", "productname", "string"), \
            ("transactionamount", "string", "transactionamount", "int")],\
            transformation_ctx = "apply_mapping")

        dynamic_frame.printSchema()
        sprkdf = dynamic_frame.toDF()
        
        # Write to S3 iceberg Sink
        sprkdf.writeTo("glue_catalog.icebergdemodb.customer").tableProperty('format-version', '2').append()

## Read Input Kinesis Data Stream 

sourceData = glueContext.create_data_frame.from_catalog( \
    database = "icebergdemodb", \
    table_name = "clickstreamtable", \
    transformation_ctx = "datasource0", \
    additional_options = {"startingPosition": "TRIM_HORIZON", "inferSchema": "true"})


sourceData.printSchema()

glueContext.forEachBatch(frame = sourceData, batch_function = processBatch, options = {"windowSize": "100 seconds", "checkpointLocation": checkpoint_location})
job.commit()
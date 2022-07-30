CREATE TABLE icebergdemodb.customer(
year string,
month string,
day string,
hour string,
minute string,
customerid string,
firstname string,
lastname string,
dateofbirth string,
city string,
buildingnumber string,
streetaddress string,
state string,
zipcode string,
country string,
countrycode string,
phonenumber string,
productname string,
transactionamount int)
LOCATION '<S3 Location URI>'
TBLPROPERTIES (
  'table_type'='ICEBERG',
  'format'='parquet',
  'write_target_data_file_size_bytes'='536870912',
  'optimize_rewrite_delete_file_threshold'='10'
);

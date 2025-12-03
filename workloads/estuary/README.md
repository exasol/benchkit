# Estuary Warehouse Benchmark

Official Site: https://github.com/estuary/estuary-warehouse-benchmark

## Description

This is a benchmark using the TPC-H schema and data, but different queries.

> [!WARNING]
> The benchmark is currently non-functional for the official scale factor of 1000:
> The generator classes try top create unique numbers, which is simply not possible given the
> required number of rows and data types.

## Main Focus

- Unfiltered table scans
- some UNION ALL
- some window functions (analytical / OVER)
- Splitting strings into multiple rows (LATERAL VIEW / CROSS APPLY / UNNEST / LATERAL FLATTEN / ...)

## Official Reference Numbers

| Vendor                    | Sizing              | Hardware           | Pricing                             | TCOB<sup>1</sup>  | runtime<sup>3</sup> |
|---------------------------|---------------------|--------------------|-------------------------------------|-------------------|---------------------|
| Snowflake Standard Edition | Small               | ?                  | 0.14 DpM<sup>2</sup>                | $68.64            | 490 min             |
| Snowflake Standard Edition | Medium              | ?                  | 0.29                                | $70.64            | 244 min             |
| Snowflake Standard Edition | Large               | ?                  | 0.60                                | $66.61            | 111 min             |
| Redshift | RA3.Large Node-2    | ?                  | x                                   | $92               | -                   |
| Redshift | DC2.8XLarge Node-2  | ?                  | 4.02                                | $460              | 114 min             |    
| Databricks Classic Edition | Medium (max Node-1) | ?                  | 0.16                                | $94.28            | 589 min             |
| Databricks Classic Edition | Large max (Node-1)  | ?                  | 0.12                                | $95               | 792 min             |
| Databricks Classic Edition | Xlarge (max Node-1) | ?                  | 0.33                                | $106.14           | 322 min             |
| Microsoft Fabric | DW3000c             | ?                  | 0.99                                | $340              | 343 min             |
| Microsoft Fabric | DW1500c             | ?                  | 0.48                                | $290              | 604 min             |
| Microsoft Fabric | DW500c              | ?                  | x                                   | $236              | -                   |
| BigQuery | serveless           | ?                  | 15.64                               | $241              | 15 min              |

Notes:

1. TCOB: Total Cost Of Benchmark ("run each query once")
2. DpM: Dollar per Minute
3. Estimated benchmark execution time calculated as TCOB/DpM

> [!CAUTION]
> Given that only snowflake and databricks actually finished the Frankenstein query,
> the "total cost" numbers provided by the Estuary report seem highly questionable.

## Exasol Numbers (TBD)

| Variant         | Sizing             | Hardware           | Pricing<sup>1</sup>                             |  runtime | TCOB |
|-----------------|--------------------|--------------------|-------------------------------------|-------------------|--|
| Showcase System | 6x c6i.metal       | 768 vCPU, 1536 GiB |  0.62 |
| Big Memory      | 1x x2idn.16xlarge  | 64 vCPU, 1024 GiB  | 0.16 |
| Big CPU | 1x m7a.48xlarge | 192vCPU, 768 GiB | 0.22 | 

Notes:

1. Raw AWS on-demand pricing without EBS / S3 costs and Exasol license

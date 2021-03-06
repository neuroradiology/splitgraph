# Splitgraph example projects

## Introduction

This subdirectory contains various self-contained projects and snippets that can be used
as templates for your own experiments with Splitgraph.

Each example has a README file. Some of these examples get or push data from/to the Splitgraph registry at data.splitgraph.com and so require you to be logged into it.

## Contents

  * [import-from-csv](./import-from-csv): Import data from a CSV file into a Splitgraph image.
  * [import-from-mongo](./import-from-mongo): Import data from MongoDB into Splitgraph.
  * [pg-replication](./pg-replication): Use Splitgraph as a PostgreSQL logical replication client.
  * [push-to-other-engine](./push-to-other-engine): Share data with other Splitgraph engines.
  * [push-to-object-storage](./push-to-object-storage): Upload data to S3-compatible object storage when pushing to another Splitgraph engine.
  * [iris](./iris): Manipulate and query Splitgraph data from a Jupyter notebook.
  * [bloom-filter](./bloom-filter): Showcase using bloom filters to query large datasets with a limited amount of cache.
  * [splitfiles](./splitfiles): Use Splitfiles to build Splitgraph data images, track their provenance and keep them up to date.
  * [splitgraph-cloud](./splitgraph-cloud): Publish data on Splitgraph Cloud and try out the REST API provided by [PostgREST](http://postgrest.org/en/latest/) that gets generated for every dataset on there.
  * [postgrest](./postgrest): Run [PostgREST](http://postgrest.org/en/latest/) locally against the Splitgraph engine.
  * [us-election](./us-election): A real-world Splitfile example that joins multiple datasets.
  * [benchmarking](./benchmarking): A collection of Jupyter notebooks benchmarking various aspects of Splitgraph against synthetic and real-world datasets.
  * [dbt](./dbt): Use the [dbt](https://getdbt.com) CLI against the Splitgraph engine, enriching your dbt-built datasets with versioning, sharing and packaging capabilities.
  * [postgis](./postgis): Use Splitgraph, [PostGIS](https://postgis.net/) and [GeoPandas](https://geopandas.org/) to plot geospatial data.
  * [pgadmin](./pgadmin): Use [pgAdmin](https://www.pgadmin.org) with Splitgraph. 
  * [sample_splitfiles](./sample_splitfiles): A collection of loose Splitfiles that run against interesting datasets on Splitgraph Cloud.

## Contributing

The template example in [templates](./template) has a sample `example.yaml` file. Alternatively, you can copy one of the existing examples. Note that most examples that use the `example.yaml` format and don't require logging into Splitgraph are tested with a suite in the [test](./test) subdirectory.

In addition, all examples have [Asciinema casts](https://asciinema.org/) generated for them automatically at release time which are then available to be embedded into the website, see [the script](../.ci/rebuild_asciicasts.sh).

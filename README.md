# sdx-transform-cora

[![Build Status](https://travis-ci.org/ONSdigital/sdx-transform-cora.svg?branch=develop)](https://travis-ci.org/ONSdigital/sdx-transform-cora)

SDX Transform service for processing CORA destined survey data

## Getting started

### Pure python

It's recommended to use ``virtualenv``

```shell
$ make
$ make test
```

### Docker

```shell
$ docker build -t sdx-transform-cora
```

## Configuration

Some of important environment variables available for configuration are listed below:

| Environment Variable    | Example                               | Description
|-------------------------|---------------------------------------|----------------
| SDX_SEQUENCE_URL        | `http://sdx-sequence:5000`            | URL of the ``sdx-sequence`` service
| FTP_HOST                | `\\\\NP3-------370\\SDX_preprod\\`    | FTP host
| SDX_FTP_IMAGE_PATH      | `EDC_QImages`                         | Location of EDC Images
| SDX_FTP DATA_PATH       | `EDC_QData`                           | Location of EDC data
| SDX_FTP_RECEIPT_PATH    | `EDC_QReceipts`                       | Location of EDC receipts

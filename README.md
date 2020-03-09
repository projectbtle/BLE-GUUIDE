# UUID Functionality Mapper
A framework that enables mapping functionality to BLE UUIDs by combining data from various sources.

## Prerequisites
* Install all packages mentioned in `requirements.txt`. (Use `pip install -r requirements.txt`.)
* Install the NLTK corpora.

## Usage
### 0. APK List
Specify the list of APKs that are to be used for analysis within `config/apks.txt`.

### 1. UUID Extraction
To use the UUID functionality mapper, you first need an object containing the UUIDs extracted from one or more APKs. This file has to be in the following format:
```
{
  <unique_apk_name1>: {
    "pkg": <apk_package_name>,
    "uuids": {
      <uuid1>: {
        "methods": [
          <method1_that_accesses_uuid>,
          <method2_that_accesses_uuid>,
          ...
        ]
      },
      <uuid2>: {
        ...
      }
    }
  },
  <unique_apk_name2>: {
    ...
  }
}
```

For our paper, we used an adapted version of [BLEScope](https://dl.acm.org/doi/10.1145/3319535.3354240). Please contact the authors if you require the tool. Alternatively, you can use the uuid-extractor at [this repo](https://github.com/projectbtle/uuid-extractor) with some modifications to the output file.


### 2. Pre-analysis Setup
Execute `pre-analysis-setup.py` to extract artifacts from APKs and download data from Play and SIG. This requires a reasonable powerful machine, as the artifact extraction utilises Androguard, which has fairly high memory usage. It also requires an internet connection.

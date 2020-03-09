# UUID Functionality Mapper
A framework that enables mapping functionality to BLE UUIDs by combining data from various sources.

## Prerequisites
* Install all packages mentioned in `requirements.txt`. (Run `pip install -r requirements.txt`.)
* Install the NLTK corpora as described [here](https://www.nltk.org/data.html).

## Usage
### 1. APK List
Specify the list of APKs that are to be used for analysis within `config/apks.txt`. Absolute paths, one per line.

### 2. UUID Extraction
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

For our paper, we used an adapted version of [BLEScope](https://dl.acm.org/doi/10.1145/3319535.3354240). Please contact the authors to obtain the tool. Alternatively, you can use the UUID Extractor at [this repo](https://github.com/projectbtle/uuid-extractor) with some modifications to the output file. 

#### Notes:
* The file must be named `uuid-extractor-output.json` and must be present within the `input-output` directory.
* The method names in the file should be in smali format. If they are in Soot format, then use the `soot-to-smali.py` conversion tool within `utils` to convert the (methods within the) file to the expected format.

### 3. Pre-analysis Setup
Execute `pre-analysis-setup.py` to extract artifacts from APKs and obtain data from Play and SIG. 

#### Notes:
* This step requires a reasonable powerful machine, as the artifact extraction utilises Androguard, which has fairly high memory usage. It also requires an internet connection to download data from Play/SIG.
* Depending on the number of APKs that are being analysed, this step can also result in significant storage space requirements.

### 4. Functionality Mapping and Analysis
Execute `uuid-functionality-mapper.py` with the required parameters.

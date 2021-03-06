# BLE GUUIDE
A framework that enables mapping functionality to Bluetooth Low Energy (BLE) UUIDs and APKs by combining data from various sources.

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
* The file must be named `uuid_extractor_output.json` and must be present within the `input_output` directory.
* The method names in the file should be in smali format. If they are in Soot format, then use the `soot_to_smali.py` conversion tool within `utils` to convert the (methods within the) file to the expected format.

### 3. Pre-analysis Setup
Execute `pre_analysis_setup.py` to extract artifacts from APKs and obtain data from Play and SIG. 

#### Notes:
* This step requires a reasonable powerful machine, as the artifact extraction utilises Androguard, which has fairly high memory usage. It also requires an internet connection to download data from Play/SIG.
* Depending on the number of APKs that are being analysed, this step can also result in significant storage space requirements.

### 4. Functionality Mapping and Analysis
Execute `ble_guuide.py` with the required parameters.

```
usage: ble_guuide.py [-h] [-s] [-m]

A tool for performing functionality mapping for BLE UUIDs.

optional arguments:
  -h, --help   show this help message and exit
  -s, --stats  perform statistical analysis over extracted UUIDs. Results will be printed to console.
  -m, --map    perform functionality mapping over extracted UUIDs. Results will be saved to JSON.

Note that this tool has only been tested with Python 3.8.0. Some functionality will likely not work with versions less
than 3.4.
```
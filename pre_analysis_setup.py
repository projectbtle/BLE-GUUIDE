# Setup the required files for UUID functionality mapping.
# This script should be run after UUID extraction and before functionality mapping.

import os
import sys
import json
import requests
from androguard.misc import *
from androguard.core import *
from androguard import session

class PreAnalysisSetup:
    def __init__(self, basepath):        
        # Initialise paths.
        self.base_dir = basepath
        self.utils_dir = os.path.abspath(os.path.join(
            self.base_dir,
            'utils'
        ))
        
        sys.path.append(os.path.abspath(self.utils_dir))
        from strings_fields_extractor import StringsFieldsExtractor
        self.sf_extractor = StringsFieldsExtractor(self.base_dir)
        
    def fn_perform_pre_analysis_setup(self):
        apk_list_file = os.path.join(
            self.config_dir,
            'apks.txt'
        )
        
        apk_list = open(apk_list_file).read().splitlines()
        for path_to_apk in apk_list:
            self.fn_perform_per_apk_setup(path_to_apk)
            
    def fn_perform_per_apk_setup(self, path_to_apk):
        # Strings/fields extraction.
        self.sf_extractor.fn_extract_fields_and_strings(path_to_apk)
import os
import json
import requests
from androguard.misc import *
from androguard.core import *
from androguard import session

class StringsFieldsExtractor:
    def __init__(self, basepath):
        self.io_dir = os.path.abspath(os.path.join(
            self.base_dir,
            'input-output'
        ))
        self.config_dir = os.path.abspath(os.path.join(
            self.base_dir,
            'config'
        ))
        self.res_dir = os.path.abspath(os.path.join(
            self.base_dir,
            'resources'
        ))
        self.common_dir = os.path.abspath(os.path.join(
            self.res_dir,
            'common'
        ))
        self.app_specific_dir = os.path.abspath(os.path.join(
            self.res_dir,
            'app-specific'
        ))
        self.strings_dir = os.path.abspath(os.path.join(
            self.app_specific_dir,
            'strings'
        ))
        self.fields_dir = os.path.abspath(os.path.join(
            self.app_specific_dir,
            'fields'
        ))
        
        
    def fn_extract_fields_and_strings(self, path_to_apk):
        self.dx = None
        try:
            sess = get_default_session()
            _, _, self.dx = AnalyzeAPK(path_to_apk, session=sess)
        except:
            return
            
        filename = os.path.basename(path_to_apk)
        apkname = filename.replace('.apk', '')
        
        # Extract strings.
        strings_out = os.path.join(self.strings_dir, apkname + '.json')
        self.fn_extract_strings(strings_out)
        
        # Extract fields.
        fields_out = os.path.join(self.fields_dir, apkname + '.json')
        self.fn_extract_fields(fields_out)
        
    def fn_extract_strings(self, outpath):
        string_object = {}
        all_strings_analysis_objs = self.dx.get_strings()
        for string_analysis_obj in all_strings_analysis_objs:
            string_value = string_analysis_obj.get_orig_value()
            xref_from = string_analysis_obj.get_xref_from()
            for element in xref_from:
                class_name = element[1].get_class_name()
                method_name = element[1].get_name()
                desc_name = element[1].get_descriptor()
                desc_name_only = desc_name
                full_name = class_name + '->' + method_name + desc_name_only
                if full_name not in string_object:
                    string_object[full_name] = []
                string_object[full_name].append(string_value)
        with open(outpath, 'w') as f:
            json.dump(string_object, f, indent=4)
            
    def fn_extract_fields(self, outpath):
        field_object = {}
        field_xref_read = {}
        field_xref_write = {}
        for field_analysis in self.dx.find_fields():
            field_name = field_analysis.get_field().get_name()

            # Field definitions.
            field_class = field_analysis.get_field().get_class_name()
            if field_class not in field_object:
                field_object[field_class] = []
            if field_name not in field_object[field_class]:
                field_object[field_class].append(field_name)

            # Field reads.
            for one_xref_read in field_analysis.get_xref_read():
                field_xref_read_method = one_xref_read[1]
                field_xref_read_class_method = \
                    field_xref_read_method.get_class_name() \
                    + '->' \
                    + field_xref_read_method.get_name() \
                    + field_xref_read_method.get_descriptor()
                if field_xref_read_class_method not in field_xref_read:
                    field_xref_read[field_xref_read_class_method] = []
                if field_name not in field_xref_read[field_xref_read_class_method]:
                    field_xref_read[field_xref_read_class_method].append(field_name)

            # Field writes.
            for one_xref_write in field_analysis.get_xref_write():
                field_xref_write_method = one_xref_write[1]
                field_xref_write_class_method = \
                    field_xref_write_method.get_class_name() \
                    + '->' \
                    + field_xref_write_method.get_name() \
                    + field_xref_write_method.get_descriptor()
                if field_xref_write_class_method not in field_xref_write:
                    field_xref_write[field_xref_write_class_method] = []
                if field_name not in field_xref_write[field_xref_write_class_method]:
                    field_xref_write[field_xref_write_class_method].append(field_name)

        with open(outpath, 'w') as f:
            json.dump(field_object, f, indent=4)
        xref_read_outpath = outpath.replace('.json', '_xref_read.json')
        with open(xref_read_outpath, 'w') as f:
            json.dump(field_xref_read, f, indent=4)
        xref_write_outpath = outpath.replace('.json', '_xref_write.json')
        with open(xref_write_outpath, 'w') as f:
            json.dump(field_xref_write, f, indent=4)
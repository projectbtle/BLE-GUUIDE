import os
import json
from category-analysis import CategoryAnalyser

class ApkMatcher:
    def __init__(self, basepath, is_validation_mode=False, path_to_extractor_output=None):
        # Configs.
        self.bool_is_validation_mode = is_validation_mode
        self.bool_save_temp_file = save_temp_files
        
        # Initialise paths.
        self.base_dir = basepath
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
        
        # Initialise.
        self.fn_initialise_ignore_uuids()
        
        # Load extractor output.
        extractor_output_file = os.path.join(
            self.io_dir,
            'uuid-extractor-output.json'
        )
        if path_to_extractor_output != None:
            extractor_output_file = path_to_extractor_output
        if os.path.isfile(extractor_output_file):
            with open(extractor_output_file) as f1:
                self.obj_extractor_output = json.load(f1)
            
        # Load KFUs.
        self.fn_load_kfus()
        
        # Initialise CategoryAnalyser.
        self.ca = CategoryAnalyser()
        
        # Initialise output object.
        self.obj_output = {}

    def fn_load_kfus(self):
        kfus_file = os.path.join(self.common_dir, 'kfus.json')
        with open(kfus_file) as f0:
            obj_kfus = json.load(f0)
        # Generate KFU list.
        self.kfu_list = []
        for level1_key in obj_kfus:
            for level2_key in obj_kfus[level1_key]:
                for uuid in obj_kfus[level1_key][level2_key]:
                    if uuid not in self.kfu_list:
                        self.kfu_list.append(uuid)
        
    def fn_get_functionality(self):
        checked_uuid_method_pairs = {}
        for apk in self.obj_extractor_output:
            for uuid in self.obj_extractor_output[apk]:
                if uuid in self.list_ignore_uuids:
                    continue
                    
                # In normal mode, we don't test KFUs.
                # In validation mode, we don't check UFUs.
                if self.bool_is_validation_mode == True:
                    if uuid not in self.kfu_list:
                        continue
                else:
                    if uuid in self.kfu_list:
                        continue

                # Add keys to output object.
                if apk not in self.obj_output:
                    self.obj_output[apk] = {}
                if uuid not in self.obj_output[apk]:
                    self.obj_output[apk][uuid] = {
                        'component_categories': {},
                        'final_category': 'N/A'
                    }
                    
                methods_list = []
                # If we have already checked the exact same UUID and 
                #  methods before, don't re-check.
                methods_list = \
                    self.obj_extractor_output[apk]['uuids'][uuid]['methods']
                methods_list.sort()
                str_methods = str(methods_list)
                if uuid not in checked_uuid_method_pairs:
                    checked_uuid_method_pairs[uuid] = {
                        'methods': '',
                        'categories': {}
                    }
                if str_methods == checked_uuid_method_pairs[uuid]['methods']:
                    assigned_categories = \
                        checked_uuid_method_pairs[uuid]['categories']
                    self.obj_output[apk][uuid]['component_categories'] = \
                        assigned_categories
                    com_cat = \
                        self.obj_output[apk][uuid]['component_categories']['combined_categories']
                    if len(list(set(com_cat))) == 1:
                        self.obj_output[apk][uuid]['final_category'] = \
                            com_cat[0]
                    continue
                
                # Get analysis output.
                uuid_categories = self.fn_perform_analysis_for_uuid(apk, methods_list)
                
                # Update list of checked uuid-methods, so that we needn't
                #  repeat it again.
                checked_uuid_method_pairs[uuid]['methods'] = str_methods
                checked_uuid_method_pairs[uuid]['categories'] = \
                    uuid_categories
                    
                # Update output 
                self.obj_output[apk][uuid]['component_categories'] = \
                    uuid_categories
                com_cat = \
                    self.obj_output[apk][uuid]['component_categories']['combined_categories']
                if len(list(set(com_cat))) == 1:
                    self.obj_output[apk][uuid]['final_category'] = \
                        com_cat[0]
        return self.obj_output
                
    def fn_get_per_apk_functionality(self, apk):
        per_apk_output = {}
        for uuid in self.obj_extractor_output[apk]:
            if uuid in self.list_ignore_uuids:
                continue
                
            # In normal mode, we don't test KFUs.
            # In validation mode, we don't check UFUs.
            if self.bool_is_validation_mode == True:
                if uuid not in self.kfu_list:
                    continue
            else:
                if uuid in self.kfu_list:
                    continue

            # Add keys to output object.
            if uuid not in per_apk_output:
                per_apk_output[uuid] = {
                    'component_categories': {},
                    'final_category': 'N/A'
                }
                
            methods_list = []
            # If we have already checked the exact same UUID and 
            #  methods before, don't re-check.
            methods_list = \
                self.obj_extractor_output[apk]['uuids'][uuid]['methods']
            methods_list.sort()

            # Get analysis output.
            uuid_categories = self.fn_perform_analysis_for_uuid(apk, methods_list)

            # Update output 
            per_apk_output[uuid]['component_categories'] = \
                uuid_categories
            com_cat = \
                per_apk_output[uuid]['component_categories']['combined_categories']
            if len(list(set(com_cat))) == 1:
                per_apk_output[uuid]['final_category'] = \
                    com_cat[0]
        return per_apk_output
        
    def fn_perform_analysis_for_uuid(self, apk, methods_list):
        out_categories = {
            'api_categories' = [],
            'string_categories' = [],
            'field_categories' = [],
            'combined_categories' = []
        }
        
        # Load strings file.
        strings_json = os.path.join(
            self.strings_dir,
            apk + '.json'
        )
        if os.path.isfile(strings_json):
            with open(strings_json) as fs:
                apk_strings = json.load(fs)
        else:
            apk_strings = {}
        
        # Load fields file.
        fields_json = os.path.join(
            self.fields_dir,
            apk + '_xref_read.json'
        )
        if os.path.isfile(fields_json):
            with open(fields_json) as fs:
                apk_fields = json.load(fs)
        else:
            apk_fields = {}
            
        for smali_class_method in methods_list:
            # API check.
            smali_class = smali_class_method.split('->')[0]
            smali_method_desc = smali_class_method.split('->')[1]
            smali_method = smali_method_desc.split('(')[0]
            class_end = smali_class.split('/')[-1]
            last_class_part_method = class_end + smali_method
            name_categories = self.ca.match_text(last_class_part_method, single_word=True)
            set_categories = list(set(name_categories['category_subcategory']))
            for category_subcategory in set_categories:
                out_categories['api_categories'].append(category_subcategory)
                
            # Strings check.
            strings_list = []
            if smali_class_method in apk_strings:
                strings_list = apk_strings[smali_class_method]
            for individual_string in strings_list:
                name_categories = self.ca.match_text(individual_string, single_word=True)
                set_categories = list(set(name_categories['category_subcategory']))
                for category_subcategory in set_categories:
                    out_categories['string_categories'].append(category_subcategory)
                
            # Fields check.
            fields_list = []
            if smali_class_method in apk_fields:
                fields_list = apk_fields[smali_class_method]
            for individual_field in fields_list:
                name_categories = self.ca.match_text(individual_field, single_word=True)
                set_categories = list(set(name_categories['category_subcategory']))
                for category_subcategory in set_categories:
                    out_categories['field_categories'].append(category_subcategory)
            
        # Combine.
        out_categories['combined_categories'] = out_categories['api_categories'] \
                                                + out_categories['string_categories'] \
                                                + out_categories['field_categories']
        return out_categories
        
    def fn_initialise_ignore_uuids(self):
        self.list_ignore_uuids = [
            '00002900-0000-1000-8000-00805F9B34FB',
            '00002901-0000-1000-8000-00805F9B34FB',
            '00002902-0000-1000-8000-00805F9B34FB',
            '00002903-0000-1000-8000-00805F9B34FB',
            '00002904-0000-1000-8000-00805F9B34FB',
            '00002905-0000-1000-8000-00805F9B34FB',
            '00002906-0000-1000-8000-00805F9B34FB',
            '00002907-0000-1000-8000-00805F9B34FB',
            '00002908-0000-1000-8000-00805F9B34FB',
            '00002909-0000-1000-8000-00805F9B34FB',
            '0000290A-0000-1000-8000-00805F9B34FB',
            '0000290B-0000-1000-8000-00805F9B34FB',
            '0000290C-0000-1000-8000-00805F9B34FB',
            '0000290D-0000-1000-8000-00805F9B34FB',
            '0000290E-0000-1000-8000-00805F9B34FB'
        ]
        
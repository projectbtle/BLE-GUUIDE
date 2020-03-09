import os
import sys
import copy
import json
import logging

# BLE adopted prefix, suffixes.
RESERVED_BLE_PREFIX = '0000'
RESERVED_BLE_SUFFIX = '-0000-1000-8000-00805F9B34FB'


class UUIDAnalyser:
    def __init__(self):
        # Set up logger.
        logging.basicConfig()
        self.logger = logging.getLogger('uuid-analyser')
        self.logger.setLevel(logging.DEBUG)
        
        # Set up directory paths.
        self.curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.base_dir = os.path.abspath(os.path.join(
            self.curr_dir,
            '..',
            '..'
        ))
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

        # Initialise objects.
        self.input_obj_uuids_per_apk = {}
        self.input_obj_apks_per_uuid = {}
        
        # Extractor output.
        self.input_extractor = {}
        self.fn_read_extractor_output()
        
        # Initialise Known UUIDs.
        self.input_obj_kfus = {}
        self.fn_initialise_kfu_obj()
        
        # Read in SLDs info.
        self.input_obj_slds = {}
        self.fn_initialise_slds_obj()
        
        # Create object containing adopted UUIDs.
        self.input_obj_ble_adopted_uuids = {}
        self.input_obj_ble_service_uuids = {}
        self.fn_initialise_adopted_uuid_obj()
        
        # Create list of 16-bit member UUIDs.
        self.input_ble_member_uuids = []
        self.fn_initialise_member_uuids()
        
        # Assign values to per-APK and per-UUID objects.
        self.fn_initialise_apk_uuid_obj()
        
        # Objects to be populated later.
        self.obj_apks_at_least_one_adopted_uuid = {}
        self.obj_apks_at_least_one_nongapgattgss_adopted_uuid = {}
        self.obj_apks_only_adopted = {}
        self.obj_apks_only_gattgapgss = {}
        self.obj_apks_notonly_gattgapgss = {}
        self.obj_apks_only_adopted_with_mismatches = {}
        self.obj_apks_only_adopted_no_mismatches = {}
    
    def get_stats(self):
        # Identify APKs with at least one extracted UUID.
        self.fn_get_num_apks_with_extracted_uuids()
        
        # Identify KFU/UFUs
        self.fn_get_kfu_ufu()
        
        # Identify APKs with at least one non-GAP/GATT/GSS adopted UUID.
        self.fn_id_apks_with_at_least_one_adopted_uuid()
        
        # Identify APKs with only adopted UUIDs.
        self.fn_id_apks_with_only_adopted_uuids()
        
        # Identify APKs with only gatt/gap/gss UUIDs.
        self.fn_id_apks_with_only_gattgapgss_uuids()
        
        # Identify the various categories.
        self.fn_get_breakdown_of_adopted_uuid_categories()
        
        # Identify UUIDs with incorrect use of BLE reserved range.
        self.fn_id_uuids_with_incorrect_use_of_reserved_range()
        
        # Identify APKs with incorrect use of Bluetooth reserved range.
        self.fn_id_apks_with_incorrect_use_of_reserved_range()
        
        # Include dfu related stuff.
        self.fn_dfu_analysis()

    def fn_read_extractor_output(self):
        src_file = os.path.join(self.io_dir, 'uuid-extractor-output.json')
        with open(src_file) as f0:
            input_extractor = json.load(f0)
        for sha in input_extractor:
            self.input_extractor[sha.upper()] = input_extractor[sha]
            
    def fn_initialise_slds_obj(self):
        self.logger.info('Initialising SLDs data.')
        slds_data_file = os.path.join(
            self.common_dir,
            'slds.json'
        )
        with open(slds_data_file) as f:
            self.input_obj_slds = json.load(f)
      
    def fn_initialise_kfu_obj(self):
        self.logger.info('Initialising KFU data.')
        kfu_file = os.path.join(
            self.common_dir,
            'kfus.json'
        )
        with open(kfu_file) as f:
            self.input_obj_kfus = json.load(f)
    
    def fn_initialise_adopted_uuid_obj(self):
        self.logger.info('Initialising adopted UUID data.')
        adopted_uuid_list_file = os.path.join(
            self.common_dir,
            'adopted-uuid-list.csv'
        )
        with open(adopted_uuid_list_file) as f:
            adopted_uuid_list = f.read().splitlines()

        for line in adopted_uuid_list:
            line = line.strip()
            if line == '':
                continue
            split_line = line.split(',')
            if len(split_line) != 4:
                continue
            adopted_uuid = (split_line[2].strip())[2:]
            service = split_line[3].strip()
            self.input_obj_ble_adopted_uuids[adopted_uuid.upper()] = service
            if service not in self.input_obj_ble_service_uuids:
                self.input_obj_ble_service_uuids[service] = []
            self.input_obj_ble_service_uuids[service].append(adopted_uuid)
    
    def fn_initialise_member_uuids(self):
        self.logger.info('Initialising member UUID list.')
        member_uuid_list_file = os.path.join(
            self.common_dir,
            'sig-member-list.txt'
        )
        with open(member_uuid_list_file) as f:
            member_uuid_list = f.read().splitlines()
        for member_uuid in member_uuid_list:
            self.input_ble_member_uuids.append(member_uuid.strip().upper())

    def fn_initialise_apk_uuid_obj(self):
        self.logger.info('Initialising per-APK and per-UUID objects.')

        for apk_sha in self.input_extractor:            
            self.input_obj_uuids_per_apk[apk_sha] = {}
            self.fn_add_uuids_to_apk_object(apk_sha)
        self.logger.debug('Done initialising per-APK and per-UUID objects.')
        num_apks = len(self.input_obj_uuids_per_apk.keys())
        self.logger.info('Data set of ' + str(num_apks) + ' APKs.')
        num_uuids = len(self.input_obj_apks_per_uuid.keys())
        self.logger.info('Data set has ' + str(num_uuids) + ' unique UUIDs.')
            
    def fn_add_uuids_to_apk_object(self, apk_sha):
        self.input_obj_uuids_per_apk[apk_sha]['pkg'] = \
                self.input_extractor[apk_sha]['pkg']
        self.input_obj_uuids_per_apk[apk_sha]['uuids'] = {}
        for uuid in self.input_extractor[apk_sha]['uuids']:
            self.fn_add_uuid_to_primary_objects(uuid, apk_sha)
            
    def fn_add_uuid_to_primary_objects(self, uuid, apk_sha):
        uuid_part = uuid.strip().upper()
        if uuid_part == '00000000-0000-1000-8000-00805F9B34FB':
            return
            
        methods = \
            self.input_extractor[apk_sha]['uuids'][uuid]['methods']
        
        # Add to per-apk object.
        uuid_object = self.input_obj_uuids_per_apk[apk_sha]['uuids']
        if uuid_part not in uuid_object:
            uuid_object[uuid_part] = {}
            uuid_object[uuid_part]['methods'] = []
        for method_part in methods:
            if method_part not in uuid_object[uuid_part]['methods']:
                uuid_object[uuid_part]['methods'].append(method_part)
        
        # Add to per-uuid object.
        if uuid_part not in self.input_obj_apks_per_uuid:
            self.input_obj_apks_per_uuid[uuid_part] = {}
            self.input_obj_apks_per_uuid[uuid_part]['apks'] = {}
            self.input_obj_apks_per_uuid[uuid_part]['methods'] = {}
        if apk_sha not in self.input_obj_apks_per_uuid[uuid_part]['apks']:
            self.input_obj_apks_per_uuid[uuid_part]['apks'][apk_sha] = []
        apk_method_list = self.input_obj_apks_per_uuid[uuid_part]['apks'][apk_sha]
        for method_part in methods:
            if method_part not in apk_method_list:
                apk_method_list.append(method_part)
            if method_part not in self.input_obj_apks_per_uuid[uuid_part]['methods']:
                self.input_obj_apks_per_uuid[uuid_part]['methods'][method_part] = []
        apk_list = self.input_obj_apks_per_uuid[uuid_part]['methods'][method_part]
        pkg_sha = self.input_obj_uuids_per_apk[apk_sha]['pkg'] + ' ' + apk_sha
        if pkg_sha not in apk_list:
            apk_list.append(pkg_sha)
        
    def fn_is_uuid_adopted(self, uuid):
        uuid = uuid.upper()
        if uuid[0:4] != RESERVED_BLE_PREFIX:
            return False
        if uuid[8:] != RESERVED_BLE_SUFFIX:
            return False
        if uuid[4:8] not in self.input_obj_ble_adopted_uuids:
            return False
        return True
        
    def fn_is_uuid_adopted_non_gapgattgss(self, uuid):
        uuid = uuid.upper()
        is_adopted = self.fn_is_uuid_adopted(uuid)
        if is_adopted == False:
            return False
        service_type = self.input_obj_ble_adopted_uuids[uuid[4:8]]
        service_type = service_type.strip()
        if service_type in ['GATT', 'GAP', 'GSS']:
            return True
        return False
        
    """ Analysis start """

    def fn_get_num_apks_with_extracted_uuids(self):
        self.logger.info('Identifying APKs with at least one extracted UUID.')
        total_count = 0
        for apk in self.input_obj_uuids_per_apk:
            all_uuids = self.input_obj_uuids_per_apk[apk]['uuids']
            if all_uuids == {}:
                continue
            total_count += 1
        self.logger.info(
            str(total_count) 
            + ' APKs have at least one extracted UUID.'
        )
        
    def fn_get_kfu_ufu(self):
        self.logger.info('Identifying KFUs and UFUs.')
        self.fn_get_num_kfu_ufu()
        self.fn_get_apks_kfu_ufu()
        
    def fn_get_num_kfu_ufu(self):
        all_uuids = list(self.input_obj_apks_per_uuid.keys()) 
        self.list_all_ufus = []
        num_uuids = 0
        num_kfu = 0
        num_ufu = 0
        for uuid in all_uuids:
            num_uuids += 1
            ufu = True
            for category in self.input_obj_kfus:
                if type(self.input_obj_kfus[category]) is list:
                    for kfu in self.input_obj_kfus[category]:
                        if uuid == kfu:
                            ufu = False
                            break
                else:
                    for subcategory in self.input_obj_kfus[category]:
                        for kfu in self.input_obj_kfus[category][subcategory]:
                            if uuid == kfu:
                                ufu = False
                                break
                        if ufu == False:
                            break
            if ufu == True:
                num_ufu += 1
                self.list_all_ufus.append(uuid)
            else:
                num_kfu += 1
        self.logger.info('Total unique UUIDs: ' + str(num_uuids))
        self.logger.info('Num KFUs: ' + str(num_kfu))
        self.logger.info('Num UFUs: ' + str(num_ufu))
        
    def fn_get_apks_kfu_ufu(self):
        self.obj_apks_all_kfu = {}
        self.obj_apks_all_ufu = {}
        self.obj_apks_both_kfu_ufu = {}
        all_kfus = []
        for category in self.input_obj_kfus:
            if type(self.input_obj_kfus[category]) is list:
                for kfu in self.input_obj_kfus[category]:
                    if kfu not in all_kfus:
                        all_kfus.append(kfu)
            else:
                for subcategory in self.input_obj_kfus[category]:
                    for kfu in self.input_obj_kfus[category][subcategory]:
                        if kfu not in all_kfus:
                            all_kfus.append(kfu)
        num_apps_all_kfu = 0
        num_apps_all_ufu = 0
        num_apps_both = 0
        num_apps_none = 0
        for apk in self.input_obj_uuids_per_apk:
            kfu = False
            ufu = False
            if len(self.input_obj_uuids_per_apk[apk]['uuids']) == 0:
                num_apps_none += 1
                continue
            for uuid in self.input_obj_uuids_per_apk[apk]['uuids']:
                if uuid in all_kfus:
                    kfu = True
                else:
                    ufu = True
            if (kfu == True):
                if (ufu == True):
                    num_apps_both += 1
                    self.obj_apks_both_kfu_ufu[apk] = self.input_obj_uuids_per_apk[apk]
                else:
                    num_apps_all_kfu += 1
                    self.obj_apks_all_kfu[apk] = self.input_obj_uuids_per_apk[apk]
            else:
                num_apps_all_ufu += 1
                self.obj_apks_all_ufu[apk] = self.input_obj_uuids_per_apk[apk]
        self.logger.info('Num apps with all KFUs: ' + str(num_apps_all_kfu))
        self.logger.info('Num apps with all UFUs: ' + str(num_apps_all_ufu))
        self.logger.info('Num apps with both: ' + str(num_apps_both))
        self.logger.info('Num apps with none: ' + str(num_apps_none))
        
    def fn_id_apks_with_at_least_one_adopted_uuid(self):
        self.logger.info('Identifying APKs with at least one non-GAP/GATT/GSS adopted UUID.')
        for apk in self.input_obj_uuids_per_apk:
            all_uuids = self.input_obj_uuids_per_apk[apk]['uuids']
            if all_uuids == {}:
                continue
            adopted_count = 0
            adopted_nongapgattgss_count = 0
            for uuid in all_uuids:
                if self.fn_is_uuid_adopted(uuid) == False:
                    continue
                adopted_count += 1
                if self.fn_is_uuid_adopted_non_gapgattgss(uuid) == False:
                    continue
                adopted_nongapgattgss_count += 1
            if adopted_count > 0:
                self.obj_apks_at_least_one_adopted_uuid[apk] = \
                    copy.deepcopy(self.input_obj_uuids_per_apk[apk])
            if adopted_nongapgattgss_count > 0:
                self.obj_apks_at_least_one_nongapgattgss_adopted_uuid[apk] = \
                    copy.deepcopy(self.input_obj_uuids_per_apk[apk])
                    
        # Print logging info.
        num_apks_at_leastone_adopted_uuid = len(
            list(self.obj_apks_at_least_one_adopted_uuid.keys())
        )
        self.logger.info(
            str(num_apks_at_leastone_adopted_uuid) 
            + ' APKs have at least one adopted UUID.'
        )
        num_apks_at_leastone_nonggg_adopted_uuid = len(
            list(self.obj_apks_at_least_one_nongapgattgss_adopted_uuid.keys())
        )
        self.logger.info(
            str(num_apks_at_leastone_nonggg_adopted_uuid) 
            + ' APKs have at least one (non-GAP/GATT/GSS) adopted UUID.'
        )
            
    def fn_id_apks_with_only_adopted_uuids(self):
        self.logger.info('Identifying APKs with only adopted UUIDs.')
        for apk in self.input_obj_uuids_per_apk:
            is_all_adopted = self.fn_analyse_adopted_for_single_apk(apk)
            if is_all_adopted == True:
                self.obj_apks_only_adopted[apk] = \
                    copy.deepcopy(self.input_obj_uuids_per_apk[apk])

        # Print logging info.
        num_apks_adopted_uuids_only = len(
            list(self.obj_apks_only_adopted.keys())
        )
        self.logger.info(
            str(num_apks_adopted_uuids_only) 
            + ' APKs have only adopted UUIDs'
        )
            
    def fn_analyse_adopted_for_single_apk(self, apk):
        all_uuids = self.input_obj_uuids_per_apk[apk]['uuids']
        if all_uuids == {}:
            return False
        for uuid in all_uuids:
            if self.fn_is_uuid_adopted(uuid) == False:
                return False
        return True
    
    def fn_id_apks_with_only_gattgapgss_uuids(self):
        self.logger.info('Identifying APKs with only GATT/GAP/GSS UUIDs.')
        for apk in self.obj_apks_only_adopted:
            is_all_gattgapgss = self.fn_analyse_gattgapgss_for_single_apk(apk)
            if is_all_gattgapgss == True:
                self.obj_apks_only_gattgapgss[apk] = \
                    copy.deepcopy(self.obj_apks_only_adopted[apk])
            else:
                self.obj_apks_notonly_gattgapgss[apk] = \
                    copy.deepcopy(self.obj_apks_only_adopted[apk])

        # Print logging info.
        num_apks_gattgapgss_uuids_only = len(
            list(self.obj_apks_only_gattgapgss.keys())
        )
        self.logger.info(
            str(num_apks_gattgapgss_uuids_only) 
            + ' adopted-only APKs have only GATT/GAP/GSS UUIDs'
        )
        num_apks_no_gattgapgss_uuids = len(
            list(self.obj_apks_notonly_gattgapgss.keys())
        )
        self.logger.info(
            str(num_apks_no_gattgapgss_uuids) 
            + ' adopted-only APKs have UUIDs other than GATT/GAP/GSS '
            + '(but may include GATT/GAP/GSS as well)'
        )
    
    def fn_analyse_gattgapgss_for_single_apk(self, apk):
        all_uuids = self.obj_apks_only_adopted[apk]['uuids']
        if all_uuids == {}:
            return False
        for uuid in all_uuids:
            if self.fn_is_uuid_adopted_non_gapgattgss(uuid) == False:
                return False
        return True
    
    def fn_get_breakdown_of_adopted_uuid_categories(self):
        self.apks_per_adopted_uuid_category = {}
        for service in self.input_obj_ble_service_uuids:
            self.apks_per_adopted_uuid_category[service] = []
            
        for uuid in self.input_obj_apks_per_uuid:
            is_adopted = self.fn_is_uuid_adopted(uuid)
            if is_adopted == False:
                continue
            adoped_uuid_part = uuid[4:8]
            service_name = self.input_obj_ble_adopted_uuids[adoped_uuid_part]
            all_apks = self.input_obj_apks_per_uuid[uuid]['apks']
            for one_apk in all_apks:
                if one_apk not in self.apks_per_adopted_uuid_category[service_name]:
                    self.apks_per_adopted_uuid_category[service_name].append(one_apk)
        
        for service in self.apks_per_adopted_uuid_category:
            unique_apks = list(set(self.apks_per_adopted_uuid_category[service]))
            self.logger.info(
                '   '
                + service
                + '   '
                + str(len(unique_apks))
            )
    
    def fn_id_apks_with_incorrect_use_of_reserved_range(self):
        self.logger.info(
            'Identifying APKs with incorrect use of BLE reserved range.'
        )
        incorrect_uuid_apks = 0
        for apk in self.input_obj_uuids_per_apk:
            incorrect_per_apk = False
            for uuid in self.input_obj_uuids_per_apk[apk]['uuids']:
                if ((uuid[0:4] == RESERVED_BLE_PREFIX) and (uuid[8:] == RESERVED_BLE_SUFFIX)):
                    if ((uuid[4:8] not in self.input_obj_ble_adopted_uuids) and 
                            (uuid[4:8] not in self.input_ble_member_uuids)):
                        incorrect_per_apk = True
                        break
            if incorrect_per_apk == True:
                incorrect_uuid_apks += 1
        self.logger.info(
                str(incorrect_uuid_apks)
                + ' APKs use the BLE reserved range incorrectly.'
            )
    
    def fn_id_uuids_with_incorrect_use_of_reserved_range(self):
        self.logger.info(
            'Identifying UUIDs with incorrect use of BLE reserved range.'
        )
        incorrect_uuids = 0
        for uuid in self.input_obj_apks_per_uuid:
            incorrect_per_uuid = False
            if ((uuid[0:4] == RESERVED_BLE_PREFIX) and (uuid[8:] == RESERVED_BLE_SUFFIX)):
                if ((uuid[4:8] not in self.input_obj_ble_adopted_uuids) and 
                        (uuid[4:8] not in self.input_ble_member_uuids)):
                    incorrect_per_uuid = True
            if incorrect_per_uuid == True:
                incorrect_uuids += 1
        self.logger.info(
                str(incorrect_uuids)
                + ' UUIDs use the BLE reserved range incorrectly.'
            )
            
    def fn_dfu_analysis(self):
        self.logger.info(
            'Getting DFU information.'
        )
        apks_per_chipset = {}
        for chipset in self.input_obj_kfus['DFU']:
            apks_per_chipset[chipset] = []
            for chipset_uuid in self.input_obj_kfus['DFU'][chipset]:
                if chipset_uuid not in self.input_obj_apks_per_uuid:
                    continue
                apks_per_uuid = self.input_obj_apks_per_uuid[chipset_uuid]['apks']
                for apk in apks_per_uuid:
                    if apk not in apks_per_chipset[chipset]:
                        apks_per_chipset[chipset].append(apk)
                        
        apks_with_dfu_uuids = []
        for chipset in apks_per_chipset:
            self.logger.info(
                '   '
                + chipset
                + '   '
                + str(len(apks_per_chipset[chipset]))
            )
            for apk in apks_per_chipset[chipset]:
                if apk not in apks_with_dfu_uuids:
                    apks_with_dfu_uuids.append(apk)
        unique_apks_with_dfu_uuids = list(set(apks_with_dfu_uuids))
        self.logger.info(
                str(len(unique_apks_with_dfu_uuids))
                + ' APKs have at least one DFU UUID'
            )
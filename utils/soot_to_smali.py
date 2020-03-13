import json


class SootToSmali:
    def __init__(self):
        pass
        
    def convert_soot_json_to_smali(self, path_to_json, path_to_out_json):
        with open(path_to_json) as infile:
            in_uuids = json.load(infile)
        for apk in in_uuids:
            for uuid in in_uuids[apk]['uuids']:
                all_methods = []
                for method in in_uuids[apk]['uuids'][uuid]['methods']:
                    smali_method = self.convert_soot_method_to_smali(method)
                    if smali_method not in all_methods:
                        all_methods.append(smali_method)
                in_uuids[apk]['uuids'][uuid]['methods'] = all_methods
        with open(path_to_out_json, 'w') as outfile:
           json.dump(in_uuids, outfile, indent=4)
    
    def convert_soot_method_to_smali(self, java_method):
        # Remove leading "<".
        java_method = java_method[1:]
        # Class part is initial bit. Get rid of trailing ":"
        java_class = (java_method.split(' ')[0]).replace(':', '')
        # Convert class part to smali.
        smali_class = 'L' + java_class.replace('.', '/') + ';'
        # Method and partial descriptor are the 3rd component when splitting by space.
        java_method_desc = java_method.split(' ')[2]
        # We only want the method, not descriptor.
        java_method_part = java_method_desc.split('(')[0]
        # Combine class and method parts.
        smali_method = smali_class + '->' + java_method_part
        return smali_method
        
        
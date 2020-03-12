import os
import argparse


class UuidFunctionMapper:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.src_dir = os.path.abspath(os.path.join(
            self.base_dir,
            'src'
        ))
        self.io_dir = os.path.abspath(os.path.join(
            self.base_dir,
            'input-output'
        ))
        self.analyser_dir = os.path.abspath(os.path.join(
            self.src_dir,
            'analyser'
        ))
        sys.path.append(os.path.abspath(self.analyser_dir))
        from analyser import UUIDStatsAnalyser
        stats_analyser = UUIDStatsAnalyser(self.base_dir)

        self.fmap_dir = os.path.abspath(os.path.join(
            self.src_dir,
            'functionality-mapper'
        ))
        sys.path.append(os.path.abspath(self.fmap_dir))
        from apk-matcher import ApkMatcher
        apk_matcher = ApkMatcher(self.base_dir)
        
        self.bool_stats_gather = False
        self.bool_map_functionality = False
        self.argparser = None
        self.fn_set_args()
        self.fn_get_user_args()
        
    def fn_set_args(self):
        self.argparser = argparse.ArgumentParser(
            description = 'A tool for performing functionality mapping'
                          + ' for BLE UUIDs.',
            epilog = 'Note that this tool has only been '
                     + 'tested with Python 3.8.0. '
                     + 'Will NOT work with versions less than 3.4.\n'
        )
        
        self.argparser.add_argument(
            '-s',
            '--stats',
            nargs='?',
            action='store_true',
            const = self.bool_stats_gather,
            default = False,
            help = 'perform statistical analysis '
                   + 'over extracted UUIDs. '
                   + 'Results will be printed to console.'
        )
        
        self.argparser.add_argument(
            '-m',
            '--map',
            nargs='?',
            action='store_true',
            const = self.bool_map_functionality,
            default = False,
            help = 'perform functionality mapping '
                   + 'over extracted UUIDs. '
                   + 'Results will be saved to JSON.'
        )
        
    def fn_get_user_args(self):
        args = self.argparser.parse_args()
        if args.stats:
            self.bool_stats_gather = args.stats
        if args.map:
            self.bool_map_functionality = args.map
        
    def fn_main(self):
        if self.bool_stats_gather == True:
            stats_analyser.fn_get_stats()
        if self.bool_map_functionality == True:
            apk_output = apk_matcher.fn_get_functionality()
            apkoutfile = os.path.join(self.io_dir, 'apk-matcher-output.json')
            with open(apkoutfile, 'w') as f:
                json.dump(apk_output, f, indent=4)
            
            
        
if __name__ == '__main__':
    uuid_function_mapper = UuidFunctionMapper()
    uuid_function_mapper.fn_main()
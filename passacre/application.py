from passacre.config import load as load_config
from passacre.generator import generate_from_config

import argparse
from getpass import getpass
import math
import pprint

class Passacre(object):
    subcommands = 'generate', 'entropy'

    def load_config(self):
        self.config = load_config(open('config.yaml'))

    def generate_action(self, args):
        password = getpass()
        if password != getpass('Confirm password: '):
            raise ValueError("passwords don't match")
        site = raw_input('Site: ')
        print generate_from_config(password, site, self.config)

    def entropy_action(self, args):
        entropy = [
            (site, math.log(site_config['multibase'].max_encodable_value + 1, 2))
            for site, site_config in self.config.iteritems()
        ]
        pprint.pprint(entropy)

    def build_parser(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        for subcommand in self.subcommands:
            subparser = subparsers.add_parser(subcommand)
            args_method = getattr(self, '%s_args' % (subcommand,), None)
            if args_method is not None:
                args_method(subparser)
            subparser.set_defaults(func=getattr(self, '%s_action' % (subcommand,)))
        return parser

    def main(self, args=None):
        self.load_config()
        args = self.build_parser().parse_args(args)
        args.func(args)

def main(args=None):
    Passacre().main(args)

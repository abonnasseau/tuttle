#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
from optparse import OptionParser


def main():
    """Main entry point for the project."""
    usage = 'bin/project'
    parser = OptionParser(usage=usage)
    parser.add_option('-x', '--example',
                  default='example-value',
                  dest='example',
                  help='An example option')
    print "Main"

if __name__ == '__main__':
    sys.exit(main())
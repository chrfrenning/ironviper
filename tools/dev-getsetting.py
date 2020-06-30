#!/usr/bin/env python2.7
import os
import toml
import sys

try:
    configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
    configuration = toml.load(configuration_file_name)

    if ( len(sys.argv) < 2 ):
        print "Specify setting to load as an argument to this process"
        exit(1)
    else:
        print configuration[sys.argv[1]]
        exit(0)
except Exception as ex:
    print ex.message;
    exit(2)
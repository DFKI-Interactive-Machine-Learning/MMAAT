# -*- coding: utf-8 -*-
'''
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
'''
import getopt
import logging as log
import os
import pickle
import sys

def write_csv_header(headers, csvfile):
    '''
        Writes header of results in csv file and appends them to global performance list
        :Parameters:
            headers - list with headers
            csvfile - path to file
    '''
    if  not os.path.exists(os.path.dirname(csvfile)) :
        os.makedirs(os.path.dirname(csvfile))
    with open(csvfile, 'w') as results_file :
        results_file.write(";".join([str(header) for header in headers]))
        results_file.write("\n")
    
def append_results(results, csvfile):
    '''
        Writes results in csv file and appends them to global performance list
        :Parameters:
            results - list with results
            csvfile - path to file
    '''
    with open(csvfile, 'a') as results_file :
        if type(results[0]) == list : 
            for result in results :
                results_file.write(";".join([str(x) for x in result]))
                results_file.write("\n")
        else :
            results_file.write(";".join([str(x) for x in results]))
            results_file.write("\n")
            
def serialize_object(obj, fname) :
    '''
        Serializes a file.
        :Parameters:
            obj - object to serialize
            fname - location of file
    '''
    output = open(fname, 'wb')
    pickle.dump(obj, output)
    output.close()

def unserialize_object(fname):
    '''
        Unserializes a file.
        :Parameters:
            fname - location of serialized object
    '''
    try :
        obj = None
        if os.path.exists(fname) : 
            f_ptr = open(fname, 'rb')
            obj = pickle.load(f_ptr)
            f_ptr.close()
        return obj
    except ValueError :
        log.error("Error occurred while loading cache file")
        return None

class Options (object):
    """
        Options
    """
    def __init__(self):
        self.options = {}
        self.arguments = []

    def add_options(self, option, value):
        self.options[option] = value
        
    def add_argument(self, args):
        self.arguments = args
    
    def set_arguments(self, value):
        self.arguments.append(value)
        
    def has_argument(self, arg):
        return self.arguments.count(arg) > 0
       
    def has_option(self, option): 
        if isinstance(option, list) or isinstance(option, tuple) :
            for opt in option :
                if self.options.has_key(opt) :
                    return True
            return False
        return self.options.has_key(option)
    
    def option(self, opt, default):
        getoption = opt
        if isinstance(opt, list) or isinstance(opt, tuple) :
            for o in opt :
                if self.options.has_key(o) :
                    getoption = o

        try:
            return self.options[getoption] 
        except :
            return default

   
def read_commandline(args, short="chdl:i:o:b:",
                           long_des=["cache", "help", "debug",
                                 "loglevel=", "input=", "output=", "batch="]):
    '''
    Reads the command line and parses options and arguments.
    Parameters:
        args - String
            arguments from the commandline
        short - String 
            short version for options
        long - list of strings 
            long version for options
    Returns:
        Option structure
    '''     
    option = Options()
    try:
        opts, args = getopt.getopt(args, short , long_des)
        for o, a in opts:
            # remove dashes
            if o.startswith("--") :
                o = o[2:]
            if o.startswith("-") :
                o = o[1:]
            option.add_options(o, a)
        for a in args :
            option.add_argument(a)
    except getopt.GetoptError, err:
        # print help information and exit:
        print "ERROR : {0}".format(str(err)) # will print something like "option -a not recognized"
        sys.exit(2)
    return option

def __add_zeros__(num, cnt=2):
    '''
        Adds a defined number of leading zeros.
        Parameters:
            num - Integer
                Number
            cnt - Integer
                length of the number positions
        Returns:
            String with leading zeros if needed
    '''
    cnt = cnt - len(str(num))
    nulls = '0' * cnt
    return '%s%s' % (nulls, num)




# -*- coding: utf-8 -*-
"""
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
"""
import logging
import os
__author__ = "Markus Weber <Markus.Weber@dfki.de>"
__status__ = "alpha"
__version__ = "0.1"
__date__ = "1. July 2013"

LEVELS = {'debug':    logging.DEBUG,
          'info':     logging.INFO,
          'warning':  logging.WARNING,
          'error':    logging.ERROR,
          'critical': logging.CRITICAL}

def calc_indices(desc):
    """
    Calculates an index mapping.
    Arguments:
    desc -- description of features
    Returns:
    mapping
    """
    indices = {}
    for i in xrange(len(desc)) :
        # Nasty quick fix handyY handY bug
        if desc[i] == 'handyY' :
            indices['handY'] = i
        indices[desc[i]] = i
    indices['timestamp'] = len(desc)
    indices['target'] = len(desc) + 1
    indices['seqid'] = len(desc)  + 2
    return indices

def set_descriptions(desc):
    """
        Sets the global descriptions.
        Arguments:
            desc - descriptions used in application.

    """
    global FEATURES, INDICES
    FEATURES = desc
    INDICES = calc_indices(desc)


def merge(labels, default):
    """
    Adds missing labels from default label set.
    Arguments:
    labels  -- already existing labels
    default -- labels which exist by default
    """
    labels.extend([d for d in default if d not in labels])
    return labels


def read_conf(fname):
    """
    Reads values from a conf file.
    Arguments:
        fname -- path to conf file.
    """
    if os.path.exists(fname) :
        with open(fname, 'r') as conffile:
            return [value_name.strip() for  value_name in conffile.readlines()]
    return []


def set_classes(cls):
    """
        Sets the global classes.
        Arguments:
            cls - classes used in application.
    """
    global CLASSES, CLASSIDS
    classes_ini = os.path.join(CONFIG_PATH, 'classes.ini')
    import data
    CLASSES = merge(cls, read_conf(classes_ini))
    for i in xrange(len(CLASSES)) :
        ID_CLASSES[CLASSES[i]] = i


def set_attention(cls):
    """
        Sets attention.
        Arguments:
            cls - classes used in application.
    """


# -------------------------- Directories  ----------------------------------------
MMAAT_SHARE = '/usr/share/MMAAT/data'
RESOURCES_PATH = None
MMAAT_INSTALLED = os.path.exists(MMAAT_SHARE)
if MMAAT_INSTALLED :
    DATA_PATH = MMAAT_SHARE
else : # development structure
    DATA_PATH = os.path.join(os.path.dirname(__file__), '../data')
RESOURCES_PATH = os.path.join(DATA_PATH, 'resources')
CONFIG_PATH    = os.path.join(RESOURCES_PATH, 'config')
IMAGES_PATH    = os.path.join(RESOURCES_PATH, 'images')
ICONS_PATH     = os.path.join(RESOURCES_PATH, 'icons')
# -------------------------- Configuration files ---------------------------------
IGNORE_FEATURES_CONF = os.path.join(CONFIG_PATH, 'ignorefeatures.ini')
FEATURES_CONF        = os.path.join(CONFIG_PATH, 'features.ini')
CLASSES_CONF         = os.path.join(CONFIG_PATH, 'classes.ini')
ATTENTION_CONF       = os.path.join(CONFIG_PATH, 'attention.ini')
# -------------------------- Structures ------------------------------------------
"""
    Structures:
        CLASSES         : List of all classes
        ID_CLASSES      : Mapping from class name to ID
        FEATURES        : Name of all features
        INDICES         : Mapping name of header to index
        IGNORE_FEATURES : Ignore these features when importing

"""
ID_CLASSES      = {}
ID_ATTENTION    = {}
FEATURES        = read_conf(FEATURES_CONF)
CLASSES         = read_conf(CLASSES_CONF)
IGNORE_FEATURES = read_conf(IGNORE_FEATURES_CONF)
ATTENTION       = read_conf(ATTENTION_CONF)
INDICES         = {}

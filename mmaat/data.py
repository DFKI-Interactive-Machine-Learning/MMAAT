# -*- coding: utf-8 -*-
'''
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
'''
import xml.dom.minidom as dom
import csv
import h5py as h5
import mmaat
import mmaat.analysis.processing as p
import numpy as np
import os
import shutil


def fid(feature,desc):
    return desc.index(feature)
def normalization_factors(dset, method='2sigma'):
    nf = len(dset.getSequence(0)[0][0])
    total = 0
    means = np.zeros((nf), dtype=float)
    sds = np.zeros((nf), dtype=float)
    for si in xrange(dset.getNumSequences()) :
        for vec in dset.getSequence(si)[0] :
            total += 1
            for fi in xrange(nf) : means[fi] += vec[fi]
    means /= total
    for si in xrange(dset.getNumSequences()) :
        for vec in dset.getSequence(si)[0] :
            for fi in xrange(nf) : sds[fi] += (vec[fi] - means[fi]) ** 2
    sds /= total
    sds = np.sqrt(sds)
    return means, sds * 2

# -------------------------- PyBrain sequential dataset -----------------------
def add_to_dataset(dset,h5file,features=mmaat.FEATURES, classes=mmaat.CLASSES):
    '''
    Adding data to the sequential dataset.
    Arguments:
    dset     -- dataset
    h5file   -- h5 data file
    features -- Selected features
    '''
    d = list(h5file['data_desc']['description'][:])
    len_classes = len(classes)
    signal = h5file['data']['signal']
    target = h5file['data']['target']

    dset.newSequence()
    for i in xrange(len(signal)) :
        si = signal[i]
        ti = target[i]
        dat = [si[fid(x,d)] for x in features]
        tar = [0] * len_classes
        tar[ti] = 1
        if all([dat[0] == item for item in dat]) :
            continue
        dset.addSample(dat,tar)

def load_numpy_dataset(h5dir,features=mmaat.FEATURES):
    '''
    Load dataset.
    Arguments:
        h5dir    -- directory with h5 files.
        features -- features used

    '''
    dataset = []
    targets = []
    for fname in os.listdir(h5dir) :
        if not fname.endswith(".h5") : continue
        h5file = h5.File(os.path.join(h5dir,fname),"r")
        if not 'classes' in h5file['data_desc'] : continue #file must be labeled
        d = list(h5file['data_desc']['description'][:])
        signal = h5file['data']['signal']
        target = h5file['data']['target']
        for i in xrange(len(signal)) :
            si = signal[i]
            ti = target[i]
            dat = [si[fid(x,d)] for x in features]
            tar = 1 if ti > 0 else 0
            dataset.append(dat)
            targets.append(tar)
        h5file.close()
    return np.array(dataset), np.array(targets)


def read_description(hdf5_obj) :
    '''
    Reads the description from the data structure.

    Arguments:
        h5_obj -- the HDF5 object
    '''
    desc = hdf5_obj['data_desc']['description'][:]
    classes = hdf5_obj['data_desc']['classes'][:]
    if  isinstance(desc, np.ndarray) and desc.shape[0] == 1:
        desc = [desc[0]]
    if  isinstance(classes, np.ndarray) and classes.shape[0] == 1:
        classes = [classes[0]]
    #h5 has own string objects, that do not work with Qt
    desc = [str(x) for x in desc]
    classes = [str(x) for x in classes]
    return desc, classes

def get_array_data_for_object(h5_obj):
    """
    Extracts data from HDF5 object and converts it to a numpy array.

    Arguments:
    h5_obj -- the HDF5 object

    Returns: numpy array with data of 'target' and 'seqid' fields appended to data
             of the 'signal' field in the HDF5 'data' directory
    """
    try :
        signal = h5_obj['data']['signal']
        target = h5_obj['data']['target']
        timestamp = h5_obj['data']['timestamp']
        a = np.zeros((len(signal),len(mmaat.FEATURES) + 3),dtype=np.float32)
        a[:,:-3] = signal
        a[:,-3] = timestamp
        a[:,-2] = target
        return a
    except :
        return np.array()

def get_array_data(fname):
    """
    Reads an HDF5 data file and converts it to a numpy array.

    Arguments:
    fname -- the name of the HDF5 file

    Returns: numpy array with data of 'target' and 'seqid' fields appended to data
             of the 'signal' field in the HDF5 'data' directory
    """
    f = h5.File(fname,'r')
    try :
        return get_array_data_for_object(f)
    finally :
        f.close()

def get_labels(fname):
    """
    Reads targets from a HDF5 data file and converts it to a numpy array.

    Arguments:
    h5_obj -- the HDF5 object

    Returns: numpy array with data of 'target'
    """
    f = h5.File(fname,'r')
    try :
        return get_labels_for_object(f)
    finally :
        f.close()

def get_labels_for_object(h5_obj):
    """
    Reads data from HDF5 object and converts it to a numpy array.

    Arguments:
    h5_obj -- the HDF5 object

    Returns: numpy array with data of 'target'
    """
    labels = h5_obj['data']['target'][:]
    return labels

def read_hand_signature(fname):
    """
    Read hand signature data from csv file and converts it to numpy array.

    Arguments:
    fname -- the name of the csv file

    Returns: numpy array
    """
    if not os.path.exists(fname) :
        return None
    data = []
    with open(fname, 'rb') as csvfile:
        datareader = csv.reader(csvfile, delimiter=',', quotechar='|')
        bHeader = True
        headers = []
        for row in datareader:
            if bHeader :
                for i in xrange(len(row)) :
                    headers.append(row[i])
                bHeader = False
            else :
                data.append([round(float(v), 4) for v in row][::-1])
    return np.array(data, dtype=np.float32)

def read_signatures(dname):
    """
    Read hand signatures from directory

    Arguments:
    dname -- the name of directory

    Returns: numpy array
    """
    signatures = []
    lst = [x for x in os.listdir(dname) if x.endswith('.csv')]
    lst = sorted(lst,key=lambda a : int(a[:-4]))
    for sfile in lst:
        signatures.append(read_hand_signature(os.path.join(dname, sfile)))
    return signatures

def convert_csv_to_hdf(fname, fname_out, preserve_target=True, classes=[], exclude=[], rel_data=[]):
    """
    Read data from csv file and converts it to h5.

    Arguments:
    fname           -- the name of the csv file
    fname_out       -- export hdf5 name
    preserve_target -- if already a h5-file with target exists
    classes         -- list of classes
    exclude         -- list of excludes
    rel_data        -- list of relative data this additionally computes relative features

    """
    lHeader = []
    num_samples = 0
    excludeHeaders = []
    excludeIndex = []
    includeIndex = []
    headerIndex = {}
    data = []
    if not os.path.exists(fname) or not os.path.isfile(fname) :
        return
    with open(fname, 'rb') as csvfile:
        datareader = csv.reader(csvfile, delimiter=',', quotechar='|')
        bHeader = True
        for row in datareader:
            if bHeader :
                for i in xrange(len(row)) :
                    headerIndex[row[i]] = i
                    if row[i] in exclude :
                        excludeHeaders.append(row[i].lower())
                        excludeIndex.append(i)
                    else :
                        lHeader.append(row[i])
                        includeIndex.append(i)

                bHeader = False
            else :
                data.append([round(float(v), 4) for v in row])
                num_samples += 1
    target = None
    for hi in xrange(len(lHeader)) :
        if lHeader[hi] in rel_data :
            lHeader.append('relative {0}'.format(lHeader[hi]))
            index = headerIndex[lHeader[hi]]
            print len(data), " i : ", index, " -> ", lHeader[hi]
            rel = p.absolute_to_relative([val[index] for val in data])
            for i in xrange(len(data)):
                data[i].append(rel[i])
            includeIndex.append(len(data[0])-1)

    if os.path.exists(fname_out) :
        target = get_labels(fname_out) # we want to ensure NOT to use already existing labeled data
        shutil.move(fname_out, '{0}.bck.h5'.format(fname_out))
    else :
        target = np.zeros((num_samples),dtype=np.int32)
    npdata = np.array(data, dtype=np.float32)
    f = h5.File(fname_out,'w')
    try :
        data_group = f.create_group('data')
        data_desc_group = f.create_group('data_desc')
        data_group.create_dataset('seqid', data=np.zeros((num_samples),dtype=np.int32))
        data_group.create_dataset('signal', data=npdata[:, includeIndex])
        for e in xrange(len(excludeHeaders)) :
            data_group.create_dataset(excludeHeaders[e],
                        data=npdata[:,excludeIndex[e]])
        data_group.create_dataset('target', data=target)
        data_desc_group.create_dataset('classes', data=classes)
        data_desc_group.create_dataset('description', data=lHeader)
    finally :
        f.close()


def get_child(node, name):
    """
    Get the child with the given name
    Parameters:
    node -- node
    name -- name of the node
    """
    for n in node.childNodes:
        if name and n.nodeName == name:
            return n

def get_children_of(node):
    """
    Get the element children.

    """
    return filter(lambda x: x.nodeType == x.ELEMENT_NODE, node.childNodes)

def get_float_value(node):
    return float(node.firstChild.data.strip())

def parse_position(node):
    g_local = get_child(node, 'localposition')
    g_pos   = get_child(node, 'globalposition')
    return [get_float_value(get_child(g_local, 'x')), get_float_value(get_child(g_local, 'y')), get_float_value(get_child(g_local, 'z')),
            get_float_value(get_child(g_pos, 'x')), get_float_value(get_child(g_pos, 'y')), get_float_value(get_child(g_pos, 'z'))]

def parse_euler(node):
    x_val = get_child(node, 'x')
    y_val = get_child(node, 'y')
    z_val = get_child(node, 'z')
    return [get_float_value(x_val), get_float_value(y_val), get_float_value(z_val)]

def convert_xmldir_to_hdf(dname, fname_out, preserve_target=True, classes=[], exclude=[], rel_data=[]):
    """
    Read data from csv file and converts it to h5.

    Arguments:
    fname           -- the name of the csv file
    fname_out       -- export hdf5 name
    preserve_target -- if already a h5-file with target exists
    classes         -- list of classes
    exclude         -- list of excludes
    rel_data        -- list of relative data this additionally computes relative features

    """
    lHeader = []
    num_samples = 0
    timestamps = []
    data = {}
    if not os.path.exists(dname) or not os.path.isdir(dname) :
        return
    for tr_xml in [fname for fname in os.listdir(dname) if fname.endswith('.xml')] :
        dom_model = dom.parse(os.path.join(dname, tr_xml))
        timestamps.append(int(fname[:-4]))
        if dom_model.firstChild.nodeName !=  'pose' : continue
        root = dom_model.documentElement
        for angle in  get_children_of(get_child(root, 'joints')) :
            n = 'joint_{0}'.format(str(angle.nodeName))
            if n not in data :
                data[n] = []
            data[n].append(parse_euler(get_child(angle, 'euler')))
        for pos in get_children_of(get_child(root, 'bodyparts')) :
            n = 'position_{0}'.format(str(pos.nodeName))
            if n not in data :
                data[n] = []
            data[n].append(parse_position(pos))
        num_samples += 1
    target = None
    odata = []
    for h, val in data.items() :
        if len(val[0]) == 3 :
            lHeader.append('{0}_x'.format(h))
            lHeader.append('{0}_y'.format(h))
            lHeader.append('{0}_z'.format(h))
            for i in xrange(3) :
                odata.append([v[i] for v in val])
        elif len(val[0]) == 6 :
            lHeader.append('{0}_local_x'.format(h))
            lHeader.append('{0}_local_y'.format(h))
            lHeader.append('{0}_local_z'.format(h))
            lHeader.append('{0}_global_x'.format(h))
            lHeader.append('{0}_global_y'.format(h))
            lHeader.append('{0}_global_z'.format(h))
            for i in xrange(6) :
                odata.append([v[i] for v in val])

    if os.path.exists(fname_out) :
        target = get_labels(fname_out) # we want to ensure NOT to use already existing labeled data
        shutil.move(fname_out, '{0}.bck.h5'.format(fname_out))
    else :
        target = np.zeros((num_samples),dtype=np.int32)
    npdata = np.array(odata, dtype=np.float32).reshape(num_samples, len(lHeader))
    f = h5.File(fname_out,'w')
    try :
        data_group = f.create_group('data')
        data_desc_group = f.create_group('data_desc')
        data_group.create_dataset('timestamps', data=timestamps)
        data_group.create_dataset('seqid', data=np.zeros((num_samples),dtype=np.int32))
        data_group.create_dataset('signal', data=npdata)
        data_group.create_dataset('target', data=target)
        data_desc_group.create_dataset('classes', data=classes)
        data_desc_group.create_dataset('description', data=lHeader)
    finally :
        f.close()

def save_labels(labels, fname):
    '''
    Saves labels to csv.
    Arguments:
    labels -- list of tuples of indices (begin_index, end_index, label)
    fname  -- file path
    '''
    with open(fname, 'wb') as csvfile:
        labelwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        labelwriter.writerow(['begin index', 'end index', 'label'])
        for begin, end, label in labels :
            labelwriter.writerow([begin, end, label])

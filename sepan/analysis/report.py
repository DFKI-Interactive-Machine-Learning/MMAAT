# -*- coding: utf-8 -*-
'''
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
'''
import data_tools as dt
import multiprocessing as mp
import numpy as np
import os

PAMAP_DESC = [
    "ula_x","ula_y","ula_z","lla_x","lla_z", #left arm
    "ura_x","ura_y","ura_z","lra_x","lra_z", #right arm
    "ull_x","ull_y","ull_z","lll_x","lll_z", #left leg
    "url_x","url_y","url_z","lrl_x","lrl_z", #right leg
    "tor_x","tor_y","tor_z", #torso
    "pel_x","pel_y","pel_z" #pelvis
]


def generate_pamap_report_var(dbfile, report_file=None):
    PROCESSOR_POOL = mp.Pool(mp.cpu_count() - 1)
    
    # Create directory for report
    if not (report_file is None) :
        report_path = os.path.dirname(report_file)
        if not os.path.exists(report_path) : os.makedirs(report_path)
    
    #load "gesture" data
    data = np.load(dbfile)
    all_samples = {}
    for k in data.keys() :
        exnr,_ = k.split("/")
        if not exnr in all_samples : all_samples[exnr] = []
        all_samples[exnr].append((data[k],None)) #must be tuple for compatibility with dt.get_gesture_variance
    
    #reduce number of samples where needed
    maxsamp = 20
    for g in all_samples :
        samples = all_samples[g]
        oldlen = len(samples)
        if oldlen <= maxsamp : continue
        nsamples = []
        for _ in xrange(maxsamp) :
            s = samples.pop(np.random.randint(len(samples)))
            nsamples.append(s)
        all_samples[g] = nsamples
        nlen = len(nsamples)
        print "Reduced number of samples for class {:s} from {:d} to {:d}".format(g,oldlen,nlen)
    
    #reset report file
    if not (report_file is None) :
        with open(report_file,'w') as f :
            f.write("gesture 1;gesture 2;feature;variance\n")
    
    #get the variances
    for g1 in all_samples :
        for g2 in all_samples :
            PROCESSOR_POOL.apply_async(dt.get_gesture_variance,(g1, g2, all_samples, PAMAP_DESC, report_file))
    PROCESSOR_POOL.close()
    PROCESSOR_POOL.join()
    dt.variance_report_to_matrices(report_file)

def generate_report_var(data_dir, report_path=None, callback_done=None):
    '''
    Generates a report for a data directory.
    
    Arguments:
        data_dir    -- Directory with all data files
        report_path -- Path where the report should be generated.
    '''
    PROCESSOR_POOL = mp.Pool(mp.cpu_count() - 1)
    if data_dir is None or data_dir == "" : return
    report_path = os.path.join(report_path, 'variances')
    report_file = os.path.join(report_path, 'variance.csv')
    # Create directory for report
    if not (report_file is None) :
        report_path = os.path.dirname(report_file)
        if not os.path.exists(report_path) : os.makedirs(report_path)
    
    # collect all data files
    h5_files = [os.path.join(data_dir, fname) for fname in os.listdir(data_dir) if fname.endswith('.h5') ]
    # extract the gestures 
    all_gestures = {}
    DATA_DESCRIPTION = None
    for h5_file in h5_files :
        gestures, desc = dt.extract_gestures(h5_file, report_path, plotdata=False,ignoreData=['amplitudeThresholdUsed', 'frameNumber','timeStamp',
                                 'errCode','nbCandidate','timeActive', 'class', 'objectID',
                                 'action'])
        DATA_DESCRIPTION = desc
        for key, val in gestures.items() :
            if not all_gestures.has_key(key) :
                all_gestures[key] = []
            all_gestures[key].extend(val)
    
    #reset report file
    if not (report_file is None) :
        with open(report_file,'w') as f :
            f.write("gesture 1;gesture 2;feature;variance\n")
    
    #get the variances
    for g1 in all_gestures :
        for g2 in all_gestures :
            PROCESSOR_POOL.apply_async(dt.get_gesture_variance,(g1, g2, all_gestures, DATA_DESCRIPTION, report_file))
    PROCESSOR_POOL.close()
    PROCESSOR_POOL.join()
    dt.variance_report_to_matrices(report_file)
    if callback_done is not None : callback_done("Variance report")
    

def generate_report_dist(data_dir, report_path=None, callback_done=None):
    '''
    Generates a report for a data directory.
    
    Arguments:
        data_dir    -- Directory with all data files
        report_path -- Path where the report should be generated.
    '''
    PROCESSOR_POOL = mp.Pool(mp.cpu_count() - 1)
    if data_dir is None or data_dir == "" : return
    
    if report_path is None :
        report_path = os.path.join(data_dir, 'report')
    # Create directory for report
    if not os.path.exists(report_path) :
        os.makedirs(report_path)
    # collect all data files
    h5_files = [os.path.join(data_dir, fname) for fname in os.listdir(data_dir) if fname.endswith('.h5') ]
    # extract the gestures 
    all_gestures = {}
    for h5_file in h5_files :
        gestures, desc = dt.extract_gestures(h5_file, report_path, plotdata=False,ignoreData=['amplitudeThresholdUsed', 'frameNumber','timeStamp',
                                 'errCode','nbCandidate','timeActive', 'class', 'objectID',
                                 'action'])
        for key, val in gestures.items() :
            if not all_gestures.has_key(key) :
                all_gestures[key] = []
            all_gestures[key].extend(val)
    results = {}        
    for gesture, _ in all_gestures.items() :
        print "Starting analysis for gesture '{1}' [examples] := {0}".format(gesture, len(all_gestures[gesture]))
        gpath = os.path.join(report_path, gesture)
        if not os.path.exists(gpath) :
            os.makedirs(gpath)
        #dt.analyse_gesture(gpath, gesture, samples)
        results[gesture] = PROCESSOR_POOL.apply_async(dt.analyse_gesture,(gpath, gesture, all_gestures, True))

    PROCESSOR_POOL.close()
    PROCESSOR_POOL.join()
    if callback_done is not None : callback_done("Innerclass distance report")
    #dt.cluster_features(all_gestures, DATA_DESCRIPTION)    
    
# -*- coding: utf-8 -*-
'''
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
'''
from matplotlib import cm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import csv
import h5py as h5
import matplotlib.pyplot as p
import sepan
import sepan.data as data
import numpy as np
import os


def load_images(dirname, ending):
    '''
    Loads PNGs from a directory.
    
    Arguments:
    dirname -- directory with the images of the videos stream
    ending  -- type of image
    '''
    if not os.path.exists(dirname) or not os.path.isdir(dirname) : return []
    img_list = [os.path.join(dirname,x) for x in os.listdir(dirname) if x.endswith(ending)]
    img_list.sort(key = lambda a : int(os.path.basename(a)[:-4]))
    return img_list

def extract_gestures(h5_fname, report_path, plotdata=True, ignoreData=[]) :
    '''
    Extracting gestures from the data files (needs labeled data).
        
    Arguments:
        h5_fname    -- Path to h5 file.
        report_path -- Path of the report.
        plotdata    -- Flag if the data should be plotted. [default=True]
    '''
    h5_obj = h5.File(h5_fname,'r')
    desc, classes = data.read_description(h5_obj)
    indices = sepan.calc_indices(desc)
    # ---- not all information from the signal is relevant --------------
    includeIndex = []
    data_desc = []
    for i in xrange(len(desc)) : 
        if not desc[i] in ignoreData :
            includeIndex.append(indices[desc[i]])
            data_desc.append(desc[i])
    # -------------------------------------------------------------------
    zdirname = h5_fname[:-3] + '_zimage'
    pgmlist = load_images(zdirname, 'pgm')
    timestamps = h5_obj['data']['timestamp'][:]
    signal = h5_obj['data']['signal'][:, includeIndex]
    target = h5_obj['data']['target'][:]
    last_label = target[0]
    start = None
    gdata = {}
    for i in xrange(1, len(target)) :
        if target[i] != last_label :
            if start == None :
                start = i
                last_label = target[i]
            else :
                gesture_path = os.path.join(report_path, classes[last_label])
                if plotdata :
                    plot_gesture_data(gesture_path, '{0}_{1}-{2}'.format(os.path.basename(h5_fname), start, i), 
                                      timestamps[start:i], signal[start:i,], indices)
                current_gesture = classes[last_label]
                if not gdata.has_key(current_gesture) :
                    gdata[current_gesture] = []
                gdata[current_gesture].append((signal[start:i,], pgmlist[start:i], data_desc))
                last_label = target[i]
                start = None
    h5_obj.close()
    return gdata, data_desc

def plot_gesture_data(gesture_path, name, timestamps, signal, indices):
    '''
    Plots the gesture data.
    
    Arguments:
    gesture_path -- Path where to store the gesture data -> each gesture in its own directory
    name         -- Unique name of the gesture.
    timestamps   -- List of timestamp
    signal       -- Signal
    indices      -- indices 
    '''
    # Create directory for report
    if not os.path.exists(gesture_path) :
        os.makedirs(gesture_path)
        
    p3d.plot_hand_data(os.path.join(gesture_path, '{0}'.format(name)), signal, indices)
    p.xlabel('time (s)')
    p.ylabel('values')
    p.legend('nbActivePixels')
    if timestamps == None :
        p.plot(signal)
    else:
        p.plot(timestamps, signal[:, indices['nbActivePixels']])
    p.savefig(os.path.join(gesture_path, 'signal-{0}.png'.format(name)), dpi=200)
    p.close()

def get_gesture_variance(gest1,gest2,all_gestures,desc,report_file):
    """
    Finds the variance between two gestures for each feature
    """
    g1samp = all_gestures[gest1]
    g2samp = all_gestures[gest2]
    n1 = len(g1samp)
    n2 = len(g2samp)
    nf = g1samp[0][0].shape[1]
    skip = 0 #counts how many comparisons where skipped
    data = []
    distances = {}
    for i in xrange(n1) :
        s1 = g1samp[i][0]
        for j in xrange(n2) :
            if gest1 == gest2 and i == j : #do not count distances between identical sequences 
                skip += 1; continue
            s2 = g2samp[j][0]
            for p in xrange(nf):
                if not p in distances : distances[p] = []
                dist, _, path = mlpy.dtw_std(s1[:,p], s2[:,p], dist_only=False, squared=True)
                p_len = len(path[0])
                ndist = dist / float(p_len)
                distances[p].append(ndist)
    N = n1*n2 - skip
    variances = []
    with open(report_file,'a') as f :
        for p in xrange(nf) :
            var = 1.0*np.sum(distances[p])/N
            variances.append(var)
            f.write("{gest1:s};{gest2:s};{feature:s};{var:.3f}\n".format(gest1=gest1,gest2=gest2,feature=desc[p],var=var))
    print "Variances between '{:s}' and '{:s}' have been calculated".format(gest1,gest2)
    return variances

def variance_report_to_matrices(report_file):
    path = os.path.dirname(report_file)
    data = np.loadtxt(report_file,delimiter=";",dtype=object,skiprows=1)
    gestures = []
    features = []
    hashmap = {}
    
    for i in xrange(len(data)) :
        if len(data[i]) < 4 :
            print data[i]
            continue
        g1  = data[i][0]
        g2  = data[i][1]
        f   = data[i][2]
        var = data[i][3]
        if g1 not in gestures : gestures.append(g1)
        if f not in features : features.append(f)
        hashmap[g1+g2+f] = float(var)
    gestures = sorted(gestures)
    features = sorted(features)
    N = len(gestures)

    #M = len(features)
    varmats = []
    binmats = []
    for f in features :
        img_file = os.path.join(path,"var_{:s}.png".format(f))
        img_file_bin = os.path.join(path,"bin_{:s}.png".format(f))
        print "Processing feature {}".format(f)
        mat = np.zeros((N,N),dtype=float)
        for i in xrange(N) :
            for j in xrange(N) :
                mat[i,j] = hashmap[gestures[i]+gestures[j]+f] if hashmap.has_key(gestures[i]+gestures[j]+f) else 0.
        save_gesture_matrix(mat,gestures,img_file)
        
        binmat = np.zeros((N,N),dtype=int)
        for i in xrange(N) :
            for j in xrange(N) :
                distinctive = mat[i,i] < 0.8*mat[i,j] and mat[j,j] < 0.8*mat[i,j]
                binmat[i,j] = distinctive
        save_gesture_matrix(binmat,gestures,img_file_bin)
        varmats.append(mat)
        binmats.append(binmat)
    varsum = np.sum(varmats,axis=0)
    binsum = np.sum(binmats,axis=0)
    save_gesture_matrix(binsum,gestures,os.path.join(path,"SUM_bin.png"))
    save_gesture_matrix(varsum,gestures,os.path.join(path,"SUM_var.png"))

def save_gesture_matrix(mat,gestures,fname):
    N = len(gestures)
    F = p.figure()
    F.subplots_adjust(left=0.1,right=0.9,top=0.9,bottom=0.15,wspace=0,hspace=0)
    ax = F.add_subplot(111)
    ax.imshow(mat)
    ax.set_xticks(range(N))
    ax.set_xticklabels(gestures,rotation="vertical")
    ax.set_yticks(range(N))
    ax.set_yticklabels(gestures,rotation="horizontal")
    F.savefig(fname)
    p.close(F)
    
def analyse_gesture(report_path, gesture, all_samples, vis_debug=False) :
    '''
        Analysis the gesture and looks for the best feature.
        
        Arguments:
            report_path -- path for report 
            gesture     -- gesture
            samples     -- sample instances
    '''
    distances = []
    summary_features = {}
    samples = all_samples[gesture]
    DESCRIPTIONS = samples[0][2]
    stats = {}
    for i in xrange(len(samples)) : 
        for j in xrange(i+1, len(samples)):
            s1 = samples[i][0]; s2 = samples[j][0]
            # Only calculate the statistics for a sequence once  
            if not stats.has_key(i) :
                stats[i] = (np.mean(s1, axis=0), np.var(s1, axis=0), np.std(s1, axis=0))
            if not stats.has_key(j) :
                stats[j] = (np.mean(s2, axis=0), np.var(s2, axis=0), np.std(s2, axis=0))
            # -------------------------------------------------
            #dimg1 = samples[i][1];dimg2 = samples[j][1]  
            for p in xrange(s1.shape[1]): 
                dist, cost, path = mlpy.dtw_std(s1[:,p], s2[:,p], dist_only=False, squared=True)
                p_len = len(path[0])
                ndist = dist / float(p_len)
                mean_var =  np.mean([stats[i][2][p], stats[j][2][p]])
                ndist_u = ndist / mean_var if  mean_var > 0 else ndist
                if vis_debug :
                    # Create a directory for each gesture
                    path = os.path.join(report_path,DESCRIPTIONS[p])
                    if not os.path.exists(path) :
                        os.makedirs(path)
                    save_cost_matrix(s1[:,p], s2[:,p], cost, path, dist, os.path.join(report_path, '{0}-{1}.png'.format(i,j)))
                distances.append((DESCRIPTIONS[p], i, j, dist, ndist, ndist_u, stats[i][0][p], stats[i][1][p], stats[i][2][p], 
                                                                               stats[j][0][p], stats[j][1][p], stats[j][2][p]))
    with open(os.path.join(report_path, 'feature_analysis.csv'), 'wb') as csvfile:
        feat_an_writer = csv.writer(csvfile, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        feat_an_writer.writerow(['feature', 'signal 1 ID', 'signal 2 ID', 'distance', 'normalized distance', 'experimental distance',
                                  'mean (s1)', 'var (s1)', 'std (s1)', 'mean (s2)', 'var (s2)', 'std (s2)' ])
        for row in distances :
            feat_an_writer.writerow([str(val).replace('.', ',') for val in row])
    with open(os.path.join(report_path, 'feature_analysis_summary.csv'), 'wb') as summary_file :
        summary = csv.writer(summary_file, delimiter=';',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        
        for val in distances :
            if not summary_features.has_key(val[0]) :
                summary_features[val[0]] = []
            summary_features[val[0]].append(val[1:])
        summary.writerow(['feature', 'mean distance', 'mean norm distance', 'max normalized distance', 'min normalize distance', 'mean experimental distance', 'max experimental distance', 'min experimental distance',])        
        for feat, samples in summary_features.items() :
            list_dist = [v[2] for v in samples]
            list_dist_norm = [v[3] for v in samples]
            list_edist_norm = [v[4] for v in samples]
            summary.writerow([feat, str(np.mean(list_dist)).replace('.', ','), 
                                    str(np.mean(list_dist_norm)).replace('.', ','), 
                                    str(np.max(list_dist_norm)).replace('.', ','), 
                                    str(np.min(list_dist_norm)).replace('.', ','),
                                    str(np.mean(list_edist_norm)).replace('.', ','), 
                                    str(np.max(list_edist_norm)).replace('.', ','), 
                                    str(np.min(list_edist_norm)).replace('.', ',')])
    return distances, summary_features, stats
    
def save_cost_matrix(seq1, seq2, cost, path, dist, img):
    ''' 
        Saves the cost matrix of a comparison of two sequences.
        :Parameters:
            seq   - timestamps
            signal - signal
            freqs  - frequency
            pxx    - 
            img    - location of image
    
    '''
    fig = p.figure(1)
    p.grid(True)
    ax = fig.add_subplot(111)
    cax = ax.imshow(cost.T, origin='lower', cmap=cm.get_cmap('gist_heat_r'), interpolation='nearest')
    ax.plot(path[0], path[1], 'w')
    
    ax.set_aspect(1.)
    divider = make_axes_locatable(ax)
    axSeq1 = divider.append_axes("top", 1.2, pad=0.1, sharex=ax)
    axSeq2 = divider.append_axes("left", 1.2, pad=0.1, sharey=ax)
    ax_cb = divider.new_horizontal(size="5%", pad=0.05)
    fig.add_axes(ax_cb)
    axSeq1.plot(seq1)
    axSeq1.set_ylim(np.amin(seq1), np.amax(seq1))
    axSeq2.set_xlim(np.amin(seq2), np.amax(seq2))
    axSeq2.plot(seq2, range(0, len(seq2)))
    
    for tl in axSeq1.get_xticklabels():
        tl.set_visible(False)
    for tl in axSeq2.get_xticklabels():
        tl.set_visible(False)
    for tl in ax.get_yticklabels():
        tl.set_visible(False)
    
    ax.set_xlim((0., cost.shape[0]))
    ax.set_ylim((0., cost.shape[1]))
    cbar = p.colorbar(cax, cax=ax_cb)
    ax_cb.yaxis.tick_right()
    cbar.set_label('Distance')
    p.savefig(img, dpi=300)
    p.close()
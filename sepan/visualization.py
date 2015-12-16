# -*- coding: utf-8 -*-
'''
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
'''
from sepan import INDICES
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import os


def plot_hand_trajectory(data,frm=None,to=None):
    """
    Shows a 3D plot of the hand position (blue) and finger position (red)

    Arguments:
    data -- the data to visualize as numpy array (same format as returned by get_array_data())

    Keyword-Arguments:
    frm -- starting index from which to plot (default 0)
    to  -- end index of plotting range (default len(data))
    """
    if frm is None : frm = 0
    if to is None : to = len(data)
    f = plt.figure()
    ax = f.add_subplot(111, projection="3d")

    #prune data from 0-lines
    #data = [x for x in data if x[INDICES["nbCandidate"]] > 0]
    #data = np.array(data,dtype=int)

    fi = ["fingerX","fingerY","fingerZ"]
    finger = [data[frm:to,INDICES[i]] for i in fi]
    hi = ["handX","handyY","handZ"]
    hand = [data[frm:to,INDICES[i]] for i in hi]
    ax.plot(finger[0],finger[1],finger[2],color="blue")
    ax.plot(hand[0],hand[1],hand[2],color="red")
    plt.show()


def plot_recognition(inputs, classification, gt, dname, hz=50, labels=None, xoff=0, xtick_span=None, figsize=None, stepsize=500):
    """
    Constructs a evaluation plot for early recognition

    :Parameters:
        inputs     - a numpy array containing the network input (i.e. the sensor data)
        output     - a numpy array containing the network classification
        output_gt  - a numpy array containing the ideal ground truth classification output
        output_raw - a numpy array containing the raw network output
        dname      - the directory name where the plot should be stored

    :Keyword-Paramters:
        hz     - the sampling frequency (used for x axis labels)
        labels - a list of labels for the exercise classes
    """
    if figsize is None : figsize = (20, 10)
    if xtick_span is None : xtick_span = len(inputs) / 10
    if not os.path.exists(dname) : os.makedirs(dname)

    for b in np.arange(0, len(gt), stepsize) :
        e = b + stepsize
        xvals = [1.0 * (x + xoff) / 30 for x in xrange(len(inputs[b:e]))]
        xlim = (xvals[0], xvals[-1])
        xticks = np.arange(np.ceil(xvals[0] / 50) * 50, xvals[-1], xtick_span)
        xticklabels = np.array(xticks, dtype=int)
        f = plt.figure(figsize=figsize, dpi=200)
        ax = f.add_subplot(211)
        ax.set_title("RAW Input")
        ax.plot(xvals, inputs[b:e])
        ax.set_xlim(xlim)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        # ax.set_xlabel("time[s]")
        ax.set_ylabel("signal")

        ax = f.add_subplot(212)
        ax.set_title("Classification")
        ax.plot(xvals, gt[b:e], color="blue", label="ground truth")
        ax.plot(xvals, classification[b:e], color="red", label="classification")
        ax.set_xlim(xlim)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        ax.set_ylim((0, len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.grid(True, axis='y')
        # ax.set_xlabel("time[s]")
        ax.set_ylabel("class")
        ax.legend()
        f.subplots_adjust(left=0.07, right=0.95)
        f.savefig(os.path.join(dname,'{0}-{1}.png'.format(b, e)))
        plt.close(f)

def make_plot(inputs,output,output_gt,output_raw,fname,hz=30,labels=None,xoff=0,xtick_span=None,figsize=None, stepsize=500):
    """
    Constructs a evaluation plot for early recognition

    Parameters:
        inputs     - a numpy array containing the network input (i.e. the sensor data)
        output     - a numpy array containing the network classification
        output_gt  - a numpy array containing the ideal ground truth classification output
        output_raw - a numpy array containing the raw network output
        fname      - the file name where the plot should be stored

    Keyword-Paramters:
        hz     - the sampling frequency (used for x axis labels)
        labels - a list of labels for the exercise classes
    """
    if labels is None : labels = ["BLANK", "GESTURE"]
    if figsize is None : figsize = (20,10)
    if xtick_span is None : xtick_span = len(inputs)/10

    for b in np.arange(0, len(output_gt), stepsize) :
        e = b + stepsize
        xvals = [1.0*(x+xoff)/30 for x in xrange(len(inputs[b:e]))]
        xlim = (xvals[0],xvals[-1])
        xticks = np.arange(np.ceil(xvals[0]/50)*50,xvals[-1],xtick_span)
        xticklabels = np.array(xticks,dtype=int)
        f = plt.figure(figsize=figsize,dpi=200)
        ax = f.add_subplot(311)
        ax.set_title("Raw Input")
        ax.plot(xvals,inputs[b:e])
        ax.set_xlim(xlim)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        #ax.set_xlabel("time[s]")
        ax.set_ylabel("signal")

        ax = f.add_subplot(312)
        ax.set_title("Classification")
        ax.plot(xvals,output_gt[b:e],color="blue",label="ground truth")
        ax.plot(xvals,output[b:e],color="red",label="classification")
        ax.set_xlim(xlim)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        ax.set_ylim((0,len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.grid(True,axis='y')
        #ax.set_xlabel("time[s]")
        ax.set_ylabel("class")
        ax.legend()

        ax = f.add_subplot(313)
        ax.set_title("Raw Output")
        lines = ax.plot(xvals,output_raw[b:e])
        ax.set_xlim(xlim)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        ax.set_ylim((-0.1,1.3))
        ax.set_xlabel("time[s]")
        ax.set_ylabel("net output")
        ax.legend(lines,labels,ncol=len(lines),loc="best",fontsize="x-small")

        f.subplots_adjust(left=0.07,right=0.95)

        f.savefig('{0}_{1}-{2}.png'.format(fname, b, e))
        plt.close(f)

# -*- coding: utf-8 -*-
'''
 DFKI GmbH 200x - 2011
 All rights reserved.
 Maintainer: Markus Weber
'''
from matplotlib import mlab
from scipy.fftpack import fft
from scipy.signal import kaiserord, firwin
from scipy.signal.signaltools import lfilter
import numpy as np

def signal_filter(data, SAMPLE_RATE = 100):
    '''
        Signal filter
    '''
    
    #------------------------------------------------
    # Create a FIR filter and apply it to x.
    #------------------------------------------------
    
    # The Nyquist rate of the signal.
    nyq_rate = SAMPLE_RATE / 2.0
    # The desired width of the transition from pass to stop,
    # relative to the Nyquist rate.  We'll design the filter
    # with a 5 Hz transition width.
    width = 10.0 / nyq_rate
    # The desired attenuation in the stop band, in dB.
    ripple_db = 70.0
    # Compute the order and Kaiser parameter for the FIR filter.
    N, beta = kaiserord(ripple_db, width)
    # The cutoff frequency of the filter.
    cutoff_hz = 1.0
    # Use firwin with a Kaiser window to create a lowpass FIR filter.
    taps = firwin(N, cutoff_hz / nyq_rate, window=('kaiser', beta))
    # Use lfilter to filter x with the FIR filter.
    filtered_x = lfilter(taps, 1.0, data)
    return filtered_x


def smooth(x, window_len=50, window='hanning'):
    """
    Smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal (1 dim)
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."


    if window_len < 3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


    s = np.r_[2 * x[0] - x[window_len:1:-1], x, 2 * x[-1] - x[-1:-window_len:-1]]
    if window == 'flat': #moving average
        w = np.ones(window_len, 'd')
    else:
        w = eval('np.{0}(window_len)'.format(window))

    y = np.convolve(w / w.sum(), s, mode='same')
    return y[window_len - 1:-window_len + 1]


def autocorr(x):
    '''
        Performs an autocorrelation on the signal.
        :Paramters:
            x - array of values (1 dim)
        :Return:
            autocorrelation
    '''
    result = np.correlate(x, x, mode='full')
    return result[result.size / 2:]

def fft_transform(x):
    '''
        Performs an fourier transformation on the signal.
        :Paramters:
            x - array of values
        :Return:
            fft
    '''
    return fft(x)
   
def psd(signal, RATE=100):
    ''' 
        Computes the power density spectrum for a signal.
        :Parameters:
            signal - signal
            RATE - is the sampling frequency.
        :Returns:
            power density spectrum
    '''
    pxx, freqs = mlab.psd(signal, Fs=RATE)
    return pxx, freqs

def absolute_to_relative(series):
    '''
        Normalizes the timeseries.
        :Parameters:
            series - series with absolute values
        :Returns:
            relative series -  sequence of values v_i - v_i-1
    '''
    rel_list = [float(series[vi] - series[vi-1]) for vi in xrange(1, len(series))]
    rel_list.insert(0, series[0])
    if isinstance(series, np.ndarray) :
        return np.array(rel_list)
    return rel_list
        

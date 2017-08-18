# -*- coding: utf-8 -*-
'''
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
'''
from PyQt4 import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from mmaat.ui.models.sensordata import SensorDataModelSegment
import logging
import matplotlib.pyplot as plt
import numpy as np
import time

log = logging.getLogger("mmaat.ui.widgets.plots")


def hexcolor(color) :
    r = hex(color[0])[2:]
    g = hex(color[1])[2:]
    b = hex(color[2])[2:]
    if len(r) == 1 : r = "0"+r
    if len(g) == 1 : g = "0"+g
    if len(b) == 1 : b = "0"+b
    return r+g+b

def textypos_by_ylim(ylim):
    return ylim[1] - 0.1 * abs(ylim[1] - ylim[0])

class SensorPyplotView(FigureCanvas):
    mouse_released = QtCore.pyqtSignal(QtGui.QMouseEvent)
    mouse_pressed_left = QtCore.pyqtSignal(QtGui.QMouseEvent)
    mouse_pressed_right = QtCore.pyqtSignal(QtGui.QMouseEvent)
    mouse_dragged_left = QtCore.pyqtSignal(QtGui.QMouseEvent)
    mouse_dragged_right = QtCore.pyqtSignal(QtGui.QMouseEvent)
    ylim_changed = QtCore.pyqtSignal(float,float)
    xlim_changed = QtCore.pyqtSignal(float,float,bool)
    subplotbounds = [0.02,0.98,0.02,0.98]
    def __init__(self, UPDATE_FRAMERATE=25):
        self.seg_default_color = "#99BB99"
        self.figure = plt.Figure(figsize=(8, 4), dpi=100)
        plt.ion()
        self.figure.subplots_adjust(
            left=self.subplotbounds[0],
            right=self.subplotbounds[1],
            bottom=self.subplotbounds[2],
            top=self.subplotbounds[3])
        FigureCanvas.__init__(self,self.figure)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        self.eval_seg = None
        self.eval_ref_seg = None
        self.model = None
        self.lines = {}
        self.anim = None
        self.ylim = (0,0)
        ''' Segments '''
        self.segments = {}
        self.segment_labels = {}
        self.segment_colors = {}
        self.drawing_trigger = False
        '''--------------------------------------'''
        self.updates = 0
        ''' Update timer '''
        self.update_time = 0.05
        self.cum_update_time = 0
        self.timer_id = -1
        self.last_update = time.time()
        self.sleep_time = (1. / UPDATE_FRAMERATE) * 1000
        # save the clean slate background -- everything but the animated line
        # is drawn and saved in the pixel buffer background
        self.background = None
        self.canvas = None
        self.axes = None
        self.old_size = None
        self.old_xlim = None
        self.old_ylim = None
        self.has_new_data = False
        self.autoscale_y = False


    def set_model(self,model):
        '''
        Sets the model with the sensordata.
        :Parameters:
            model - Sensor data model
        '''
        self.model = model
        self.model.dataset_changed.connect(self._has_new_data_slot)
        self.model.new_dataset.connect(self.new_plot)
        self.model.sig_update_channels.connect(self._has_new_data_slot)

    def mouseMoveEvent(self, event):
        if not self.isEnabled(): return
        if int(event.buttons()) == QtCore.Qt.LeftButton:
            self.mouse_dragged_left.emit(event)
        elif int(event.buttons()) == QtCore.Qt.RightButton:
            self.mouse_dragged_right.emit(event)
    def mouseReleaseEvent(self, event):
        if not self.isEnabled() : return #disable all functionality
        self.mouse_released.emit(event)
    def mousePressEvent(self, event):
        if int(event.buttons()) == QtCore.Qt.RightButton:
            self.mouse_pressed_right.emit(event)
        elif int(event.buttons()) == QtCore.Qt.LeftButton:
            self.mouse_pressed_left.emit(event)
    def _has_new_data_slot(self):
        self.has_new_data = True
        self.data_changed()
    def new_plot(self):
        #clear old data
        for sid in self.segments.keys()[:] : self.remove_segment(sid)
        for k in self.lines.keys() : self._rmline(k)
        if self.anim != None : self.anim.remove()
        self.anim = None
        self.figure.clf()
        y_min = float("inf")
        y_max = -float("inf")
        x_min = 0
        #insert new data
        if not self.model is None :
            x_min = self.model.get_data_offset()
            self.axes = self.figure.add_subplot(111)
            self.axes.set_autoscaley_on(False)
            self.axes.set_autoscalex_on(False)
            # Store figure size
            self.old_size = self.axes.bbox.width, self.axes.bbox.height
            vchan = self.model.get_visible_channels()
            for c in vchan :
                xdata,ydata = self._getxy(c)
                ls = self.axes.plot(xdata,ydata,color=np.array(c.get_color())/255.0, animated=True,linestyle="-")
                self.lines[str(c.get_channel_id())+"/"+c.get_name()] = ls[0] # it is only one line
                if len(ydata) > 0 :
                    yspan = (min(ydata),max(ydata))
                    if yspan[0] < y_min : y_min = yspan[0]
                    if yspan[1] > y_max : y_max = yspan[1]
            if len(vchan) == 0 : y_min,y_max = (-1,1)
            self.axes.grid()
            self.draw()
        self.ylim = [y_min,y_max]
        if not self.lines is None :
            # Setting the boundaries
            x_max = x_min + len(self.model)
            self.axes.set_xlim(x_min, x_max)
            self.axes.set_ylim(self.ylim[0],self.ylim[1])
            self.old_xlim = (x_min,x_max)
            self.old_ylim = self.ylim
            self.xlim_changed.emit(x_min,x_max,False)
            self.ylim_changed.emit(self.ylim[0],self.ylim[1])
        yticks = self.axes.get_yticklabels()
        for t in yticks :
            t.set_size("x-small")
        xticks = self.axes.get_xticklabels()
        for t in xticks :
            t.set_size("x-small")
        self.canvas = self.figure.canvas
        self.background = self.canvas.copy_from_bbox(self.axes.bbox)
        self.data_changed()

    def _rmline(self,key):
        if not key in self.lines : return
        del self.lines[key]

    def _ckey(self,channel):
        return str(channel.get_channel_id())+"/"+channel.get_name()

    def set_segments(self,segments):
        '''
            Sets the segments.
            :Parameters:
                segments - dict with segments
        '''
        if self.axes == None : return
        for k in self.segments.keys() :
            self.remove_segment(k)
        for s in segments :
            self.add_segment(s)
        self.data_changed()

    def add_segment(self,segment,color=None,alpha=0.5):
        '''
        Adds a segment with a defined color.
        :Parameters:
            segment - segment
            color - color of the segment
            alpha - alpha value of segment
        '''
        if self.axes == None or segment == None : #
            return #for robustness
        if color == None :
            color = self.seg_default_color
        else :
            color = "#"+hexcolor(color)
        start,end = segment.get_bounds()
        sid = segment.get_sid()
        idx = segment.get_idx()
        self.segments[sid] = self.axes.axvspan(start,end,color=color,alpha=alpha,animated=True)
        self.segment_colors[sid] = color
        if not (self.model.get_label(idx, sid) is None) : #only add label text if this is a DATA segment
            self.segment_labels[sid] = self.axes.annotate(
                segment.get_name(),(start,0),
                xytext=(start,textypos_by_ylim(self.ylim)),
                textcoords="data",
                animated=True,
                fontsize="small"
            )
            self.set_segment_color(sid,self.model.get_label_color(sid))
        self.data_changed()

    def set_segment_color(self,sid,newcolor=None):
        '''
        Sets the color of a segment.
            sid - id of the segment
            newcolor - new color of the segment
        '''
        if not self.segments.has_key(sid) : return
        seg = self.segments[sid]
        if not newcolor is None :
            col = "#"+hexcolor(newcolor)
        else :
            col = self.seg_default_color
        seg.set_color(col)
        self.segment_colors[sid] = col
        self.data_changed()

    def remove_segment(self,sid):
        '''
        Removes a segment.
            sid - id of the segment
        '''
        if not sid in self.segments.keys() : return
        self.segments[sid].remove()
        del self.segments[sid]
        del self.segment_colors[sid]
        if sid in self.segment_labels :
            del self.segment_labels[sid]
        self.data_changed()

    def set_segments_visible(self,vis):
        for sid in self.segments :
            line = self.segments[sid]
            line.set_visible(vis)
        self.data_changed()

    def set_segment_visible(self,sid,vis):
        if not sid in self.segments : return #robustness fix
        line = self.segments[sid]
        line.set_visible(vis)
        self.data_changed()

    def update_segment(self,a1,a2=None,a3=None):
        '''
        Updates the segments.
        '''
        if a2 == None or a3 == None :
            sid = a1.get_sid()
            idx = a1.get_idx()
            start,end = a1.get_bounds()
        else :
            sid,start,end = (a1,a2,a3)
        if not sid in self.segments.keys() :
            self.add_segment(SensorDataModelSegment(idx, sid,start,end))
        else :
            boundary = self.segments[sid].get_xy()
            boundary[0,0] = start
            boundary[1,0] = start
            boundary[2,0] = end
            boundary[3,0] = end
            self.segments[sid].set_xy(boundary)
            if sid in self.segment_labels :
                self.set_segment_color(sid,self.model.get_label_color(sid))
                self.segment_labels[sid].set_text(self.model.get_label(idx,sid).get_name())
                self.segment_labels[sid].xyann = (start,textypos_by_ylim(self.ylim))
        self.data_changed()

    def data_changed(self):
        if self.drawing_trigger or not self.isVisible() : return
        since_last = time.time() - self.last_update
        wait_for = max((0, self.sleep_time - since_last))
        QtCore.QTimer.singleShot(wait_for, self.draw_plot)
        self.drawing_trigger = True

    def resizeEvent(self, event):
        FigureCanvas.resizeEvent(self, event)
        self.draw_plot()

    def update_plot(self):
        if self.axes is None : return
        self.axes.grid()
        if not self.model is None :
            active_channels = self.model.get_visible_channels()
            active_keys = [self._ckey(c) for c in active_channels]
            for k in self.lines.keys() :
                #remove lines that have been disabled
                if not k in active_keys :
                    self._rmline(k)
                    continue
                #update data
                idx = active_keys.index(k)
                c = active_channels[idx]
                l = self.lines[k]
                xdata,ydata = self._getxy(c)
                l.set_ydata(ydata)
                l.set_xdata(xdata)

            #add lines that where enabled
            for i in xrange(len(active_channels)) :
                if not active_keys[i] in self.lines.keys() :
                    c = active_channels[i]
                    xdata,ydata = self._getxy(c)
                    ls = self.axes.plot(xdata,ydata,color=np.array(c.get_color())/255.0, animated=True,linestyle='-')
                    self.lines[active_keys[i]] = ls[0]
            if self.autoscale_y :
                ymin,ymax = self.model.get_visible_yspan()
                self.axes.set_ylim((ymin,ymax))
                self.ylim_changed.emit(ymin,ymax)
        self.data_changed()

    def animation_step(self,i):
        if self.axes == None : return
        if not self.anim is None :
            self.anim.remove()
        self.anim = self.axes.vlines(i,self.axes.axis()[2],self.axes.axis()[3],linestyles="dashed",color="black", animated=True)
        self.data_changed()

    def get_number_of_samples(self):
        return self.model.get_number_of_samples()

    def get_ylim(self):
        if self.axes == None : return None
        return self.axes.get_ylim()

    def get_xlim(self):
        if self.axes == None : return None
        return self.axes.get_xlim()

    def set_ylim(self,bottom,top=None,silent=False):
        if self.axes == None : return # robustness fix
        if top == None : bottom,top = bottom # enables passing of tuples as only argument
        self.ylim = [bottom,top]
        self.axes.set_ylim(self.ylim)
        for k in self.segment_labels :
            l = self.segment_labels[k]
            l.xytext = (l.xytext[0],textypos_by_ylim(self.ylim))
        self.data_changed()
        if not silent : self.ylim_changed.emit(bottom,top)

    def set_xlim(self,bottom,top=None,silent=False):
        if self.axes == None : return #robustness fix
        if top == None : bottom,top = bottom # enables passing of tuples as only argument
        do = self.model.get_data_offset()
        l = len(self.model)
        ds = self.model.get_data_size()
        if self.model != None and (do > bottom or top > do+l) and top < ds :
            log.warning("trying to display data that is not in memory (xlim {xmin},{xmax} / memory buffer {bmin},{bmax})".format(
                xmin=bottom,
                xmax=top,
                bmin=do,
                bmax=do+l)
            )
        self.axes.set_xlim([bottom,top])
        self.data_changed()
        self.xlim_changed.emit(bottom,top,silent)

    def draw_plot(self):#timerEvent(self, evt):
        '''
            Called by the update mechanism.
        '''
        st = time.time()
        try :
            if self.canvas is None or self.axes is None: return
            self.axes.grid()
            if self.has_new_data :
                self.update_plot()
                self.has_new_data = False
            current_size = self.axes.bbox.width, self.axes.bbox.height
            current_xlim = self.axes.get_xlim()
            current_ylim = self.axes.get_ylim()
            if self.old_size != current_size \
              or current_xlim[0] != self.old_xlim[0] or current_xlim[1] != self.old_xlim[1] \
              or current_ylim[0] != self.old_ylim[0] or current_ylim[1] != self.old_ylim[1] :
                yticks = self.axes.get_yticklabels()
                for t in yticks :
                    t.set_size("x-small")
                xticks = self.axes.get_xticklabels()
                for t in xticks :
                    t.set_size("x-small")
                self.old_size = current_size
                self.old_ylim = current_ylim
                self.old_xlim = current_xlim
                self.draw()
                self.background = self.copy_from_bbox(self.axes.bbox)

            self.canvas.restore_region(self.background)
            self.draw_lines()
            self.draw_segments()
            self.draw_anim_line()
            # just redraw the axes rectangle
            self.blit(self.figure.bbox)
            self.updates += 1
            self.last_update = time.time()
        finally :
            self.update_time = time.time() - st # for debug issues
            self.cum_update_time += self.update_time
            #if self.updates > 0 : self.update_time = self.cum_update_time * 1.0 / self.updates #TODO remove
            self.drawing_trigger = False

    def draw_lines(self):
        '''
        Draws the lines in the plot.
        '''
        for k in self.lines.keys() :
            self.axes.draw_artist(self.lines[k])

    def draw_segments(self):
        '''
        Draws the segments in the plot.
        '''
        for k in self.segments.keys() :
            self.axes.draw_artist(self.segments[k])
            if k in self.segment_labels :
                self.axes.draw_artist(self.segment_labels[k])

    def draw_anim_line(self):
        '''
        Draws the vertical animation line.
        '''
        if not self.anim is None :
            self.axes.draw_artist(self.anim)
    def showEvent(self,evt):
        FigureCanvas.showEvent(self,evt)
        if (evt) : self.data_changed() #draw changes that have happened since we where last visible
    def _getxy(self,channel):
        y = channel.get_data()[::4] #TODO no hardcoded subsampling
        x = np.arange(len(y))*4 + channel.get_offset()
        return x,y
    def set_autoscale_y(self,auto):
        self.autoscale_y = auto


class SegmentPyplotView(FigureCanvas):
    new_segment_bounds = QtCore.pyqtSignal()
    def __init__(self,text=""):
        self.figure = plt.Figure(figsize=(4, 2), dpi=100)
        plt.ion()
        self.subplotbounds = [0.05,0.95,0.05,0.95]
        self.figure.subplots_adjust(
            left=self.subplotbounds[0],
            right=self.subplotbounds[1],
            bottom=self.subplotbounds[2],
            top=self.subplotbounds[3])
        FigureCanvas.__init__(self,self.figure)
        self.canvas = self.figure.canvas
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        self.data_model = None
        self.vis_model = None
        self.segment = (0,0)
        self.has_new_data = False
        self.axes = self.figure.add_subplot(111)
        self.axes.annotate(text,(0,1),xytext=(5,-18),textcoords="offset points",xycoords="axes fraction",size="x-small")
        self.axes.set_autoscaley_on(False)
        self.axes.set_autoscalex_on(False)
        self.lines = {}
        self.ylim = [0,0]
        self.ymin_auto = -1 #remember minimum y value from channel data
        self.ymax_auto = 1 #remember maximum y value from channel data
        self.background = None
        self.drawing_trigger = False
        self.background_changed = False
        self.sleep_time = 1000 / 30.0
        self.last_update = time.time()

    def set_models(self,data_model,visibility_model):
        self.data_model = data_model
        self.vis_model = visibility_model
        self.vis_model.sig_update_channels.connect(self.data_changed)

    def set_segment_bounds(self,start=None,end=None,bounds=None):
        if bounds != None :
            start,end = bounds
        if start == None : start = self.segment[0]
        if end == None : end = self.segment[1]
        if start >= end : raise Exception("SegmentPyplotView: invalid segment (start({start}) >= end({end}))".format(start=start,end=end))
        self.segment = (start,end)
        self.has_new_data = True
        self.background_changed = True
        self.data_changed()

    def data_changed(self):
        if self.drawing_trigger : return
        since_last = time.time() - self.last_update
        wait_for = max((0, self.sleep_time - since_last))
        QtCore.QTimer.singleShot(wait_for,self.draw_all)
        self.drawing_trigger = True

    def draw_all(self):
        #t = time.time()
        self.update_data()
        self.draw_background()
        self.draw_plot()
        #print "time since last update: %dms , update took: %dms" % ((time.time() - self.last_update)*1000,(time.time()-t)*1000)
        self.last_update = time.time()
        self.drawing_trigger = False

    def update_data(self):
        if not self.has_new_data : return
        self.ymin_auto = np.Inf
        self.ymax_auto = -np.Inf
        chans = self.data_model.get_active_channels()
        o = self.data_model.get_data_offset()
        for c in chans :
            data = c.get_data()[self.segment[0]-o:self.segment[1]-o]
            ckey = self._ckey(c)
            if ckey in self.lines :
                self.lines[ckey][0].set_xdata(range(len(data)))
                self.lines[ckey][0].set_ydata(data)
            else :
                self.lines[ckey] = self.axes.plot(data,color=np.array(c.get_color())/255.0,animated=True)
            #remember minimum and maximum for autoscaling
            if len(data) == 0 :
                self.ymin_auto = -1
                self.ymax_auto = 1
            else :
                ymin,ymax = min(data),max(data)
                if ymin < self.ymin_auto : self.ymin_auto = ymin
                if ymax > self.ymax_auto : self.ymax_auto = ymax
        self.axes.set_xlim(0,self.segment[1]-self.segment[0])
        self.has_new_data = False
        self.background_changed = True
        self.new_segment_bounds.emit()

    def draw_background(self):
        if self.background_changed :
            yticks = self.axes.get_yticklabels()
            for t in yticks :
                t.set_size("x-small")
            xticks = self.axes.get_xticklabels()
            for t in xticks :
                t.set_size("x-small")
            self.draw()
            if self.axes != None :
                self.background = self.copy_from_bbox(self.axes.bbox)
            else :
                self.background = self.copy_from_bbox(self.figure.bbox)
            self.background_changed = False
        else :
            self.canvas.restore_region(self.background)

    def reset(self):
        self.figure.clf()
        self.lines = {}
        self.axes = None

    def set_ylim(self,ymax=None,ymin=None,lim=None):
        if lim != None :
            ymin,ymax = lim
        if ymin == None and ymax == None :
            ymin = self.ymin_auto
            ymax = self.ymax_auto
        if ymin != None : self.ylim[0] = ymin
        if ymax != None : self.ylim[1] = ymax
        self.axes.set_ylim(self.ylim)
        self.background_changed = True
        self.data_changed()

    def resizeEvent(self,evt):
        FigureCanvas.resizeEvent(self,evt)
        self.background_changed = True
        self.data_changed()

    def draw_plot(self):
        if self.vis_model == None : return
        vchans = self.vis_model.get_visible_channels() if self.vis_model.get_sensordata() != None else self.data_model.get_active_channels()
        for chan in vchans :
            ckey = self._ckey(chan)
            if ckey in self.lines :
                for l in self.lines[ckey] : self.figure.draw_artist(l)
        self.blit(self.figure.bbox)

    def _ckey(self,channel):
        return channel.get_channel_id()+"/"+channel.get_name()

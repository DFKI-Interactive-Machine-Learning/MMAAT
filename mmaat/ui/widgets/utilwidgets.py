# -*- coding: utf-8 -*-
'''
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
'''
from PyQt4 import QtCore, QtGui
from sepan.ui.models.sensordata import SensorDataModelSegment
import logging
import sepan

log = logging.getLogger("sepan.ui.widgets.utilwidgets")

APP_DESCRIPTION = '''
Sequential Pattern Analysis Toolkit (SePAnT).

'''

ANIMSLIDER_STYLESHEET = """QSlider::groove:horizontal {
                                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                                border-radius: 3px;
                                height: 15px;
                        }
                        QSlider::handle:horizontal {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                            border: 1px solid #5c5c5c;
                            width: 5px;
                            border-radius: 3px;
                        }"""

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, icon_path, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, parent)
        self.setIcon(QtGui.QIcon(icon_path))
        self.iconMenu = QtGui.QMenu(parent)
        appabout = self.iconMenu.addAction("About")
        self.setContextMenu(self.iconMenu)
        self.connect(appabout,QtCore.SIGNAL('triggered()'),self.showAbout)


    def showAbout(self):
        self.iconMenu.setEnabled(False)
        QtGui.QMessageBox.about(None, self.tr("About SePAnT"), self.tr(APP_DESCRIPTION))
        # Re-enable the tray icon menu
        self.iconMenu.setEnabled(True)

    def showMessage(self, title, text):
        QtGui.QMessageBox.information(None, self.tr(title), self.tr(text))

class Tab(QtGui.QWidget):
    moved_by_user = QtCore.pyqtSignal(float)
    mouse_pressed = QtCore.pyqtSignal(QtGui.QMouseEvent)
    mouse_released = QtCore.pyqtSignal(QtGui.QMouseEvent)
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self)
        self.h = 50
        self.w = 6
        self.margin = 1
        self.color = QtGui.QColor(0,0,0,255)
        self.color_normal = QtGui.QColor(0,0,0,255)
        self.color_highlight = QtGui.QColor(255,0,0,255)
        self.leftof = None
        self.rightof = None
        self.highlighted = False
        self.relx = 0.0
        self.rely = 1.0
    def setColor(self,color):
        self.color = color
        self.color_normal = color
        self.repaint()
    def sizeHint(self):
        return QtCore.QSize(self.w+self.margin*2,self.h)
    def minimumSizeHint(self):
        return self.sizeHint()
    def paintEvent(self,event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing,on=True)
        ctop = QtCore.QPoint(self.w/2.0,0)
        lbot = QtCore.QPoint(0,self.h)
        rbot = QtCore.QPoint(self.w,self.h)
        for p in [ctop,lbot,rbot] :
            p.setX(p.x()+self.margin)
            p.setY(p.y()+self.margin)

        painter.setBrush(self.color)
        painter.setPen(self.color)
        painter.drawPolygon(ctop,lbot,rbot)
        painter.end()
    def set_rel_pos(self,x=None,y=None):
        if not x is None : self.relx = x
        if not y is None : self.rely = y
        self.update_real_position()
    def update_real_position(self):
        x = self.relx * self.parentWidget().width()
        x -= self.w/2 #relative x determines where _center_ of widget is located
        y = self.rely * self.parentWidget().height()
        y -= self.h #relative y determines where _bottom_ of widget is located
        self.move(x,y)
    def get_rel_pos(self):
        return self.relx,self.rely
    def mouseMoveEvent(self,event):
        event.accept()
        p = event.pos()
        p2 = QtCore.QPoint(p.x()+self.w/2.0,p.y())
        p2 = self.mapToParent(p2)
        pw = self.parentWidget().width()
        relx = (p2.x()-self.w/2.0)/pw
        if relx < 0 : relx = 0
        if relx > 1 : relx = 1
        if self.leftof != None and self.leftof.isVisible() and self.leftof.get_rel_pos()[0] < relx : return
        if self.rightof != None and self.rightof.isVisible() and self.rightof.get_rel_pos()[0] > relx : return
        self.set_rel_pos(relx, self.rely)
        self.moved_by_user.emit(self.get_rel_pos()[0])
    def mouseReleaseEvent(self,event):
        self.mouse_released.emit(event)
    def mousePressEvent(self,event):
        self.mouse_pressed.emit(event)
    def resizeEvent(self,event):
        event.accept()
        self.update_real_position()
    def always_left_of(self,other):
        self.leftof = other
    def always_right_of(self,other):
        self.rightof = other
    def set_highlighted(self,highlighted,with_connected_tabs=True):
        if highlighted :  self.color = self.color_highlight
        else :          self.color = self.color_normal
        if with_connected_tabs and self.leftof != None :
            self.leftof.set_highlighted(highlighted,with_connected_tabs=False)
        if with_connected_tabs and self.rightof != None :
            self.rightof.set_highlighted(highlighted,with_connected_tabs=False)
        self.highlighted = highlighted
        self.repaint()
    def is_highlighted(self):
        return self.highlighted

class TabBar(QtGui.QWidget):
    mouse_pressed = QtCore.pyqtSignal(QtGui.QMouseEvent,float)
    mouse_released = QtCore.pyqtSignal(QtGui.QMouseEvent,float)

    def __init__(self, _name):
        QtGui.QWidget.__init__(self)
        self.ticks = []
        self.bigticks = []
        self.bordercolor = QtGui.QColor(0,0,0,255)
        self.name = _name

    def paintEvent(self,event):
        painter = QtGui.QPainter()
        painter.begin(self)
        white = QtGui.QColor(255,255,255,255)
        black = QtGui.QColor(0,0,0,255)
        transparent = QtGui.QColor(255,255,255,0)
        painter.setBrush(white)
        painter.setPen(white)
        painter.drawRect(QtCore.QRect(0,0,self.width(),self.height()))
        painter.setBrush(black)
        painter.setPen(black)
        for t in self.ticks :
            t = t*self.width()
            painter.drawLine(t,self.height(),t,int(self.height()*2.0/3.0))
        for t in self.bigticks :
            t = t*self.width()
            painter.drawLine(t,self.height(),t,int(self.height()*1.0/3.0))
        painter.setBrush(transparent)
        painter.setPen(self.bordercolor)
        painter.drawRect(QtCore.QRect(0,0,self.width()-1,self.height()-1))
        painter.end()

    def set_ticks(self,ticks):
        self.ticks = ticks
        self.repaint()

    def set_bigticks(self,bigticks):
        self.bigticks = bigticks
        self.repaint()

    def resizeEvent(self,event):
        event.accept()
        for c in self.children() :
            if isinstance(c,Tab) : c.resizeEvent(event)

    def mouseReleaseEvent(self,event):
        if not self.isEnabled() : return #disable all functionality
        relx = self.get_relx(event.pos().x())
        self.mouse_released.emit(event,relx)

    def mousePressEvent(self,event):
        if not self.isEnabled() : return #disable all functionality
        relx = self.get_relx(event.pos().x())
        self.mouse_pressed.emit(event,relx)

    def get_relx(self,absx):
        return 1.0*absx/self.width()

class SingleItemMaintainAspectRatioLayout(QtGui.QLayout):
    ALIGN_CENTER = "center"
    ALIGN_NORTHWEST = "nw"
    def __init__(self,wbh):
        QtGui.QLayout.__init__(self)
        self.theitem = None
        self.wbh = wbh
        self.align = self.ALIGN_NORTHWEST
    def addItem(self,item):
        self.theitem = item
    def count(self):
        return 1 if self.theitem != None else 0
    def itemAt(self,index):
        if index == 0 : return self.theitem
        return None
    def takeAt(self,index):
        if index == 0 :
            return self.theitem
        return None
    def minimumSize(self):
        return QtCore.QSize() if self.theitem == None else self.theitem.minimumSize()
    def setGeometry(self,rect):
        QtGui.QLayout.setGeometry(self,rect)
        if rect.height() * self.wbh > rect.width() :
            #can only fit width
            w = rect.width()
            h = rect.width() * 1.0 / self.wbh
        else :
            #can only fit height
            h = rect.height()
            w = rect.height() * self.wbh
        h = round(h)
        w = round(w)
        if self.align == self.ALIGN_NORTHWEST :
            xoff = 0
            yoff = 0
        else :
            xoff = int((rect.width() - w)/2.0)
            yoff = int((rect.height() - h)/2.0)
        if self.theitem != None :
            self.theitem.setGeometry(QtCore.QRect(rect.x()+xoff,rect.y()+yoff,w,h))
    def set_alignment(self,align):
        self.align = align
    def sizeHint(self):
        return QtCore.QSize() if self.theitem == None else self.theitem.sizeHint()
    def set_aspect_ratio(self,wbh):
        self.wbh = wbh

class AxisLayout(QtGui.QLayout):
    RELATIVE_SPACING = "rel"
    ABSOLUTE_SPACING = "abs"
    def __init__(self,canvas,spacing=3):
        QtGui.QLayout.__init__(self)
        self.canvas = canvas
        self.clist = []
        self.hspaces = []
        self.woffs = []
        self.spacing = spacing
        self.addWidget(canvas)
    def addItem(self,item):
        self.clist.append(item)
        self.hspaces.append((0,0,self.ABSOLUTE_SPACING))
        self.woffs.append(0)
    def count(self):
        return len(self.clist)
    def itemAt(self,index):
        return self.clist[index] if index < len(self.clist) else None
    def takeAt(self,index):
        return self.clist[index] if index < len(self.clist) else None
    def minimumSize(self):
        m = self.canvas.minimumSize()
        ch = 0
        for c in self.clist[1:] :
            ch += c.minimumSize().height()
        return QtCore.QSize(m.width(),m.height()+ch+len(self.clist)*self.spacing)
    def _canvash(self,rect):
        h = rect.height()
        for i in xrange(len(self.clist)) :
            if i == 0 : continue # do not count canvas itself
            h -= self.spacing
            h -= self.clist[i].minimumSize().height()
        return h
    def setGeometry(self,rect):
        QtGui.QLayout.setGeometry(self,rect)
        canvas_h = self._canvash(rect)
        self.canvas.setGeometry(rect.x(),rect.y(),rect.width(),canvas_h)
        y = rect.y() + canvas_h + self.spacing
        for i in xrange(len(self.clist)) :
            if i == 0 : continue # item number 0 is canvas
            child = self.clist[i]
            l,r,tp = self.hspaces[i]
            h = child.minimumSize().height()
            x = rect.x()
            if tp == self.ABSOLUTE_SPACING :
                x += l
                w = rect.width() - l - r
            else :
                al = int(l * rect.width())
                ar = int(r * rect.width())
                x += al
                w = rect.width() - al - ar
            if self.woffs[i] != 0 :
                x -= self.woffs[i]/2
                w += self.woffs[i]
            child.setGeometry(QtCore.QRect(x,y,w,h))
            y += self.spacing + h
    def set_alignment(self,align):
        self.align = align
    def set_horizontal_spacing(self,item,left,right,stype=RELATIVE_SPACING):
        i = self.indexOf(item)
        self.hspaces[i] = (left,right,stype)
    def set_width_offset(self,item,offset):
        i = self.indexOf(item)
        self.woffs[i] = offset
    def sizeHint(self):
        sh = self.canvas.sizeHint()
        ch = 0
        for c in self.clist :
            ch += c.sizeHint().height()
        return QtCore.QSize(sh.width(),sh.height()+ch)

class FSQSpinBox(QtGui.QSpinBox):
    focus_gained = QtCore.pyqtSignal()
    def __ini__(self):
        QtGui.QSpinBox.__init__(self)
    def focusInEvent(self,evt):
        QtGui.QSpinBox.focusInEvent(self,evt)
        self.focus_gained.emit()
        evt.accept()

class QLabelTable(QtGui.QFrame):
    def __init__(self):
        QtGui.QFrame.__init__(self)
        self.setStyleSheet("QFrame {background-color:white; }")
        self.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        self.l = QtGui.QGridLayout()
        self.dummy = QtGui.QWidget()
        self.l.addWidget(self.dummy)
        self.setLayout(self.l)
        self.lrows = []
    def _remove_dummy(self):
        self.l.setRowStretch(len(self.lrows),0)
        self.l.removeWidget(self.dummy)
        self.dummy.setParent(None)
    def _add_dummy(self):
        self.l.addWidget(self.dummy)
        self.l.setRowStretch(len(self.lrows),1)
    def add_row(self,*qlabels):
        self._remove_dummy()
        for i in xrange(len(qlabels)) :
            self.l.addWidget(qlabels[i],len(self.lrows),i)
        self.lrows.append(qlabels)
        self._add_dummy()
    def remove_row(self,index):
        oldrows = self.lrows[:]
        oldrows.pop(index)
        self.remove_all()
        for row in oldrows:
            self.add_row(row)
    def remove_all(self):
        for r in self.lrows :
            for l in r :
                self.l.removeWidget(l)
                l.setParent(None) #needed because otherwise widget is still partly displayed

class QCallbackThread(QtCore.QThread):
    def __init__(self,cb):
        self.cb = cb
        QtCore.QThread.__init__(self)
    def run(self):
        self.cb()

class PlotControlTab():
    """
    Model class representing a single Tab in a PlotControl widget
    """
    def __init__(self,tid,pos,tab,color=QtGui.QColor(0,0,0),shadow_tab=None):
        """
        Creates a PlotControlTab widget with all options

        Arguments:
        tid   -- tab id (anything that can be used as dictionary key)
        pos   -- position of the tab in absolute coordinates
        tab   -- the actual Tab widget

        Keyword-arguments:
        color      -- QColor object for the color of the Tab (default black)
        shadow_tab -- Tab widget that is used as shadow on the global TabBar (default None)
        """
        self.tid = tid
        self.pos = pos
        self.color = color
        self.tab = tab
        self.shadow_tab = shadow_tab
    def has_shadow(self):
        """
        Returns True if this Tab has a shadow Tab on the global TabBar
        """
        return not self.shadow_tab is None

class PlotControlSegment():
    """
    Model class representing a Segment with two Tabs in a PlotControl widget
    """
    def __init__(self, idx, sid,start,end,start_tab,end_tab,color=QtGui.QColor(0,0,0),start_tab_shadow=None,end_tab_shadow=None,has_visualization=False):
        """
        Creates a PlotControlSegment widget with all options

        Arguments:
        idx       -- index
        sid       -- segment id (anything that can be used as dictionary key)
        start     -- starting point of the segment in absolute coordinates
        end       -- end point of the segment in absolute coordinates
        start_tab -- actual Tab widget for the starting point of the segment
        end_tab   -- actual Tab widget for the end point of the segment

        Keyword-arguments:
        color             -- QColor object for the color of the segment Tabs (default black)
        start_tab_shadow  -- Tab widget used as shadow of the start tab on the global TabBar (default None)
        end_tab_shadow    -- Tab widget used as shadow of the end tab on the global TabBar (default None)
        has_visualization -- if True the Segment will be visualized in the Pyplot widget (default False)
        """
        self.idx = idx
        self.sid = sid
        self.start = start
        self.end = end
        self.color = color
        self.start_tab = start_tab
        self.end_tab = end_tab
        self.start_tab_shadow = start_tab_shadow
        self.end_tab_shadow = end_tab_shadow
        self.has_visualization = has_visualization
        self.is_visible = True
    def to_sdms(self):
        """
        Converts the current state of the segment into a SensorDataModelSegment object

        Returns: a SensorDataModelSegment object with sid, start and end point of this segment
        """
        return SensorDataModelSegment(self.idx,self.sid,self.start,self.end)
    def has_shadow(self):
        """
        Returns True if the Tabs of this segment have a shadow Tab on the global TabBar
        """
        return not self.start_tab_shadow is None and not self.end_tab_shadow is None

class PlotControl(QtGui.QWidget):
    """
    Highly specialized widget for the control of a SensorPyplotView widget,
    including GUI elements for controlling animation, segments, xlim and ylim.

    The layout will be as follows:

    |-------------------------------------------|
    |             SensorPyplotView              |
    |                                           |
    |                                           |
    |-------------------------------------------|
    |            local TabBar                   |
    |-------------------------------------------|
    |            global TabBar                  |
    |-------------------------------------------|
    | animation buttons |      | ylim control   |
    |-------------------------------------------|

    The local and global TabBars can contain single Tabs or segments consisting
    of two tabs. Tabs and segments on the local TabBar can have a "shadow" on
    the global TabBar. This shadow will have a darker and less saturated color
    than the main tab/segment and will move along with it, always having the
    same absolute coordinates.

    Elements on the local TabBar are displayed in local coordinates, that is the
    same coordinate system as the SensorPyplotView. The global TabBar works with
    global coordinates and includes by default a (black) segment that can be used
    to set the display section of the plot (and thus of the local TabBar).
    """
    def __init__(self,view,include_animation_control=True,attention_mode=True):
        """
        Creates a new PlotControl widget that will control the given SensorPyplotView

        NOTE: The control widgets will only work when a model is assigned to this widget
        via set_model()

        Arguments:
        view -- the SensorPyplotView widget that should be controlled

        Keyword-Arguments:
        include_animation_control -- if True, the widget will contain GUI elements to control
                                 the animation of plot data (default True)
        """
        QtGui.QWidget.__init__(self)
        self.include_animation_control = include_animation_control
        self.label_mode = None
        self.model = None
        self.animation_tab_id = None
        self.xlim_segment_id = None
        self.view = view
        self.data_size = 0
        self.counter = 0
        self.counter_t = 0
        self.local_segments = {}
        self.global_segments = {}
        self.local_tabs = {}
        self.global_tabs = {}
        self.lb_mrc = None
        self.gb_mrc = None
        self.stash_anim_pos = 0
        self.stash_xlim_pos = (0,1)
        self.max_xspan = 30000
        self.stop_cb = None
        self.xspan = None
        self.t_en = True
        self.p_en = True
        self.sbm_en = True
        self.ROI_seg_x = None
        self.ROI_xlim_x = None
        self.sid = None
        self.idx = None
        self.animation_point = None
        self.tabend_selected = False
        self.local_bar = TabBar('local')
        self.local_bar.setMinimumSize(100,15)
        self.global_bar = TabBar('global')
        self.global_bar.setMinimumSize(100,15)
        self.axislayout = AxisLayout(self.view)
        self.start_button = QtGui.QPushButton("Play")
        self.stop_button = QtGui.QPushButton("Stop")
        self.ymin_l = QtGui.QLabel("Min y:")
        self.ymax_l = QtGui.QLabel("Max y:")
        self.ymin_input = QtGui.QDoubleSpinBox()
        self.ymin_input.setMinimum(-10)
        self.ymax_input = QtGui.QDoubleSpinBox()
        self.yauto_button = QtGui.QPushButton("Auto")
        self.indexspinner_l = QtGui.QLabel("Index:")
        self.indexspinner = QtGui.QSpinBox()
        self.indexspinner.setMinimum(0)
        self.indexspinner.setSingleStep(1)
        self.buttonlayout = QtGui.QHBoxLayout()
        self.main_layout = QtGui.QVBoxLayout()
        self.filler = QtGui.QWidget()
        fp = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
        fp.setHorizontalStretch(10)
        self.filler.setSizePolicy(fp)
        left_sp = self.view.subplotbounds[0]
        right_sp = 1 - self.view.subplotbounds[1]
        self.bAttention = attention_mode
        self.axislayout.addWidget(self.local_bar)
        self.axislayout.addWidget(self.global_bar)

        self.axislayout.set_horizontal_spacing(self.local_bar, left_sp, right_sp)
        self.axislayout.set_horizontal_spacing(self.global_bar, left_sp, right_sp)

        if self.include_animation_control :
            self.buttonlayout.addWidget(self.start_button)
            self.buttonlayout.addWidget(self.stop_button)
        self.buttonlayout.addWidget(self.filler)
        if attention_mode :
            lable_mode = QtGui.QComboBox()
            self.buttonlayout.addWidget(QtGui.QLabel("Labeling mode:"))
            self.buttonlayout.addWidget(lable_mode)
            lable_mode.addItems(["gestures", "attention"])
            lable_mode.currentIndexChanged.connect(self.set_label_mode)
        self.buttonlayout.addWidget(self.yauto_button)
        self.buttonlayout.addWidget(self.indexspinner_l)
        self.buttonlayout.addWidget(self.indexspinner)
        self.buttonlayout.addWidget(self.ymin_l)
        self.buttonlayout.addWidget(self.ymin_input)
        self.buttonlayout.addWidget(self.ymax_l)
        self.buttonlayout.addWidget(self.ymax_input)
        self.main_layout.addLayout(self.axislayout)
        self.main_layout.addLayout(self.buttonlayout)
        self.setLayout(self.main_layout)
        self._maintain_input_states()

    def set_label_mode(self, mode):
        '''
            Sets the label mode.
            :Parameter:
                mode -- labeling mode
        '''
        self.model.set_label_mode(mode)

    def get_label_mode(self):
        '''
            Returns the label mode.
            :Returns:
                current
        '''
        return self.model.get_label_mode()

    def set_ylim_spinner_range(self,ymin,ymax):
        """
        Sets the range of the spinners for adjusting ymin and ymax (will also
        change the size of the display elements)

        Arguments:
        ymin -- absolute minimum value to be expected
        ymax -- absolute maximum value to be expected
        """
        self.ymin_input.setMinimum(ymin)
        self.ymax_input.setMinimum(ymin)
        self.ymin_input.setMaximum(ymax)
        self.ymax_input.setMaximum(ymax)

    def connect_signals(self):
        """
        Helper function that handles necessary Qt signal connections.

        This method is invoked in the set_model() method and should not
        be invoked manually.
        """
        if self.include_animation_control :
            self.start_button.clicked.connect(self._play_pause)
            self.stop_button.clicked.connect(self._stop)
        self.local_bar.mouse_released.connect(self._lb_mouse_release)
        self.global_bar.mouse_released.connect(self._gb_mouse_release)
        self.yauto_button.clicked.connect(self._autoresizey)
        self.view.ylim_changed.connect(self._ylim_changed)
        self.view.xlim_changed.connect(self._xlim_changed)
        self.view.mouse_released.connect(self._view_mouse_released)
        self.local_bar.mouse_released.connect(self._view_mouse_released)
        self.view.mouse_pressed_left.connect(self._view_mouse_pressed_left)
        self.view.mouse_dragged_left.connect(self._view_mouse_dragged_left)
        self.view.mouse_pressed_right.connect(self._view_mouse_pressed_right)
        self.view.mouse_dragged_right.connect(self._view_mouse_dragged_right)
        self.indexspinner.valueChanged.connect(self._spinner_index_changed_)
        self.model.new_dataset.connect(self._data_changed)
        self.model.dataset_changed.connect(self._check_xspan)

        changeslot1 = lambda i : None if self.view.get_ylim() is None else self.view.set_ylim(i, self.view.get_ylim()[1], silent=True)
        changeslot2 = lambda i : None if self.view.get_ylim() is None else self.view.set_ylim(self.view.get_ylim()[0], i, silent=True)
        self.ymin_input.valueChanged.connect(changeslot1)
        self.ymax_input.valueChanged.connect(changeslot2)
        self.set_label_mode(0)
        #default tabs and segments
        self._add_default_tabs()
        self._add_default_segments()

    def _play_pause(self):
        if self.model.is_in_animation() :
            self.model.stop_animation()
            self.start_button.setText("Play")
        else :
            self.model.start_animation()
            self.start_button.setText("Pause")

    def _stop(self):
        if self.model is None : return
        self.model.stop_animation(reset=True)
        self.start_button.setText("Play")
        if not self.stop_cb is None :
            self.stop_cb()

    def select_tabend(self):
        self.tabend_selected = True

    def _model_set_display_point(self,x):
        self.model.set_animation_step(x)

    def _model_get_display_point(self):
        return self.model.get_animation_step()

    def _view_mouse_released(self, evt):
        try :
            gpos = self._view_reltoabs(evt)
            if not (self.ROI_xlim_x is None):
                self.remove_segment('selection')
                if self.ROI_xlim_x < gpos : self.set_xlim(self.ROI_xlim_x, gpos)
                elif self.ROI_xlim_x > gpos: self.set_xlim(gpos, self.ROI_xlim_x)
                #elif self.ROI_xlim_x == gpos : pass
            if not self.animation_point is None :
                dp = self.animation_point
                if dp < self.get_xlim()[0] : dp = self.get_xlim()[0]
                if dp >= self.get_xlim()[1] : dp = self.get_xlim()[1]-1
                self._model_set_display_point(dp)
            if not (self.ROI_seg_x is None) :
                ret_val = None
                if self.get_label_mode() == 0 :
                    ret_val = QtGui.QInputDialog.getItem(self,"Choose segment label", "Label:", sepan.CLASSES)
                else :
                    ret_val = QtGui.QInputDialog.getItem(self,"Choose segment label", "Label:", sepan.ATTENTION)
                name = str(ret_val[0]) #return type is tuple with string first and boolean second
                if ret_val[1] :
                    self.model.set_segment_name(self.idx, self.sid,name)
                else :
                    self.model.remove_segment(self.idx, self.sid)
        finally :
            self.ROI_xlim_x = None
            self.ROI_seg_x = None
            self.animation_point = None

    def _spinner_index_changed_(self, i):
        self.model.set_animation_step(i)

    def _view_mouse_pressed_right(self, evt):
        glopos = self._view_reltoabs(evt)
        if self.animation_point is None:
            self.animation_point = self._model_get_display_point()
        if self.ROI_xlim_x is None:
            self.add_segment(self.model.get_label_mode(), 'local', glopos, glopos + 10, global_shadow = True, color = QtGui.QColor(255, 0, 0), sid = 'selection', has_visualization = True)
            self.ROI_xlim_x = glopos

    def _view_mouse_dragged_right(self,evt):
        if self.ROI_xlim_x is None : return
        glopos = self._view_reltoabs(evt)
        if glopos > self.ROI_xlim_x: self.move_segment('selection', end = glopos)
        elif glopos < self.ROI_xlim_x: self.move_segment('selection', start = glopos)
        self._model_set_display_point(glopos)

    def _view_mouse_pressed_left(self, evt):
        if not self.sbm_en : return
        glopos = self._view_reltoabs(evt)
        if self.animation_point is None:
            self.animation_point = self._model_get_display_point()
        if self.ROI_seg_x is None:
            self.sid = self.model.add_segment(glopos, glopos+1, idx=self.model.get_label_mode())
            self.idx = self.model.get_label_mode()
            self.ROI_seg_x = glopos
    def _view_mouse_dragged_left(self,evt):
        if not self.sbm_en : return
        if self.ROI_seg_x is None : return
        glopos = self._view_reltoabs(evt)
        if glopos > self.ROI_seg_x: self.model.move_segment(self.idx, self.sid, end = glopos)
        elif glopos < self.ROI_seg_x: self.model.move_segment(self.idx, self.sid, start = glopos)
        self._model_set_display_point(glopos)
    def _view_reltoabs(self, evt):
        relpos = (evt.pos().x()-(self.view.width()-self.local_bar.width())/2.)/self.local_bar.width()
        if relpos > 1: relpos = 1.
        elif relpos < 0: relpos = 0.
        return self._reltoabs(relpos, 'local')
    def _lb_mouse_release(self,mevt,relx):
        absx = self._reltoabs(relx, "local")
        if not self.lb_mrc is None :
            self.lb_mrc(mevt,absx)
    def _gb_mouse_release(self,mevt,relx):
        absx = self._reltoabs(relx, "global")
        if not self.gb_mrc is None :
            self.gb_mrc(mevt,absx)
    def _add_default_tabs(self):
        if self.include_animation_control :
            anim_cb = lambda sid,x : self.model.set_animation_step(x)
            self.animation_tab_id = self.add_tab("local", self.stash_anim_pos, anim_cb, None, True, QtGui.QColor(0,0,255), "animation_tab")
    def _add_default_segments(self):
        s,e = self.stash_xlim_pos
        self.xlim_segment_id = self.add_segment(0,"global", s, e,move_callback=self._xlim_tab_moved, mouse_release_callback= self._xlim_segment_moved, sid="xlim_segment")
    def _raise_default_tabs(self):
        if self.include_animation_control and self.animation_tab_id in self.local_tabs :
            self.local_tabs[self.animation_tab_id].tab.raise_()
        if self.xlim_segment_id in self.global_segments :
            xseg = self.global_segments[self.xlim_segment_id]
            xseg.start_tab.raise_()
            xseg.end_tab.raise_()

    def _xlim_tab_moved(self,idx,sid,start=None,end=None):
        xmin, xmax = self.get_xlim()
        if start != None :
            if xmax-start > self.max_xspan :
                self.move_segment(self.xlim_segment_id, end=start+self.max_xspan)
        elif end != None :
            if end-xmin > self.max_xspan :
                self.move_segment(self.xlim_segment_id, start=end-self.max_xspan)

    def _xlim_segment_moved(self,evt,sid,start=None,end=None,load_data=True):
        if not evt is None and evt.button() != QtCore.Qt.LeftButton : return
        xseg = self.global_segments[self.xlim_segment_id]
        if start is None : start = xseg.start
        if end   is None : end   = xseg.end
        #log.debug("PlotControl xlim segment moved, setting xlim to %d,%d" % (start,end))
        if not self.animation_tab_id is None :
            anim = self.local_tabs[self.animation_tab_id]
            if anim.pos < start :
                self.move_tab(self.animation_tab_id,start)
                self.model.set_animation_step(start)
            elif anim.pos > end :
                self.move_tab(self.animation_tab_id,end)
                self.model.set_animation_step(end)
        if load_data :
            self.model.load_into_memory(start,end)
        self.view.set_xlim(start,end)

    def _data_changed(self):
        self.xspan = self._get_data_size()
        self.indexspinner.setMaximum(self.xspan)
        self._maintain_input_states()
        self._autoresizey()
    def _check_xspan(self):
        nxspan = self._get_data_size()
        try :
            if nxspan != self.xspan :
                adjust = lambda tab,pos : tab.set_rel_pos(self._abstorel(pos, "global")) if not tab is None else None
                for t in self.global_tabs.values() :
                    adjust(t.tab,t.pos)
                for s in self.global_segments.values() :
                    adjust(s.start_tab,s.start)
                    adjust(s.end_tab,s.end)
                for t in self.local_tabs.values() :
                    adjust(t.shadow_tab,t.pos)
                for s in self.local_segments.values() :
                    adjust(s.start_tab_shadow,s.start)
                    adjust(s.end_tab_shadow,s.end)
        finally :
            self.xspan = nxspan
    def _get_data_size(self):
        if self.model is None :
            self.data_size = 1
        else :
            self.data_size = max(1,self.model.get_data_num_samples())
        return self.data_size
    def _reltoabs(self,relx,domain):
        if domain == "local" :
            xmin,xmax = self.get_xlim()
            span = xmax - xmin
            return int(round(1.0 * relx * span + xmin))
        elif domain == "global" :
            return int(round(1.0*relx*self._get_data_size()))
        else :
            raise Exception("Unrecognized domain %s" % str(domain))
    def _abstorel(self,absx,domain):
        if domain == "local" :
            xmin,xmax = self.get_xlim()
            span = xmax - xmin
            offset = xmin
            return 1.0 * (absx - offset) / span
        elif domain == "global" :
            return 1.0*absx/self._get_data_size()
        else :
            raise Exception("Unrecognized domain %s" % str(domain))
    def _animation_step(self,i):
        if self.animation_tab_id is None : return
        self.start_button.setText("Pause" if  self.model.is_in_animation() else "Play")
        self.move_tab(self.animation_tab_id,i)
        # Disconnect signal to avoid a loop
        self.indexspinner.valueChanged.disconnect(self._spinner_index_changed_)
        self.indexspinner.setValue(i)
        self.indexspinner.valueChanged.connect(self._spinner_index_changed_)
    def _animation_stopped(self):
        if not self.include_animation_control : return
        self.start_button.setText("Play")
    def _ylim_changed(self,i,j):
        self.ymin_input.setValue(i)
        self.ymax_input.setValue(j)
    def _xlim_changed(self,i,j,silent):
        if not silent :
            self.move_segment(self.xlim_segment_id,int(round(i)),int(round(j)))
        self._update_tab_visibility(i,j)
    def _update_tab_visibility(self,xmin,xmax):
        in_display_area = lambda x : x >= xmin and x <= xmax
        for seg in self.local_segments.values() :
            seg.start_tab.setVisible(in_display_area(seg.start) and seg.is_visible)
            seg.end_tab.setVisible(in_display_area(seg.end) and seg.is_visible)
            if seg.start_tab.isVisible() :
                seg.start_tab.set_rel_pos(self._abstorel(seg.start, "local"))
            if seg.end_tab.isVisible() :
                seg.end_tab.set_rel_pos(self._abstorel(seg.end, "local"))
        for tab in self.local_tabs.values() :
            tab.tab.setVisible(in_display_area(tab.pos))
            if tab.tab.isVisible() :
                tab.tab.set_rel_pos(self._abstorel(tab.pos, "local"))

    def _autoresizey(self):
        ymin = 0
        ymax = 1
        chans = self.model.get_visible_channels()
        xmin,xmax = self.get_xlim()
        o = self.model.get_data_offset()
        if len(chans) > 0 :
            cymin = [min(c.get_data()[xmin-o:xmax-o]) for c in chans]
            cymax = [max(c.get_data()[xmin-o:xmax-o]) for c in chans]
            ymin = min(cymin)
            ymax = max(cymax)
            ymin = ymin - 0.01 * (ymax - ymin)
            ymax = ymax + 0.01 * (ymax - ymin)
        self.view.set_ylim(ymin,ymax)

    def set_model(self,model):
        """
        Sets the model of this PlotControl and calls self.connect_signals() to connect all
        necessary Qt signals. This needs to be called before this widget can be used.

        Arguments:
        model -- a SensorDataModel object
        """
        self.model = model
        self.view.set_model(model)
        self.connect_signals()

    def add_tab(self,domain,x,move_callback=None,mouse_release_callback=None,global_shadow=False,color=QtGui.QColor(0,0,0),tid=None):
        """
        Adds a new single tab to the local or the global TabBar.

        Arguments:
        domain -- "local" or "global", determines if the tab is placed on the local or global TabBar
        x      -- position of the Tab in global coordinates

        Keyword-arguments:
        move_callback          -- callback function of the form move_callback(tid,x) that is invoked
                                  when the tab is moved by the user. Arguments are the tab id and
                                  the x position in absolute coordinates to which the tab has
                                  been moved. (default None)
        mouse_release_callback -- callback function of the form mouse_release_callback(tid,event,x)
                                  that is invoked when the user releases a mouse key on the tab.
                                  Arguments are the tab id, the QMouseEvent and the current position
                                  of the tab in absolute coordinates. (default None)
        global_shadow          -- if True, a local Tab will have a shadow Tab on the global TabBar.
                                  This shadow tab is not movable by the user. It is only used to
                                  indicate the Tab position in global coordinates. Only meaningful
                                  if domain == "local". (default False)
        color                  -- the color of the Tab widget. This color is used to infer the color
                                  of the shadow tab if present (which will be darker and less saturated).
                                  (default black)
        tid                    -- the id of the tab. If set to None, a default id will be generated
                                  by a counter. Ids can be anything that can be used as dictionary key,
                                  but have to be unique. (default None)

        Returns:
        The tab id that has been assigned to the new tab (identical to tid if (not tid is None))
        """
        tab = Tab()
        if tid is None :
            tid = self.counter_t
            self.counter_t += 1
        else :
            if tid in self.local_tabs or tid in self.global_tabs :
                raise Exception("Duplicate tab id %d" % tid)
        tab.h = 15
        tab.setColor(color)
        shadow_tab = None
        if domain == "local" :
            tab.setParent(self.local_bar)
            if global_shadow :
                shadow_tab = Tab()
                shadow_tab.h = 15
                shadow_tab.setColor(self._get_pale_color(color))
                shadow_tab.setParent(self.global_bar)
                shadow_tab.setEnabled(False)
                shadow_tab.lower()
                shadow_tab.show()
            self.local_tabs[tid] = PlotControlTab(tid, x, tab, color, shadow_tab)
        elif domain == "global" :
            tab.setParent(self.global_bar)
            tab.show()
            self.global_tabs[tid] = PlotControlTab(tid, x, tab, color, shadow_tab)
        if not move_callback is None :
            tab.moved_by_user.connect(lambda relx : self._tab_moved_by_user(0,tid, move_callback, relx, "single"))
        #FIXME mouse_release_callback is not handled correctly
        if not mouse_release_callback is None :
            tab.mouse_released.connect(lambda relx : mouse_release_callback(self._reltoabs(relx,domain)))
        self.move_tab(tid,x)
        self._raise_default_tabs()
        return tid
    def move_tab(self,tid,x):
        """
        Moves a single tab to a given global position

        Arguments:
        tid -- the tab id
        x   -- the new position in global coordinates
        """
        if self.model is None or self.model.get_sensordata() is None : return #robustness
        tab = None
        if tid in self.local_tabs :
            tab_obj = self.local_tabs[tid]
            tab_obj.pos = x
            tab = tab_obj.tab
            relx = self._abstorel(x,"local")
            tab.set_rel_pos(relx)
            if tab_obj.has_shadow() :
                shadow_tab = tab_obj.shadow_tab
                relx_s = self._abstorel(x,"global")
                shadow_tab.set_rel_pos(relx_s)
            if not self.get_xlim() is None :
                xmin,xmax = self.get_xlim()
                tab.setVisible(x >= xmin and x <= xmax)
        elif tid in self.global_tabs :
            tab_obj = self.global_tabs[tid]
            tab_obj.pos = x
            tab = tab_obj.tab
            relx = self._abstorel(x,"global")
            tab.set_rel_pos(relx)

    def remove_tab(self,tid):
        """
        Removes a single tab from the corresponding TabBar (also removes shadow tabs)

        Arguments:
        tid -- the id of the tab to remove
        """
        if tid in self.local_tabs :
            tab_obj = self.local_tabs[tid]
            del self.local_tabs[tid]
        elif tid in self.global_tabs :
            tab_obj = self.global_tabs[tid]
            del self.global_tabs[tid]
        tab = tab_obj.tab
        shadow_tab = tab_obj.shadow_tab
        if not tab        is None :        tab.setParent(None); del tab
        if not shadow_tab is None : shadow_tab.setParent(None); del shadow_tab

    def remove_segment(self,sid):
        """
        Removes all tabs of a segment (also shadow tabs) from the corresponding TabBars, also
        removes visualizations if necessary.

        Arguments:
        sid -- the id of the segment to remove
        """
        if sid in self.global_segments :
            seg = self.global_segments[sid]
            del self.global_segments[sid]
        elif sid in self.local_segments :
            seg = self.local_segments[sid]
            del self.local_segments[sid]
        else : return
        start,end = seg.start_tab,seg.end_tab
        shadow_start,shadow_end = seg.start_tab_shadow,seg.end_tab_shadow
        if not start        is None :        start.setParent(None); del start
        if not end          is None :          end.setParent(None); del end
        if not shadow_start is None : shadow_start.setParent(None); del shadow_start
        if not shadow_end   is None :   shadow_end.setParent(None); del shadow_end
        if not seg is None and seg.has_visualization :
            self.view.remove_segment(seg.sid)

    def _get_pale_color(self,color,sat=0.5,val=0.7):
        return QtGui.QColor.fromHsv(color.hue(),color.saturation()*sat,color.value()*val)

    def add_segment(self,idx,domain,startx,endx,move_callback=None,mouse_release_callback=None,global_shadow=False,color=QtGui.QColor(0,0,0),sid=None,has_visualization=False):
        """
        Adds a new segment to the local or the global TabBar. Segments consist of a start tab and
        an end tab.

        Arguments:
        idx    -- index
        domain -- "local" or "global", determines if the segment is placed on the local or global TabBar
        startx -- position of the start tab in global coordinates
        endx   -- position of the end tab in global coordinates

        Keyword-arguments:
        move_callback          -- callback function of the form move_callback(sid,start=None,end=None)
                                  that is invoked when the start or end tab of the segment is
                                  moved by the user. Arguments are the segment id and the start or
                                  end position (only the coordinate that was changed is set) in
                                  absolute coordinates. (default None)
        mouse_release_callback -- callback function of the form
                                  mouse_release_callback(tid,event,start=None,end=None)
                                  that is invoked when the user releases a mouse key on one tab of
                                  the segment. Arguments are the segment id, the QMouseEvent
                                  and either the current position of the start tab or of the end tab
                                  in global coordinates. Only the position of the tab where the mouse
                                  event occurred will be set. (default None)
        global_shadow          -- if True, both Tabs of a local segment will have a shadow Tab
                                  on the global TabBar. This shadow tab is not movable by the user.
                                  It is only used to indicate the Tab position in global coordinates.
                                  Only meaningful if domain == "local". (default False)
        color                  -- the color of the start and end Tab widgets. This color is used to
                                  infer the color of the shadow tab and the visualization if present
                                  (both will be less saturated, the shadow tab will also be darker).
                                  (default black)
        sid                    -- the id of the segment. If set to None, a default id will be generated
                                  by a counter. Ids can be anything that can be used as dictionary key,
                                  but have to be unique. (default None)
        has_visualization      -- if True, the segment will be visualized in the plot as axvspan. this
                                  visualization will also be maintained when the segment is moved and
                                  removed when the segment is removed. (default False)

        Returns:
        The segment id that has been assigned to the new tab (identical to sid if sid is not None)
        """
        start,end = Tab(),Tab()
        if sid is None :
            self.counter += 1
            sid = self.counter
        else :
            if sid in self.local_segments or sid in self.global_segments :
                raise Exception("Duplicate segment id %d" % sid)
        start.h = 15; start.setColor(color)
        end.h = 15; end.setColor(color)
        start.always_left_of(end)
        end.always_right_of(start)
        shadow_start = None
        shadow_end = None
        if domain == "local" :
            start.setParent(self.local_bar)
            end.setParent(self.local_bar)
            if global_shadow :
                shadow_start,shadow_end = Tab(),Tab()
                shadow_start.h = 15; shadow_end.h = 15
                pale_color = self._get_pale_color(color)
                shadow_start.setColor(pale_color)
                shadow_end.setColor(pale_color)
                shadow_start.setParent(self.global_bar)
                shadow_end.setParent(self.global_bar)
                shadow_start.setEnabled(False)
                shadow_end.setEnabled(False)
                shadow_start.lower()
                shadow_end.lower()
                shadow_start.show()
                shadow_end.show()
            seg = PlotControlSegment(idx, sid, startx, endx, start, end, color, shadow_start, shadow_end, has_visualization)
            self.local_segments[sid] = seg
        elif domain == "global" :
            start.setParent(self.global_bar)
            end.setParent(self.global_bar)
            seg = PlotControlSegment(idx, sid, startx, endx, start, end, color, shadow_start, shadow_end, has_visualization)
            start.show()
            end.show()
            self.global_segments[sid] = seg
        cbs = lambda relx : self._tab_moved_by_user(idx, sid, move_callback, relx, "start")
        cbe = lambda relx : self._tab_moved_by_user(idx, sid, move_callback, relx, "end")
        start.moved_by_user.connect(cbs)
        end.moved_by_user.connect(cbe)

        start.mouse_released.connect(lambda evt : self._mouse_released_on_tab(sid, mouse_release_callback, evt, "start"))
        end.mouse_released.connect(lambda evt : self._mouse_released_on_tab(sid, mouse_release_callback, evt, "end"))

        if has_visualization :
            vis_color = self._get_pale_color(seg.color,sat=0.3,val=1)
            self.view.add_segment(seg.to_sdms(),color=(vis_color.red(),vis_color.green(),vis_color.blue()))
        self.move_segment(sid, startx, endx)
        self._raise_default_tabs()
        return sid

    def _mouse_released_on_tab(self,sid,mouse_release_callback,evt,tabtype):
        seg = None
        start = None
        end = None
        if sid in self.local_segments :
            seg = self.local_segments[sid]
            domain = "local"
        elif sid in self.global_segments :
            seg = self.global_segments[sid]
            domain = "global"
        if not seg is None and tabtype == "start" :
            start = seg.start
        elif not seg is None and tabtype == "end" :
            end = seg.end
        #reset animation point from moved segment to previous position
        if domain == "local" and tabtype != "single" and not self.animation_point is None :
            self._model_set_display_point(self.animation_point)
            self.animation_point = None
        if not mouse_release_callback is None :
            mouse_release_callback(evt,sid,start=start,end=end)

    def _tab_moved_by_user(self,idx,sid,move_callback,relx,tabtype):
        seg = None
        tab = None
        shadow_tab = None
        if tabtype == "single" and sid in self.local_tabs : #single local tab
            domain = "local"
            tab = self.local_tabs[sid]
            shadow_tab = tab.shadow_tab
        elif tabtype == "single" and sid in self.global_tabs : #single global tab
            domain = "global"
            tab = self.global_tabs[sid]
        elif tabtype != "single" and sid in self.local_segments : #local segment
            domain = "local"
            seg = self.local_segments[sid]
            shadow_tab = seg.start_tab_shadow if tabtype == "start" else seg.end_tab_shadow
        elif tabtype != "single" and sid in self.global_segments : #global segment
            domain = "global"
            seg = self.global_segments[sid]
        else :
            return #segment/tab not found

        x = self._reltoabs(relx,domain)
        #log.debug("PlotControl - {tabtype} tab with id {sid} moved by user to position {pos}".format(tabtype=tabtype,sid=sid,pos=x))

        #set display point, if we move segment tab on local tabbar
        if domain == "local" and tabtype != "single" :
            if self.animation_point is None:
                self.animation_point = self._model_get_display_point()
            self._model_set_display_point(x)

        if not tab is None : tab.pos = x
        if not seg is None and tabtype == "start" : seg.start = x
        if not seg is None and tabtype == "end"   : seg.end   = x
        #safety check if segment is set to have zero length
        if not seg is None and seg.start == seg.end :
            log.warn("PlotControl - segment with id {sid} set to zero length, adjusting bounds".format(sid=sid))
            #reset the position of the segment bound that was moved
            if tabtype == "start" :
                corrected = seg.start - 1
                rx = self._abstorel(corrected,domain)
                seg.start_tab.set_rel_pos(rx)
                seg.start = corrected
            else :
                corrected = seg.end + 1
                rx = self._abstorel(corrected,domain)
                seg.end_tab.set_rel_pos(rx)
                seg.end = corrected

        if not seg is None and seg.has_visualization : self.view.update_segment(seg.to_sdms())
        if not move_callback is None :
            if tabtype == "start" :
                move_callback(idx=idx, sid=sid,start=x)
            elif tabtype == "end" :
                move_callback(idx=idx, sid=sid,end=x)
            elif tabtype == "single" :
                move_callback(sid,x)
        if shadow_tab != None :
            shadow_tab.set_rel_pos(self._abstorel(x,"global"))

    def move_segment(self, sid,start=None,end=None):
        """
        Moves a segment to the given position.

        Arguments:
        sid -- the segment id

        Keyword-Arguments:
        start -- the new starting position. If set to None the starting position will not change (default None)
        end   -- the new end position. If set to None the end position will not change (default None)
        """
        #log.debug("PlotControl segment {sid} moved by code to position ({start},{end})".format(sid=sid,start="old" if start is None else start,end="old" if end is None else end))
        seg = None
        #handle global segment
        if sid in self.global_segments :
            seg = self.global_segments[sid]
            start_tab,end_tab = seg.start_tab,seg.end_tab
            if not start is None :
                relstart = self._abstorel(start,"global")
                start_tab.set_rel_pos(relstart)
                seg.start = start
            if not end is None :
                relend = self._abstorel(end,"global")
                end_tab.set_rel_pos(relend)
                seg.end = end

        #handle local segment
        elif sid in self.local_segments :
            seg = self.local_segments[sid]
            start_tab,end_tab = seg.start_tab,seg.end_tab
            start_shadow,end_shadow = seg.start_tab_shadow,seg.end_tab_shadow
            if not end is None :
                relend = self._abstorel(end,"local")
                end_tab.set_rel_pos(relend)
                seg.end = end
                if not end_shadow is None :
                    relend_s = self._abstorel(end,"global")
                    end_shadow.set_rel_pos(relend_s)
            if not start is None :
                relstart = self._abstorel(start,"local")
                start_tab.set_rel_pos(relstart)
                seg.start = start
                if not start_shadow is None :
                    relstart_s = self._abstorel(start,"global")
                    start_shadow.set_rel_pos(relstart_s)
        if not seg is None :
            if seg.has_visualization :
                self.view.update_segment(seg.to_sdms())
            if not self.get_xlim() is None :
                xmin,xmax = self.get_xlim()
                in_display_area = lambda x : x >= xmin and x <= xmax
                seg.start_tab.setVisible(in_display_area(seg.start))
                seg.end_tab.setVisible(in_display_area(seg.end))

    def _maintain_input_states(self):
        data_dependent = [self.local_bar,self.global_bar,self.start_button,self.stop_button,
                          self.indexspinner, self.indexspinner_l,
                          self.ymax_input,self.ymin_input,self.yauto_button]
        if self.model is None or self.model.get_sensordata() is None :
            for w in data_dependent :
                w.setEnabled(False)
        else :
            for w in data_dependent :
                w.setEnabled(True)
                #exceptions for widgets which can be disabled manually from the outside
                if (w is self.local_bar or w is self.global_bar) and self.t_en == False :
                    w.setEnabled(False)
                elif w is self.start_button and self.p_en == False :
                    w.setEnabled(False)

    def get_ylim(self):
        """
        Get the vertical span of the current display area of the plot.

        Returns: (ymin,ymax) - minimum and maximum y coordinate of plot display area
        """
        return self.ymin_input.value(),self.ymax_input.value()

    def set_ylim(self,ymin,ymax):
        """
        Set the vertical span of the current display area of the plot.

        Arguments:
        ymin -- the minimum y value displayed
        ymax -- the maximum y value displayed
        """
        self.ymin_input.setValue(ymin)
        self.ymax_input.setValue(ymax)

    def get_xlim(self):
        """
        Get the horizontal span of the current display area of the plot.

        Returns: (xmin,xmax) - minimum and maximum x coordinate of plot display area
        """
        if self.xlim_segment_id is None : return 0, self.model.get_data_num_samples()
        seg = self.global_segments[self.xlim_segment_id]
        return seg.start,seg.end

    def set_xlim(self,xmin,xmax,load_data=True):
        """
        Set the horizontal span of the current display area of the plot.

        Warning: This method may take a long time, if data has to be loaded into
        memory from a MTBFFileStream object.

        Arguments:
        xmin -- the minimum x value displayed
        xmax -- the maximum x value displayed

        Keyword-Arguments:
        load_data -- if True, will automatically ensure that the segment to display
                     is present in memory (default True)
        """
        #log.debug("PlotControl xlim change requested from outside: %d,%d" % (xmin,xmax))
        if self.xlim_segment_id is None : return
        self.move_segment(self.xlim_segment_id, xmin, xmax)
        self._xlim_segment_moved(None, self.xlim_segment_id, xmin, xmax, load_data=load_data)

    def set_segment_color(self,sid,color):
        """
        Change the color attribute of a segment.

        Arguments:
        sid   -- the segment id
        color -- QColor object representing the new segment color
        """
        seg = None
        if sid in self.local_segments :
            seg = self.local_segments[sid]
        elif sid in self.global_segments :
            seg = self.global_segments[sid]
        if not seg is None :
            seg.color = color
            seg.start_tab.setColor(color)
            seg.end_tab.setColor(color)
            if not seg.start_tab_shadow is None :
                seg.start_tab_shadow.setColor(self._get_pale_color(color))
            if not seg.end_tab_shadow is None :
                seg.end_tab_shadow.setColor(self._get_pale_color(color))
            if seg.has_visualization :
                vis_color = self._get_pale_color(color, sat=0.3, val=1)
                self.view.set_segment_color(seg.sid,(vis_color.red(),vis_color.green(),vis_color.blue()))

    def set_segment_visible(self,sid,visible):
        """
        Make a segment visible or invisible. Tabs, shadow tabs and visualizations will all
        be affected.

        Arguments:
        sid     - the segment id
        visible - if True the segment will be made visible, if False the segment will be hidden
        """
        seg = None
        xmin,xmax = self.get_xlim()
        in_display_area = lambda x : x >= xmin and x <= xmax
        if sid in self.local_segments :
            seg = self.local_segments[sid]
            if in_display_area(seg.start) :
                seg.start_tab.setVisible(visible)
            if in_display_area(seg.end) :
                seg.end_tab.setVisible(visible)
        elif sid in self.global_segments :
            seg = self.global_segments[sid]
            seg.start_tab.setVisible(visible)
            seg.end_tab.setVisible(visible)
        if not seg.start_tab_shadow is None :
            seg.start_tab_shadow.setVisible(visible)
        if not seg.end_tab_shadow is None :
            seg.end_tab_shadow.setVisible(visible)
        if seg.has_visualization :
            self.view.set_segment_visible(sid,visible)
        seg.is_visible = visible

    def clear_segments(self):
        """
        Removes all segments and single tabs from global and local TabBar and
        re-adds the default segments and tabs.
        """
        if self.animation_tab_id in self.local_tabs :
            self.stash_anim_pos = self.local_tabs[self.animation_tab_id].pos
        if self.xlim_segment_id in self.global_segments :
            xseg = self.global_segments[self.xlim_segment_id]
            self.stash_xlim_pos = (xseg.start,xseg.end)

        for sid in self.local_segments.keys() :
            self.remove_segment(sid)
        for sid in self.global_segments.keys() :
            self.remove_segment(sid)
        for tid in self.local_tabs.keys() :
            self.remove_tab(tid)
        for tid in self.global_tabs.keys() :
            self.remove_tab(tid)
        self._add_default_segments()
        self._add_default_tabs()

    def set_local_bar_mouse_release_callback(self,cb):
        """
        Sets a callback that is invoked when the mouse is released on the local TabBar.

        Can be used to invoke context menus.

        Arguments:
        cb -- the callback in the form cb(event,x). Arguments are the QMouseEvent and the
              x position in global coordinates where the event occurred.
        """
        self.lb_mrc = cb

    def set_global_bar_mouse_release_callback(self,cb):
        """
        Sets a callback that is invoked when the mouse is released on the global TabBar.

        Can be used to invoke context menus.

        Arguments:
        cb -- the callback in the form cb(event,x). Arguments are the QMouseEvent and the
              x position in global coordinates where the event occurred.
        """
        self.gb_mrc = cb

    def set_stop_button_callback(self,cb):
        """
        Sets a callback that is invoked when the stop button is clicked.

        Arguments:
        cb -- the callback as function without arguments
        """
        self.stop_cb = cb

    def set_tabbars_enabled(self,enabled):
        """
        Enables or disables manual control of tabs on the global or local TabBar
        """
        self.t_en = enabled
        self._maintain_input_states()

    def set_play_button_enabled(self,enabled):
        """
        Enables or disables the play button
        """
        self.p_en = enabled
        self._maintain_input_states()

    def set_segments_by_mouse_enabled(self,enabled):
        self.sbm_en = enabled

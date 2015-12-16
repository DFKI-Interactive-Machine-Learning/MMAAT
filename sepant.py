#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
"""
import matplotlib
matplotlib.use('Agg')
from PyQt4 import QtCore, QtGui

from sepan import ICONS_PATH
from sepan.ui.models.sensordata import SensorDataModel
from sepan.ui.widgets.plots import SensorPyplotView
from sepan.ui.widgets.utilwidgets import PlotControl, \
    SingleItemMaintainAspectRatioLayout
import cv2.cv as cv
import sepan
import sepan.ui.widgets.utilwidgets as ui
import sepan.analysis.report as report
import sepan.data as data
import sepan.utils.io as utils
import thread
import os
import re
import sys
import json

"""
Sequential Pattern Analysis Toolkit
------------------------------------
"""
class SepantUI(QtGui.QMainWindow):
    #----------------------- CONSTANTS ----------------------------------------
    ICON_NAME                = 'icon.png'
    FIXED_HEIGHT             = 320

    DEFAULT_SEGMENT_COLOR    = QtGui.QColor(0,200,100)
    #----------------------- SIGNALS ------------------------------------------
    plotcontrol_xlim_changed = QtCore.pyqtSignal(int,int,int)
    status_bar_changed       = QtCore.pyqtSignal(str,int)
    popup_triggered          = QtCore.pyqtSignal(str,str)
    SETTINGS_PATH            = sepan.CONFIG_PATH
    settings_dict            = {}
    #--------------------------------------------------------------------------

    def __init__(self):
        global ICON_NAME
        QtGui.QMainWindow.__init__(self)
        # UI config
        self.systray = ui.SystemTrayIcon(os.path.join(ICONS_PATH, self.ICON_NAME), self)
        self.setWindowIcon(QtGui.QIcon(os.path.join(ICONS_PATH, self.ICON_NAME)))
        self.setWindowTitle("Sequential Pattern Analysis Toolkit (SePAnT)")
        self.hdf5_fname = ''
        self.algorithm_params = {}
        # --------------------------------------------------------------------
        self.model = SensorDataModel()
        self.image = {}
        self.depthimage = QtGui.QImage()
        self.main_tab = QtGui.QTabWidget()
        self.main_tab.addTab(self.create_analysis_tab(), "Feature Analysis")
        self.setCentralWidget(self.main_tab)
        self.initChannelControl()
        self.setMenuBar(self.create_menu_bar())
        # ----------------------- Generics displays --------------------------
        self.displays = {}
        # --------------------------------------------------------------------
        self.session_file = os.path.join(SepantUI.SETTINGS_PATH, 'last.session')
        last_session = utils.unserialize_object(self.session_file)
        self.settings_dict = last_session if last_session is not None else {
                                 'last_save_path'  : '.',
                                 'last_data_path'  : '.',
                                 'last_report_path' : '.',
                                 'last_import_path' : '.'
                                }
        self.popup_triggered.connect(self.systray.showMessage)
        self.systray.show()

    def __add_algorithm_type__(self, cls, data, stack, combo):
        """
        Automatically adds the configuration parameters to the user interface.
        Arguments:
            cls -- current recognition class
            data  --
            stack -- Stacked layout
            combo -- Combobox, where name of method should be added
        """
        main = QtGui.QWidget()
        layout = QtGui.QGridLayout(main)
        i = 0
        for name, type_data in data.items() :
            dtype   = type_data[0]
            limits  = type_data[1]
            default = type_data[2]
            label = widget = None
            if dtype == "float" : # Float values
                label = QtGui.QLabel(name)
                widget = QtGui.QDoubleSpinBox()
                widget.setValue(float(default))
                widget.setMinimum(limits[0])
                widget.setMaximum(limits[1])
                widget.setDecimals(limits[2])
            elif dtype == "int" :
                label = QtGui.QLabel(name)
                widget = QtGui.QSpinBox()
                widget.setValue(int(default))
                widget.setMinimum(limits[0])
                widget.setMaximum(limits[1])
                widget.setSingleStep(limits[2])
            elif dtype == "select" :
                label = QtGui.QLabel(name)
                widget = QtGui.QComboBox()
                widget.addItems(limits)
            elif dtype == "bool" :
                label = QtGui.QLabel(name)
                widget = QtGui.QCheckBox()
                widget.setCheckState(QtCore.Qt.Checked if default else QtCore.Qt.Unchecked)
            if widget is not None and label is not None :
                row = i / 2
                column = (i % 2) * 2
                if column > 0 :
                    w = QtGui.QWidget()
                    sp = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
                    sp.setHorizontalStretch(4)
                    layout.addWidget(w)
                    column += 1
                layout.addWidget(label, row, column)
                layout.addWidget(widget, row, column + 1)
                i += 1
        stack.addWidget(main)

    def create_config_tab(self):
        """
        Creates dynamic configuration tab for algorithms.
        Returns:
        QtSplitter with config params.
        """
        self.config = QtGui.QWidget()
        self.config.setObjectName("config")
        self.config_tab = QtGui.QSplitter()
        self.config_tab.setOrientation(QtCore.Qt.Vertical)
        self.configl = QtGui.QVBoxLayout(self.config)
        self.config_head = QtGui.QHBoxLayout()
        self.type_head = QtGui.QHBoxLayout()
        self.f1 = QtGui.QWidget()
        fp = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
        fp.setHorizontalStretch(10)
        self.f1.setSizePolicy(fp)
        self.f2 = QtGui.QWidget()
        fp = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
        fp.setHorizontalStretch(10)
        self.f2.setSizePolicy(fp)
        self.config_data_l = QtGui.QLabel("Data:"); self.config_data_input = QtGui.QLabel("")
        self.config_data_input.setFixedSize(300, 20)
        self.config_data_l.setFixedSize(100, 20)
        self.config_data_b = QtGui.QPushButton("Load")
        self.config_data_b.setFixedSize(100, 20)
        self.config_type_l = QtGui.QLabel("Type:"); self.config_type_input = QtGui.QComboBox()
        self.config_type_input.setFixedSize(300, 20)
        self.config_type_l.setFixedSize(100, 20)
        self.config_sep1 = QtGui.QFrame()
        self.config_sep1.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Sunken)
        self.config_panel = QtGui.QStackedLayout()
        self.config_sep2 = QtGui.QFrame()
        self.config_sep2.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Sunken)
        self.config_foot = QtGui.QHBoxLayout()
        self.config_test = QtGui.QPushButton("Test network")
        self.config_train = QtGui.QPushButton("Train")
        self.config_param_opt = QtGui.QPushButton("Optimize parameters")
        self.config_type_l.setAlignment(QtCore.Qt.AlignLeft)
        self.config_data_l.setAlignment(QtCore.Qt.AlignLeft)
        self.config_head.addWidget(self.config_data_l)
        self.config_head.addWidget(self.config_data_input)
        self.config_head.addWidget(self.config_data_b)
        self.config_head.addWidget(self.f1)
        self.type_head.addWidget(self.config_type_l)
        self.type_head.addWidget(self.config_type_input)
        self.type_head.addWidget(self.f2)
        # ------------------------- Configure parameter panels -------------------------------
        self.__configure_recognition_algorithms__(self.config_panel, self.config_type_input)
        # ------------------------- Configure layout -----------------------------------------
        self.config_tab.addWidget(self.config)
        self.configl.addLayout(self.config_head)
        self.configl.addLayout(self.type_head)
        self.configl.addWidget(self.config_sep1)
        self.configl.addLayout(self.config_panel)
        self.configl.addWidget(self.config_sep2)
        self.configl.addLayout(self.config_foot )
        self.config_foot.addWidget(self.config_test)
        self.config_foot.addWidget(self.config_train)
        self.config_foot.addWidget(self.config_param_opt)
        # ------------------------- Configure signals ----------------------------------------
        dataload_call = lambda : self.configure_data_path(QtGui.QFileDialog.getExistingDirectory(
                    parent=self,
                    caption="Choose data directory",
                    directory=self.settings_dict['last_data_path']))
        self.config_data_b.clicked.connect(dataload_call)
        return self.config_tab

    def create_analysis_tab(self):
        """
        Configures an analysis tab.
        Returns:
        configure panel
        """

        self.save = QtGui.QPushButton("Save As...")
        config_tab = QtGui.QWidget()
        config_tab_l = QtGui.QVBoxLayout(config_tab)
        self.upper = QtGui.QWidget()
        self.upper.setObjectName("upper")
        #lower pat
        self.lower_2 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.lower_2.setHandleWidth(10)
        self.lower_2.setObjectName("lower_2")
        self.channelcontrol = QtGui.QTreeView()
        self.channelcontrol.setObjectName("channelcontrol")
        self.channelview = QtGui.QWidget()
        self.cvlayout = QtGui.QVBoxLayout(self.channelview)
        self.channelview.setObjectName("channelview")
        self.sensorview = SensorPyplotView()
        self.plotcontrol = PlotControl(self.sensorview)
        self.plotcontrol.set_ylim_spinner_range(-100000,1000000)
        #putting things together
        self.upper.setFixedHeight(self.FIXED_HEIGHT)
        self.lower_2.addWidget(self.channelcontrol)
        self.lower_2.addWidget(self.plotcontrol)
        config_tab_l.addWidget(self.upper)
        config_tab_l.addWidget(self.lower_2)

        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 793, 23))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        QtCore.QMetaObject.connectSlotsByName(self)
        return config_tab

    def setup_image_displays(self, idxs):
        """
        Dynamically sets up the image displays.
        :Parameter:
        idxs - list of indices
        """
        #putting things together
        layout = QtGui.QHBoxLayout(self.upper)
        for idx in idxs :
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Preferred)
            # ------------ Scene image -------------------------------------------------------------
            display = QtGui.QLabel()
            display.setScaledContents(True)
            display.setObjectName("display:{0}".format(idx))
            display_w = QtGui.QWidget()
            display_l = SingleItemMaintainAspectRatioLayout(4.0/3.0)
            display_l.set_alignment(SingleItemMaintainAspectRatioLayout.ALIGN_NORTHWEST)
            display_l.addWidget(display)
            display_w.setLayout(display_l)
            display_w.setSizePolicy(sizePolicy)
            display_w.setFixedHeight(240)
            display_w.setFixedWidth(self.FIXED_HEIGHT)
            layout.addWidget(display_w)
            self.displays[idx] = display

    def create_menu_bar(self):
        """
        Creates the application menu bar.
        Returns:
            configured menu bar
        """
        mbar = QtGui.QMenuBar(self)
        m_file = mbar.addMenu("Data")
        m_report = mbar.addMenu("Feature Analysis")
        m_export = mbar.addMenu("Export")
        a_opensession = QtGui.QAction(QtGui.QIcon(os.path.join(ICONS_PATH, 'config.png')),
                              "Open Session file..",self)
        a_dopen = QtGui.QAction(QtGui.QIcon(os.path.join(ICONS_PATH, 'hdf.png')),
                              "Open HDF file..",self)
        a_dimport = QtGui.QAction(QtGui.QIcon(os.path.join(ICONS_PATH, 'csv_text.png')),
                                "Import CSV file..",self)
        a_report = QtGui.QAction(QtGui.QIcon(os.path.join(ICONS_PATH, 'report.png')),
                               "Generate report..",self)
        a_export = QtGui.QAction(QtGui.QIcon(os.path.join(ICONS_PATH, 'export.png')),
                               "Export labels..",self)
        openssessionslot = lambda : self.set_session(QtGui.QFileDialog.getOpenFileName(
                    parent=m_file,
                    caption="Choose session file..",
                    filter="*.session",
                    directory=self.settings_dict['last_data_path']))
        openslot = lambda : self.set_hdf_sessionfile(QtGui.QFileDialog.getOpenFileName(
                    parent=m_file,
                    caption="Choose hd5 file..",
                    filter="*.h5",
                    directory=self.settings_dict['last_data_path']))
        exportcsv = lambda : self.export_target_csv(QtGui.QFileDialog.getSaveFileName(
                    parent=m_file,
                    caption="Save csv file..",
                    filter='CSV files (*.csv)',
                    directory=self.settings_dict['last_import_path']))
        reportcall = lambda : self.generatereport(QtGui.QFileDialog.getExistingDirectory(
                    parent=m_report,
                    caption="Choose data directory",
                    directory=self.settings_dict['last_data_path']), QtGui.QFileDialog.getExistingDirectory(
                    parent=m_report,
                    caption="Choose report directory",
                    directory=self.settings_dict['last_report_path']),
                    self.report_done)
        importcsv = lambda : self.import_csv(QtGui.QFileDialog.getOpenFileName(
                    parent=m_file,
                    caption="Choose export csv file..",
                    filter="*.csv",
                    directory=self.settings_dict['last_import_path']))
        a_opensession.triggered.connect(openssessionslot)
        a_dopen.triggered.connect(openslot)
        a_dimport.triggered.connect(importcsv)
        a_report.triggered.connect(reportcall)
        a_export.triggered.connect(exportcsv)
        m_file.addAction(a_opensession)
        m_file.addAction(a_dopen)
        m_file.addAction(a_dimport)
        m_export.addAction(a_export)
        m_report.addAction(a_report)
        return mbar

    def generatereport(self, data_dir, output_dir, callback):
        """
            Generates a report of the feature quality.
            Arguments:
                data_dir -- directory with data
                out_dir  -- directory with report for output
        """
        data_dir = str(data_dir)
        out_dir = str(output_dir)
        self.settings_dict['last_data_path'] = data_dir
        self.settings_dict['last_report_path'] = out_dir
        thread.start_new_thread(report.generate_report_var,(data_dir, out_dir, callback))

    def report_done(self, name):
        """'
        Called, when report is ready.
        """
        self.popup_triggered.emit("Report Update", "Report generated: {0}".format(name))

    def set_segments_slot(self):
        self.plotcontrol.clear_segments()

        for s in self.model.get_labels() :
            self.add_segment_slot(s.get_idx(), s.get_sid())

    def update_segment_slot(self, idx, sid):
        seg = self.model.get_label(idx, sid)
        if seg is None : return #robustness fix
        self.plotcontrol.move_segment(sid, seg.get_start(), seg.get_end())

    def add_segment_slot(self, idx, sid):
        seg = self.model.get_label(idx, sid)
        popup_s = QtGui.QMenu()
        f1 = lambda : self.model.remove_segment(idx,sid)
        f2 = None
        if self.model.get_label_mode() == 0 :
            f2 = lambda : self.model.relabel_segment(idx, sid,
                            str(QtGui.QInputDialog.getItem(self,"Update segment label", "Label:", sepan.CLASSES)[0]))
        else :
            f2 = lambda : self.model.relabel_segment(idx, sid,
                            str(QtGui.QInputDialog.getItem(self,"Update segment label", "Label:", sepan.ATTENTION)[0]))
        popup_s.addAction("Remove label", f1)
        popup_s.addAction("Update label", f2)
        popup_e = QtGui.QMenu()
        popup_e.addAction("Remove label", f1)
        popup_e.addAction("Update label", f2)
        mcb = self.model.move_segment
        mrcb = lambda evt,sid,start=None,end=None : self.show_popup_slot(evt, sid, start, end, popup_s, popup_e)
        self.plotcontrol.add_segment(
            idx,
            "local",
            seg.get_start(),
            seg.get_end(),
            move_callback=mcb,
            mouse_release_callback=mrcb,
            global_shadow=True,
            color=self.DEFAULT_SEGMENT_COLOR,
            sid=sid,
            has_visualization=True)

    def show_popup_slot(self,evt,sid,start,end,popup_s,popup_e):
        if evt.button() == QtCore.Qt.RightButton :
            if not start is None : popup_s.exec_(evt.globalPos())
            elif not end is None : popup_e.exec_(evt.globalPos())

    def stop_all(self):
        """
        Helper function to stop all operations that perform some kind of ongoing procedure at once.

        Used to ensure that only one such operation may run at a time
        """
        self.model.stop_animation()
        self.plotcontrol.set_tabbars_enabled(True)
        self.plotcontrol.set_play_button_enabled(True)

    def initChannelControl(self):
        """
        Initializes the channel control element.
        """
        self.plotcontrol_xlim_changed.connect(self.change_plotcontrol_xlim0)
        self.status_bar_changed.connect(self.statusbar.showMessage,QtCore.Qt.QueuedConnection)
        self.channelcontrol.clicked.connect(self.model.update)
        self.model.new_segment_data.connect(self.set_segments_slot)
        self.model.segment_added.connect(self.add_segment_slot)
        self.model.segment_removed.connect(self.remove_segment_slot)
        self.model.segment_changed.connect(self.update_segment_slot)
        self.model.animation_step.connect(lambda i : self.animation_slot(i, self.model))
        self.channelcontrol.setModel(self.model)
        self.plotcontrol.set_model(self.model)
        self.plotcontrol.set_stop_button_callback(self.stop_all)
        self.tabs = {}

    def change_plotcontrol_xlim0(self,idx,s,e):
        self.plotcontrol.set_xlim(s,e,load_data=False)

    def remove_segment_slot(self, sid):
        self.plotcontrol.remove_segment(sid)

    def set_image(self, idx, fname):
        """
        Sets the scence image.
        :Parameters:
                fname - file name of the RGB image.
        """
        if idx not in self.image.keys() :
            self.image[idx] = QtGui.QImage()
        self.image[idx].load(fname)
        self.displays[idx].setPixmap(QtGui.QPixmap.fromImage(self.image[idx]))

    def set_depth_image(self, fname):
        """
        Sets the zimage.
        :Parameters:
                fname - file name of the zimage.
        """
        dimg = cv.LoadImageM(fname)
        self.depthimage = QtGui.QImage(dimg.tostring(), dimg.width, dimg.height, QtGui.QImage.Format_RGB888)
        self.depthdisplay.setPixmap(QtGui.QPixmap.fromImage(self.depthimage))

    def set_session(self, _session_file):
        """
        Sets the session file, which contains information about the used sensors.
        :param _session_file: - json encoded session file
        :return:
        """
        session_fname = str(_session_file)
        if session_fname is None or session_fname == "" : return # ignore if nothing is selected
        data_dir = os.path.dirname(session_fname)
        with open(session_fname) as data_file:
            data = json.load(data_file)
            h5file = os.path.join(data_dir,data['device'][0]['sessionfile'])
            depthimg = os.path.join(data_dir, data['depth-camera'][0]['depth'])
            colorimg = os.path.join(data_dir, data['depth-camera'][0]['color'])
            self.hdf5_fname = str(h5file)
            if self.hdf5_fname is None or self.hdf5_fname == "" : return # ignore if nothing is selected
            self.model.store_labels()
            self.settings_dict['last_data_path'] = os.path.dirname(self.hdf5_fname)
            #----------------------------------------------------------------------------------------------------
            self.model.set_sensor_data(self.hdf5_fname)
            self.model.add_image_folder(colorimg)
            self.model.add_image_folder(depthimg)
            self.model.sync_images()
            self.update_statusbar(0)
            self.setup_image_displays(self.model.get_image_idxs())
            self.animation_slot(0, self.model)

    def set_hdf_sessionfile(self, _hdf5_fname):
        """
            Sets the HDF5 session file.
            :Parameters:
                hdf5_fname - file name of the hdf5 file.
        """
        self.hdf5_fname = str(_hdf5_fname)
        if self.hdf5_fname is None or self.hdf5_fname == "" : return # ignore if nothing is selected
        self.set_hdf(self.hdf5_fname)
        dirname = self.hdf5_fname[:-3] + '_image'
        if not os.path.exists(dirname) :
            dirname = os.path.join(os.path.dirname(self.hdf5_fname), 'images')
        self.model.set_indexed_imagedir(dirname)
        self.update_statusbar(0)
        self.setup_image_displays(self.model.get_image_idxs())
        self.animation_slot(0, self.model)

    def set_hdf(self, _hdf5_fname):
        """
            Sets the HDF5 file.
            :Parameters:
                hdf5_fname - file name of the hdf5 file.
        """
        self.model.store_labels()
        self.settings_dict['last_data_path'] = os.path.dirname(self.hdf5_fname)
        self.model.set_sensor_data(self.hdf5_fname)

    def configure_data_path(self, data_dir):
        data_dir = str(data_dir)
        if data_dir is None or data_dir == '' : return
        self.config_data_input.setText(data_dir)
        for a in self.algorithm_params.itervalues() :
            a.set_data_dir(data_dir)


    def import_csv(self, csv_fname):
        """
        Imports csv file new features.
        Arguments:
        csv_fname -- path to csv
        """
        fname = str(csv_fname)
        if fname is None or fname == '' : return
        self.settings_dict['last_import_path'] = os.path.dirname(fname)
        h5_name = re.sub(r".csv",".h5", fname)
        if h5_name == self.hdf5_fname : self.model.close()
        data.convert_csv_to_hdf(fname, h5_name, True,
                                sepan.CLASSES,
                                sepan.IGNORE_FEATURES)
        self.set_hdf(h5_name)


    def export_target_csv(self, export_file) :
        """
        Exports the target to an export file.
        Arguments:
        export_file -- path to export file
        """
        fname = str(export_file)
        if fname is None or fname == '' : return
        data.save_labels([(sensor_model_segment.get_start(),
                          sensor_model_segment.get_end(),
                          sensor_model_segment.get_name())
                          for sensor_model_segment in self.model.get_labels()],
                          fname)

    def update_statusbar(self, i):
        """
        Updates the status bar with the current index.
        Parameters:
        i - data index
        """
        self.statusbar.showMessage('{} : [index] : {}'.format(self.hdf5_fname, i))

    def animation_slot(self, step, model):
        """
        Sets the current index of the display data.
        :Parameters:
                step - index of the current dataset
                model - data model
       """
        if model.sensordata is None : return
        # Update status bar
        self.update_statusbar(step)
        # Update Slider
        self.plotcontrol._animation_step(step)
        # Update images
        idxs = model.get_image_idxs()
        for idx in idxs :
            fname = model.get_png_fname(idx, step)
            if fname is not None :
                self.set_image(idx, fname)


    def closeEvent(self, evt):
        """
        Store labels when closing the application.
        evt - event
        """
        if self.model is not None :
            self.model.store_labels()
        if not os.path.exists(SepantUI.SETTINGS_PATH) :
            os.makedirs(SepantUI.SETTINGS_PATH)
        utils.serialize_object(self.settings_dict, self.session_file)
        self.systray.hide()

if __name__ == "__main__" :
    app = QtGui.QApplication(sys.argv)
    ui = SepantUI()
    ui.show()
    sys.exit(app.exec_())
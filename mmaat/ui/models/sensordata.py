"""
 DFKI GmbH 2013 - 20xx
 All rights reserved.
 Maintainer: Markus Weber
"""
from PyQt4 import QtCore, QtGui
import h5py as h5
import sepan
import sepan.data as data
import numpy as np
import os
import time

HORIZONTAL_HEADERS = ["Channel"]


def hsv_display_colors(ncolors, hrange=(0,360), srange=(255,255), vrange=(65,255), nh='auto', ns=1, nv='auto'):
    if ns == 'auto' : ns = 1 #saturation has rather poor discriminative power
    needed = lambda x : int(np.ceil(1.0*ncolors/x/ns))
    if nh == 'auto' and nv == 'auto' :
        nh = 8 #8 hues clearly distinguishable as 'primary colors'
        nv = needed(nh)
    elif nh == 'auto':
        nh = needed(nv)
    elif nv == 'auto':
        nv = needed(nh)
    getval = lambda rng,idx,n: int(round(rng[0] + 1.0*idx/n*(rng[1]-rng[0])))
    clist = []
    for i in xrange(ncolors) :
        hidx = i / nv / ns
        sidx = i / nv
        vidx = i % nv
        h = getval(hrange,hidx,nh)
        s = getval(srange,sidx,ns)
        v = getval(vrange,vidx,nv)
        clist.append((h,s,v))
    return clist

class BaseTreeItem(object):
    """
    an item that can be used to populate a tree view, knowing it's place in the model
    """

    def __init__(self, name, inParentItem, inColor):
        """
        Derive specific tree item objects from this guy
        Override the specific methods that the model needs
        @param inParentItem: The parent of a type BaseTreeItem
        """
        self.parent = inParentItem
        self.name = name
        self.children = []
        self.color = inColor
        if inParentItem is not None :
            self.parent.AddChild(self)
        self.cbstate = QtCore.Qt.Checked

    def CheckedState(self):
        return self.cbstate

    def SetState(self, state):
        self.cbstate = state
        for ch in self.children :
            ch.SetState(self.cbstate)

    def toggle_state(self):
        state = QtCore.Qt.Checked if self.cbstate == QtCore.Qt.Unchecked else QtCore.Qt.Unchecked
        self.SetState(state)

    def Color(self):
        return self.color

    def AddChild(self, inChild):
        """
        @param inChild: The child to add, of a type BaseTreeItem
        """

        self.children.append(inChild)

    def Path(self):
        if self.parent is None :
            return self.name
        pStr = self.parent.Path()
        return '{} -> {}'.format(pStr, self.name)

    def DepthPath(self):
        if self.parent is None :
            return 0
        d = self.parent.DepthPath()
        return d + 1

    def GetChildByName(self, name):
        for c in self.children :
            if c.name == name :
                return c
        return None

    def HasChild(self, name):
        return self.GetChildByName(name) is not None

    def GetChildCount(self):
        """
        @return: The number of children this item holds
        """

        return len(self.children)

    def GetChild(self, row):
        """
        @return: The child living at that specific row index (starting from 0)
        """
        if row >= 0 and row < len(self.children) :
            return self.children[row]
        else :
            return None

    def GetParent(self):
        """
        @return: simply returns the parent for this item, of a type BaseTreeItem
        """

        return self.parent

    def ColumnCount(self):
        """
        @return: The amount of columns this tree item has
        needs to be implemented by derived classes
        """

        raise Exception("Column Count Not Specified!!")

    def Data(self, inColumn):
        """
        @return: Returns the data to display!
        Needs the be implemented by derived classes
        """

        raise Exception("Data gather method not implemented!")

    def Parent(self):
        """
        @return: the BaseTreeItem parent object
        """
        return self.parent

    def Row(self):
        """
        @return the row this item resides on (int)
        """

        if self.parent:
            return self.parent.children.index(self)
        return 0

    def __len__(self):
        "@return number of children"
        return len(self.children)

class SensorDataGroupTreeItem(BaseTreeItem):
    """
    Represents a data group in the tree
    """

    def __init__(self, inParent, inGroupName, inColor):
        """
        Initializes itself with a BaseTreeItem derived object and a stencil
        @param inParent: The node to parent
        @param inStencil: The stencil as data object
        """
        super(SensorDataGroupTreeItem, self).__init__(inGroupName, inParent, inColor)

    def __str__(self, *args, **kwargs):
        return '[group] : ' + self.name

    def ColumnCount(self):
        """
        Holds only 1 column
        """
        return 1

    def Data(self, inColumn):
        """
        @return: The name of the stencil
        """

        if inColumn == 0:
            return self.name
        return ""

class SensorTreeItem(BaseTreeItem):
    """
    represents a Sensor item
    """
    def __init__(self, inParent, inSensorChannel, inColor):
        """
        Initializes itself with a BaseTreeItem derived object and a stamp
        @param inParent: A Root Tree Item
        @param inStamp:  A Sensor object
        """

        super(SensorTreeItem, self).__init__(inSensorChannel.name, inParent, inColor)
        self.sensorChannel = inSensorChannel

    def ColumnCount(self):
        """
        Holds only 1 column
        """
        return len(HORIZONTAL_HEADERS)

    def Data(self, inColumn):
        """
        @return: The name of the stamp
        """

        if inColumn == 0 :
            return self.name
        elif inColumn == 1 :
            return self.sensorChannel.get_channel_id()
        return ""

    def SetState(self, state):
        self.cbstate = state
        self.sensorChannel.set_visible(True if state == QtCore.Qt.Checked else False)

    def SensorChannel(self):
        return self.sensorChannel

    def __str__(self, *args, **kwargs):
        return '[item] : ' + self.name

class RootTreeItem(BaseTreeItem):
    """
    Represents the root of the tree
    """

    def __init__(self):
        """
        The root has no parents and no data it needs to retrieve info from
        """
        super(RootTreeItem, self).__init__("ROOT",None, None)

    def ColumnCount(self):
        """
        Holds only 1 column
        """
        return 1

    def Data(self, inColumn):
        """
        The root doesn't get displayed and for that reason has no meaning
        But because I like providing meaning, i give it a return value
        """
        if inColumn == 0:
            return "Sensor Channels"
        return ""
    def __str__(self, *args, **kwargs):
        return '[ROOT]'

class SensorDataModelChannel():
    """
    Model class representing a sensor data channel and it's display values.
    """
    def __init__(self,name, model,channelid, c):
        """
        Constructs a new channel

        Arguments:
        name      -- the name of the channel as a human-readable string
        color     -- the color as tuple (r,g,b) in which the channel should be displayed,
                     values for r,g and b must be between 0 and 255
        model     -- the SegmentationDataModel to which the channel belongs (needed to generate
                     QModelIndex objects)
        channelid -- the id of this channel, defining it's category
        c         -- color
        """
        self.name = name
        self.cbstate = QtCore.Qt.Checked
        self.model = model
        self.cid = channelid
        self.ymax = 1
        self.ymin = -1
        self.datacb = lambda : []
        self.data = []
        self.offset = 0
        self.color = c
        self.visible = True

    def get_color(self): return self.color
    def is_visible(self): return self.visible
    def set_visible(self, b) : self.visible = b
    def toggle_visible(self): self.visible = not self.visible
    def get_name(self): return self.name
    def get_index(self): return self.index
    def set_data(self,data): self.data = data
    def set_data_callback(self,cb): self.datacb = cb
    def get_data(self):
        if not self.data is None : return self.data # prefer stored data over callback mechanism
        d = self.datacb()
        return d
    def get_data_callback(self):
        return self.datacb
    def get_channel_id(self): return self.cid
    def get_ckey(self): return self.cid+"/"+self.name
    def get_max_y(self):
        return self.ymax
    def get_min_y(self):
        return self.ymin
    def set_ylim(self,ymin=None,ymax=None):
        if ymin != None : self.ymin = ymin
        if ymax != None : self.ymax = ymax
    def update_ylim(self):
        data = self.get_data()
        self.ymin = min(data)
        self.ymax = max(data)
    def get_offset(self):
        return self.offset
    def set_offset(self,offset):
        self.offset = offset


class SensorDataModelSegment(object):
    """
    Model class representing a segmentation segment consisting of one start and one end point
    """
    def __init__(self,idx,sid,start,end,name="NONE"):
        self.sid = sid
        self.idx = idx
        self.start = start
        self.end = end
        self.name = name

    def __repr__(self, *args, **kwargs):
        return '[idx={0}, sid={1}, start={2}, start={3}, name={4}]'.format(self.idx, self.sid, self.start, self.end, self.name)

    def __str__(self, *args, **kwargs):
        return 'SensorDataModelSegment [idx={0}, sid={1}, start={2}, start={3}, name={4}]'.format(self.idx, self.sid, self.start, self.end, self.name)

    def get_bounds(self):
        return (self.start,self.end)

    def get_start(self):
        return self.start

    def get_end(self):
        return self.end

    def set_start(self,start):
        self.start = start

    def set_end(self,end):
        self.end = end

    def get_idx(self):
        return self.idx

    def get_sid(self):
        return self.sid

    def get_name(self):
        return self.name

    def set_name(self,name):
        self.name = name


class DataModel():
    def __init__(self):
        self.CHANNELNAMES = []
        self.channeldata = {}
        self.sensordata = None
        self.len_sensordata = 0
        self.begin = 0
        self.end = 0
        self.segmentmode = 0
    def set_label_mode(self, mode):
        """
            Sets the label mode.
            :Parameter:
                mode -- labeling mode
        """
        self.segmentmode = mode
    def get_label_mode(self):
        """
            Returns the label mode.
            :Returns:
                current
        """
        return self.segmentmode
    def get_all_channels(self):
        """
        Returns all channels that are defined for this model, regardless of whether they are
        selected for display or have any data available

        Returns: a list of lists where each sub-list is a channel group
        """
        return self.channeldata.values()

    def get_visible_channels(self):
        """
        Returns all single sensor channels that contain data and are selected for display

        Returns: a list of visible SensorDataModelChannel objects (objects for whole bodyparts
                 are not included)
        """
        return self.get_active_channels()
    def get_active_channels(self):
        """
        Returns all single sensor channels that contain data

        Returns: a list of active SensorDataModelChannel objects (objects for whole are not included)
        """
        channels = []
        if self.sensordata == None : return channels
        for c in self.channeldata[1:] :
            channels.append(c)
        return channels

    def get_visible_yspan(self):
        """
        Returns the maximum and minimum data values among all _visible_ channels

        Returns: miny,maxy where miny/maxy are the minimum/maximum data values found
                 in channels obtained via self.get_visible_channels()
        """
        channels = self.get_visible_channels()
        if len(channels) == 0 : return 0,0
        miny = np.Inf
        maxy = -np.Inf
        for c in channels :
            a = np.array(c.get_data())
            if len(a) < 1 : continue
            cmax = np.amax(a)
            cmin = np.amin(a)
            if cmax > maxy : maxy = cmax
            if cmin < miny : miny = cmin
        return (miny,maxy)

    def __len__(self):
        if self.sensordata == None : return 0 #robustness fix
        return self.get_data_num_samples()

    def set_sensor_data(self,sd):
        self.sensordata = sd

    def get_sensordata(self):
        return self.sensordata

    def reset_channel_data(self,sensordata=None,channeldata=None):
        if sensordata is None : sensordata = self.sensordata
        if channeldata is None : channeldata = self.channeldata
        signal = sensordata['data']['signal']
        for channel in self.channeldata :
            i_pos = sepan.INDICES[channel.get_name()]
            channel.set_data(signal[self.begin:self.end,i_pos])
            channel.set_offset(self.begin)
    def get_data_offset(self):
        return self.begin
    def get_data_size(self):
        return len(self)
    def get_data_num_samples(self) :
        return 0  if self.sensordata is None else self.len_sensordata

    def get_segment_data(self,seg):
        if self.sensordata is None or self.len_sensordata == 0 : return None
        if seg == None : return None
        return self.sensordata[seg.get_start():seg.get_end()]

class SensorDataModel(QtCore.QAbstractItemModel, DataModel):
    """
    Model class for sensor data in the context of the UI,
    captures display selection state of individual channels,
    animation state, segmentation and data changes

    Also serves as a QTreeView model for channel selection

    All changes made to one of the properties mentioned above
    should always be communicated via messages of the corresponding
    SegmentationDataModel
    """
    new_dataset = QtCore.pyqtSignal()       #emitted when the underlying dataset has been replaced
    dataset_changed = QtCore.pyqtSignal()   #emitted when the underlying dataset has been modified
    new_segment_data = QtCore.pyqtSignal()  #emitted when segmentation data has been completely replaced
    segment_changed = QtCore.pyqtSignal(int,int)#emitted when position of a single segment changed (argument = segment id)
    segment_added = QtCore.pyqtSignal(int,int)  #emitted when a new segment has been added (but not when new_segment_data is emitted)
    segment_removed = QtCore.pyqtSignal(int,int)#emitted when a new segment has been removed (but not when new_segment_data is emitted)
    animation_step = QtCore.pyqtSignal(int) #emitted when the animation step that should be displayed has changed
    animation_stopped = QtCore.pyqtSignal() #emitted when an ongoing animation has reached the last step
    dynamic_connection_terminated = QtCore.pyqtSignal() #emitted when the dynamic connection has been terminated and no more data will be received
    refmot_sid_changed = QtCore.pyqtSignal(int) #emitted when selecting the segment that is used as reference motion
    sig_update_channels = QtCore.pyqtSignal()           # emitted when view needs to update
    SEGMENT_TYPES = ('gestures', 'attention')
    
    def __init__(self):
        self.UNKNOWN           = "unknown" #channel-id indicating an unknown channel
        QtCore.QAbstractItemModel.__init__(self)
        DataModel.__init__(self)
        self.t = None #timer for animation
        self.channelUpdaterT = None # Updater for channel streaming data
        self.anim_start = (0,0) #timestamp and time step where animation was started
        self.anim_interval = 1/30.0 #determines update frequency during animation in seconds
        self.i = 0 #timestep for animation
        self.next_sid = 0 #segment id for SensorDataModelSegment objects
        self.segments = {}
        for i in range(len(SensorDataModel.SEGMENT_TYPES)) :
            self.segments[i] = []
        self.attention_segments = []
        self.interactive_lastupdate = 0
        self.interactive_updateinterval = 1 / 10.0
        self.channeldata = [] #contains a list of SensorDataModelChannel
        self.sensordata = None
        self.pnglst = []
        self.sensorfname = None
        self.rows = 0
        self.label_colors = {}
        self.default_label_color = (153,187,153) #green with low saturation
        self.signatureslst = []
        self.signatures = []
        self.idx = []
        self.png_by_index = {}
        # set the root item to add other items to
        self.rootItem = RootTreeItem()

    def update_channels(self, names):
        """
            Updates the channels.
            :Parameter:
                names - list of names
        """
        self.CHANNELNAMES = names
        n = len(self.CHANNELNAMES)
        color = (255,0,0)
        ncolors = 10
        nshades = int(np.ceil(1.0*n/ncolors))
        cid = 1
        for i in xrange(n) :
            split = self.CHANNELNAMES[i].split(' ')
            shade = i % nshades
            color = i / nshades
            color2 = QtGui.QColor()
            color2.setHsv(360.0*color/ncolors,255.0,64.0 + 192.0*shade/nshades)
            rgb = color2.toRgb()
            c = SensorDataModelChannel(self.CHANNELNAMES[i], self,cid,
                                       [rgb.red(), rgb.blue(), rgb.green()])
            c.set_ylim(-1,1)
            self.channeldata.append(c)
            l_s = len(split)
            parent = self.rootItem
            for si in xrange(l_s) :
                name = split[si]
                item = None
                if si == (l_s - 1) :
                    item = SensorTreeItem(parent, c, color2)
                else :
                    if parent.HasChild(name) :
                        item = parent.GetChildByName(name)
                    else :
                        item = SensorDataGroupTreeItem(parent, name, color2)
                parent = item
            cid += 1
        self.refmot_channels = {}
        self.refmot_data = None
        for k in self.channeldata :
            self.refmot_channels[k] = []
        self.xoff = 0

    # reimplemented methods
    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.Parent()
        if parentItem == self.rootItem:
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.Row(), 0, parentItem)
        # new methods

    def index(self, row, column, parent):
        """
        The index is used to access data by the view
        This method overrides the base implementation, needs to be overridden
        @param row: The row to create the index for
        @param column: Not really relevant, the tree item handles this
        @param parent: The parent this index should be created under
        """
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        parentItem = self.nodeFromIndex(parent)

        childItem = parentItem.GetChild(row)
        if not childItem is None:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def rowCount(self, parentindex):
        """
        Returns the amount of rows a parent has
        This comes down to the amount of children associated with the parent
        @param parentindex: the index of the parent
        """
        node = self.nodeFromIndex(parentindex)
        if node is None:
            return 0
        return len(node)

    def nodeFromIndex(self, index):
        """
        Returns item from index.
        @return: item
        """
        return index.internalPointer() if index.isValid() else self.rootItem

    def columnCount(self, parent=None):
        """
        Returns column count.
        @return: column count
        """
        if parent and parent.isValid():
            return parent.internalPointer().ColumnCount()
        else:
            return len(HORIZONTAL_HEADERS)

    def get_number_of_samples(self):
        """
        Gets the number of samples.
        @return: number of samples
        """
        return len(self.sensordata) if self.sensordata is not None else 0

    def get_image_idxs(self):
        """
        Returns the images indexes.
        @return: list of indexes
        """
        return self.png_by_index.keys()

    def get_png_fname(self, idx, i):
        return None if i < 0 or i >= len(self.png_by_index[idx]) else self.png_by_index[idx][i]

    def data(self, index, role):
        """
        The view calls this to extract data for the row and column associated with the parent object
        @param index: the parentindex to extract the data from
        @param role: the data accessing role the view requests from the model
        """
        if not index.isValid():
            return QtCore.QVariant()
        # get the item out of the index
        item = index.internalPointer()
        if role == QtCore.Qt.CheckStateRole :
            return item.CheckedState()
        # Return the data associated with the column
        elif role == QtCore.Qt.DisplayRole:
            return item.Data(index.column())
        elif role == QtCore.Qt.ForegroundRole :
            return QtGui.QBrush(item.Color())
        # Otherwise return default
        return QtCore.QVariant()

    def headerData(self,section,orientation,role=QtCore.Qt.DisplayRole):
        if (orientation == QtCore.Qt.Horizontal and
        role == QtCore.Qt.DisplayRole):
            try:
                return QtCore.QVariant(HORIZONTAL_HEADERS[section])
            except IndexError:
                pass

        return QtCore.QVariant()

    def flags(self,index):
        if not index.isValid() : return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled

    # new methods
    def _load_filelist_(self, dirname, ending):
        """
        Loads file list with a specific ending from a directory.

        Argumens:
        dirname -- directory with files
        ending  -- type of file
        """
        if not os.path.exists(dirname) or not os.path.isdir(dirname) : return []
        img_list = [os.path.join(dirname,x) for x in os.listdir(dirname) if x.endswith(ending)]
        if len(img_list) == 0 : return
        example = os.path.basename(img_list[0])
        prefixidx = example.find('_') + 1# if indexed there will be a prefix 0_
        sufidx =  len(example) - example.find('.')
        img_list.sort(key = lambda a : int(os.path.basename(a)[prefixidx:-sufidx]))
        return img_list

    def load_signatures(self, dirname, ending):
        """
        Loads PNGs from a directory.

        Arguments:
        dirname -- directory with the images of the videos stream
        ending  -- type of image
        """
        if not os.path.exists(dirname) or not os.path.isdir(dirname) : return []
        img_list = [os.path.join(dirname,x) for x in os.listdir(dirname) if x.endswith(ending)]
        img_list.sort(key = lambda a : int(os.path.basename(a)[:-4]))
        return img_list

    def split_images(self, pngs):
        """
            Splitting dependent on the prefix.
            :Parameters:
                pngs - list of png
        """
        split = {}
        for png in pngs :
            cid = int(os.path.basename(png)[:1])
            if not cid in split.keys() :
                split[cid] = []
            split[cid].append(png)
        return split

    def set_sensor_data(self, hdf5_file):
        """
        Reads data for each channel from a sensordata object, overwriting any previously obtained data

        Arguments:
        hdf5_file -- the SensorData object from which data should be read

        Emits the following signals:
        dataChanged(QModelIndex,QModelIndex) - once for each root item in the tree view
        self.new_dataset                     - once after all other operations returned
        """
        self.sensordata = h5.File(hdf5_file,'r')
        self.sensorfname = hdf5_file
        desc, classes = data.read_description(self.sensordata)
        self.len_sensordata = len(self.sensordata['data']['signal'])
        self.label_colors = {}
        colors = [QtGui.QColor.fromHsv(h,s,v).getRgb()[:-1] for h,s,v in hsv_display_colors(len(classes),srange=(100,100),vrange=(180,180),nv=1)]
        for i in xrange(len(classes)) :
            self.label_colors[classes[i]] = colors[i]
        sepan.set_descriptions(desc)
        sepan.set_classes(classes)
        self.update_channels(desc)
        self.end = self.get_data_num_samples()
        self.interactive_lastupdate = 0
        self.signatures = [None] * len(self.signatureslst)
        # first remove all old rows
        self.clean_channels()
        self.setup_channels_and_segments()

    def add_image_folder(self, dirname):
        """
        Adds a new image folder.
        :param dirname: path
        """
        nidx = len(self.png_by_index)
        if os.path.exists(dirname) :
            self.png_by_index[nidx] = self._load_filelist_(dirname, 'png')

    def sync_images(self):
        """
        Syncs images with sampling rate of tracking device.
        """
        pbi_dict = {}
        for key, pnglst in self.png_by_index.iteritems():
            ts = self.sensordata['data']['timestamp'][:]
            example = pnglst[0]
            base = os.path.basename(example)
            dname = os.path.dirname(example)
            sufidx =  (len(base) - base.find('.'))
            suffix = base[-(sufidx - 1):]
            its = np.array([int(os.path.basename(x)[:-sufidx]) for x in pnglst],dtype=long)
            if np.all(ts == 0) : return
            pbi = []
            len_img = its.size
            j = 0
            for i in xrange(len(ts)) :
                if ts[i] > its[j] and j < len_img - 1:
                    j += 1
                pbi.append(os.path.join(dname,"{0}.{1}".format(its[j], suffix)))
            assert len(pbi) == len(ts)
            pbi_dict[key] = pbi
        self.png_by_index = pbi_dict

    def set_indexed_imagedir(self, dirname):
        """
        Sets indexed image directory.
        :param dirname - directory path to indexed images
        """
        self.pnglst  = self.split_images(self._load_filelist_(dirname, 'png') if os.path.exists(dirname) else [])
        self.png_by_index = self.get_images_by_index(self.pnglst, dirname) if os.path.exists(dirname) else []
        self.img_len = len(self.pnglst)


    def get_images_by_index(self, pngdict, dname, img_format='png'):
        pbi_dict = {}
        for key, pnglst in pngdict.iteritems():
            ts = self.sensordata['data']['timestamp'][:]
            its = np.array([int(os.path.basename(x)[2:-4]) for x in pnglst],dtype=long)
            if np.all(ts == 0) : return pngdict
            pbi = []
            len_img = its.size
            j = 0
            for i in xrange(len(ts)) :
                if ts[i] > its[j] and j < len_img - 1:
                    j += 1
                pbi.append(os.path.join(dname,"{0}_{1}.{2}".format(key, its[j], img_format)))
            assert len(pbi) == len(ts)
            pbi_dict[key] = pbi
        return pbi_dict

    def get_signature(self, i):
        """
        Returns the hand signature at index i.
        Arguments:
            i -- index
        """
        if i < len(self.signatures) and i >= 0 :
            if self.signatures[i] is None :
                self.signatures[i] = data.read_hand_signature(self.signatureslst[i])
            return self.signatures[i]
        return None

    def setup_channels_and_segments(self):
        self.init_channels()
        self.reset_channel_data()
        self._maintain_ylims(None) #reset ylim data for all channels
        #reset segmentation data
        self.segments[self.segmentmode] = []
        target = self.sensordata['data']['target'][:]
        attention = None
        if 'attention' in self.sensordata['data'] :
            attention =  self.sensordata['data']['attention']
        last_label = target[0]
        last_attention = None
        if attention is not None :
            last_attention = np.argmax(attention[0])
        start = None
        start_attention = None
        inclass = False
        inattention = False
        for i in xrange(1, len(target)) :
            if target[i] != last_label :
                if start == None :
                    start = i
                    inclass = True
                elif inclass :
                    self.add_segment(start, i, sepan.CLASSES[last_label])
                    if not target[i] == 0 : # Two classes are directly connected
                        start = i
                        inclass = True
                    else :
                        start = None
                        inclass = False
                last_label = target[i]
            if attention is not None :
                a = np.argmax(attention[i])
                if a != last_attention :
                    if start_attention == None :
                        start_attention = i
                        inattention = True
                    elif inattention :
                        self.add_segment(start_attention, i, sepan.ATTENTION[last_attention], 1)
                        if not a == 0 : # Two classes are directly connected
                            start_attention = i
                            inattention = True
                        else :
                            start_attention = None
                            inattention = False
                    last_attention = a
        self.new_dataset.emit()
        self.new_segment_data.emit()

    def interactive_step(self,data):
        if self.first_update :
            self.setup_channels_and_segments()
            self.first_update = False
        else :
            self.append_data(data)
        if time.time() - self.interactive_lastupdate  > self.interactive_updateinterval :
            self.set_animation_step(-1)
            self.dataset_changed.emit()
            self.interactive_lastupdate = time.time()

    def crop_sensor_data(self, begin, end):
        """
            Crops the sensor data to its new size.
            :Parameters:
                begin - begin of segment
                end   - end of segment
        """
        #stash and update old segments as (start,end) tuples
        segments = [ (seg.get_start()-begin,seg.get_end()-begin) for seg in self.segments[self.segmentmode] if seg.get_bounds()[0] > begin and seg.get_bounds()[1] < end]
        self.set_sensor_data(self.sensordata[begin:end])
        #apply stashed segments
        self.set_segments(segments)

    def clean_channels(self):
        old = self.rows
        self.rows = 0
        if old > 0 :
            self.rowsRemoved.emit(QtCore.QModelIndex(),0,old)
        self.sig_update_channels.emit()

    def init_channels(self):
        """"
        Initializes channel information, determines values for self.rows
        """
        if self.rows != 0 : return #only need to update rows and locations once
        rows = 0
        for channel in self.channeldata :
            channel.set_data_callback(lambda : [])
            rows += 1
        self.rows = rows

        if rows > 0 :
            self.rowsInserted.emit(QtCore.QModelIndex(),0,rows-1)
        self.sig_update_channels.emit()

    def get_visible_channels(self):
        """
        Returns all single sensor channels that contain data and are selected for display

        Returns: a list of visible SensorDataModelChannel objects
        """
        channels = []
        if self.sensordata == None : return channels
        for c in self.channeldata :
            if c.is_visible() : channels.append(c)
        return channels

    def update(self,index):
        """
        Switches the checkbox-state of a channel entry in the tree-view as reaction
        to a user clicking on that channel entry

        When necessary the state of child- or parent- entries is also changed to
        maintain the invariant that a parent entry is selected iff at least one of
        its children is selected.

        Arguments:
        index -- the QModelIndex of the item that has been clicked by the user

        Emits the following signals:
        dataChanged(QModelIndex,QModelIndex) -- for each entry that has been modified
        """
        index.internalPointer().toggle_state()
        self.dataChanged.emit(index,index)
        self.sig_update_channels.emit()

    def notify_channel_update(self):
        """
        Used to notify the model, that a sig_update_channels event should be emitted
        (needed when channel selection states are modified externally)

        Emits the following signals:
        sig_update_channels() -- once
        """
        self.sig_update_channels.emit()

    def start_animation(self):
        """
        Starts an animation timer that updates the animation step every self.anim_interval seconds,
        assuming that the data is sampled at 100hz

        The animation will start at the current index self.i
        """
        if self.is_in_animation() : return # already running
        if len(self.get_active_channels()) == 0 : return # no data for animation available
        self.anim_start = (time.time(),self.i)
        self.t = QtCore.QTimer(self)
        self.t.setSingleShot(False)
        self.t.setInterval(self.anim_interval)
        self.t.timeout.connect(self.do_animation_step)
        self.t.start()

    def is_in_animation(self):
        """
        Returns true if an animation is currently running
        """
        return self.t != None and self.t.isActive()

    def do_animation_step(self):
        """
        Slot for the animation timer, updates the animation step once under the assumption that
        100 steps have to be added to the starting index for each second that has passed since
        the last call of self.start_animation() (i.e. sampling rate of 100hz)

        If the new animation step that should be displayed is larger than the index of the last
        datapoint that is available, the animation will be stopped.

        Emits the following signals:
        self.animation_step - once to indicate the updated animation state
        """
        sss = (time.time() - self.anim_start[0]) #seconds since start
        newi = self.anim_start[1] + int(round(sss * 30)) # sample rate is 100hz => 100 steps per second
        if newi < self.get_data_offset() + len(self) :
            self.i = newi
            self.animation_step.emit(self.i)
        else :
            self.t.stop()
            self.t = None
            self.animation_stopped.emit()

    def set_animation_step(self,i):
        """
        Manually sets the animation step to the given index. If an animation is currently running,
        it is stopped.

        Arguments:
        i -- the timestep to which the animation should be set

        Emits the following signals:
        self.animation_step -- once to indicate the updated animation state
        """
        n = len(self)
        self.stop_animation(reset=False)
        self.i = i if i >= 0 else max(n + i,0)
        self.animation_step.emit(self.i)

    def get_animation_step(self):
        return self.i

    def stop_animation(self,reset=False):
        """
        Stops the animation (if the timer is currently active)

        Keyword-Arguments:
        reset -- if True, the animation step will be reset to 0 (default: False)

        Emits the following signals:
        self.animation_step -- once if reset == True
        """
        if self.is_in_animation() :
            self.t.stop()
            self.animation_stopped.emit()

        if reset :
            self.i = 0
            self.animation_step.emit(0)

    def set_segments(self,segments):
        """
        Replaces segment data

        Arguments:
        segments -- list of values of the form (minx,maxx) where minx is the start of a
                    segment and maxx is the end of a segment

        Emits the following signals:
        self.new_segment_data -- once after all other operations have returned
        """
        self.next_sid = 0
        self.segments[self.segmentmode] = []
        for s in segments :
            if isinstance(s, SensorDataModelSegment) :
                self.segments[self.segmentmode].append(s)
            else :
                self.segments[self.segmentmode].append(SensorDataModelSegment(self.next_sid,s[0],s[1]))
            self.next_sid += 1
        self.new_segment_data.emit()

    def get_labels(self):
        """
        Returns the current segment data

        Returns: list of SensorDataModelSegment objects
        """
        return self.segments[self.segmentmode][:]

    def get_label(self, idx, sid):
        """
        Returns a single segment object

        Arguments:
        sid -- the segment id as obtained from SensorDataModelSegement.get_sid()

        Returns: the SensorDataModelSegment with the given sid or None if no such
                 object was found
        """
        for s in self.segments[idx] :
            if s.get_sid() == sid : return s
        return None

    def get_label_color(self,sid):
        """
        Returns the color that should be assigned to the segment with the given sid

        Arguments:
        sid -- the sid of the segment

        Returns: tuple (r,g,b) in range(255)
        """
        for s in self.segments[self.segmentmode] :
            if s.get_sid() == sid :
                name = s.get_name()
                if name in self.label_colors : return self.label_colors[name]
                else : return self.default_label_color

    def add_segment(self,start,end,name="NONE", idx=0):
        """
        Adds a new segment object to the model

        Arguments:
        start -- the starting point of the segment
        stop -- the end point of the segment

        Returns:
        the segment id of the new segment

        Emits the following signals:
        self.segment_added -- once
        """
        sid = self.next_sid
        self.next_sid += 1
        self.segments[idx].append(SensorDataModelSegment(idx,sid,start,end,name=name))
        self.segment_added.emit(idx, sid)
        return sid

    def remove_segment(self,idx, sid):
        """
        Removes a segment object from the model

        Arguments:
        sid -- the segment id as obtained from SensorDataModelSegement.get_sid()

        Emits the following signals:
        self.segment_removed -- once
        """
        s = self.get_segment(idx, sid)
        if s == None : return
        if self.get_label_mode() == 1 :
            self.attention_segments.remove(s)
        else :
            self.segments[self.segmentmode].remove(s)
        self.segment_removed.emit(idx, sid)

    def relabel_segment(self, idx, sid, label):
        """
        Assigns a different label to the segment.

        Arguments:
        sid   -- the segment id as obtained from SensorDataModelSegement.get_sid()
        label -- new name of the label
        Emits the following signals:
        self.segment_changed -- once if start != None or end != None

        """
        s = self.get_segment(idx,sid)
        if s is not None :
            s.set_name(label)
        self.segment_changed.emit(idx, sid)

    def save_segment(self,sid,filename):
        if filename == "" : return
        seg = self.get_segment(sid)
        seg = [int(x) for x in seg.get_bounds()]
        self.sensordata[seg[0]:seg[1]].write(filename)
    def get_segment(self,idx,sid):
        """
        Returns a single segment object

        Arguments:
        sid -- the segment id as obtained from SensorDataModelSegement.get_sid()

        Returns: the SensorDataModelSegment with the given sid or None if no such
                 object was found
        """
        for s in self.segments[idx] :
            if s.get_sid() == sid : return s
        return None
    def move_segment(self,idx,sid,start=None,end=None):
        """
        Moves a segment object to a new location

        Arguments:
        idx -- index
        sid -- the segment id as obtained from SensorDataModelSegement.get_sid()

        Keyword-Arguments:
        start -- the new starting point of the segment; if None, the old value will be used (default: None)
        stop -- the new end point of the segment; if None, the old value will be used (default: None)

        Emits the following signals:
        self.segment_changed -- once if start != None or end != None
        """
        s = self.get_label(idx,sid)
        if s == None : return
        if start != None : s.set_start(start)
        if end != None : s.set_end(end)
        if start != None or end != None :
            self.segment_changed.emit(idx,sid)

    def store_labels(self):
        """
        Closes the dataset.
        And stores the labels in h5 file.
        """
        if self.sensordata is None : return
        if self.sensordata.id :
            self.sensordata.close()
        try :
            h5_file = h5.File(self.sensorfname,'a')
            h5_file['data']['target'][:] = 0
            for seg in self.segments[self.segmentmode] :
                h5_file['data']['target'][seg.start:seg.end] = sepan.ID_CLASSES[seg.name]
        except Exception as e :
            print e
        finally:
            h5_file.close()

    def set_segment_name(self,idx,sid,name):
        """
            Set segment name.
            :Parameters:
                idx -- index
                sid -- segment id
                name -- name of the segment name
        """
        s = self.get_label(idx,sid)
        if s == None : return
        s.set_name(name)
        self.segment_changed.emit(idx, sid)
    def get_visible_yspan(self):
        vchans = self.get_visible_channels()
        if len(vchans) == 0 : return -1,1 #default values
        ymins = [c.get_min_y() for c in vchans]
        ymaxs = [c.get_max_y() for c in vchans]
        return min(ymins),max(ymaxs)

    def _maintain_ylims(self,data):
        if data is None : return

    def _check_ylim_update(self,channel,new_yvalue):
        if channel.get_max_y() < new_yvalue : channel.set_ylim(ymax=new_yvalue)
        if channel.get_min_y() > new_yvalue : channel.set_ylim(ymin=new_yvalue)
    def get_data_offset(self):
        return self.begin
    def get_data_size(self):
        return self.get_data_num_samples()

    def load_into_memory(self,lower,upper):
        self.begin = lower
        self.end = upper
        self.reset_channel_data()
        self.dataset_changed.emit()
        self._maintain_ylims(None) #reset ylim data

    def close(self):
        """
        Closes the data file.
        """
        if self.sensordata is not None :
            self.sensordata.close()
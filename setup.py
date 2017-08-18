from distutils.core import setup
from py2exe.build_exe import py2exe
from distutils.filelist import findall
import os, sys
import numpy
import matplotlib

import mmaat.ui
# We need to import the glob module to search for all files.
import glob
import mpl_toolkits
opts = {
    'py2exe': { "includes" : ["sip",  "PyQt4", "matplotlib.backends",  "matplotlib.backends.backend_qt4agg",
                              "cv2",
                              "h5py", "h5py.defs", "h5py.utils", "h5py._proxy", "h5py.h5ac",
                               "scipy","scipy.sparse.csgraph._validation", "scipy.special._ufuncs_cxx",
                              "scipy.linalg.cython_blas", "scipy.linalg.cython_lapack",
                               "matplotlib.figure","pylab", "numpy",
                               "scipy","scipy.sparse.csgraph._validation",
                               "matplotlib.backends.backend_tkagg", "mpl_toolkits.axes_grid1"


                               ],
                'excludes': ['_gtkagg', '_tkagg', '_agg2', '_cairo', '_cocoaagg',
                             '_fltkagg', '_gtk', '_gtkcairo', 'wx._core' ],
                'dll_excludes': ['libgdk-win32-2.0-0.dll',
                                 'libgobject-2.0-0.dll']
              }
       }

# Save matplotlib-data to mpl-data ( It is located in the matplotlib\mpl-data
# folder and the compiled programs will look for it in \mpl-data
# note: using matplotlib.get_mpldata_info

data_files = [(r'data/resources/icons', glob.glob('../data/resources/icons/*.*'))
                  ].extend(matplotlib.get_py2exe_datafiles())
build_exe_options = {"packages": ['mmaat', 'mmaat.ui', 'mmaat.ui.models',
                                  'mmaat.ui.widgets', 'mmaat.utils', 'mmaat.analysis'],
                     "excludes": ['_gtkagg', '_tkagg', '_agg2', '_cairo', '_cocoaagg',
                             '_fltkagg', '_gtk', '_gtkcairo', 'wx._core' ]}
setup(
    windows=[{"script":'mmaatt.py'}],
    options=opts,
    data_files=data_files,
    name='mmaatt',
    version='1.0',
    description='Sequential Pattern Analysis Toolkit',
    author='Markus Weber',
    author_email='markus.weber@dfki.de',
    packages=['mmaat', 'mmaat.ui', 'mmaat.ui.models',
              'mmaat.ui.widgets', 'mmaat.utils', 'mmaat.analysis']
)

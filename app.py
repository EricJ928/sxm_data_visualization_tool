"""
Created on 25-Feb-2022
@author: Junxiang (Eric) Jia
"""


import numpy as np
import os
import glob
import shutil
import sys

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5 import uic
from PyQt5.QtWidgets import QFileDialog
import pyqtgraph as pg

import sxmReader


class sxmViewerApp(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.file_dir = ''
        self.fnames = []
        self.findex = 0
        self.findex_max = 0
        self.log_moved = []
        self.ui = uic.loadUi('ui.ui', self)
        # self.resize(900, 600)
        self.setWindowTitle('SXM Viewer')

        fileType = ['.sxm', '.npy']
        colormap = ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges',
                    'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn',
                    'YlGn', 'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring', 'summer', 'autumn', 'winter',
                    'cool', 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper', 'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
                    'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic', 'flag', 'prism', 'ocean', 'gist_earth',
                    'terrain', 'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 'gist_rainbow', 'rainbow',
                    'jet', 'turbo', 'nipy_spectral', 'gist_ncar']

        self.comboBox_fileType.addItems(fileType)
        self.comboBox_colormap.addItems(colormap)

        self.set_colormap()
        # cmap = pg.colormap.getFromMatplotlib('viridis')
        # self.graphicsView.setColorMap(cmap)
        self.ui.openButton.clicked.connect(self.openFileNameDialog)
        self.previousButton.clicked.connect(self.previous_image)
        self.nextButton.clicked.connect(self.next_image)
        self.previousButton.setShortcut('a')
        self.nextButton.setShortcut('d')

        self.checkBox_fitPlane.stateChanged.connect(lambda: self.update_image(self.fnames[self.findex]))

        self.comboBox_fileType.activated[str].connect(self.get_fnames)
        self.comboBox_colormap.activated[str].connect(self.set_colormap)
        self.comboBox_fname.activated[str].connect(self.comboBox_fname_update)

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        self.file_dir = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        print(self.file_dir)
        os.chdir(self.file_dir)

        self.get_fnames()

    def get_fnames(self):
        self.fnames = []
        self.findex = 0
        self.findex_max = 0
        self.comboBox_fname.clear()

        ft = self.comboBox_fileType.currentText()
        self.fnames = glob.glob(f'*{ft}')
        self.findex_max = len(self.fnames)
        self.comboBox_fname.addItems(self.fnames)

        if self.findex_max == 0:
            self.label_errMsg.setText(f'Error: No {ft} file found!')
            self.lineEdit_findex.setText('0/0')
            return

        self.update_image(self.fnames[self.findex])

    def comboBox_fname_update(self):
        self.findex = self.comboBox_fname.currentIndex()
        self.update_image(self.fnames[self.findex])

    def update_image(self, fn):
        if self.comboBox_fileType.currentText() == '.npy':
            data = np.load(fn)
        elif self.comboBox_fileType.currentText() == '.sxm':
            data, pixels, real = self.read_sxm(fn)
            self.label_pixels.setText('Pixels: {}x{}'.format(pixels['x'], pixels['y']))
            self.label_size.setText('Size: {:.0f}x{:.0f} nm'.format(real['x'], real['y']))

        if self.checkBox_fitPlane.isChecked():
            data = self.subtract_2d_plane(data)
        data *= 1e9
        self.graphicsView.setImage(data.T)
        self.lineEdit_findex.setText('{}/{}'.format(self.findex+1, self.findex_max))
        self.label_errMsg.setText('No Error')

    def read_sxm(self, fn):
        load = sxmReader.NanonisSXM(fn)
        xx = load.retrieve_channel_data('Z')
        scan_dir = load.header['SCAN_DIR'][0][0]
        pixels = {'x': int(load.header['SCAN_PIXELS'][0][0]),
                  'y': int(load.header['SCAN_PIXELS'][0][1])}
        real = {'x': 1e9 * float(load.header['SCAN_RANGE'][0][0]),
                'y': 1e9 * float(load.header['SCAN_RANGE'][0][1])}
        if scan_dir == 'up':
            data = np.flip(xx, axis=0)
        else:
            data = xx
        return data, pixels, real

    def previous_image(self):
        if len(self.fnames) == 0 or self.findex == 0:
            return
        self.findex -= 1
        self.comboBox_fname.setCurrentText(self.fnames[self.findex])
        self.update_image(self.fnames[self.findex])

    def next_image(self):
        if len(self.fnames) == 0 or self.findex == self.findex_max:
            return
        self.findex += 1
        self.comboBox_fname.setCurrentText(self.fnames[self.findex])
        self.update_image(self.fnames[self.findex])

    def set_colormap(self):
        current_cm = self.comboBox_colormap.currentText()
        cmap = pg.colormap.getFromMatplotlib(current_cm)
        self.graphicsView.setColorMap(cmap)

    def subtract_2d_plane(self, img):
        m = img.shape[0]
        X1, X2 = np.mgrid[:m, :m]

        # Regression
        X = np.hstack((np.reshape(X1, (m*m, 1)), np.reshape(X2, (m*m, 1))))
        X = np.hstack((np.ones((m*m, 1)), X))

        YY = np.reshape(img, (m*m, 1))
        theta = np.dot(np.dot(np.linalg.pinv(np.dot(X.transpose(), X)), X.transpose()), YY)
        plane = np.reshape(np.dot(X, theta), (m, m))

        # Subtraction
        img_sub = img - plane

        return img_sub


if __name__ == '__main__':
    os.chdir(sys.path[0])
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = sxmViewerApp()
    mainWindow.show()
    sys.exit(app.exec_())

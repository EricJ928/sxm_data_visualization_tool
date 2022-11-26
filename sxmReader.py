import os
import numpy as np


class NanonisSXM():
    """
    Read all channels from Nanonis .sxm binary file and return requested data.

    Parameters:     img : rank2 numpy array with the same shape [0] and [1]
                        Input image.
    Return:         img_aug : rank3 numpy array
                        Data augmentation of 8 new images (mirror and/or rotate by 90/180/270 degrees).
    """

    def __init__(self, fname):
        self.fname = fname
        assert self.fname.endswith('.sxm')
        assert os.path.exists(self.fname)
        self.header = {}
        self.size = {}
        self.channels = []
        
        self._read_file()

    def _read_file(self):
        """
        Read in both both header and data in Nanonis .sxm binary file.
        """
        with open(self.fname, 'rb') as fs:
            header_ended = False
            line = ''
            key = ''
            while not header_ended:
                line = fs.readline()
                if line == b':SCANIT_END:':
                    header_ended = True
                else:
                    if line[:1] == b':':
                        key = line.split(b':')[1].decode('ascii')
                        self.header[key] = []
                    else:
                        if line: # remove empty lines
                            self.header[key].append(line.decode('ascii').split())
            self.size['pixels'] = {
                'x': int(self.header['SCAN_PIXELS'][0][0]),
                'y': int(self.header['SCAN_PIXELS'][0][1]),
            }
            self.size['real'] = {
                'x': float(self.header['SCAN_RANGE'][0][0]),
                'y': float(self.header['SCAN_RANGE'][0][1]),
            }
            
    def _return_channels(self):
        pass
import os
import struct
import numpy as np
import pandas as pd


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
        self.channels_name = []
        
        self._read_file()
        self._read_channel_names()

    def _read_file(self):
        """
        Read in both both header and data in Nanonis .sxm binary file.
        """
        with open(self.fname, 'rb') as fs:
            header_ended = False
            line = ''
            key = ''
            while not header_ended:
                line = fs.readline().rstrip()
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
            
    def _read_channel_names(self):
        self.channels = pd.DataFrame(self.header['DATA_INFO'][1:], 
                  columns=self.header['DATA_INFO'][0])
        self.channels_name = self.channels['Name'].to_list()
    
    def list_channels(self):
        print('Available channels:')
        print(self.channels_name)
    
    def retrieve_channel_data(self, channel_name, direction='forward'):
        """Function for retrieving a specific channel data.

        Args:
            channel_name (str): Channel name
            direction (str, optional): Scan direction. Defaults to 'forward'.

        Returns:
            str: Retrieved data.
        """
        channel_pos = 0
        df = self.channels
        for i in range(df.shape[0]):
            if df['Name'][i] == channel_name:
                if df['Direction'][i] == 'both' and direction == 'backward':
                    channel_pos += 1
                if df['Direction'][i] == 'both' or df['Direction'][i] == direction:
                    break
                return None
            elif df['Direction'][i] == 'both':
                channel_pos += 2
            else:
                channel_pos += 1
        data_per_channel = self.size['pixels']['x'] * self.size['pixels']['y']
        
        fhandle = open(self.fname, 'rb')
        read_all = fhandle.read()
        offset = read_all.find(b'\x1A\x04')
        fhandle.seek(offset+2+channel_pos*data_per_channel*4)
        
        data = struct.unpack('<>'['MSBFIRST'==self.header['SCANIT_TYPE'][0][1]]+str(data_per_channel)+{'FLOAT':'f','INT':'i','UINT':'I','DOUBLE':'d'}[self.header['SCANIT_TYPE'][0][0]], 
                             fhandle.read(4*data_per_channel))
        data = np.array(data).reshape((self.size['pixels']['y'], self.size['pixels']['x']))
        return data
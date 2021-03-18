
from threading import Timer
import requests
import os

from datetime import datetime, timedelta


class WheaterConditions(object):

    def __init__(self, interval):
        self._timer     = None
        self.interval   = interval
        self.is_running = False
        
        # Coordinates limits
        self.north = -8.5
        self.south = -9.5
        self.est = -34
        self.weast = -36.5

        # 3 days time step
        self.time_step = timedelta(days = 3)

    def get_currents(self, start_time, end_time, filename):
        # http://ncss.hycom.org/thredds/ncss/GLBy0.08/latest?var=water_u&var=water_v&north=-8.5&west=-36.5&east=-34&south=-9.5&disableProjSubset=on&horizStride=1&time_start=2021-03-17T12%3A00%3A00Z&time_end=2021-03-20T00%3A00%3A00Z&timeStride=1&vertCoord=0.0&accept=netcdf4
        # Building url string
        url = 'http://ncss.hycom.org/thredds/ncss/GLBy0.08/latest?var=water_u&var=water_v&'
        url += 'north=' + self.north + '&'
        url += 'west=' + self.west + '&'
        url += 'east=' + self.east + '&'
        url += 'south=' + self.south + '&'
        url += 'disableProjSubset=on&horizStride=1&'
        url += 'time_start=' + start_time.year + '-' + start_time.month + '-' + start_time.day
        url += 'T' + start_time.hour + '%3A' + start_time.minute + '%3A' + start_time.second + 'Z&'
        url += 'time_end=' + end_time.year + '-' + end_time.month + '-' + end_time.day
        url += 'T' + end_time.hour + '%3A' + end_time.minute + '%3A' + end_time.second + 'Z&'
        url += 'timeStride=1&vertCoord=0.0&accept=netcdf4'

        # making request
        r = requests.get(url, allow_redirects=True)

        # Save file
        if os.path.exists(filename):
            os.remove(filename)

        with open(filename, 'wb') as currentsFile:
            currentsFile.write(r.content)

    def _run(self):
        current_time = datetime.now()
        end_time = current_time + self.time_step

        print('Getting currents wheater data')
        self.get_currents(current_time, end_time, 'assets/currents.nc')

        print('Getting wind wheater data')

        self.is_running = False
        self.start()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
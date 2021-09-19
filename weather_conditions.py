
from threading import Timer
import requests
import os

from datetime import datetime, timedelta


class WeatherConditions(object):

    def __init__(self, interval, north=-8.5, south=-11, east=-34, west=-36.5):
        self._timer     = None
        self.interval   = interval
        self.is_running = False
        
        # Coordinates limits
        self.north = north
        self.south = south
        self.east = east
        self.west = west

        # considering run step interval and 2 more days
        self.time_step = timedelta(seconds = interval) + timedelta(days = 2) 

        # First run
        current_time = datetime.now() - timedelta(days = 1)
        end_time = current_time + self.time_step

        print('Getting currents weather data')
        self.get_currents(current_time, end_time, 'assets/currents.nc')

        print('Getting wind weather data')
        self.get_wind(current_time, end_time, 'assets/wind.nc')

    def get_currents(self, start_time, end_time, filename):
        # http://ncss.hycom.org/thredds/ncss/GLBy0.08/latest?var=water_u&var=water_v&north=-8.5&west=-36.5&east=-34&south=-9.5&disableProjSubset=on&horizStride=1&time_start=2021-03-17T12%3A00%3A00Z&time_end=2021-03-20T00%3A00%3A00Z&timeStride=1&vertCoord=0.0&accept=netcdf4
        # Building url string
        url = 'http://ncss.hycom.org/thredds/ncss/GLBy0.08/latest?var=water_u&var=water_v&'
        url += 'north=' + str(self.north) + '&'
        url += 'west=' + str(self.west) + '&'
        url += 'east=' + str(self.east) + '&'
        url += 'south=' + str(self.south) + '&'
        url += 'disableProjSubset=on&horizStride=1&'
        url += 'time_start=' + str(start_time.year) + '-' + str(start_time.month) + '-' + str(start_time.day)
        url += 'T' + str(start_time.hour) + '%3A' + str(start_time.minute) + '%3A' + str(start_time.second) + 'Z&'
        url += 'time_end=' + str(end_time.year) + '-' + str(end_time.month) + '-' + str(end_time.day)
        url += 'T' + str(end_time.hour) + '%3A' + str(end_time.minute) + '%3A' + str(end_time.second) + 'Z&'
        url += 'timeStride=1&vertCoord=0.0&accept=netcdf'

        print(url)

        # making request
        r = requests.get(url, allow_redirects=True)

        # Save file
        if os.path.exists(filename):
            os.remove(filename)

        with open(filename, 'wb') as currentsFile:
            currentsFile.write(r.content)
            currentsFile.close()
        
    def get_wind(self, start_time, end_time, filename):
        url = 'https://thredds.ucar.edu/thredds/ncss/grib/NCEP/GFS/Global_0p25deg/Best?var=u-component_of_wind_height_above_ground&var=v-component_of_wind_height_above_ground&'
        url += 'north=' + str(self.north) + '&'
        url += 'west=' + str(self.west) + '&'
        url += 'east=' + str(self.east) + '&'
        url += 'south=' + str(self.south) + '&'
        url += 'disableProjSubset=on&horizStride=1&'
        url += 'time_start=' + str(start_time.year) + '-' + str(start_time.month) + '-' + str(start_time.day)
        url += 'T' + str(start_time.hour) + '%3A' + str(start_time.minute) + '%3A' + str(start_time.second) + 'Z&'
        url += 'time_end=' + str(end_time.year) + '-' + str(end_time.month) + '-' + str(end_time.day)
        url += 'T' + str(end_time.hour) + '%3A' + str(end_time.minute) + '%3A' + str(end_time.second) + 'Z&'
        url += 'timeStride=1&vertCoord=10.0&accept=netcdf'

        print(url)

        # making request
        r = requests.get(url, allow_redirects=True)

        # Save file
        if os.path.exists(filename):
            os.remove(filename)

        with open(filename, 'wb') as windFile:
            windFile.write(r.content)
            windFile.close()

    def _run(self):
        current_time = datetime.now() - timedelta(days = 1)
        end_time = current_time + self.time_step

        print('Getting currents weather data')
        self.get_currents(current_time, end_time, 'assets/currents.nc')

        print('Getting wind weather data')
        self.get_wind(current_time, end_time, 'assets/wind.nc')

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
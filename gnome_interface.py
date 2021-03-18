import os
import sys

import shutil
from datetime import datetime, timedelta

import numpy as np

from gnome import scripting
from gnome.basic_types import datetime_value_2d
from gnome.utilities.remote_data import get_datafile

from gnome.model import Model

from gnome.maps import MapFromBNA
from gnome.environment import Wind, Tide
from gnome.spill import (point_line_release_spill,
                         InitElemsFromFile,
                         Spill)

from gnome.spill.release import release_from_splot_data


from gnome.spill_container import SpillContainer

from gnome.persist import load

from gnome.spill.substance import GnomeOil

from gnome.spill.initializers import plume_initializers

from gnome.utilities.distributions import UniformDistribution

from gnome.movers import RandomMover, GridCurrentMover,  GridWindMover

from gnome.outputters import Renderer
from gnome.outputters import NetCDFOutput

from gnome import utilities

import netCDF4 as nc

class GnomeInterface:
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        self.mapfile = get_datafile(os.path.join(base_dir, './assets/alagoas-coast.bna'))
        self.gnome_map = MapFromBNA(self.mapfile, refloat_halflife=6)
        
        oil_name = 'GENERIC MEDIUM CRUDE'
        wd = UniformDistribution(low=.0002, high=.0002)
        self.subs = GnomeOil(oil_name,initializers=plume_initializers(distribution=wd))
        
        self.new_oil = []

        
    def step(self, start_time):
        print('Computing new gnome step')
        base_dir = os.path.dirname(__file__)

        model = Model(start_time=start_time, 
            duration=timedelta(minutes=5), 
            time_step=timedelta(minutes=5),
            map=self.gnome_map,
            uncertain=False,
            cache_enabled=False)
        
        # Add reported oil (at current time)
        if len(self.new_oil) > 0:
            for oil in self.new_oil:
                release = SpartialRelease(release_time=start_time, start_position=oil)
                model.spills += Spill(release=release, substance=self.subs)
            self.new_oil = []

        # Add already present oil particles
        try:
            f = open('./assets/step.txt')
            f.close()
            release = release_from_splot_data(start_time,
                                            './assets/step.txt')
            model.spills += Spill(release=release, substance=self.subs)        
        except IOError:
            pass

        model.movers += RandomMover(diffusion_coef=10000)

        #curr_file = get_datafile(os.path.join(base_dir, './assets/corrente15a28de09.nc'))
        curr_file = get_datafile(os.path.join(base_dir, './assets/currents.nc'))
        model.movers += GridCurrentMover(curr_file, num_method='Euler')

        #wind_file = get_datafile(os.path.join(base_dir, './assets/vento15a28de09.nc'))
        wind_file = get_datafile(os.path.join(base_dir, './assets/wind.nc'))
        w_mover = GridWindMover(wind_file)
        w_mover.uncertain_speed_scale = 1
        w_mover.wind_scale = 2
        model.movers += w_mover

        renderer = Renderer(self.mapfile, os.path.join(base_dir, 'images'), image_size=(900, 600),
            output_timestep=timedelta(minutes=5),
            draw_ontop='forecast')
        
        renderer.viewport = ((-35.5, -9.5), (-34, -8.5)) #1/4 N alagoas
        model.outputters += renderer

        netcdf_file = os.path.join(base_dir, './assets/step.nc')
        scripting.remove_netcdf(netcdf_file)
        model.outputters += NetCDFOutput(netcdf_file, which_data='standard', surface_conc='kde')

        for step in model:
            pass
            #print "step: %.4i -- memuse: %fMB" % (step['step_num'], utilities.get_mem_use())
        #model.full_run()
        print('Computed new gnome step')

    def get_particles(self):
        base_dir = os.path.dirname(__file__)
        netcdf_file = os.path.join(base_dir, './assets/step.nc')
        # read nc and prepare particles lat lon
        data = nc.Dataset(netcdf_file)
        lon = np.array(data['longitude'][:])
        lat = np.array(data['latitude'][:])
        status_codes = np.array(data['status_codes'][:]) #'0: not_released, 2: in_water, 3: on_land, 7: off_maps, 10: evaporated, 12: to_be_removed, 32: on_tideflat,'
        pc = np.array(data['particle_count'][:]) #'1-number of particles in a given timestep'

        lon = lon[len(lon) - pc[-1]:len(lon)]
        lat = lat[len(lat) - pc[-1]:len(lat)]
        status_codes = status_codes[len(status_codes) - pc[-1]:len(status_codes)]

        lon = lon[np.where(status_codes == 2)]
        lat = lat[np.where(status_codes == 2)]

        return lon, lat
    
    def add_oil(self, lon, lat):
        oil = np.array([[lon[i], lat[i]] for i in range(len(lon))])
        self.new_oil.append(oil)

    def save_particles(self, lon, lat):
        particles = np.array([[lon[i], lat[i], 1] for i in range(len(lon))])
        np.savetxt('./assets/step.txt', particles)



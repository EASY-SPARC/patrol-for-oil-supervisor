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

class GnomeInterface:
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        self.mapfile = get_datafile(os.path.join(base_dir, './assets/alagoas-coast.bna'))
        self.gnome_map = MapFromBNA(self.mapfile, refloat_halflife=6)
        
        oil_name = 'GENERIC MEDIUM CRUDE'
        wd = UniformDistribution(low=.0002, high=.0002)
        self.subs = GnomeOil(oil_name,initializers=plume_initializers(distribution=wd))

        
    def step(self, start_time, new_particles):
        base_dir = os.path.dirname(__file__)

        model = Model(start_time=start_time, 
            duration=timedelta(minutes=5), 
            time_step=timedelta(minutes=5),
            map=self.gnome_map,
            uncertain=False,
            cache_enabled=False)
        

        if (new_particles):
            release = release_from_splot_data(start_time, './assets/contiguous.txt')
            model.spills += Spill(release=release, substance=self.subs)

        try:
            f = open('./assets/step.txt')
            f.close()
            release2 = release_from_splot_data(start_time,
                                            './assets/step.txt')
            model.spills += Spill(release=release2, substance=self.subs)        
        except IOError:
            pass

        model.movers += RandomMover(diffusion_coef=10000)

        curr_file = get_datafile(os.path.join(base_dir, './assets/corrente15a28de09.nc'))
        model.movers += GridCurrentMover(curr_file, num_method='Euler')

        wind_file = get_datafile(os.path.join(base_dir, './assets/vento15a28de09.nc'))
        w_mover = GridWindMover(wind_file)
        w_mover.uncertain_speed_scale = 1
        w_mover.wind_scale = 2
        model.movers += w_mover

        renderer = Renderer(self.mapfile, os.path.join(base_dir, 'images'), image_size=(900, 600),
            output_timestep=timedelta(minutes=5),
            draw_ontop='forecast')
        
        renderer.viewport = ((-35.5, -9.5), (-34, -8.5)) #1/4 N alagoas
        model.outputters += renderer

        netcdf_file = os.path.join(base_dir, 'step.nc')
        scripting.remove_netcdf(netcdf_file)
        model.outputters += NetCDFOutput(netcdf_file, which_data='standard', surface_conc='kde')

        for step in model:
            print "step: %.4i -- memuse: %fMB" % (step['step_num'], utilities.get_mem_use())

        return [0, 0]

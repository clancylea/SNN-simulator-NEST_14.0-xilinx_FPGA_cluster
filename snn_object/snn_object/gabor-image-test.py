#!/bin/ipython

# ---LICENSE-BEGIN - DO NOT CHANGE OR MOVE THIS HEADER
# This file is part of the Neurorobotics Platform software
# Copyright (C) 2014,2015,2016,2017 Human Brain Project
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# ---LICENSE-END

import numpy as np
import cv2
import sys
import pyNN.nest as sim
import pathlib as plb
import time
import argparse as ap

import common as cm
import network as nw
import visualization as vis
import time

parser = ap.ArgumentParser(description='SNN feature detector')
parser.add_argument('--refrac-c1', type=float, default=.1, metavar='MS',
                    help='The refractory period of neurons in the C1 layer in ms')
parser.add_argument('--refrac-s1', type=float, default=.1, metavar='MS',
                    help='The refractory period of neurons in the S1 layer in ms')
parser.add_argument('--refrac-s2', type=float, default=.1, metavar='MS',
                    help='The refractory period of neurons in the S2 layer in ms')
parser.add_argument('--scales', default=[1.0, 0.71, 0.5, 0.35, 0.25],
                    nargs='+', type=float,
                    help='A list of image scales for which to create layers.\
                    Defaults to [1, 0.71, 0.5, 0.35, 0.25]')
parser.add_argument('--plot-c1-spikes', action='store_true',
                    help='Plot the spike trains of the C1 layers')
parser.add_argument('--plot-s2-spikes', action='store_true',
                    help='Plot the spike trains of the S2 layers')
parser.add_argument('--sim-time', default=100, type=float, help='Simulation time')
parser.add_argument('--target-name', type=str,
                    help='The name of the already edge-filtered image to be\
                    recognized')
args = parser.parse_args()

sim.setup(threads=4)

layer_collection = {}

target_img = cv2.imread(args.target_name, cv2.CV_8UC1)
print('Create S1 layers')
t1 = time.clock()
layer_collection['S1'] =\
    nw.create_gabor_input_layers_for_scales(target_img, args.scales)
nw.create_cross_layer_inhibition(layer_collection['S1'])
print('S1 layer creation took {} s'.format(time.clock() - t1))

print('Create C1 layers')
t1 = time.clock()
layer_collection['C1'] = nw.create_C1_layers(layer_collection['S1'],
                                             args.refrac_c1)
nw.create_local_inhibition(layer_collection['C1'])
print('C1 creation took {} s'.format(time.clock() - t1))

print('Creating S2 layers')
t1 = time.clock()
layer_collection['S2'] = nw.create_S2_layers(layer_collection['C1'], args)
print('S2 creation took {} s'.format(time.clock() - t1))

for layer_name in ['C1']:
    if layer_name in layer_collection:
        for layers in layer_collection[layer_name].values():
            for layer in layers:
                layer.population.record('spikes')
for layer in layer_collection['S2'].values():
    layer.population.record(['spikes', 'v'])

print('========= Start simulation =========')
start_time = time.clock()
sim.run(args.sim_time)
end_time = time.clock()
print('========= Stop  simulation =========')
print('Simulation took', end_time - start_time, 's')

t1 = time.clock()
if args.plot_c1_spikes:
    print('Plotting C1 spikes')
    vis.plot_C1_spikes(layer_collection['C1'], plb.Path(args.target_name).stem)
    print('Plotting spiketrains took {} s'.format(time.clock() - t1))

if args.plot_s2_spikes:
    print('Plotting S2 spikes')
    vis.plot_S2_spikes(layer_collection['S2'], plb.Path(args.target_name).stem)
    print('Plotting spiketrains took {} s'.format(time.clock() - t1))

sim.end()

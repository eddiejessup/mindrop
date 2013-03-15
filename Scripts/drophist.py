#! /usr/bin/python3

import os
import sys
import glob
import yaml
import matplotlib.pyplot as pp
import numpy as np
import utils

n_bins = 15

if sys.argv[-1] == '-h':
    print('l_rot vf acc acc_err t')
    sys.argv = sys.argv[:-1]

for dirname in sys.argv[1:]:
    fname = sorted(glob.glob('%s/r/*.npy' % dirname))[-1]

    yaml_args = yaml.safe_load(open('%s/params.yaml' % dirname, 'r'))
    n = int(yaml_args['particle_args']['n'])
    R_drop = float(yaml_args['obstruction_args']['droplet_args']['R'])
    l_rot = yaml_args['particle_args']['motile_args']['rot_diff_args']['l_rot_0']
    vf = float(yaml_args['particle_args']['collide_args']['vf'])

    r = utils.vector_mag(np.load(fname))
    f, R = np.histogram(r, bins=n_bins, range=[0.0, R_drop])
    rho = f / (R[1:] ** 2 - R[:-1] ** 2)

    bulk_rho = n / (np.pi * R_drop ** 2)
    acc = rho[-1] / bulk_rho
    print('%f %f %f %s' % (l_rot, vf, acc, os.path.splitext(os.path.basename(fname))[0]))

#    pp.bar(R[:-1], rho, width=(R[1]-R[0]))
#    pp.xlim([0.0, 1.0])
#    pp.show()
#! /usr/bin/python

import argparse
import os
import glob
import yaml
import numpy as np
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as pp
import utils

mpl.rc('font', family='serif', serif='STIXGeneral')

def parse_dir(dirname, samples=1):
    yaml_args = yaml.safe_load(open('%s/params.yaml' % dirname, 'r'))
    dim = yaml_args['dim']
    R_drop = yaml_args['obstruction_args']['droplet_args']['R']
    try:
        collide_args = yaml_args['particle_args']['collide_args']
    except KeyError:
        r_c = 0.0
    else:
        r_c = yaml_args['particle_args']['collide_args']['R']
    R_drop += r_c/2.0
    r_fnames = sorted(glob.glob('%s/r/*.npy' % dirname))

    # minus 1 is because we don't want to use the initial positions if we have multiple measurements
    if len(r_fnames) > 1: available = len(r_fnames) - 1
    # if we only have one measurement we can't do otherwise
    else: available = len(r_fnames)
    # zero means use all available samples
    if samples == 0: samples = available
    if available < samples:
        raise Exception('Requested %i samples but only have %i available for %s' % (samples, available, dirname))

    rs = []
    for i in range(samples):
        r = np.load(r_fnames[-i])

        if r.ndim == 2:
            r_diff = utils.vector_mag(r[:, np.newaxis, :] - r[np.newaxis, :, :])
            sep_min = np.min(r_diff[r_diff > 0.0])
            if sep_min < 1.9 * r_c:
                raise Exception('Collision algorithm not working %f %f' % (sep_min, 2.0 * r_c))
            r = utils.vector_mag(r)

        rs.append(r)
    rs = np.array(rs)
    vf = (rs.shape[1] * utils.sphere_volume(r_c, dim)) / utils.sphere_volume(R_drop, dim)
    return rs, dim, R_drop, vf

def histo(rs, dim, R_drop, norm=False, bins=100):
    fs = []
    for r in rs:
        f_cur, R_edges = np.histogram(r, bins=bins, range=[0.0, 1.1 * R_drop])
        fs.append(f_cur)
    fs = np.array(fs)
    f = np.mean(fs, axis=0)
    f_err = np.std(fs, axis=0) / np.sqrt(fs.shape[0])

    V_edges = utils.sphere_volume(R_edges, dim)
    dV = V_edges[1:] - V_edges[:-1]
    rho = f / dV
    rho_err = f_err / dV
    R = 0.5 * (R_edges[:-1] + R_edges[1:])

    if norm:
        dR = R_edges[1] - R_edges[0]
        rho_area = rho.sum() * dR
        rho /= rho_area
        rho_err /= rho_area
    else:
        rho_0 = rs.shape[1] / utils.sphere_volume(R_drop, dim)
        rho /= rho_0
        rho_err /= rho_0
    return R, rho, rho_err

def mean_set(sets, set_params):
    set_mean = np.zeros_like(sets[0])
    set_mean[:2] = sets[:, :2].mean(axis=0)
    set_mean[2] = np.std(sets[:, 1], axis=0) / np.sqrt(len(sets))
    params_mean = set_params.mean(axis=0)
    return set_mean[np.newaxis, ...], params_mean[np.newaxis, ...]

def collate(dirs, bins=100, norm=False, samples=1):
    sets, params = [], []
    for dirname in dirs:
        rs, dim, R_drop, vf = parse_dir(dirname, samples)
        R, rho, rho_err = histo(rs, dim, R_drop, norm, bins)
        sets.append((R, rho, rho_err))
        params.append((R_drop, vf, rs.shape[1], dirname))
    return np.array(sets), np.array(params)

def set_plot(sets, params, norm, errorbars=True):
    fig = pp.figure()
    ax = fig.gca()
    inds_sort = np.lexsort(params.T)
    sets = sets[inds_sort]
    params = params[inds_sort]

    dupes = False
    for i in range(len(params)):
        for i1 in range(i + 1, len(params)):
            if np.all(params[i, :-1] == params[i1, :-1]):
                dupes = True
                break

    for set, param in zip(sets, params):
        R, rho, rho_err = set
        R_drop, vf, n, dirname = param
        R_drop, vf, n = float(R_drop), float(vf), int(n)
        label = r'%g$\mu\mathrm{m}$, %.2g%% n=%g' % (R_drop, 100.0 * vf, n)
        if dupes: label += r' dir: %s' % dirname
        if errorbars:
            ax.errorbar(R / R_drop, rho, yerr=rho_err, label=label, marker=None, lw=3)
        else:
            ax.plot(R / R_drop, rho, label=label, lw=3)

    leg = ax.legend(loc='upper left', fontsize=16)
    leg.set_title(r'Droplet radius, Volume fraction', prop={'size': 18})
    ax.set_xlim([0.0, (R / R_drop).max()])
    ax.set_ylim([0.0, None])
    ax.set_xlabel(r'$r / \mathrm{R}$', fontsize=20)
    if norm: ax.set_ylabel(r'$\frac{\rho(r)}{\, \sum{\rho(r)}}$', fontsize=24)
    else: ax.set_ylabel(r'$\rho(r) \, / \, \rho_0$', fontsize=20)
    pp.show()

parser = argparse.ArgumentParser(description='Analyse droplet distributions')
parser.add_argument('dirs', nargs='*',
    help='Directories')
parser.add_argument('-b', '--bins', type=int, default=30,
    help='Number of bins to use')
parser.add_argument('-n', '--norm', default=False, action='store_true',
    help='Whether to normalise plots to have the same area')
parser.add_argument('-m', '--mean', default=False, action='store_true',
    help='Whether to take the mean of all data sets')
parser.add_argument('-s', '--samples', type=int, default=1,
    help='Number of samples to use to generate distribution, 0 for maximum')
parser.add_argument('--noerr', default=False, action='store_true',
    help='Whether to hide errorbars')

args = parser.parse_args()
if args.dirs == []: args.dirs = os.listdir(os.curdir)
args.dirs = [f for f in args.dirs if os.path.isdir(f)]
sets, params = collate(args.dirs, args.bins, args.norm, args.samples)
if args.mean: sets, params = mean_set(sets, params)
set_plot(sets, params, args.norm, not args.noerr)
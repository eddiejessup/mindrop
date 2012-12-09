'''
Created on 13 Jan 2012

@author: s1152258
'''

import matplotlib, matplotlib.pyplot as P
import utils
import _clusters
from params import *

class Box_analyser():
    def __init__(self, box, datdir='../dat/', 
                 plot_flag=False, plot_type='v', plot_save_flag=False, 
                 plot_every=1, plot_start_time=0.0, 
                 ratio_flag=False, ratio_every=1,
                 clusters_flag=False, clusters_every=1, clusters_R_cutoff=1.0, 
                 state_flag=False, state_every=1):
        if datdir[-1] != '/': datdir += '/'
        self.datdir = datdir

        # Ratio
        self.ratio_flag = ratio_flag
        if self.ratio_flag:
            if box.walls.alg not in ['trap', 'traps']:
                self.ratio_flag = False
            else:
                self.ratio_every = ratio_every
                f_ratio = open(self.datdir + 'ratio.dat', 'w')
                f_ratio.close()

        # Clusters
        self.clusters_flag = clusters_flag
        if self.clusters_flag:
            if box.walls.alg != 'maze': 
                self.clusters_flag = False
            else:
                self.clusters_every = clusters_every
                self.clusters_R_cutoff = clusters_R_cutoff
                f_clusters = open(self.datdir + 'clusters.dat', 'w')
                f_clusters.write('# r_cut: %f\n' % self.clusters_R_cutoff)
                f_clusters.write('time n_clusters\n')
                f_clusters.close()

        # State
        self.state_flag = state_flag
        self.state_every = state_every
        self.state_params()

        # Plotting
        self.plot_save_flag = plot_save_flag
        self.plot_every = plot_every
        self.plot_start_time = plot_start_time
        self.plot_flag = plot_flag
        self.plot_type = plot_type
        if self.plot_flag:
            if self.plot_type not in ['f', 'c', 'v']:
                raise Exception('Invalid plot type')
            self.plot_type = plot_type
            L_half = box.walls.L / 2.0
            self.extent = [-L_half, +L_half, 
                           -L_half, +L_half]
            self.fig = P.figure(1, figsize=(10, 6))
            if not self.plot_save_flag:
                P.ion()
                P.show()

    def plot_update(self, box, t, iter_count):
        if self.plot_flag:
            self.ax = self.fig.add_subplot(1, 1, 1)

            if self.plot_type == 'w': overlay = box.walls.a
            elif self.plot_type == 'f': overlay = box.f.a
            elif self.plot_type == 'c': overlay = box.c.a

            if box.walls.dim == 1:
                i = np.arange(box.walls.M)
                r = box.walls.i_to_r(i)
                self.ax.plot(r, overlay)
                self.ax.hist(box.motiles.r[:, 0], bins=200)

            elif box.walls.dim == 2:
                self.ax.imshow(box.walls.a.T, cmap=matplotlib.cm.gray,
                               interpolation='nearest',
                               extent=self.extent, origin='lower')
                o = self.ax.imshow(overlay.T, cmap=matplotlib.cm.summer,
                                   interpolation='nearest', extent=self.extent, 
                                   origin='lower', alpha=0.8)
                P.colorbar(o)

                v = box.motiles.v.copy()
                utils.vector_unitise_safer(v)
                self.ax.quiver(box.motiles.r[:, 0], box.motiles.r[:, 1], 
                               v[:, 0], v[:, 1], 
                               angles='xy', pivot='start')

            else: raise Exception('Box plotting not implemented in >2d')

        if self.plot_save_flag:
            name = iter_count // self.plot_every
            P.savefig(self.datdir + 'img/%05i_t=%07.2f.png' % (name, t), dpi=100)

        self.fig.canvas.draw()
        self.fig.clf()

    def ratio_update(self, box, t):
        assert box.walls.alg in ['trap', 'traps'], \
            'Ratio data only meaningful for trap-like walls'

        motiles_i = box.walls.r_to_i(box.motiles.r)
        w_half = box.walls.w_half

        n_trap = n_nontrap = 0
        for i_x, i_y in motiles_i:
            trappy = False
            for mid_x, mid_y in box.walls.traps_i:    
                if ((mid_x - w_half < i_x < mid_x + w_half) and 
                    (mid_y - w_half < i_y < mid_y + w_half)):
                    trappy = True
                    break
            if trappy: n_trap += 1
            else: n_nontrap += 1

        assert n_trap + n_nontrap == box.motiles.N, \
            'Ratio calculation not counted all motiles'

        d_trap = float(n_trap) / box.walls.A_traps_i
        d_nontrap = float(n_nontrap) / (box.walls.A_free_i - 
                                        box.walls.A_traps_i)
        ratio = d_trap / d_nontrap

        f_ratio = open(self.datdir + 'ratio.dat', 'a')
        f_ratio.write('%10f %10f\n' % (t, ratio))
        f_ratio.close()

    def clusters_update(self, box, t):
        n_clusters = _clusters.number_of_clusters_calc(box.motiles.r, 
                                                       self.clusters_R_cutoff, 
                                                       box.walls.L)
        f_clusters = open(self.datdir + 'clusters.dat', 'a')
        f_clusters.write('%10f %10f\n' % (t, n_clusters))
        f_clusters.close()

    def state_params(self):
        f = open(self.datdir + 'params.dat', 'w')
        f.write('GENERAL: \n')
        f.write('DIM: %g\n' % DIM)
        f.write('DELTA_t: %g\n' % DELTA_t)

        f.write('\nMOTILES: \n')
        f.write('NUM_MOTILES: %i\n' % NUM_MOTILES)
        f.write('v_BASE: %g\n' % v_BASE)
        f.write('COLLIDE_FLAG: %i\n' % COLLIDE_FLAG)
        if COLLIDE_FLAG:
            f.write('COLLIDE_R: %g\n' % COLLIDE_R)
        f.write('QUORUM_FLAG: %i\n' % QUORUM_FLAG)
        if QUORUM_FLAG:
            f.write('QUORUM_R: %g\n' % QUORUM_R)
            f.write('QUORUM_SENSE: %g\n' % QUORUM_SENSE)
        if DIM > 1:
            f.write('BC_ALG: %s\n' % WALL_HANDLE_ALG)
        f.write('v_ALG: %s\n' % v_ALG)
        if v_ALG == 't':
            f.write('p_BASE: %g\n' % p_BASE)
            f.write('p_ALG: %s\n' % p_ALG)
            if p_ALG == 'g':
                f.write('RAT_GRAD_SENSE: %g\n' % RAT_GRAD_SENSE)
            elif p_ALG == 'm':
                f.write('RAT_MEM_t_MAX: %g\n' % RAT_MEM_t_MAX)
                f.write('RAT_MEM_SENSE: %g\n' % RAT_MEM_SENSE)
        elif v_ALG == 'v':
            f.write('VICSEK_R: %g\n' % VICSEK_R)
            f.write('VICSEK_SENSE: %g\n' % VICSEK_SENSE)
            f.write('VICSEK_ETA: %g\n' % VICSEK_ETA)

        f.write('\nFIELD: \n')
        f.write('L: %g\n' % L)
        f.write('LATTICE_SIZE: %i\n' % LATTICE_SIZE)
        f.write('f_0: %g\n' % f_0)
        f.write('D_c: %g\n' % D_c)
        f.write('c_SOURCE_RATE: %g\n' % c_SOURCE_RATE)
        f.write('c_SINK_RATE: %g\n' % c_SINK_RATE)
        f.write('f_PDE_FLAG: %i\n' % f_PDE_FLAG)
        if f_PDE_FLAG:
            f.write('D_f: %g\n' % D_f)
            f.write('f_SINK_RATE: %g\n' % f_SINK_RATE)

        if DIM > 1:
            f.write('\nWALLS: \n')
            f.write('WALL_ALG: %s\n' % WALL_ALG)
            if WALL_ALG in ['trap', 'traps']:
                f.write('TRAP_LENGTH: %g\n' % TRAP_LENGTH)
                f.write('TRAP_SLIT_LENGTH: %g\n' % TRAP_SLIT_LENGTH)
            elif WALL_ALG == 'maze':
                f.write('MAZE_SIZE: %i\n' % MAZE_SIZE)
                f.write('MAZE_SEED: %i\n' % MAZE_SEED)            
        f.close()

    def state_update(self, box, t, iter_count):
        name = iter_count // self.state_every
        fname = self.datdir + ('state/%06i_t=%07.1f.npz' % (name, t))
        np.savez(fname, t=np.array([t]),  
                 r=box.motiles.r, v=box.motiles.v, f=box.f.a, c=box.c.a)

    def update(self, box, t, iter_count):
        if (self.ratio_flag) and (iter_count % self.ratio_every == 0):
            self.ratio_update(box, t)
        if (self.clusters_flag) and (iter_count % self.clusters_every == 0):
            self.clusters_update(box, t)
        if (self.state_flag) and (iter_count % self.state_every == 0):
            self.state_update(box, t, iter_count)
        if ((self.plot_flag) and (iter_count % self.plot_every == 0) and 
            (t > self.plot_start_time)):
            self.plot_update(box, t, iter_count)

    def final(self):
        if self.ratio_flag: self.f_ratio.close()
        if self.clusters_flag: self.f_clusters.close()
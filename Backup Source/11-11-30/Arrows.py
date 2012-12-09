'''
Created on 9 Oct 2011

@author: Elliot
'''

from params import *
import utils

class Arrows():
    def __init__(self, num_arrows, dt, rate_base, attractitude, box):
        self.num_arrows = num_arrows
        self.dt = dt
        self.rate_base = rate_base
        self.attractitude = attractitude
        self.v = 1.0
        self.dim = box.dim

        # Algorithm choice
        self.rates_update = self._rates_update_chemo       
        self.wall_handle = self._wall_aligning

        self._rs_initialise(box)
        self._vs_initialise()
        self._rates_initialise()

    def _rs_initialise(self, box):
        self.rs = np.empty([self.num_arrows, self.dim], dtype=np.float)

        for i_dim in range(self.dim):
            self.rs[:, i_dim] = np.random.uniform(-box.L_half,
                                                  +box.L_half,
                                                  self.num_arrows)

        i_lattice = box.i_lattice_find(self.rs)
        for i_arrow in range(self.num_arrows):
            while box.is_wall(i_lattice[i_arrow]):
                for i_dim in range(self.dim):
                    self.rs[i_arrow, i_dim] = np.random.uniform(-box.L_half,
                                                                +box.L_half)
                i_lattice[i_arrow] = box.i_lattice_find(np.array([self.rs[i_arrow]]))

    def _vs_initialise(self):
        vs_p = np.empty([self.num_arrows, self.dim], dtype=np.float)
        vs_p[:, 0] = self.v
        vs_p[:, 1] = np.random.uniform(-np.pi, np.pi, self.num_arrows)
        self.vs = utils.polar_to_cart(vs_p)

    def _rates_initialise(self):
        self.rates = np.empty([self.num_arrows], dtype=np.float)

    def rs_update(self, box):
        rs_test = self.rs + self.vs * self.dt
        i_obstructed, i_lattice_test = box.i_obstructed_find(rs_test)

        for i_arrow in i_obstructed:
            r_cell_test = box.r_cell_find(i_lattice_test[i_arrow])
            i_lattice_source = box.i_lattice_find(self.rs[i_arrow])

            r_source_rel = self.rs[i_arrow] - r_cell_test
            sides = np.sign(r_source_rel)
    
            delta_i_lattice = np.abs(i_lattice_source - i_lattice_test[i_arrow])
            adjacentness = delta_i_lattice.sum()

            # If test cell is same as source cell
            if adjacentness == 0:
                break
            # If test cell is directly adjacent to original
            elif adjacentness == 1:
                # Find dimension where i_lattice has changed
                dim_hit = delta_i_lattice.argmax()
            elif adjacentness == 2:
                # Dimension with largest absolute velocity component
                dim_bias = np.abs(self.vs[i_arrow]).argmax()
                i_lattice_new = i_lattice_test[i_arrow, :]
                i_lattice_new[1 - dim_bias] += sides[1 - dim_bias]
                if not box.is_wall(i_lattice_new):
                    dim_hit = 1 - dim_bias
                else:
                    dim_nonbias = 1 - dim_bias
                    i_lattice_new = i_lattice_test[i_arrow, :]
                    i_lattice_new[dim_nonbias] += sides[1 - dim_nonbias]
                    if not box.is_wall(i_lattice_new):
                        dim_hit = 1 - dim_nonbias
                    # Must be that both adjacent cells are walls
                    else:
                        dim_hit = [0, 1]
            # Change position to just off obstructing cell edge
            rs_test[i_arrow, dim_hit] = (r_cell_test + sides * (box.dx_half + box.wall_buffer))[dim_hit]
            self.wall_handle(i_arrow, dim_hit)

        # Note, need to extend movement to fill time-step    
        self.rs[:] = rs_test[:]

    def vs_update(self):
        self._tumble()

    def _tumble(self):
        dice_roll = np.random.uniform(0.0, 1.0, self.num_arrows)
        i_tumblers = np.where(dice_roll < self.rates * self.dt)[0]
        vs_p = utils.cart_to_polar(self.vs[i_tumblers])
        vs_p[:, 1] = np.random.uniform(-np.pi, np.pi, i_tumblers.shape[0])
        self.vs[i_tumblers] = utils.polar_to_cart(vs_p)

    def _grad_find(self, field, dx, i_lattice):
        traj = np.asarray(np.sign(self.vs), dtype=np.int)
        for i_arrow in range(self.num_arrows):
            dim_bias = np.abs(self.vs[i_arrow]).argmax()
            traj[i_arrow, 1 - dim_bias] = 0

        grad = (field[(i_lattice + traj)[:, 0], (i_lattice + traj)[:, 1]] -
                field[(i_lattice - traj)[:, 0], (i_lattice - traj)[:, 1]]) / dx 
        return grad

# Tumbling rate algorithms

    def _rates_update_const(self, box):
        self.rates[:] = self.rate_base

    def _rates_update_grad(self, box):
        self.rates[:] = self.rate_base
        i_lattice = box.i_lattice_find(self.rs)
        grad_attract = self._grad_find(box.attract_get(), box.dx_get(), i_lattice)
        self.rates -= self.grad_sens * grad_attract

    def _rates_update_integral(self, box):
        return

# / Tumbling rate algorithms

# Wall handling algorithms

    def _wall_specular(self, i_arrow, dim_hit):
        self.vs[i_arrow, dim_hit] *= -1.0

    def _wall_aligning(self, i_arrow, dim_hit):
        direction = self.vs[i_arrow].copy()
        direction[dim_hit] = 0.0
        if utils.vector_mag(direction) < ZERO_THRESH:
            self.vs[i_arrow] = (random.choice([1.0, -1.0]) *
                                np.array([self.vs[i_arrow, 1],
                                          -self.vs[i_arrow, 0]]))
        else:
            self.vs[i_arrow] = utils.vector_unitise(direction) * utils.vector_mag(self.vs[i_arrow])

    def _wall_bounceback(self, i_arrow, dim_hit):
        self.vs[i_arrow] *= -1.0
        
    def _wall_stalling(self, i_arrow, dim_hit):
        self.vs[i_arrow, dim_hit] = 0.0

# / Wall handling Algorithms
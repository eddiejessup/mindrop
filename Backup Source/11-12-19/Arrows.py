'''
Created on 9 Oct 2011

@author: Elliot
'''

from params import *
import utils

class Arrows():
    def __init__(self, box, num_arrows, 
                 grad_sense,
                 n_mem, mem_sense, 
                 onesided_flag, rate_alg, bc_alg):
        self.num_arrows = num_arrows
        self.onesided_flag = onesided_flag

        self.run_length_base = 1.0
        self.rate_base = 1.0

        self.v = self.run_length_base * self.rate_base

        if bc_alg == 'spec': self._wall_handle = self._wall_specular
        elif bc_alg == 'align': self._wall_handle = self._wall_aligning
        elif bc_alg == 'bback': self._wall_handle = self._wall_bounceback
        elif bc_alg == 'stall': self._wall_handle = self._wall_stalling

        if rate_alg == 'const': 
            self.rates_update = self._rates_update_const
        elif rate_alg == 'grad': 
            self.grad_sense = grad_sense
            self.rates_update = self._rates_update_grad
        elif rate_alg == 'mem': 
            self.mem_sense = mem_sense
            self.rates_update = self._rates_update_mem

        self._rs_initialise(box)
        self._vs_initialise(box)
        self._rates_initialise(n_mem, rate_alg)

        self.zeros = np.zeros_like(self.rates)
        
    def _rs_initialise(self, box):
        self.rs = np.empty([self.num_arrows, box.dim_get()], dtype=np.float)
        L_half = box.L_get() / 2.0

        for i_dim in range(box.dim_get()):
            self.rs[:, i_dim] = np.random.uniform(-L_half, +L_half,
                                                  self.num_arrows)

        i_lattice = box.i_lattice_find(self.rs)
        for i_arrow in range(self.num_arrows):
            while box.is_wall(i_lattice[i_arrow]):
                for i_dim in range(box.dim_get()):
                    self.rs[i_arrow, i_dim] = np.random.uniform(-L_half, +L_half)
                i_lattice[i_arrow] = box.i_lattice_find(np.array([self.rs[i_arrow]]))

    def _vs_initialise(self, box):
        vs_p = np.empty([self.num_arrows, box.dim_get()], dtype=np.float)
        vs_p[:, 0] = self.v
        vs_p[:, 1] = np.random.uniform(-np.pi, np.pi, self.num_arrows)
        self.vs = utils.polar_to_cart(vs_p)

    def _mem_kernel_find(self, n_mem):
        # Transient / Steady-state compromise parameter, 0.5 good
        A = 0.5
        N = 1.0 / np.sqrt(0.8125 * np.square(A) - 0.75 * A + 0.5)
        t_s = np.arange(0.0, float(n_mem) / self.rate_base, DELTA_t, dtype=np.float)
        g_s = self.rate_base * t_s
        self.K = (N * self.mem_sense * self.rate_base * np.exp(-g_s) * 
                  (1.0 - A * (g_s + (np.square(g_s)) / 2.0)))

        print('Kernel quasi-integral: %f' % (self.K.sum() * DELTA_t))
#        print('Kernel sensible quasi-integral: %f' % (self.K.sum() * DELTA_t * FOOD_0 * self.num_arrows * ATTRACT_RATE / (BREAKDOWN_RATE * WALL_RESOLUTION * LATTICE_RESOLUTION)))
#        P.plot(t_s * self.rate_base, self.K)
#        P.show()

    def _rates_initialise(self, n_mem, rate_alg):
        self.rates = np.empty([self.num_arrows], dtype=np.float)
        if rate_alg == 'mem':
            self._mem_kernel_find(n_mem)
            self.attract_mem = np.zeros([self.num_arrows, self.K.shape[0]], dtype=np.float)

    def rs_update(self, box):
        rs_test = self.rs + self.vs * DELTA_t
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
            rs_test[i_arrow, dim_hit] = (r_cell_test + 
                                         sides * 
                                         ((box.dx_get() / 2.0) + 
                                          box.cell_buffer_get()))[dim_hit]
            self._wall_handle(i_arrow, dim_hit)

        # Note, need to extend movement to fill time-step    
        self.rs[:] = rs_test[:]

    def vs_update(self):
        self._tumble()

    def _tumble(self):
        dice_roll = np.random.uniform(0.0, 1.0, self.num_arrows)
        i_tumblers = np.where(dice_roll < (self.rates * DELTA_t))[0]
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

    def _integral_find(self):
        return np.sum(self.attract_mem * self.K, axis=1) * DELTA_t

# Tumbling rate algorithms

    def _rates_update_const(self, box):
        self.rates[:] = self.rate_base

    def _rates_update_grad(self, box):
        i_lattice = box.i_lattice_find(self.rs)
        grad_attract = self._grad_find(box.attract_get(), box.dx_get(), i_lattice)
        self.rates = self.rate_base - self.grad_sense * grad_attract
        if self.onesided_flag:
            self.rates = np.minimum(self.rates, self.rate_base)

    def _rates_update_mem(self, box):
        i_lattice = box.i_lattice_find(self.rs)
        self.attract_mem[:, 1:] = self.attract_mem[:, :-1]
        attract = box.attract_get()
        for i_arrow in range(self.num_arrows):
            self.attract_mem[i_arrow, 0] = attract[i_lattice[i_arrow, 0],
                                                   i_lattice[i_arrow, 1]]
        self.rates = self.rate_base * (1.0 - self._integral_find())
        if self.onesided_flag:
            self.rates = np.minimum(self.rates, self.rate_base)
        print('Min rate: %f\tMax rate: %f\tMean rate: %f' % 
              (min(self.rates), max(self.rates), np.mean(self.rates)))

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
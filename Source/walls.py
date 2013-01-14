import numpy as np
import utils
import fields
import maze as maze_module

BUFFER_SIZE = 0.999

def shrink(w_old, n):
    if n < 1: raise Exception('Shrink factor >= 1')
    elif n == 1: return w_old
    elif n % 2 != 0: raise Exception('Shrink factor must be odd')
    M = w_old.shape[0]
    w_new = np.zeros(w_old.ndim * [M * n], dtype=w_old.dtype)
    mid = n // 2
    for x in range(M):
        x_ = x * n
        for y in range(M):
            y_ = y * n
            if w_old[x, y]:
                w_new[x_ + mid, y_ + mid] = True
                if w_old[utils.wrap_inc(M, x), y]:
                    w_new[x_ + mid:x_ + n, y_ + mid] = True
                if w_old[utils.wrap_dec(M, x), y]:
                    w_new[x_:x_ + mid, y_ + mid] = True
                if w_old[x, utils.wrap_inc(M, y)]:
                    w_new[x_ + mid, y_ + mid:y_ + n] = True
                if w_old[x, utils.wrap_dec(M, y)]:
                    w_new[x_ + mid, y * n:y_ + mid] = True
    return w_new

class Parametric(object):
    def __init__(self, parent_env, num, delta, R_c_min, R_c_max):
        self.parent_env = parent_env
        self.num = num
        self.delta = delta

        # Generate obstacles
        self.r_c = np.zeros([self.num, self.parent_env.dim], dtype=np.float)
        self.R_c = np.zeros([self.num], dtype=np.float)
        m = 0
        while m < self.num:
            valid = True
            self.R_c[m] = np.random.uniform(R_c_min, R_c_max)
            self.r_c[m] = np.random.uniform(-self.parent_env.L_half + 1.1*self.R_c[m], self.parent_env.L_half - 1.1*self.R_c[m], self.parent_env.dim)
            # Check obstacle doesn't intersect any of those already positioned
            for m_2 in range(m):
                if utils.circle_intersect(self.r_c[m], self.R_c[m], self.r_c[m_2], self.R_c[m_2]):
                    valid = False
                    break
            if valid: m += 1
        self.R_c_sq = self.R_c ** 2

        self.d = self.R_c.min() if self.num > 0 else self.parent_env.L_half

    def get_A_free(self):
        return self.parent_env.get_A() - np.pi * np.sum(self.R_c_sq)

    def is_obstructed(self, r):
        for m in range(self.num):
            if utils.vector_mag(r - self.r_c[m]) < self.R_c[m]:
                return True
        return False

    def obstruct(self, motiles):
        motiles.r += motiles.v * self.parent_env.dt
        motiles.r[motiles.r > self.parent_env.L_half] -= self.parent_env.L
        motiles.r[motiles.r < -self.parent_env.L_half] += self.parent_env.L

        # Align with obstacles
        r_rels = motiles.r[:, np.newaxis] - self.r_c[np.newaxis, :]
        r_rels_mag_sq = utils.vector_mag_sq(r_rels)
        for n in range(motiles.N):
            for m in range(self.num):
                if r_rels_mag_sq[n, m] < self.R_c_sq[m]:
                    u = utils.vector_unit_nonull(r_rels[n, m])
                    v_dot_u = np.sum(motiles.v[n] * u)
                    v_mag = utils.vector_mag(motiles.v[n])
                    theta_v_u = np.arccos(v_dot_u / v_mag)
                    # If particle-surface angle is below stickiness threshold (delta)
                    if theta_v_u > np.pi/2.0 - self.delta:
                        # New direction is old one without component parallel to surface normal
                        v_new = motiles.v[n] - v_dot_u * u
                        motiles.v[n] = utils.vector_unit_nonull(v_new) * v_mag
                        # New position is on the surface, slightly inside (by a distance b) to keep particle inside at next iteration
                        b = 1.001 * (self.R_c[m] - (self.R_c[m] ** 2 - (utils.vector_mag(motiles.v[n]) * self.parent_env.dt) ** 2) ** 0.5)
                        motiles.r[n] = self.r_c[m] + u * (self.R_c[m] - b)
                    break

    def to_field(self, dx):
        # This is all very clever and numpy-ey, soz
        M = int(self.parent_env.L / dx)
        if self.num > 0:
            axes = [i + 1 for i in range(self.parent_env.dim)] + [0]
            inds = np.transpose(np.indices(self.parent_env.dim * [M]), axes=axes)
            rs = -self.parent_env.L_half + (inds + 0.5) * dx
            r_rels = rs[:, :, np.newaxis, :] - self.r_c[np.newaxis, np.newaxis, :, :]
            r_rels_mag_sq = utils.vector_mag_sq(r_rels)
            return np.asarray(np.any(r_rels_mag_sq < self.R_c_sq, axis=-1), dtype=np.uint8)
        else:
            return np.zeros(self.parent_env.dim * [M], dtype=np.uint8)

class Walls(fields.Field):
    def __init__(self, parent_env, dx):
        fields.Field.__init__(self, parent_env, dx)
        self.parent_env = parent_env
        self.a = np.zeros(self.parent_env.dim * (self.M,), dtype=np.uint8)
        self.d = self.parent_env.L_half

    def get_A_free_i(self):
        return np.logical_not(self.a).sum()

    def get_A_free(self):
        return self.parent_env.get_A() * (float(self.get_A_free_i()) / float(self.get_A_i()))

    def is_obstructed(self, r):
        return self.a[tuple(self.r_to_i(r).T)]

    def obstruct(self, motiles):
        inds_old = self.r_to_i(motiles.r)
        motiles.r += motiles.v * self.parent_env.dt
        motiles.r[motiles.r > self.parent_env.L_half] -= self.parent_env.L
        motiles.r[motiles.r < -self.parent_env.L_half] += self.parent_env.L
        inds_new = self.r_to_i(motiles.r)

#        dx_half = BUFFER_SIZE * (self.dx / 2.0)
#        for i in np.where(self.is_obstructed(motiles.r))[0]:
#            for i_dim in np.where(inds_new[i] != inds_old[i])[0]:
#                motiles.r[i, i_dim] = self.i_to_r(inds_old[i, i_dim]) + dx_half * np.sign(motiles.v[i, i_dim])
#                motiles.v[i, i_dim] = 0.0

#        assert not self.is_obstructed(motiles.r).any()

        # Scale speed to v_0
        motiles.v = utils.vector_unit_nullrand(motiles.v) * motiles.v_0

    def to_field(self, dx):
        if dx == self.dx:
            return self.a
        else:
            raise NotImplementedError

class Closed(Walls):
    def __init__(self, parent_env, dx, d):
        Walls.__init__(self, parent_env, dx)
        self.d_i = int(d / dx) + 1
        self.d = self.d_i * self.dx
        self.a[...] = False
        for i_dim in range(self.a.ndim):
            inds = self.parent_env.dim * [Ellipsis]
            for i in range(self.d_i):
                inds[i_dim] = i
                self.a[inds] = True
                inds[i_dim] = -(i + 1)
                self.a[inds] = True

class Traps(Walls):
    def __init__(self, parent_env, dx, n, d, w, s):
        Walls.__init__(self, parent_env, dx)
        self.n = n
        self.d_i = int(d / self.dx) + 1
        self.w_i = int(w / self.dx) + 1
        self.s_i = int(s / self.dx) + 1
        self.d = self.d_i * self.dx
        self.w = self.w_i * self.dx
        self.s = self.s_i * self.dx

        if self.w < 0.0 or self.w > self.parent_env.L:
            raise Exception('Invalid trap width')
        if self.s < 0.0 or self.s > self.w:
            raise Exception('Invalid slit length')

        if self.n == 1:
            self.traps_f = np.array([[0.50, 0.50]], dtype=np.float)
        elif self.n == 4:
            self.traps_f = np.array([[0.25, 0.25], [0.25, 0.75], [0.75, 0.25],
                [0.75, 0.75]], dtype=np.float)
        elif self.n == 5:
            self.traps_f = np.array([[0.25, 0.25], [0.25, 0.75], [0.75, 0.25],
                [0.75, 0.75], [0.50, 0.50]], dtype=np.float)
        else:
            raise Exception('Traps not implemented for this number of traps')

        w_i_half = self.w_i // 2
        s_i_half = self.s_i // 2
        self.traps_i = np.asarray(self.M * self.traps_f, dtype=np.int)
        for x, y in self.traps_i:
            self.a[x - w_i_half - self.d_i:x + w_i_half + self.d_i + 1,
                   y - w_i_half - self.d_i:y + w_i_half + self.d_i + 1] = True
            self.a[x - w_i_half:x + w_i_half + 1,
                   y - w_i_half:y + w_i_half + 1] = False
            self.a[x - s_i_half:x + s_i_half + 1,
                   y + w_i_half:y + w_i_half + self.d_i + 1] = False

    def get_A_traps_i(self):
        A_traps_i = 0
        for x, y in self.traps_i:
            A_traps_i += np.logical_not(self.a[x - w_i_half: x + w_i_half + 1, y - w_i_half:y + w_i_half + 1]).sum()
        return A_traps_i

    def get_A_traps(self):
        return self.A * (float(self.get_A_traps_i()) / float(self.get_A_free_i))

    def get_fracs(self, r):
        inds = self.r_to_i(r)
        n_traps = [0 for i in range(len(self.traps_i))]
        for i_trap in range(len(self.traps_i)):
            mix_x, mid_y = self.traps_i[i_trap]
            w_i_half = self.w_i // 2
            low_x, high_x = mid_x - w_i_half, mid_x + w_i_half
            low_y, high_y = mid_y - w_i_half, mid_y + w_i_half
            for i_x, i_y in inds:
                if low_x < i_x < high_x and low_y < i_y < high_y:
                    n_traps[i_trap] += 1
        return [float(n_trap) / float(r.shape[0]) for n_trap in n_traps]

class Maze(Walls):
    def __init__(self, parent_env, dx, d, seed=None):
        Walls.__init__(self, parent_env, dx)
        if self.parent_env.L / self.dx % 1 != 0:
            raise Exception('Require L / dx to be an integer')
        if self.parent_env.L / self.d % 1 != 0:
            raise Exception('Require L / d to be an integer')
        if (self.parent_env.L / self.dx) / (self.parent_env.L / self.d) % 1 != 0:
            raise Exception('Require array size / maze size to be integer')

        self.seed = seed
        self.d = d

        self.M_m = int(self.parent_env.L / self.d)
        self.d_i = int(self.M / self.M_m)
        maze = maze_module.make_maze_dfs(self.M_m, self.parent_env.dim, self.seed)
        self.a[...] = utils.extend_array(maze, self.d_i)

# cython: profile=True
'''
Created on 9 Mar 2012

@author: ejm
'''

import numpy as np

cimport cython
cimport numpy as np
cimport utils_c

def grad_calc_1d(np.ndarray[np.float_t, ndim=1] field, 
                 np.ndarray[np.float_t, ndim=2] grad,
                 np.ndarray[np.uint8_t, ndim=1] walls, 
                 double dx):
    cdef unsigned int i_x
    cdef unsigned int i_inc, i_dec
    cdef unsigned int M_x = walls.shape[0]
    cdef np.float_t dx_double = 2.0 * dx, interval

    for i_x in range(M_x):
        if not walls[i_x]:
            interval = dx_double

            i_inc = utils_c.wrap_inc(M_x, i_x)
            i_dec = utils_c.wrap_dec(M_x, i_x)
            if walls[i_inc]:
                i_inc = i_x
                interval = dx
            if walls[i_dec]:
                i_dec = i_x
                interval = dx

            grad[i_x, 0] = (field[i_inc] - field[i_dec]) / interval
        else:
            grad[i_x, 0] = 0.0

def grad_calc_2d(np.ndarray[np.float_t, ndim=2] field, 
                 np.ndarray[np.float_t, ndim=3] grad,
                 np.ndarray[np.uint8_t, ndim=2] walls, 
                 double dx):
    cdef unsigned int i_x, i_y
    cdef unsigned int i_inc, i_dec
    cdef unsigned int M_x = walls.shape[0], M_y = walls.shape[1]
    cdef np.float_t dx_double = 2.0 * dx, interval

    for i_x in range(M_x):
        for i_y in range(M_y):
            if not walls[i_x, i_y]:
                interval = dx_double
                i_inc = utils_c.wrap_inc(M_x, i_x)
                i_dec = utils_c.wrap_dec(M_x, i_x)
                if walls[i_inc, i_y]:
                    i_inc = i_x
                    interval = dx
                if walls[i_dec, i_y]:
                    i_dec = i_x
                    interval = dx
                grad[i_x, i_y, 0] = (field[i_inc, i_y] - field[i_dec, i_y]) / interval

                i_inc = utils_c.wrap_inc(M_y, i_y)
                i_dec = utils_c.wrap_dec(M_y, i_y)
                if walls[i_x, i_inc]:
                    i_inc = i_y
                    interval = dx
                if walls[i_x, i_dec]:
                    i_dec = i_y
                    interval = dx
                grad[i_x, i_y, 1] = (field[i_x, i_inc] - field[i_x, i_dec]) / interval
            else:
                grad[i_x, i_y, 0] = 0.0
                grad[i_x, i_y, 1] = 0.0

def grad_calc_3d(np.ndarray[np.float_t, ndim=3] field, 
                 np.ndarray[np.float_t, ndim=4] grad,
                 np.ndarray[np.uint8_t, ndim=3] walls,  
                 double dx):
    cdef unsigned int i_x, i_y, i_z
    cdef unsigned int i_inc, i_dec
    cdef unsigned int M_x = walls.shape[0], M_y = walls.shape[1], M_z = walls.shape[2]
    cdef np.float_t dx_double = 2.0 * dx, interval

    for i_x in range(M_x):
        for i_y in range(M_y):
            for i_z in range(M_z):
                if not walls[i_x, i_y, i_z]:
                    interval = dx_double
                    i_inc = utils_c.wrap_inc(M_x, i_x)
                    i_dec = utils_c.wrap_dec(M_x, i_x)                    
                    if walls[i_inc, i_y, i_z]:
                        i_inc = i_x
                        interval = dx
                    if walls[i_dec, i_y, i_z]:
                        i_dec = i_x
                        interval = dx
                    grad[i_x, i_y, i_z, 0] = (field[i_inc, i_y, i_z] - field[i_dec, i_y, i_z]) / interval

                    interval = dx_double                    
                    i_inc = utils_c.wrap_inc(M_y, i_y)
                    i_dec = utils_c.wrap_dec(M_y, i_y)
                    if walls[i_x, i_inc, i_z]:
                        i_inc = i_y
                        interval = dx
                    if walls[i_x, i_dec, i_z]:
                        i_dec = i_y
                        interval = dx
                    grad[i_x, i_y, i_z, 1] = (field[i_x, i_inc, i_z] - field[i_x, i_dec, i_z]) / interval

                    i_inc = utils_c.wrap_inc(M_z, i_z)
                    i_dec = utils_c.wrap_dec(M_z, i_z)                    
                    if walls[i_x, i_y, i_inc]:
                        i_inc = i_z
                        interval = dx
                    if walls[i_x, i_y, i_dec]:
                        i_dec = i_z
                        interval = dx
                    grad[i_x, i_y, i_z, 2] = (field[i_x, i_y, i_inc] - field[i_x, i_y, i_dec]) / interval
                else:
                    grad[i_x, i_y, i_z, 0] = 0.0
                    grad[i_x, i_y, i_z, 1] = 0.0
                    grad[i_x, i_y, i_z, 2] = 0.0

def laplace_calc_1d(np.ndarray[np.float_t, ndim=1] field, 
                    np.ndarray[np.float_t, ndim=1] laplace,
                    np.ndarray[np.uint8_t, ndim=1] walls, 
                    double dx):
    cdef unsigned int i_x
    cdef unsigned int i_inc, i_dec
    cdef unsigned int M_x = walls.shape[0]
    cdef np.float_t dx_sq = dx * dx, diff

    for i_x in range(M_x):
        if not walls[i_x]:
            diff = 0.0

            i_inc = utils_c.wrap_inc(M_x, i_x)
            i_dec = utils_c.wrap_dec(M_x, i_x)
            if not walls[i_inc]:
                diff += field[i_inc] - field[i_x]
            if not walls[i_dec]:
                diff += field[i_dec] - field[i_x]

            laplace[i_x] = diff / dx_sq
        else:
            laplace[i_x] = 0.0            

def laplace_calc_2d(np.ndarray[np.float_t, ndim=2] field, 
                    np.ndarray[np.float_t, ndim=2] laplace,
                    np.ndarray[np.uint8_t, ndim=2] walls, 
                    double dx):
    cdef unsigned int i_x, i_y
    cdef unsigned int i_inc, i_dec
    cdef unsigned int M_x = walls.shape[0], M_y = walls.shape[1]
    cdef np.float_t dx_sq = dx * dx, diff

    for i_x in range(M_x):
        for i_y in range(M_y):
            if not walls[i_x, i_y]:
                diff = 0.0

                i_inc = utils_c.wrap_inc(M_x, i_x)
                i_dec = utils_c.wrap_dec(M_x, i_x)
                if not walls[i_inc, i_y]:
                    diff += field[i_inc, i_y] - field[i_x, i_y]
                if not walls[i_dec, i_y]:
                    diff += field[i_dec, i_y] - field[i_x, i_y]

                i_inc = utils_c.wrap_inc(M_y, i_y)
                i_dec = utils_c.wrap_dec(M_y, i_y)
                if not walls[i_x, i_inc]:
                    diff += field[i_x, i_inc] - field[i_x, i_y]
                if not walls[i_x, i_dec]:
                    diff += field[i_x, i_dec] - field[i_x, i_y]

                laplace[i_x, i_y] = diff / dx_sq
            else:
                laplace[i_x, i_y] = 0.0

def laplace_calc_3d(np.ndarray[np.float_t, ndim=3] field, 
                    np.ndarray[np.float_t, ndim=3] laplace,
                    np.ndarray[np.uint8_t, ndim=3] walls, 
                    double dx):
    cdef unsigned int i_x, i_y, i_z
    cdef unsigned int i_inc, i_dec
    cdef unsigned int M_x = walls.shape[0], M_y = walls.shape[1], M_z = walls.shape[2]
    cdef np.float_t dx_sq = dx * dx, diff

    for i_x in range(M_x):
        for i_y in range(M_y):
            for i_z in range(M_z):
                if not walls[i_x, i_y, i_z]:
                    diff = 0.0

                    i_inc = utils_c.wrap_inc(M_x, i_x)
                    i_dec = utils_c.wrap_dec(M_x, i_x)
                    if not walls[i_inc, i_y, i_z]:
                        diff += field[i_inc, i_y, i_z] - field[i_x, i_y, i_z]
                    if not walls[i_dec, i_y, i_z]:
                        diff += field[i_dec, i_y, i_z] - field[i_x, i_y, i_z]

                    i_inc = utils_c.wrap_inc(M_y, i_y)
                    i_dec = utils_c.wrap_dec(M_y, i_y)
                    if not walls[i_x, i_inc, i_z]:
                        diff += field[i_x, i_inc, i_z] - field[i_x, i_y, i_z]
                    if not walls[i_x, i_dec, i_z]:
                        diff += field[i_x, i_dec, i_z] - field[i_x, i_y, i_z]

                    i_inc = utils_c.wrap_inc(M_z, i_z)
                    i_dec = utils_c.wrap_dec(M_z, i_z)
                    if not walls[i_x, i_y, i_inc]:
                        diff += field[i_x, i_y, i_inc] - field[i_x, i_y, i_z]
                    if not walls[i_x, i_y, i_dec]:
                        diff += field[i_x, i_y, i_dec] - field[i_x, i_y, i_z]

                    laplace[i_x, i_y, i_z] = diff / dx_sq
    
                else:
                    laplace[i_x, i_y, i_z] = 0.0

def density_calc_1d(np.ndarray[np.float_t, ndim=1] f, 
                    np.ndarray[np.int_t, ndim=2] inds, 
                    np.float_t inc):
    cdef unsigned int i_x
    cdef unsigned int i_part
    for i_x in range(f.shape[0]):
        f[i_x] = 0.0
    for i_part in range(inds.shape[0]):
        f[inds[i_part]] += inc    

def density_calc_2d(np.ndarray[np.float_t, ndim=2] f, 
                    np.ndarray[np.int_t, ndim=2] inds, 
                    np.float_t inc):
    cdef unsigned int i_x, i_y
    cdef unsigned int i_part
    for i_x in range(f.shape[0]):
        for i_y in range(f.shape[1]):
            f[i_x, i_y] = 0.0
    for i_part in range(inds.shape[0]):
        f[inds[i_part, 0], inds[i_part, 1]] += inc

def density_calc_3d(np.ndarray[np.float_t, ndim=3] f, 
                    np.ndarray[np.int_t, ndim=2] inds, 
                    np.float_t inc):
    cdef unsigned int i_x, i_y, i_z
    cdef unsigned int i_part
    for i_x in range(f.shape[0]):
        for i_y in range(f.shape[1]):
            for i_z in range(f.shape[2]):
                f[i_x, i_y, i_z] = 0.0
    for i_part in range(inds.shape[0]):
        f[inds[i_part, 0], inds[i_part, 1], inds[i_part, 2]] += inc    

def r_sep_calc(np.ndarray[np.float_t, ndim=2] r,
               np.ndarray[np.float_t, ndim=3] r_sep, 
               np.ndarray[np.float_t, ndim=2] R_sep_sq, 
               double L):
    cdef unsigned int i_1, i_2, i_dim
    cdef np.float_t L_half = L / 2.0
    for i_1 in range(r.shape[0]):
        for i_2 in range(i_1 + 1, r.shape[0]):
            R_sep_sq[i_1, i_2] = 0.0
            for i_dim in range(r.shape[1]):
                r_sep[i_1, i_2, i_dim] = utils_c.wrap_real(L, L_half, r[i_1, i_dim] - r[i_2, i_dim])
                R_sep_sq[i_1, i_2] += utils_c.square(r_sep[i_1, i_2, i_dim])

def collide(np.ndarray[np.float_t, ndim=2] v, 
            np.ndarray[np.float_t, ndim=3] r_sep, 
            np.ndarray[np.float_t, ndim=2] R_sep_sq, 
            double R_c_sq):
    cdef unsigned int i_1, i_2, i_dim

    # If any collision has occured, set both motiles' speeds to zero
    for i_1 in range(v.shape[0]):
        for i_2 in range(i_1 + 1, v.shape[0]):
            if R_sep_sq[i_1, i_2] < R_c_sq:
                for i_dim in range(v.shape[1]):
                    v[i_1, i_dim] = 0.0
                    v[i_2, i_dim] = 0.0
                break

    # Set new velocity to net separation vector
    for i_1 in range(v.shape[0]):
        for i_2 in range(i_1 + 1, v.shape[0]):
            if R_sep_sq[i_1, i_2] < R_c_sq:
                for i_dim in range(v.shape[1]):
                    v[i_1, i_dim] += r_sep[i_1, i_2, i_dim]
                    v[i_2, i_dim] -= r_sep[i_1, i_2, i_dim]

def vicsek_align(np.ndarray[np.float_t, ndim=2] v,
                 np.ndarray[np.float_t, ndim=2] v_temp, 
                 np.ndarray[np.float_t, ndim=2] R_sep_sq, 
                 double R_max_sq):
    ''' Apply vicsek algorithm with squared radius R_sep_sq to motiles with 
    velocities v and separation distances R_sep_sq '''
    cdef unsigned int i_1, i_2, i_dim

    for i_1 in range(v.shape[0]):
        for i_dim in range(v.shape[1]):
            v_temp[i_1, i_dim] = v[i_1, i_dim]

    for i_1 in range(v.shape[0]):
        for i_2 in range(i_1 + 1, v.shape[0]):
            if R_sep_sq[i_1, i_2] < R_max_sq:
                for i_dim in range(v.shape[1]):
                    v[i_1, i_dim] += v_temp[i_2, i_dim]
                    v[i_2, i_dim] += v_temp[i_1, i_dim]

@cython.boundscheck(False)
def rat_mem_integral_calc(np.ndarray[np.float_t, ndim=1] c_cur, 
                          np.ndarray[np.float_t, ndim=2] c_mem, 
                          np.ndarray[np.float_t, ndim=1] K_dt, 
                          np.ndarray[np.float_t, ndim=1] integrals):
    cdef unsigned int i_n, i_t, i_t_max = c_mem.shape[1] - 1
    cdef np.float_t integral

    for i_n in range(c_mem.shape[0]):
        # Shift old memories down, enter new memory, and do integral
        integral = 0.0
        for i_t in range(i_t_max):
            c_mem[i_n, i_t_max - i_t] = c_mem[i_n, i_t_max - i_t - 1]
            integral += c_mem[i_n, i_t_max - i_t] * K_dt[i_t_max - i_t]
        c_mem[i_n, 0] = c_cur[i_n]
        integral += c_mem[i_n, 0] * K_dt[0]
        integrals[i_n] = integral
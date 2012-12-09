'''
Created on 16 Nov 2011

@author: s1152258
'''

import numpy as np
import pylab

import utils

def lattice_diffuse_test():
    a = np.zeros([100, 100], dtype=np.float)
    a[50, 50] = 10.0
    
    lat = np.zeros_like(a, dtype=np.bool)
    
    d_arr = np.zeros_like(a)
    d_const = 0.1
    
    pylab.ion()
    pylab.show()
    
    fig = pylab.figure()
    sim = fig.add_subplot(1, 1, 1)
    sim.axes.get_xaxis().set_visible(False)
    sim.axes.get_yaxis().set_visible(False)
    
    while True:
        utils.lattice_diffuse(lat, a, d_const, d_arr)
        sim.imshow(a, interpolation='nearest')
        fig.canvas.draw()
        sim.cla()
        print(a.sum())

#dt = 0.01
#
#t = 100.0
#ts = np.arange(0.0, t, dt, dtype=np.float)
#Is = np.zeros_like(ts)
#
#N = 8.0 / np.sqrt(21)
#A = 0.5
#M = 1.0
#L = 1.0
#
#t_m = 10.0
#
#t_s = np.arange(0.0, t_m, dt, dtype=np.float)
#cs = np.empty_like(t_s)
#g = L * t_s
#R = N * M * L * np.exp(-g) * (1 - A * (g + (g ** 2) / 2.0))
#
#cs[:] = 1.0
#c_new = 1.0
#
#for i_t in range(len(ts)):
#    for i_t_ in range(len(t_s)):
#        Is[i_t] += cs[i_t_] * R[i_t_]
#    Is[i_t] *= dt
#    cs[:-1] = cs[1:]
#    cs[0] = c_new
#
#pylab.plot(ts, Is)
#pylab.show()

dt = 0.01
t_max = 10.0

N = 8.0 / np.sqrt(21)
A = 0.5
M = 1.0
L = 1.0

t_m = 10.0

t_s = np.arange(0.0, t_m, dt, dtype=np.float)
cs = np.empty_like(t_s)
g = L * t_s
K = N * M * L * np.exp(-g) * (1 - A * (g + (g ** 2) / 2.0))

cs[:] = 1.0
c_new = 1.0

I = (cs * K * dt).sum()
print(I)

cs[:-1] = cs[1:]
cs[0] = c_new
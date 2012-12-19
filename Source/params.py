import numpy as np

# OUTPUT
DAT_EVERY = 500

# GENERAL
DIM = 2
DELTA_t = 0.1
RUN_TIME_MAX = np.inf
RANDOM_SEED = 135 # Set to None to change each run

# MOTILES
MOTILE_DENSITY = 3.5e-3
v_0 = 20.0
## TUMBLING
TUMBLE_FLAG = True
p_0 = 1.0
TUMBLE_ALG = 'm'
TUMBLE_GRAD_SENSE = 20.0
TUMBLE_MEM_SENSE = 25.0
TUMBLE_MEM_t_MAX = 8.0 / p_0
## VICSEK
VICSEK_FLAG = False
VICSEK_R = 3.0
## FORCE
FORCE_FLAG = False
FORCE_SENSE = 5000.0
## NOISE
NOISE_FLAG = False
NOISE_D_ROT = 2.0
## COLLISIONS
COLLIDE_FLAG = False
COLLIDE_R = 2.0

# FIELD
L_RAW = 1200.0
DELTA_x = 4.0
## ATTRACTANT
c_PDE_FLAG = True
D_c = 20.0
c_SOURCE_RATE = 1.0
c_SINK_RATE = 0.01
## FOOD
f_0 = 1.0
f_PDE_FLAG = False
D_f = D_c
f_SINK_RATE = c_SOURCE_RATE

# WALLS
WALL_ALG = 'blank'
## TRAP
TRAP_WALL_WIDTH = 10.0
TRAP_LENGTH = 150.0
TRAP_SLIT_LENGTH = 40.0
## MAZE
MAZE_WALL_WIDTH = 60.0
MAZE_SEED = 150

if FORCE_FLAG:
    if not FORCE_FLAG: raw_input('non-noisy forcies, sure?')
    SENSE = FORCE_SENSE
    if VICSEK_FLAG: ALG = 'fv'
    else: ALG = 'force'
elif TUMBLE_FLAG:
    if NOISE_FLAG: raw_input('noisy tumblers, sure?')
    SENSE = TUMBLE_MEM_SENSE
    ALG = 'rat'
else:
    SENSE = None

HYST_FLAG = False
HYST_RATE_TUMBLE = 0.5e-3
HYST_MAX_TUMBLE = 150.0
HYST_RATE_FORCE = 0.125
HYST_MAX_FORCE = 12000

#DAT_DIR = '../Data/%s_%s_%s' % (WALL_ALG, ALG, RANDOM_SEED)
DAT_DIR = '../Data/%s_%s' % (ALG, SENSE)

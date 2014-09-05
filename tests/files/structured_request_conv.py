import numpy as np
import math

# 
# this run control defines 8 parameters, with total number of expected instances
# of 1 * 1 * 1 * 1 = 1
#

# fidelity levels, 1 * 1 * 1 = 1
f_rxtr = 0
f_fc = 2
f_loc = 2

# reactor params, 1 = 1
n_rxtr = 1
r_t_f = 1.0
r_th_pu = 1.0
f_mox = 0.33 # third of a core

# supplier params, 3 = 3
r_s_th = 0.08 # 2 plants per 25 reactors
r_s_mox_uox = 0.4 
r_s_mox = 0.2 # 1 plant per 5 reactors
r_s_thox = 0.2 # 1 plant per 5 reactors
r_inv_proc = 1.

# location params, 3 = 3
n_reg = 10
r_l_c = 1.

from kpfpipe.pipeline import Pipeline
from kpfpipe.level0 import KPF0
from kpfpipe.level1 import KPF1
from kpfpipe.level2 import KPF2
import numpy as np

# Set up:

kpf0 = KPF0()
kpf0.green = np.ones((32,32), dtype=np.float) 
kpf0.red = np.ones((32,32), dtype=np.float) 
kpf0.bias_green = np.ones((32,32), dtype=np.float)*0.4
kpf0.bias_red = np.ones((32,32), dtype=np.float)*0.5 
kpf0.flat_green = np.ones((32,32), dtype=np.float)*0.2
kpf0.flat_red = np.ones((32,32), dtype=np.float)*0.1

# We might want to avoid requiring both red and green, for instance. 
#  - Could either have green/red subtract_bias functions individually
#  - Check which data is available in this KPF0 object and subtract_bias only the available data
#
# We don't want to enforce dimensionality a priori, allow more flexible input

# Recipe:
def MyRecipe(kpf0):
    p = Pipeline(level0=kpf0)
    print(p)
    p.subtract_bias()
    p.divide_flat()
    print(p)
    p.extract_spectrum()
    p.calibrate_wavelengths()
    print(p)

MyRecipe(kpf0)

## To dos:
# - Implement logging.py to keep track of information/errors in each method
# - Discuss creating level1 object as independent mandatory pipeline method
# - Think about how to make the methods more flexible (e.g. bias subtract green only)
# - Create level 1 + 2 skeletons
# - Think about what attributes each KPF Level objects need
#    - including vertical structure (e.g., orders, orderlets, etc.)
#    - pass around fits header (keeping some attributes/info from previous levels on creation of higher level object)
# 
#
#








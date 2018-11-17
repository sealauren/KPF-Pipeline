"""
Define objects used in level zero data processing
"""

class KPF0(object):
    """
    Container object for level zero data
    
    To Do: Consider making an abstract base class...
    """
    def __init__(self):
        self.header # meta data from KPF, telesceope, and observatory (dict)
        self.red # Echellogram (image) from red CCD; 2D array (row, col)
        self.green # Echellogram (image) from green CCD; 2D array (row, col)
        self.hk # Echellogram (image) from HK spectrometer CCD; 2D array (row, col)
        self.expmeter # exposure meter sequence; 3D array = time series of 2D CCD images (time, row, col)
        self.guidecam # guidecam sequence; 3D array = time series of 2D CCD images (time, row, col) [consider whether guidecam should be included;  will it be analyzed?]
        self.bias # (2D array) master bias frame for that exposure 
        self.flat # (2D array) master flat frame
        
    def to_fits(self, fn):
        """
        Optional: collect all the level 0 data into a monolithic fits file
        """
        pass
    
    
    def extract_spectra(self):
        """
        Extract spectra from red and green chips
        """
        
        for chip in chips:
            for order in orders:
                for orderlet in orderlet:
                    pass

        self.orderlets = # fill in result
        
    

level1 = level0_to_level1(level0)

def level0_to_level1(level0):
    
class Pipeline(object):
    def __init__(self, level0=None, level1=None):
        pass # no op
    
    def create_level0(self):
        level0 = kpfpipe.level0.KPF0()
        # do stuff... reading fits files
        self.level0
        self.green = self.level0.green.copy()
        
    def write_level0(self):
        self.level0.to_fits() # maybe not necessary
        
    def subtract_bias_2d(self):
        # check if master bias exists
        # subtract bias off red and green chips
        self.bias_removed = subtract_bias(self.green.current) # (2D array)
        self.green = subtract_bias(self.green.current)
        
    def divide_flat_2d(self):
        # this where brighter fatter calculations are done?
        self.flat_removed = divide_flat(self.green.current) # (2D array)
        self.green = divide_flat(self.green.current)

    def extract_spectra(self):
        # 2D images are converted into Orderlet1 objects 5 * norders
        
        self.orderlets # collection of Orderlet1 objects
        
    def correct_brighter_fatter(self):
        # maybe needed
        
        
    def create_level1(self):
        level1 = kpfpipe.level0.KPF1()
        # do stuff... reading fits files
        
        self.level1

    def to_fits(self):
        # save current configuration of Pipeline w/ astrodata
        
        
    def write_level1(self):
        self.level1.to_fits()    
        
    def calibrate_wavelength_cal(self, *args):
        # not dependent on other data from the night
    def calibrate_wavelength_all(self):
        # call function that is recipe for combining all of the etalon calibrations
        # may also combine data from previous nights
    

'''
pipe.create_level0()
pipe.write_level0('rjXXX.XXX_level0.fits')

# level1 recipe
pipe = Pipeline(level0='rjXXX.XXX_level0.fits')
pipe.subtract_bias_2d()
pipe.divide_flat_2d()
# pipe.to_fits() # Could write out current state of pipe object not only at discrete levels 0, 1, 2
pipe.correct_brighter_fatter() # perhaps needed
pipe.extract_spectra() # create orderlet1 objects (missing wav is null)
pipe.calibrate_wavelength_cal(method=method) #
## wait for specified set of spectra to be extracted code to be written
pipe.calibrate_wavelength_all(method=method)












pipe = Pipeline(level0='rjXXX.XXX_level0.fits') # if someone wants to hack on the extraction
pipe = Pipeline(level1='rjXXX.XXX_level1.fits') # if someone wants to hack on the RV

pipe.subtract_bias()

'''

class MasterFlat(KFP0):
    """
    Flat field derived from a stack of master flats
    """

class MasterBias(KPF0):
    """
    Bias frame derived from a stack of bias observations
    """

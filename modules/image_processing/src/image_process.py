
# Standard dependencies
import configparser
import numpy as np
from astropy.io import fits

# Pipeline dependencies
from kpfpipe.logger import start_logger
from kpfpipe.primitives.level0 import KPF0_Primitive
from kpfpipe.models.level0 import KPF0

# External dependencies
from keckdrpframework.models.action import Action
from keckdrpframework.models.arguments import Arguments
from keckdrpframework.models.processing_context import ProcessingContext

# Local dependencies
from modules.image_processing.src.alg import ImageProcessingAlg

# Global read-only variables
DEFAULT_CFG_PATH = 'modules/image_processing/configs/default.cfg'

class ImageProcessing(KPF0_Primitive):
    """This module defines class `BiasSubtraction,` which inherits from `KPF0_Primitive` and provides methods
    to perform the event `bias subtraction` in the recipe.

    Args:
        KPF0_Primitive: Parent class
        action (keckdrpframework.models.action.Action): Contains positional arguments and keyword arguments passed by the `BiasSubtraction` event issued in recipe.
        context (keckdrpframework.models.processing_context.ProcessingContext): Contains path of config file defined for `bias_subtraction` module in master config file associated with recipe.

    Attributes:
        rawdata (kpfpipe.models.level0.KPF0): Instance of `KPF0`,  assigned by `actions.args[0]`            
        masterbias (kpfpipe.models.level0.KPF0): Instance of `KPF0`,  assigned by `actions.args[1]`
        ffi_exts(kpfpipe.models.level0.KPF0): Instance of `KPF0`,  assigned by `actions.args[2]`
        data_type (kpfpipe.models.level0.KPF0): Instance of `KPF0`,  assigned by `actions.args[3]`
        quicklook (kpfpipe.models.level0.KPF0): Instance of `KPF0`,  assigned by `actions.args[4]`

        config_path (str): Path of config file for the computation of bias subtraction.
        config (configparser.ConfigParser): Config context.
        logger (logging.Logger): Instance of logging.Logger
        alg (modules.bias_subtraction.src.alg.BiasSubtraction): Instance of `BiasSubtraction,` which has operation codes for bias subtraction.

    """
    def __init__(self, 
                action:Action, 
                context:ProcessingContext) -> None:
        """
        BiasSubtraction constructor.

        Args:
            action (keckdrpframework.models.action.Action): Contains positional arguments and keyword arguments passed by the `BiasSubtraction` event issued in recipe:

                `action.args[0]`(kpfpipe.models.level0.KPF0)`: Instance of `KPF0` containing raw image data
                `action.args[1]`(kpfpipe.models.level0.KPF0)`: Instance of `KPF0` containing master bias data
                `action.args[2]`(kpfpipe.models.level0.KPF0)`: Instance of `KPF0` containing FITS FFI extension(s) list
                `action.args[3]`(kpfpipe.models.level0.KPF0)`: Instance of `KPF0` containing the instrument/data type
                `action.args[4]`(kpfpipe.models.level0.KPF0)`: Instance of `KPF0` containing quicklook toggle (T/F)

            context (keckdrpframework.models.processing_context.ProcessingContext): Contains path of config file defined for `bias_subtraction` module in master config file associated with recipe.

        """
        #Initialize parent class
        KPF0_Primitive.__init__(self,action,context)

        #Input arguments
        self.raw_file=self.action.args[0]
        self.correcting_file=self.action.args[1]
        #self.masterbias=self.action.args[1]
        self.ffi_exts=self.action.args[2]
        self.data_type=self.action.args[3]
        self.quicklook=self.action.args[4]

        # input configuration
        self.config = configparser.ConfigParser()
        try:
            self.config_path = context.config_path['image_processing']
        except:
            self.config_path = DEFAULT_CFG_PATH

        self.config.read(self.config_path)

        #Start logger
        self.logger=None
        if not self.logger:
            self.logger=self.context.logger
        self.logger.info('Loading config from: {}'.format(self.config_path))

        #Image processing algorithm setup

        self.alg=ImageProcessingAlg(self.raw_file,self.ffi_exts,self.quicklook,self.data_type,config=self.config,logger=self.logger)

        #Preconditions
        
        #Postconditions
        
        #Perform - primitive's action
    def _perform(self) -> None:
        """Primitive action - 
        Performs image processing by calling method 'image_processing' from ImageProcess.
        Returns the bias/dark/background corrected raw data, L0 object.

        Returns:
            Arguments object(np.ndarray): Level 0 observation data
        """
        #until master file part of data model is fixed
        correcting_file = KPF0.from_fits(self.correcting_file)
        obs_type = correcting_file.header['PRIMARY']['IMTYPE']
        print(obs_type)
        
        if obs_type == 'Bias':
            if self.logger:
                self.logger.info(f'Bias Subtraction: subtracting master bias from raw FFI(s)')
            bias_subbed = self.alg.bias_subtraction(correcting_file)
            print(bias_subbed)
        if obs_type == 'Dark':
            if self.logger:
                self.logger.info(f'Dark Subtraction: subtracting dark frame from raw FFI(s)')
            dark_subbed = self.alg.dark_subtraction(correcting_file)
        
        return Arguments(self.alg.get())
        
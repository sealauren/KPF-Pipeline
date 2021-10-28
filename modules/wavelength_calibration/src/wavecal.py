# Standard dependencies
import configparser
import numpy as np
import pandas as pd

# Pipeline dependencies
from kpfpipe.logger import start_logger
from kpfpipe.primitives.level1 import KPF1_Primitive
from kpfpipe.models.level1 import KPF1

# External dependencies
from keckdrpframework.models.action import Action
from keckdrpframework.models.arguments import Arguments
from keckdrpframework.models.processing_context import ProcessingContext

# Local dependencies
from modules.wavelength_calibration.src.alg import WaveCalibrationAlg

# Global read-only variables
DEFAULT_CFG_PATH = 'modules/wavelength_calibration/configs/default.cfg'

class WaveCalibrate(KPF1_Primitive):
    """
    This module defines class `WaveCalibrate,` which inherits from KPF1_Primitive and provides methods
    to perform the event `wavelength calibration` in the recipe.

    Args:
        KPF1_Primitive: Parent class
        action (keckdrpframework.models.action.Action): Contains positional arguments and keyword arguments passed by the `WaveCalibrationAlg` event issued in recipe.
        context (keckdrpframework.models.processing_context.ProcessingContext): Contains path of config file defined for `wavelength_cal` module in master config file associated with recipe.

    Attributes:
        l1_obj (kpfpipe.models.level1.KPF1): Instance of `KPF1`, assigned by `actions.args[0]`
        master_wavelength (kpfpipe.models.level1.KPF1): Instance of `KPF1`, assigned by `actions.args[1]`
        data_type (kpfpipe.models.level1.KPF1): Instance of `KPF1`,  assigned by `actions.args[2]`
        config_path (str): Path of config file for wavelength calibration.
        config (configparser.ConfigParser): Config context.
        logger (logging.Logger): Instance of logging.Logger
        alg (modules.wavelength_cal.src.alg.WaveCalibrationAlg): Instance of `WaveCalibrationAlg,` which has operation codes for Wavelength Calibration.
    """

    default_args_val = {
            'data_type': 'KPF'
        }

    def __init__(self, 
                action:Action,
                context:ProcessingContext) -> None:
        """
        WaveCalibrate constructor.

        Args:
            action (Action): Contains positional arguments and keyword arguments passed by the `WaveCal` event issued in recipe:
              
                `action.args[0] (kpfpipe.models.level1.KPF1)`: Instance of `KPF1` containing level 1 file
                `action.args[1] (kpfpipe.models.level1.KPF1)`: Instance of `KPF1` containing master file
                `action.args[2] (kpfpipe.models.level1.KPF1)`: Instance of `KPF1` containing data type

            context (ProcessingContext): Contains path of config file defined for `wavelength_cal` module in master config file associated with recipe.
        """
        #Initialize parent class
        KPF1_Primitive.__init__(self,action,context)

        #Input arguments
        args_keys = [item for item in action.args.iter_kw() if item != "name"]

        self.l1_obj=self.action.args[0]
        self.master_wavelength=self.action.args[1]
        self.f0_key = self.action.args[2]
        self.frep_key = self.action.args[3]
        self.quicklook = self.action.args[4]
        self.linelist_path = self.action.args[5]
        self.linelist_sub_path = self.action.args[6]
        self.extensions = self.action.args[7]
        self.data_type = self.get_args_value('data_type', action.args, args_keys)

        #Input configuration
        self.config=configparser.ConfigParser()
        try:
            self.config_path=context.config_path['wavelength_cal']
        except:
            self.config_path = DEFAULT_CFG_PATH
        self.config.read(self.config_path)

        #Start logger
        self.logger=None
        #self.logger=start_logger(self.__class__.__name__,config_path)
        if not self.logger:
            self.logger=self.context.logger
        self.logger.info('Loading config from: {}'.format(self.config_path))


        #Wavelength calibration algorithm setup
        self.alg=WaveCalibrationAlg(self.config,self.logger)

        #Preconditions
       
        #Postconditions
        
    #Perform - primitive's action
    def _perform(self) -> None:
        """Primitive action - 
        Performs wavelength calibration by calling method 'run_wave_cal' from alg.py, and saves result in FITS extensions.

        Returns:
            Level 1 data, containing wavelength-per-pixel result.
        """
        # 0. setting up extract and save extension names
        #color opts: GREEN, RED
        #prefix opts: SCI, SKY, CAL
        #suffix opts: FLUX1, FLUX2, FLUX3, FLUX (corresponding WAVEs)
        output_ext_list = []
        for ext in self.extensions:
            split_ext = ext.split('_')
            color = split_ext[0]
            prefix = split_ext[1]
            suffix = split_ext[2]

            for i in ('1','2','3'):
                if suffix.endswith(i):
                    no = '_' + i
                else:
                    no = None

            output_ext = color + prefix + 'WAVE' + no
            output_ext_list.append(output_ext)

        # 1. extracting master data
        if self.logger:
            self.logger.info("Wavelength Calibration: Extracting master data")  
        master_data=self.alg.get_master_data(self.master_wavelength)
        # master_data = self.master_wavelength.data['SCI1'][1,:,:]
        # 2. get comb frequency values
        if self.logger:
            self.logger.info("Wavelength Calibration: Getting comb frequency values ")

        print ('f0 key and frep keys:', type(self.f0_key), type(self.frep_key))

        if self.f0_key:
            if type(self.f0_key) == str:
                comb_f0 = float(self.l1_obj.header['PRIMARY'][self.f0_key])
                print("comb_f0:",comb_f0)
            if type(self.f0_key) == float:
                comb_f0 = self.f0_key
                print("comb_f0:",comb_f0)
            # else:
            #     raise ValueError('F_0 incorrectly formatted')
        else:
            raise ValueError('F_0 value not found')

        if self.frep_key:
            if type(self.frep_key) == str:
                comb_fr = float(self.l1_obj.header['PRIMARY'][self.frep_key])
                print("comb_fr:",comb_fr)
            if type(self.frep_key) == float:
                comb_fr = self.frep_key
                print("comb_fr:",comb_fr)
            # else:
            #     raise ValueError('F_Rep incorrectly formatted')
        else:
            raise ValueError('F_Rep value not found')

        # 2. starting loop
        if self.logger:
            self.logger.info("Wavelength Calibration: Starting wavelength calibration loop")

        for input_ext,output_ext in (self.extensions,output_ext_list): #change to recipe config: 'orderlette_names' 
            if cal_type == 'LFC':
                if self.l1_obj[input_ext] is not None:
                    self.logger.info("Wavelength Calibration: Running {input_ext}")
                    if self.logger:
                        self.logger.info("Wavelength Calibration: Extracting flux")
                    flux = self.l1_obj[input_ext]#0 referring to 'flux'
                    #print('flux shape:', np.shape(flux))
                    flux = np.nan_to_num(flux)
                    if self.logger:
                        self.logger.info("Wavelength Calibration: Running algorithm")  
                    wl_soln=self.alg.open_and_run_LFC(flux,master_data,comb_f0,comb_fr,self.quicklook)
                    #print('soln shape:', np.shape(wl_soln))
                    if self.logger:
                        self.logger.info("Wavelength Calibration: Saving solution output")  
                    self.l1_obj[output_ext]=wl_soln
            if cal_type == 'Etalon':
                if self.l1_obj[input_ext] is not None:
                    self.logger.info("Wavelength Calibration: Running {input_ext}")
                    if self.logger:
                        self.logger.info("Wavelength Calibration: Extracting flux")
                    flux = self.l1_obj[input_ext]#0 referring to 'flux'
                    #print('flux shape:', np.shape(flux))
                    flux = np.nan_to_num(flux)
                    if self.logger:
                        self.logger.info("Wavelength Calibration: Running algorithm")  
                    wl_soln=self.alg.open_and_run_etalon(flux,self.quicklook)
                    #print('soln shape:', np.shape(wl_soln))
                    if self.logger:
                        self.logger.info("Wavelength Calibration: Saving solution output")  
                    self.l1_obj[output_ext]=wl_soln
            if cal_type == 'ThAr':
                if self.l1_obj[input_ext] is not None:
                    self.logger.info("Wavelength Calibration: Running {input_ext}")
                    if self.logger:
                        self.logger.info("Wavelength Calibration: Extracting linelists")
                    linelist = np.load(self.linelist_path)
                    redman_w = np.array(linelist['redman_w']),dtype=float)
                    redman_i = np.array(linelist(['redman_i']),dtype=float)

                    linelist_sub = np.load(self.linelist_subset_path,allow_pickle = True)
                    assert self.l1_obj[0].header['CAL-OBJ'].startswith('ThAr')

                    flux = self.l1_obj[input_ext]#0 referring to 'flux'
                    #print('flux shape:', np.shape(flux))
                    flux = np.nan_to_num(flux)
                    flux[flux < 0] = np.min(flux[flux > 0])
                    other_wls = self.l1_obj[]
                    if self.logger:
                        self.logger.info("Wavelength Calibration: Running algorithm")  
                    wl_soln=self.alg.open_and_run_thar(flux,redman_w,redman_i,linelist_sub,other_wls,plot_toggle,self.quicklook)
                    #print('soln shape:', np.shape(wl_soln))
                    if self.logger:
                        self.logger.info("Wavelength Calibration: Saving solution output")  
                    self.l1_obj[output_ext]=wl_soln
            else: 
                raise ValueError('Wavelength calibration type not found')
        
        if self.l1_obj is not None:
            self.l1_obj.receipt_add_entry('Wavelength Calibration', self.__module__,
                                          f'config_path={self.config_path}', 'PASS')
        if self.logger:
            self.logger.info("Wavelength Calibration: Receipt written")

        if self.logger:
            self.logger.info("Wavelength Calibration: Done!")

        return Arguments(self.l1_obj)

    def get_args_value(self, key: str, args: Arguments, args_keys: list):
        v = None
        if key in args_keys and args[key] is not None:
            v = args[key]
        else:
            v = self.default_args_val[key]
        return v
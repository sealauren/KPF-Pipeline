import numpy as np
import astropy.io.fits as fits
import matplotlib.pyplot as plt
from modules.Utils.config_parser import ConfigHandler
from kpfpipe.models.level0 import KPF0
from keckdrpframework.models.arguments import Arguments
import os
from astropy import modeling

class QuicklookAlg:
    """

    """

    def __init__(self,config=None,logger=None):

        """

        """
        self.config=config
        self.logger=logger

    def qlp_procedures(self,hdulist,L1_data,output_dir):

        saturation_limit = int(self.config['2D']['saturation_limit'])*1.
        plt.rcParams.update({'font.size': 8})
        plt.rcParams['legend.fontsize'] = plt.rcParams['font.size']

        #check if output location exist, if not create it

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            os.makedirs(output_dir+'/fig')


        hdr = hdulist.header
        version = hdr['PRIMARY']['IMTYPE']

        exposure_name = hdr['PRIMARY']['OFNAME'][:-5]
        print('working on',exposure_name)

        master_file = 'None'
        if version == 'Sol_All':
            master_file = self.onfig['2D']['master_socal']
        if version == 'Etalon_All':
            master_file = self.config['2D']['master_etalon']
        if version == 'Sol_All':
            master_file = self.config['2D']['master_socal']
        if version == 'Flat_All':
            master_file = self.config['2D']['master_flat']
        if version == 'Dark':
            master_file = self.config['2D']['master_dark']
        if version == 'Bias':
            master_file = self.config['2D']['master_bias']
        if version == 'Th_All':
            master_file = self.config['2D']['master_ThAr']
        if version == 'Une_All':
            master_file = self.config['2D']['master_Une']
        if version == 'LFC_SciCal':
            master_file = self.config['2D']['master_LFC']
        '''
        ccd_color = ['GREEN_CCD','RED_CCD']
        for i_color in range(len(ccd_color)):
            counts = np.array(hdulist[ccd_color[i_color]].data,'d')
            flatten_counts = np.ravel(counts)
            if len(flatten_counts)<1: continue
            master_flatten_counts='None'
            if master_file != 'None':
                hdulist1 = fits.open(master_file)
                master_counts = np.array(hdulist1[ccd_color[i_color]].data,'d')
                master_flatten_counts = np.ravel(master_counts)


            #2D image
            plt.figure(figsize=(5,4))
            plt.subplots_adjust(left=0.15, bottom=0.15, right=0.9, top=0.9)
            plt.imshow(counts, vmin = np.percentile(flatten_counts,1),vmax = np.percentile(flatten_counts,99),interpolation = 'None',origin = 'lower')
            plt.xlabel('x (pixel number)')
            plt.ylabel('y (pixel number)')
            plt.title(ccd_color[i_color]+' '+version)
            plt.colorbar(label = 'Counts')
            plt.savefig(output_dir+'fig/'+exposure_name+'_2D_Frame_'+ccd_color[i_color]+'.pdf')
            plt.savefig(output_dir+'fig/'+exposure_name+'_2D_Frame_'+ccd_color[i_color]+'.png', dpi=1000)
            #2D difference image
            plt.close()
            if master_file != 'None' and len(master_flatten_counts)>1:
                plt.figure(figsize=(5,4))
                plt.subplots_adjust(left=0.15, bottom=0.15, right=0.9, top=0.9)
                #pcrint(counts,master_counts)
                counts_norm = np.percentile(counts,99)
                master_counts_norm = np.percentile(master_counts,99)

                difference = counts/counts_norm-master_counts/master_counts_norm

                plt.imshow(difference, vmin = np.percentile(difference,1),vmax = np.percentile(difference,99), interpolation = 'None',origin = 'lower')
                plt.xlabel('x (pixel number)')
                plt.ylabel('y (pixel number)')
                plt.title(ccd_color[i_color]+' '+version+'- Master '+version)
                plt.colorbar(label = 'Fractional Difference')
                plt.savefig(output_dir+'fig/'+exposure_name+'_2D_Difference_'+ccd_color[i_color]+'.pdf')
                plt.savefig(output_dir+'fig/'+exposure_name+'_2D_Difference_'+ccd_color[i_color]+'.png', dpi=500)
             #Hisogram
            plt.close()
            plt.figure(figsize=(5,4))
            plt.subplots_adjust(left=0.15, bottom=0.15, right=0.9, top=0.9)

            #print(np.percentile(flatten_counts,99.9),saturation_limit)
            plt.hist(flatten_counts, bins = 50,alpha =0.5, label = 'Median: ' + '%4.1f' % np.nanmedian(flatten_counts)+'; Saturated? '+str(np.percentile(flatten_counts,99.9)>saturation_limit),density = False, range = (np.percentile(flatten_counts,0.005),np.percentile(flatten_counts,99.995)))#[flatten_counts<np.percentile(flatten_counts,99.9)]
            if master_file != 'None' and len(master_flatten_counts)>1: plt.hist(master_flatten_counts, bins = 50,alpha =0.5, label = 'Master Median: '+ '%4.1f' % np.nanmedian(master_flatten_counts), histtype='step',density = False, color = 'orange', linewidth = 1 , range = (np.percentile(master_flatten_counts,0.005),np.percentile(master_flatten_counts,99.995))) #[master_flatten_counts<np.percentile(master_flatten_counts,99.9)]
            #plt.text(0.1,0.2,np.nanmedian(flatten_counts))
            plt.xlabel('Counts')
            plt.ylabel('Number of Pixels')
            plt.yscale('log')
            plt.title(ccd_color[i_color]+' '+version+' Histogram')
            plt.legend()
            plt.savefig(output_dir+'fig/'+exposure_name+'_Histogram_'+ccd_color[i_color]+'.pdf')
            plt.savefig(output_dir+'fig/'+exposure_name+'_Histogram_'+ccd_color[i_color]+'.png', dpi=200)

            #Column cut
            plt.close()
            plt.figure(figsize=(8,4))
            plt.subplots_adjust(left=0.1, bottom=0.15, right=0.9, top=0.9)

            column_sum = np.nansum(counts,axis = 0)
            #print('which_column',np.where(column_sum==np.nanmax(column_sum))[0][0])
            which_column = np.where(column_sum==np.nanmax(column_sum))[0][0] #int(np.shape(master_counts)[1]/2)

            plt.plot(np.ones_like(counts[:,which_column])*saturation_limit,':',alpha = 0.5,linewidth =  1., label = 'Saturation Limit', color = 'gray')
            plt.plot(counts[:,which_column],alpha = 0.5,linewidth =  0.5, label = ccd_color[i_color]+' '+version, color = 'Blue')
            if master_file != 'None' and len(master_flatten_counts)>1: plt.plot(master_counts[:,which_column],alpha = 0.5,linewidth =  0.5, label = 'Master', color = 'Orange')
            plt.yscale('log')
            plt.ylabel('log(Counts)')
            plt.xlabel('Row Number')
            plt.title(ccd_color[i_color]+' '+version+' Column Cut Through Column '+str(which_column))#(Middle of CCD)
            plt.ylim(1,1.2*np.nanmax(counts[:,which_column]))
            plt.legend()
            plt.savefig(output_dir+'fig/'+exposure_name+'_Column_cut_'+ccd_color[i_color]+'.pdf')
            plt.savefig(output_dir+'fig/'+exposure_name+'_Column_cut_'+ccd_color[i_color]+'.png', dpi=200)

        '''
        #moving on the 1D data
        print('working on', L1_data)
        hdulist = fits.open(L1_data)

        wav_green = np.array(hdulist['GREEN_CAL_WAVE'].data,'d')
        wav_red = np.array(hdulist['RED_CAL_WAVE'].data,'d')

        wave_soln = self.config['L1']['wave_soln']
        if wave_soln!='None':#use the master the wavelength solution
            hdulist1 = fits.open(wave_soln)
            wav_green = np.array(hdulist1['GREEN_CAL_WAVE'].data,'d')
            wav_red = np.array(hdulist1['RED_CAL_WAVE'].data,'d')




        flux_green = np.array(hdulist['GREEN_SCI_FLUX1'].data,'d')
        flux_red = np.array(hdulist['RED_SCI_FLUX1'].data,'d')#hdulist[40].data

        wav = np.concatenate((wav_green,wav_red),axis = 0)
        flux = np.concatenate((flux_green,flux_red),axis = 0)


        n = int(self.config['L1']['n_per_row']) #number of orders per panel
        cm = plt.cm.get_cmap('rainbow')

        from matplotlib import gridspec
        gs = gridspec.GridSpec(n,1 , height_ratios=np.ones(n))

        plt.rcParams.update({'font.size': 15})
        fig, ax = plt.subplots(int(np.shape(wav)[0]/n)+1,1, sharey=False,figsize=(24,16))

        plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)
        fig.subplots_adjust(hspace=0.4)

        for i in range(np.shape(wav)[0]):
            low, high = np.nanpercentile(flux[i,:],[0.1,99.9])
            flux[i,:][(flux[i,:]>high) | (flux[i,:]<low)] = np.nan
            j = int(i/n)
            rgba = cm((i % n)/n*1.)
            #print(j,rgba)
            ax[j].plot(wav[i,:],flux[i,:], linewidth =  0.3,color = rgba)

        for j in range(int(np.shape(flux)[0]/n)):
            low, high = np.nanpercentile(flux[j*n:(j+1)*n,:],[.1,99.9])
            #print(j,high*1.5)
            ax[j].set_ylim(-high*0.1, high*1.2)

        low, high = np.nanpercentile(flux,[0.1,99.9])

        ax[int(np.shape(wav)[0]/n/2)].set_ylabel('Counts',fontsize = 20)
        ax[0].set_title('1D Spectrum',fontsize = 20)
        plt.xlabel('Wavelength (Ang)',fontsize = 20)
        plt.savefig(output_dir+'fig/'+exposure_name+'_1D_spectrum.pdf')
        plt.savefig(output_dir+'fig/'+exposure_name+'_1D_spectrum.png',dpi = 200)


        #now onto the plotting of CCF
        ccf_file = '/data/L2/20220524/KP.20220524.02360.58_L2.fits'
        hdulist = fits.open(ccf_file)
        print(hdulist.info())

        ccf_color = ['GREEN_CCF','RED_CCF']
        for i_color in range(len(ccd_color)):
            ccf = np.array(hdulist[ccf_color[i_color]].data,'d')
            print(np.shape(ccf))
            step = double(self.config['RV']['step'])
            vel_grid = np.array(range(-int(np.shape(ccf)[2]/2),int(np.shape(ccf)[2]/2),1),'d')*step

            fig, ax = plt.subplots(1,1, sharex=True,figsize=(5,4))
            ax = plt.subplot()
            plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95, top=0.9)
            mean_ccf = np.nanmean(ccf,axis = 1)/np.percentile(np.nanmean(ccf,axis = 1),[99.9])
            #print('test',np.shape(mean_ccf))
            mean_ccf = np.nanmedian(mean_ccf,axis = 0)
            plt.plot(vel_grid,mean_ccf,label = hdulist[ccf_color[i_color])

            #fit the center of the ccf
            fitter = modeling.fitting.LevMarLSQFitter()#the gaussian fit of the ccf
            model = modeling.models.Gaussian1D()
            fitted_model = fitter(model, vel_grid, 1.-mean_ccf)
            gamma =fitted_model.mean.value
            std =fitted_model.stddev.value
            plt.plot([gamma,gamma],[np.nanmin(np.nanmean(ccf,axis = 0)/np.percentile(np.nanmean(ccf,axis = 0),[99.9])),1.],':',color ='gray')
            ax.text(0.6,0.3+i_color*0.2,ccf_color[i_color]+' $\gamma$ (km/s): %5.2f' % gamma,transform=ax.transAxes)
            ax.text(0.6,0.2+i_color*0.2,ccf_color[i_color]+'$\sigma$ (km/s): %5.2f' % std,transform=ax.transAxes)
        plt.xlabel('RV (km/s)')
        plt.ylabel('CCF')
        plt.title('Mean CCF')
        plt.legend()
        plt.savefig(output_dir+'fig/'+exposure_name+'_simple_ccf.pdf')
        plt.close()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 15:37:39 2024

Resting HRV analysis on data acquired from brain products system

1. Check data quality
2. Do appropriate pre-processing for HRV analyss
3. Deploy Neurokit2 analysis
4. Visualisations

Resources:
    1. Read the paper - https://link.springer.com/article/10.3758%2Fs13428-020-01516-y
    2. Github repo - https://github.com/neuropsychology/NeuroKit
    3. Interval-related Analysis - https://neurokit2.readthedocs.io/en/latest/examples/intervalrelated.html
    4. HRV - https://neurokit2.readthedocs.io/en/latest/examples/hrv.html

@author: Rahul Venugopal

"""
#%% Load libraries
import os
import numpy as np
import mne
from tkinter import filedialog
import matplotlib.pyplot as plt
import neurokit2 as nk
import pandas as pd

# Run the below code once if we hit an overflow
# Exceeded cell block limit (set 'agg.path.chunksize' rcparam)
import matplotlib as mpl
mpl.rcParams['agg.path.chunksize'] = 10000

#%% Set the data directory and results directory

data_dir = filedialog.askdirectory(title='Please select a directory with data files')
results_dir = filedialog.askdirectory(title='Please select a directory to save results')

os.chdir(data_dir) # Changing directory to data folder

filelist = []

# Go to each folder and pick up the location of .set file
for _, _, files in os.walk(data_dir):
    for file in files:
        if file.endswith(".vhdr") and 'prewm' in file :
             filelist.append(file)

#%% Looping through all the files

# Initialise a list to collect HRV measures
masterlist = []

for file_no, data in enumerate(filelist):

    os.chdir(data_dir)

    # Load the .vhdr data now
    all_data =  mne.io.read_raw_brainvision(data, preload = True)
    srate = all_data.info['sfreq']
    info = all_data.info

    # finding events in the data file
    events = mne.events_from_annotations(all_data)[0]

    # custom relabel of markers
    event_dict = {
                  'eyes_closed':100,
                  'eyes_open':101
                  }

    tmin, tmax = 0, 60
    baseline = (0, 0.0)

    # Cut the resting portion of the data
    epochs = mne.Epochs(all_data,
                    events = events,
                    event_id = event_dict,
                    tmin = tmin,tmax = tmax,
                    baseline = baseline,
                    detrend=1)

    # Pick one of the ECG channel where we can see R peak without squinting
    if 'ECG1' in all_data.ch_names:
        ecg_channel = 'ECG1'
    else:
        ecg_channel = 'ECG2'

    # Get the ECG data as 1D array
    ecg_data = np.squeeze(epochs.get_data(picks = [ecg_channel]))

    # get the filename for saving images, removing extensions
    fname = data.split('.')[0].split('_')[0]

    # Set the results folder to collect results under each filename
    os.chdir(results_dir)

    # Create sub folders for each portions of resting data
    for sessions in range(len(ecg_data)):

        # split eyes open and closed
        add_on = "EO" if sessions % 2 != 0 else "EC"

        # create a folder with subject's name
        os.makedirs(fname + '_' + add_on + '_' + str(sessions+1))

        # move to the subject folder
        os.chdir(fname + '_' + add_on + '_' + str(sessions+1))

        # Clean the ECG trace and returns a big dataframe with many params
        signals, info1 = nk.ecg_process(ecg_data[sessions,:],
                                        sampling_rate = srate)

         # Find peaks
        peaks, info2 = nk.ecg_peaks(signals["ECG_Clean"],
                                    sampling_rate = srate)

        # Get time domain and frequency domain parameters

        hrv_variables = nk.hrv(info2, show=True)

        fig = plt.gcf()
        fig.set_size_inches(18.5, 10.5)
        fig.savefig((fname + '_' + add_on + '_' + str(sessions+1) + '.png'), dpi = 600)
        plt.close()

        # Visual quality check
        nk.ecg_plot(signals)

        fig = plt.gcf()
        fig.set_size_inches(18.5, 10.5)
        fig.savefig((fname + '_' + add_on + '_' + str(sessions+1) +'_qual_check.png'), dpi = 600)
        plt.close()

        # Get meta paramaters from filename which would be useful for stats and Viz later
        hrv_variables['Subject_name'] = fname
        hrv_variables['Condition'] = add_on
        hrv_variables['Sequence'] = sessions + 1

        # add the dataframe to the list
        masterlist.append(hrv_variables)

        os.chdir('..')

        #%% Here comes the HEP
        # Adding cleaned ECG trace and identified ECG peak as a STIM
        one_epoch_data = mne.io.RawArray(np.squeeze(epochs[sessions]), info)

        # creating new ECG cleaned channel from signals dataframe
        cleaned_ECG = signals["ECG_Clean"].to_frame().transpose().to_numpy()

        # create a mne raw object of clean ECG using info and raw object
        info_ecg = mne.create_info(ch_names=['cleaned_ECG'],
                                            sfreq = srate,
                                            ch_types='ecg')

        clean_ECG = mne.io.RawArray(cleaned_ECG, info_ecg)

        # adding cleaned ECG channel to edfdata mne object
        one_epoch_data.add_channels([clean_ECG], force_update_info=True)

        # creating a STIM channel based on identified R peaks (it has to be a 2D array)
        flip_dataframe = peaks.transpose()
        stim_data = flip_dataframe.to_numpy()

        info_stim = mne.create_info(['STI'], srate, ['stim'])
        stim_raw = mne.io.RawArray(stim_data, info_stim)

        # force_update_info should be True for STIM channel
        one_epoch_data.add_channels([stim_raw], force_update_info=True)

        # Find the events (R peaks) from STIM channel
        R_peak_events =  mne.find_events(one_epoch_data, stim_channel='STI')

        # Dropping last R peak to prevent final epoch falling short in length
        R_peak_events = R_peak_events[:-1,:]

        # Epoching parameters
        tmin, tmax = -0.2, 0.6
        baseline = (-0.2,0)

        # rejecting bad epochs based on amplitude trheshold
        # reject_criteria = dict(eeg=250e-6) # 100 µV
        # flat_criteria = dict(eeg=1e-6) # 1 µV

        # Epoch the data absed on detected R peak
        HEP_epochs = mne.Epochs(one_epoch_data,
                            events = R_peak_events,
                            tmin = tmin,
                            tmax = tmax,
                            baseline = baseline,
                            detrend=1,
                            reject=None,
                            flat=None,
                            preload = True)

        # Drop bad epochs | Not working due to TOO_SHORT bug
        # HEP_epochs.drop_bad()

        # # log count of bad epochs
        # print(HEP_epochs.drop_log)
        # HEP_epochs.plot_drop_log()

        # plt.savefig(fname + '_' + add_on + '_' + str(sessions+1) + 'Log of bad epochs dropped.png',
        #             dpi = 600,
        #             backend='cairo')

        # plt.close()

        # Average to get HEP
        HEP = HEP_epochs.average()

        # See the HEP
        HEP.plot()

# Creating a dataframe from a list of dataframes
df = pd.concat(masterlist, axis=0)
df = df.reset_index(drop=True)

df.to_csv('hrv_parameters_mastersheet.csv', index=None)

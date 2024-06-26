# read and plot MPSH L2
# B. Kress, Jan. 2021

# standard packages
import sys
from icecream import ic
import matplotlib
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as pyplot
import numpy as np
from netCDF4 import Dataset as NCDataset

matplotlib.rcParams.update({'font.size': 10})
import utils as tsu

ELE_DIFF_CHANS = 10
PRO_DIFF_CHANS = 11
TELESCOPES = 5
ETEL = 2  # 2 is electron telescope #4

# input files
filenamelist = []

### modify items below ###
# RECORDS_PER_FILE = 288
RECORDS_PER_FILE = 1440  # Change this depending on timestamps?

filenamelist.append(
    'C:/Users/sarah.auriemma/Desktop/Data_new/g16/pd/dn_mpsl-l2'
    '-avg1m_g16_d20230227_v2-0-0.nc')

###################

num_input_files = len(filenamelist)
parts = filenamelist[0].split('/')
spacecraft_name = parts[-3].upper()
ic(spacecraft_name)


def mkticks(first_j2000_sec, num_input_files):
    """
    Generate tic locations for every hour and tic labels for every three
    hours for plotting.

    Args:
    first_j2000_sec (float): The J2000 seconds of the first timestamp.
    num_input_files (int): The number of input files.

    Returns:
    tuple: A tuple containing:
        - list: Tic locations for every hour.
        - list: Tic labels for every three hours.
        - str: Year string.
        - str: Month string.
        - str: Day string.
    """
    ticloc = []
    ticstr = []
    current_j2000_sec = first_j2000_sec

    # Assume each file represents one day's worth of data
    for _ in range(num_input_files):
        # Generate hourly ticks for 24 hours
        for hour in range(24):
            ticloc.append(current_j2000_sec + hour * 3600)
            # Add a label every three hours
            if hour % 3 == 0:
                ticstr.append(f'{hour:02d}')
            else:
                ticstr.append('')

        # Move to the next day
        current_j2000_sec += 24 * 3600

    # Convert first and last J2000 seconds to date strings for year, month, day
    first_date_str = str(tsu.j2000_to_posix_0d(first_j2000_sec))
    last_j2000_sec = ticloc[-1]
    last_date_str = str(tsu.j2000_to_posix_0d(last_j2000_sec))

    yearstr = first_date_str[0:4]
    if first_date_str[0:4] != last_date_str[0:4]:
        yearstr += ' - ' + last_date_str[0:4]
    monthstr = first_date_str[5:7]
    daystr = first_date_str[8:10]

    return ticloc, ticstr, yearstr, monthstr, daystr


# ic| nc_file.variables.keys(): dict_keys(['time', 'L1bRecordsInAvg',
# 'yaw_flip_flag', 'EclipseFlag', 'AvgDiffIonFlux', 'AvgDiffIonFluxUncert',
# 'DiffIonValidL1bSamplesInAvg', 'DiffIonDQFdtcSum', 'DiffIonDQFoobSum',
# 'DiffIonDQFerrSum', 'AvgDiffElectronFlux', 'AvgDiffElectronFluxUncert',
# 'DiffElectronValidL1bSamplesInAvg', 'DiffElectronDQFdtcSum',
# 'DiffElectronDQFoobSum', 'DiffElectronDQFerrSum', 'ExpectedLUTNotFound'])

variable_names_arr = ['time', 'AvgDiffIonFlux', 'AvgDiffElectronFlux']
# d_arr = ['time', 'AvgDiffProtonFlux', 'AvgDiffElectronFlux',
# 'DiffElectronEffectiveEnergy', 'AvgIntElectronFlux',
# 'IntElectronEffectiveEnergy']

variable_data = {var_name: [] for var_name in variable_names_arr}

for file in filenamelist:
    nc_file = NCDataset(file, 'r')
    ic(nc_file.variables.keys())
    ic(nc_file['AvgDiffElectronFlux'])

    for var_name in variable_names_arr:
        if var_name in nc_file.variables:
            data = nc_file.variables[var_name][:]
            # variable_fill_value = nc_file.variables[var_name]._FillValue
            variable_fill_value = 1.e-12
            # ic(var_name, variable_fill_value)
            data = np.where(data < variable_fill_value, np.nan, data)

            if var_name == 'time' and len(variable_data[var_name]) > 0:
                # Adjust time values for subsequent files
                last_time = variable_data[var_name][-1]
                time_diff = last_time - data[0]
                data += time_diff

            variable_data[var_name].extend(data)

        elif var_name == 'time' and 'L2_SciData_TimeStamp' in \
                nc_file.variables:
            variable_data[var_name].extend(
                nc_file.variables['L2_SciData_TimeStamp'][:])
        else:
            print(f"Variable '{var_name}' not found in {file}")

for var_name in variable_data:
    variable_data[var_name] = np.array(variable_data[var_name])

TimeStamp = variable_data['time'][:]

ic(variable_data['AvgIntElectronFlux'].shape)
min_value = np.nanmin(variable_data['AvgIntElectronFlux'][:, ETEL])
ic(min_value)

PLOT = 1
if (PLOT == 1):
    # The north-to-south order of telescope numbers is (3, 1, 4, 2, 5) for
    # electrons, where telescope numbers 1-5 correspond to zero-based array
    # indices 0-4 (2nd dim. of flux array) set telescope number
    effec_energy = variable_data['DiffElectronEffectiveEnergy'][ETEL, :]
    # rounded_effec_energy = np.round(effec_energy, 1)

    # mpsh_elabel = np.array(['E1 (69.4 keV)', 'E2 (131. keV)', 'E3 (179.
    # keV)', 'E4 (272. keV)', 'E5 (380. keV)', 'E6 (546. keV)', 'E7 (863
    # keV)', 'E8 (1490. keV)', 'E9 (1700. keV)', 'E10 (2910. keV)', 'E11 (>2
    # MeV)'])

    mpsh_elabel = [f"E{i + 1} ({energy:.1f} keV)" for i, energy in
                   enumerate(effec_energy)]

    # ic(mpsh_elabel)

    etel_label = ["ETel-5", 'ETel-2', 'ETel-4', 'ETel-1', 'ETel-3']

    # mpsh colormap
    from matplotlib import colors

    numcolors = 11
    mpsh_cm = np.empty([numcolors, 3], dtype=np.float64)
    #
    mpsh_cm[0, :] = colors.to_rgba('brown')[0:3]
    mpsh_cm[1, :] = colors.to_rgba('red')[0:3]
    mpsh_cm[2, :] = colors.to_rgba('orange')[0:3]
    # mpsh_cm[3,:] = colors.to_rgba('yellow')[0:3]
    # adjust yellow a little darker
    mpsh_cm[3, :] = [.95, .95, .0]
    mpsh_cm[4, :] = colors.to_rgba('greenyellow')[0:3]
    # mpsh_cm[5,:] = colors.to_rgba('green')[0:3]
    # adjust green a little lighter
    mpsh_cm[5, :] = [0., .7, 0.]
    # mpsh_cm[6,:] = colors.to_rgba('darkcyan')[0:3]
    # adjust a little lighter and greener
    mpsh_cm[6, :] = [0., .78, .76]
    # mpsh_cm[7,:] = colors.to_rgba('blue')[0:3]
    # adjust a little lighter
    mpsh_cm[7, :] = [0.11764706 / 2., 0.56470588 / 2., 1.]
    # mpsh_cm[8,:] = colors.to_rgba('darkviolet')[0:3]
    # [0.58039216, 0., 0.82745098]
    # adjust lighter
    mpsh_cm[8, :] = [0.9, .1, 1.0]
    # mpsh_cm[9,:] = colors.to_rgba('indigo')[0:3]
    # [0.29411765, 0., 0.50980392]]
    # adjust a little lighter
    mpsh_cm[9, :] = [0.49411765, 0., 0.70980392]
    mpsh_cm[10, :] = [0., 0., 0.]

    first_j2000_sec = TimeStamp[0]
    last_j2000_sec = TimeStamp[len(TimeStamp) - 1]

    xmin = first_j2000_sec
    xmax = last_j2000_sec + num_input_files * 6. * 3600.  # make room for
    # legend

    # make tick locations and labels
    HOUR_TICK_OPT = 1  # 0: no hour ticks; 1: tick mark only; 2: tick mark
    # and label
    ticloc, ticstr, yearstr, monthstr0, daystr0 = mkticks(first_j2000_sec,
                                                          num_input_files)
    date_str = yearstr + '/' + monthstr0 + '/' + daystr0
    ic(date_str)
    LFS = 10  # legend text font size

    # plot
    # pyplot.figure(1, figsize=[12, 6])
    pyplot.figure(1)
    pyplot.suptitle(f'{spacecraft_name} MPS-HI {date_str} ', fontsize=14)

    numrow = 4
    numcol = 1
    gridspec.GridSpec(numrow, numcol)

    # plot panel 1
    ax1 = pyplot.subplot2grid((numrow, numcol), (0, 0), colspan=1, rowspan=3)
    AvgDiffElectronFlux = variable_data['AvgDiffElectronFlux']
    for chan in range(ELE_DIFF_CHANS):
        pyplot.plot(TimeStamp[:], AvgDiffElectronFlux[:, ETEL, chan],
                    linewidth=2., color=mpsh_cm[chan], label=mpsh_elabel[chan])
    ymin = 1.E-3
    ymax = 2.E6
    # ymax = 1.2*np.max(TelAvgDiffEleFlux[:,:])
    # ymin = .8*np.min(np.where(TelAvgDiffEleFlux[:,:]>0,TelAvgDiffEleFlux[
    # :,:],ymax))
    pyplot.ylabel(
        etel_label[ETEL] + '\nelectrons/cm$^2$-s-str-keV')
    pyplot.xlim([xmin, xmax])
    pyplot.ylim([ymin, ymax])
    pyplot.yscale('log')
    labels = [item.get_text() for item in ax1.get_xticklabels()]
    empty_string_labels = [''] * len(labels)
    ax1.set_xticklabels(empty_string_labels)
    pyplot.legend(loc='upper right', prop={'size': LFS}, fancybox=True,
                  framealpha=1.0)

    # plot panel 2
    gridspec.GridSpec(5, 1)
    ax2 = pyplot.subplot2grid((numrow, numcol), (3, 0), colspan=1, rowspan=1)
    AvgIntElectronFlux = variable_data['AvgIntElectronFlux']
    pyplot.plot(TimeStamp[:], AvgIntElectronFlux[:, ETEL], linewidth=2.,
                color='k', label=f'MPS-HI E11 (>2 MeV)')
    ymin = 1.E1
    ymax = 1.E4
    # ymax = 1.2*np.max(TelAvgIntEleFlux)
    # ymin = .8*np.min(np.where(TelAvgIntEleFlux>0,TelAvgIntEleFlux,ymax))
    # pyplot.xlabel(yearstr, fontsize=12)
    pyplot.xlabel('UT [hours]')
    pyplot.ylabel(
        f'{spacecraft_name} MPS-HI ' + etel_label[
            ETEL] + '\nelectrons/cm$^2$-s-str')
    pyplot.xlim([xmin, xmax])
    pyplot.ylim([ymin, ymax])
    pyplot.yscale('log')

    pyplot.xticks(ticloc, ticstr, fontsize=10)
    pyplot.legend(loc='lower right', prop={'size': LFS}, fancybox=True,
                  framealpha=.5)
    # pyplot.savefig(
    #     'g16_mpsh_fluxes_' + yearstr + '-' + monthstr0 + '-' + daystr0 +
    #     '.png',
    #     bbox_inches='tight')
    pyplot.show()

import netCDF4 as nc
import argparse
import numpy as np
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import spacepy.coordinates as spcoords
import spacepy.time as spt
import spacepy.omni as omni
from datetime import datetime, timedelta
import os
import pytplot
from pyspedas import sosmag_load


if not "CDF_LIB" in os.environ:
    base_dir = "C:/Scripts/cdf3.9.0"
    os.environ["CDF_BASE"] = base_dir
    os.environ["CDF_BIN"] = base_dir + "/bin"
    os.environ["CDF_LIB"] = base_dir + "/lib"
from plotter import plot_spacecraft_positions_with_earth_and_magnetopause, \
    plot_sc_and_shue_gk2a_bytimediff

RE_EARTH = 6378
GEOSTAT = 6.6  # geostationary orbit - Re

from cdasws import CdasWs

cdas = CdasWs()
from cdasws.datarepresentation import DataRepresentation as dr

# I am using cdas to get omni data, so this is how I found what variables to
# grab
# datasets = cdas.get_datasets(observatoryGroup='OMNI', instrumentType='')
# print(datasets)

# instr = cdas.get_instruments(observatory='OMNI (1AU IP Data)')
# instr = cdas.get_instruments(observatoryGroup='OMNI (1AU IP Data)')
# print(instr)

# obs_groups = cdas.get_observatory_groups()
# for index, obs_group in enumerate(obs_groups):
#     print(obs_group['Name'])

# instr_types = cdas.get_instrument_types()
# for index, instr_type in enumerate(instr_types):
#     print(instr_type['Name'])

# datasets = cdas.get_datasets(observatoryGroup='OMNI (Combined 1AU IP Data)')
# for index, dataset in enumerate(datasets):
#     print(dataset['Id'], dataset['Label'])

# variables = cdas.get_variables('OMNI_HRO_1MIN')
# for variable in variables:
#     print(variable['Name'], " : ", variable['LongDescription'])

# # BZ_GSM, Pressure,
# print("...")
# variables = cdas.get_variables('OMNI2_H0_MRG1HR')
# for variable in variables:
#     print(variable['Name'], variable['LongDescription'])
# var_names = ['BZ_GSE1800', 'BZ_GSM1800', 'Pressure1800']

# var_names = ['BZ_GSM', 'Pressure']

# data = cdas.get_data('OMNI_HRO_1MIN', 'SYM_H', '2023-02-26T00:00:00Z',
#                      '2023-02-27T00:00:00Z', dataRepresentation=dr.XARRAY)[1]
# print(data)
# plt.plot(data.Epoch.values, data.SYM_H.values)
# plt.show()

# print(data)
# print(type(data))
# print(data.BZ_GSM.Epoch.values) # Time
# print(data.BZ_GSM.values) # Data
# print(data.Pressure.values)


# observatories = cdas.get_observatories()

# for obs_info in observatories:
#     print(obs_info['Name'])

# OMNI_1min = 'OMNI_HRO_1MIN'
# variables_to_get = ['BX_GSE', 'BY_GSE', 'BZ_GSE', 'BY_GSM', 'BZ_GSM',
# 'proton_density', 'Vx', 'Vy', 'Vz']
#
# data = cdas.get_data(OMNI_1min, variables=variables_to_get, time0=sdate_s,
# time1=edate_s)
# variables_in_dataset = data[1]


def parse_arguments():
    """
    Parse the command-line arguments.

    Returns:
        argparse.Namespace: The parsed arguments from the command line.
    """
    parser = argparse.ArgumentParser(description="Pass in orbit .nc files")
    parser.add_argument('--g16',
                        type=str,
                        help="Path to g16 orb information (must be .nc file)",
                        required=False)

    parser.add_argument('--g17',
                        type=str,
                        help="Path to g17 orb information (must be .nc file)",
                        required=False)

    parser.add_argument('--g18',
                        type=str,
                        help="Path to g18 orb information (must be .nc file)",
                        required=False)

    # Providing the orb info manually:
    # parser.add_argument('--gk2a',
    #                     type=str,
    #                     help="Path to gk2a orb information",
    #                     required=False)

    # Script will use pyspedas to get orb info:
    parser.add_argument("--gk2a", action='store_true',
                        help="Flag to indicate whether to plot gk2a")

    parser.add_argument('--timestamp',
                        type=str,
                        help="time stamp (as a string) ex. YYYYMMDD HH:MM",
                        required=True)

    return parser.parse_args()


def load_sosmag_positional_data(timestamp_str):
    """
    Load and return SOSMAG/GK2A positional data for a specific timestamp.

    Parameters:
    timestamp_str (str): Timestamp in 'YYYY-MM-DD HH:MM:SS' format.

    Returns:
    pandas.DataFrame: Dataframe containing the positional data.
    """
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')

    start_time = timestamp
    end_time = timestamp + timedelta(minutes=1)

    trange = [start_time.strftime('%Y-%m-%d %H:%M:%S'),
              end_time.strftime('%Y-%m-%d %H:%M:%S')]

    sosmag_load(trange=trange, datatype='1m')

    data_types = list(pytplot.data_quants.keys())
    data_types_array = np.array(data_types)

    # 'pos' is the positional data and always at the same index
    tvar = data_types_array[2] if len(data_types_array) > 2 else None

    if tvar:
        # Extracting data from pytplot's data structure
        positional_data = pytplot.data_quants[tvar].to_pandas()
        print(f'Loaded GK2A positional data for {timestamp_str}')
        return positional_data
    else:
        print(f"GK2A positional data not available for {timestamp_str}")
        return None


def average_of_minute_timestamp_of_GK2A(df):
    """
    Calculate the average of the first and the middle data points in a
    DataFrame.

    This function is designed to work with a DataFrame where each row
    represents
    a timestamp of GK2A positional data. It calculates the average of the data
    at the first timestamp and the data at the middle timestamp of the
    DataFrame.

    Parameters:
    df (pandas.DataFrame): DataFrame containing the positional data,
                           with each row representing a timestamp.

    Returns:
    pandas.Series: A series containing the average of the first and middle
    data points.
                   Returns None if the DataFrame is empty.

    Note:
    The function assumes that the DataFrame has an even number of rows. If
    the number
    of rows is odd, the function will use the lower middle row for the
    calculation.
    """
    if df.empty:
        print("The DataFrame is empty.")
        return None

    length_of_df = len(df.index)
    halfway_of_df = length_of_df // 2

    first_timestamp_data = df.iloc[0]
    middle_timestamp_data = df.iloc[halfway_of_df]
    average_data = (first_timestamp_data + middle_timestamp_data) / 2
    return average_data


def get_omni_values(date_str, hour, startminute, endminute):
    """
    Get BZ_imf and solar wind pressure from OMNI data.

    Parameters:
        date_str (str): Date in 'YYYY-MM-DD' format.
        time_input (int or tuple): Single minute or a range of minutes.
        is_single_minute (bool): Flag indicating if the input is a single
        minute.

    Returns:
        tuple: (BZ_imf, solar_wind_pressure)
    """

    if startminute == endminute:
        start_time = f"{date_str}T{hour}:{startminute}:00Z"
        end_time = f"{date_str}T{hour}:{endminute + 1}:00Z"
    else:
        start_time = f"{date_str}T{hour}:{startminute}:00Z"
        end_time = f"{date_str}T{hour}:{endminute}:00Z"

    data = cdas.get_data('OMNI_HRO_1MIN', ['BZ_GSM', 'Pressure'], start_time,
                         end_time, dataRepresentation=dr.XARRAY)[1]

    pressure_values = data.Pressure.values
    average_pressure = np.nanmean(pressure_values)
    max_pressure = np.nanmax(pressure_values)
    min_pressure = np.nanmin(pressure_values)

    print('BZ_imf: ')
    print(data.BZ_GSM.values)
    print('Pressure: ')
    print(pressure_values)

    print(f"Average Pressure: {average_pressure}")
    print(f"Maximum Pressure: {max_pressure}")
    print(f"Minimum Pressure: {min_pressure}")

    bz_imf = data.BZ_GSM.values[
        0] if 'BZ_GSM' in data and data.BZ_GSM.values.size > 0 else np.nan
    sw_pressure = data.Pressure.values[
        0] if 'Pressure' in data and data.Pressure.values.size > 0 else np.nan

    return bz_imf, sw_pressure


def j2000_to_datetime(timestamp):  # for sosmag data
    epoch = pd.to_datetime('2000-01-01 00:00:00')
    time_datetime = epoch + pd.to_timedelta(timestamp, unit='s')
    return time_datetime


def goes_epoch_to_datetime(timestamp):  # for GOES data
    epoch = pd.to_datetime('2000-01-01 12:00:00')
    time_datetime = epoch + pd.to_timedelta(timestamp, unit='s')
    return time_datetime


def gse_to_earth(pos, alpha=np.radians(23.5)):
    """
    Convert coordinates from GSE to Earth-centered.

    Parameters:
        pos (array-like): The position in GSE coordinates.
                          Should be an array-like structure with shape (n, 3).
        alpha (float): Rotation angle in radians. Default is 0.

    Returns:
        np.ndarray: The converted coordinates in Earth-centered system.
    """
    pos = np.array(pos)  # make sure input is a numpy array
    x_gse, y_gse, z_gse = pos[:, 0], pos[:, 1], pos[:, 2]

    x = x_gse * np.cos(alpha) + y_gse * np.sin(alpha)
    y = -x_gse * np.sin(alpha) + y_gse * np.cos(alpha)
    z = z_gse

    return np.column_stack((x, y, z))


def apply_GSE_nparraystack(pos):
    """
    Convert coordinates from GSE to Earth-centered.

    Parameters:
        pos (array-like): The position in GSE coordinates.
                          Should be an array-like structure with shape (n, 3).
        alpha (float): Rotation angle in radians. Default is 0.

    Returns:
        np.ndarray: The converted coordinates in Earth-centered system.
    """
    pos = np.array(pos)  # make sure input is a numpy array
    x_gse, y_gse, z_gse = pos[:, 0], pos[:, 1], pos[:, 2]

    x = x_gse
    y = y_gse
    z = z_gse

    return np.column_stack((x, y, z))

def apply_gse_to_earth_to_dict(coordinates_dict):
    transformed_coordinates = {}
    for satellite, coords in coordinates_dict.items():
        coord_values = np.array([[coords['X'], coords['Y'], coords['Z']]])
        earth_coords = apply_GSE_nparraystack(coord_values)

        # print(f"Original: {coords}, Transformed: {earth_coords}")  #
        # Debugging line

        transformed_coordinates[satellite] = {
            'X': earth_coords[0, 0],
            'Y': earth_coords[0, 1],
            'Z': earth_coords[0, 2]
        }
    return transformed_coordinates

def convert_GSE_from_GK2A_csv(spc_coords_file, hour):
    # gk2a_data = pd.read_csv(satellite_file)
    # # Ensure the 'time' column is in the correct format
    # # Modify the format string as needed to match your CSV data
    # gk2a_data['time'] = pd.to_datetime(gk2a_data['time'],
    #                                    format='%Y%m%d %H:%M:%S.%f')
    # # Filter the data
    # gk2a_data = gk2a_data[gk2a_data['time'].dt.hour == hour]
    # satellite_data = gk2a_data

    spc_coords = pd.read_csv(spc_coords_file)
    spc_coords['time'] = pd.to_datetime(spc_coords['time'],
                                        format='%Y-%m-%d %H:%M:%S.%f')
    spc_coords.set_index('time', inplace=True)
    spc_coords = spc_coords.resample('T').first().reset_index()

    spc_coords = spc_coords[spc_coords['time'].dt.hour == hour]

    x, y, z = spc_coords['0'], spc_coords['1'], spc_coords['2']
    # x, y, z = -14662.438, 35796.366, -16770.182

    spc_coords_df = pd.DataFrame(
        {'time': spc_coords['time'], 'X': x, 'Y': y, 'Z': z})

    return spc_coords_df


def convert_and_filter_gse_by_timestamp(spc_coords_file, timestamp):
    """
    Convert GSE (Geocentric Solar Ecliptic) coordinates to GSM (Geocentric
    Solar Magnetospheric)
    coordinates and filter the data based on a specific timestamp.

    This function reads GSE coordinates from a .nc (NetCDF) file, converts
    them to GSM coordinates,
    and filters these coordinates to include data only at the specified
    timestamp.

    Parameters:
        spc_coords_file (str): Path to the spc_coords file (must be a .nc
        file).
        timestamp_str (str): Timestamp in the format 'YYYYMMDD HH:MM' to
        filter the coordinates.

    Returns:
        pandas.DataFrame: DataFrame containing columns [time, Xgsm, Ygsm,
        Zgsm],
                          where Xgsm, Ygsm, Zgsm are the GSM coordinates in
                          RE units.
                          The 'time' column contains datetime objects.
    """

    spc_coords = nc.Dataset(spc_coords_file)
    spcCoords_time = goes_epoch_to_datetime(
        spc_coords['time'][:]).to_pydatetime().tolist()
    tickz = spt.Ticktock(spcCoords_time, 'UTC')

    x, y, z = spc_coords['gse_xyz'][:, 0], spc_coords['gse_xyz'][:, 1], \
        spc_coords['gse_xyz'][:, 2]
    pos_gse = np.column_stack((x, y, z))
    pos_gse_coords = spcoords.Coords(pos_gse, 'GSE', 'car', ticks=tickz)

    # pos_x_gse, pos_y_gse, pos_z_gse = pos_gse_coords.x[:],
    # pos_gse_coords.y[:], pos_gse_coords.z[:]
    # spc_coords_df = pd.DataFrame({'time': spcCoords_time, 'X': pos_x_gse,
    # 'Y': pos_y_gse, 'Z': pos_z_gse})
    # Filter coordinates based on hour
    # spc_coords_df['hour'] = spc_coords_df['time'].apply(lambda x: x.hour)
    # filtered_coords_df = spc_coords_df[(spc_coords_df['hour'] ==
    # hour)].drop(columns=['hour'])

    spc_coords_df = pd.DataFrame(
        {'time': spcCoords_time, 'X': pos_gse_coords.x, 'Y': pos_gse_coords.y,
         'Z': pos_gse_coords.z})
    filtered_coords_df = spc_coords_df[spc_coords_df['time'] == timestamp]

    return filtered_coords_df

def process_sat_data_inputs(args):
    """
        Process the satellite data files based on the provided command-line
        arguments.

        Parameters:
            args (argparse.Namespace): Parsed command-line arguments.

        Returns:
            dict: Dictionary containing satellite data with satellite names
            as keys.
    """
    timestamp = datetime.strptime(args.timestamp, '%Y%m%d %H:%M')
    date_str_for_filesearch = args.timestamp[:8]

    satellites_data = {}

    # Process gk2a data if the flag is set
    if args.gk2a:
        satellite_data = load_sosmag_positional_data(timestamp)
        gk2a_data = average_of_minute_timestamp_of_GK2A(satellite_data)
        satellites_data['gk2a'] = np.vstack(gk2a_data.to_numpy())

    # List of other satellites
    satellites = {
        'g16': args.g16,
        'g17': args.g17,
        'g18': args.g18
    }

    for satellite_name, satellite_file in satellites.items():
        if satellite_file:
            satellite_data = convert_and_filter_gse_by_timestamp(
                satellite_file, args.timestamp)
            satellites_data[satellite_name] = np.vstack(
                satellite_data.to_numpy())
        else:
            print(f"No file provided for {satellite_name}.")

    return satellites_data

def user_selection_criteria(satellites_data, date_str, hour):
    """
    Prompt the user to enter minute(s) as selection criteria.

    Parameters:
        satellites_data (dict): Dictionary containing satellite data.
        date_str (str): Date string in 'YYYYMMDD' format.
        hour (int): Hour of the data.
    """

    user_input = input(
        "Enter a minute (e.g., '30') or a range of minutes (e.g., '02-15'): ")

    if '-' in user_input:
        start_minute, end_minute = map(int, user_input.split('-'))
        return process_time_range(satellites_data, date_str, hour,
                                  start_minute,
                                  end_minute), start_minute, end_minute
    else:
        minute = int(user_input)
        return process_single_minute(satellites_data, date_str, hour,
                                     minute), minute, minute

def process_time_range(satellites_data, date_str, hour, start_minute,
                       end_minute):
    """
    Process and average the data within a specified time range.

    Parameters:
        satellites_data (dict): Dictionary containing satellite data.
        date_str (str): Date string in 'YYYYMMDD' format.
        hour (int): Hour of the data.
        start_minute (str): Start minute of the range.
        end_minute (str): End minute of the range.
    """
    start_timestamp = pd.to_datetime(f"{date_str} {hour}:{start_minute}:00")
    end_timestamp = pd.to_datetime(f"{date_str} {hour}:{end_minute}:00")

    coordinates_dict = {}

    for satellite_name, data in satellites_data.items():
        data['time'] = pd.to_datetime(data['time'])

        # filter data based on the timestamp range
        filtered_data = data[(data['time'] >= start_timestamp) & (
                    data['time'] <= end_timestamp)]

        # make sure filtered data is not empty before computing mean
        if not filtered_data.empty:
            average_data = filtered_data.mean()
            coordinates_dict[satellite_name] = average_data[
                ['X', 'Y', 'Z']].to_dict()

    # print(coordinates_dict)
    return coordinates_dict

def process_single_minute(satellites_data, date_str, hour, minute):
    """
    Output the data for each satellite at a single minute.

    Parameters:
        satellites_data (dict): Dictionary containing satellite data.
        date_str (str): Date string in 'YYYYMMDD' format.
        hour (int): Hour of the data.
        minute (str): The specified minute.
    """
    target_timestamp = pd.to_datetime(f"{date_str} {hour}:{minute}:00")

    coordinates_dict = {}

    for satellite_name, data in satellites_data.items():

        data['time'] = pd.to_datetime(data['time'])

        specific_data = data[data['time'] == target_timestamp]
        if not specific_data.empty:
            specific_data = specific_data.iloc[0]
            coordinates_dict[satellite_name] = specific_data[
                ['X', 'Y', 'Z']].to_dict()

    # print(coordinates_dict)
    return coordinates_dict


def transform_spacecraft_data(satellites_data):
    """
    Transform spacecraft data into a dictionary format for plotting.

    Parameters:
        satellites_data (numpy.ndarray): Array containing the stacked
        spacecraft data.
                                        Expected format: Each row represents
                                        a satellite,
                                        with columns for X, Y,
                                        and Z coordinates.

    Returns:
        dict: Dictionary with satellite names as keys and coordinate data as
        values.
    """
    transformed_dict = {}
    satellites = ['g17', 'g18', 'gk2a',
                  'g16']  # List of satellite names in the order they appear
    # in the data

    for i, satellite in enumerate(satellites):
        # Extract coordinates for each satellite
        coords = {'X': satellites_data[i, 0], 'Y': satellites_data[i, 1],
                  'Z': satellites_data[i, 2]}
        transformed_dict[satellite] = coords

    return transformed_dict


def main():
    args = parse_arguments()

    # if args.gk2a:
    #     print("Finding gk2a position.")
    #     # Code to find the gk2a position
    # else:
    #     print("User did not want gk2a plotted.")

    satellites_data = process_sat_data_inputs(args)
    transformed_dict = transform_spacecraft_data(satellites_data)

    timestamp_for_OMNI_title = args.timestamp

    date_str = args.timestamp[:8]
    hour = datetime.strptime(args.timestamp, '%Y%m%d%H').hour

    # gk2a_data = average_of_minute_timestamp_of_GK2A(
    #     load_sosmag_positional_data('2023-02-27 11:00'))
    # print(gk2a_data)
    #
    # gk2a_array = gk2a_data.to_numpy()
    # gk2a_stacked = np.vstack(gk2a_array)
    # print(gk2a_stacked)

    # User selects data based on their criteria

    # coordinates_dict, start_minute, end_minute = user_selection_criteria(
    #     satellites_data, date_str, hour)

    # timestamp_str_with_minute = args.timestamp + f'{start_minute:02d}'
    # timestamp_for_OMNI_title = datetime.strptime(timestamp_str_with_minute,
    #                                              '%Y%m%d%H%M')

    # Transform the selected coordinates from GSE to Earth-centered system
    # transformed_dict = apply_gse_to_earth_to_dict(coordinates_dict)

    # imf_bz, solar_wind_pressure = get_omni_values(date_str, hour,
    # start_minute,
    #                                               end_minute)

    # print('TIMESTAMP: ', timestamp_notnan)
    imf_bz, solar_wind_pressure = -13.75, 6.86

    # Now, you can use the plotting function from plotting.py
    # plot_spacecraft_positions_with_earth_and_magnetopause(
    # transformed_dict, solar_wind_pressure, imf_bz, timestamp_for_OMNI_title)
    plot_sc_and_shue_gk2a_bytimediff(transformed_dict, solar_wind_pressure,
                                     imf_bz, timestamp_for_OMNI_title)


if __name__ == "__main__":
    main()

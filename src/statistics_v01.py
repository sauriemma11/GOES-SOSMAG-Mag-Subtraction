import utils
import data_loader
import pandas as pd
from plotting import plotter

# # Load kp data:
# kp_data_txt_path = 'C:/Users/sarah.auriemma/Desktop/Data_new/kp_2019.txt'
# dfkp = kp.readKpData(kp_data_txt_path)
# dfkp['Time'] = pd.to_datetime(dfkp['Time'])

model_str = 'T89'
sosmag_pickle_dir = 'C:/Users/sarah.auriemma/Desktop/Data_new/6month_study' \
                    '/sosmag'
g17_pickle_dir = 'C:/Users/sarah.auriemma/Desktop/Data_new/6month_study/g17'

# Define the start and end dates for your desired date range
start_date = pd.to_datetime('2019-05-14')
end_date = pd.to_datetime('2019-05-15')

# Load and trim GK2A data
gk2a_time_list, gk2a_data_list, gk2a_89_model_list, gk2a_89_subtr_list = \
    data_loader.load_and_trim_data(
        sosmag_pickle_dir, start_date, end_date)

# Load and trim GOES-17 data
g17_time_list, g17_data_list, g17_89_model_list, g17_89_subtr_list = \
    data_loader.load_and_trim_data(
        g17_pickle_dir, start_date, end_date)


#
# gk2a_time_list = []
# gk2a_data_list = []
# gk2a_89_subtr_list = []
#
# g17_time_list = []
# g17_data_list = []
# g17_89_subtr_list = []
#
# # Load GK2A data
# for filename in os.listdir(sosmag_pickle_dir):
#     if filename.endswith('.pickle'):
#         file_path = os.path.join(sosmag_pickle_dir, filename)
#         time, ts89_gse, sat_gse = \
#             data_loader.load_model_subtr_gse_from_pickle_file(
#             file_path)
#         gk2a_time_list.extend(time)
#         gk2a_89_subtr_list.extend(ts89_gse)
#         gk2a_data_list.extend(sat_gse)
#
# # Load GOES-17 data
# for filename in os.listdir(g17_pickle_dir):
#     if filename.endswith('.pickle'):
#         file_path = os.path.join(g17_pickle_dir, filename)
#         time, ts89_gse, sat_gse = \
#             data_loader.load_model_subtr_gse_from_pickle_file(
#                 file_path)
#         g17_time_list.extend(time)
#         g17_89_subtr_list.extend(ts89_gse)
#         g17_data_list.extend(sat_gse)
#
# gk2a_time_list = [pd.to_datetime(time) for time in gk2a_time_list]
# g17_time_list = [pd.to_datetime(time) for time in g17_time_list]
###################

# TODO: fix error handling
if len(g17_data_list) == len(gk2a_data_list):
    pass
else:
    print('raise error: len not equal')

# Get |B| from data using utils
gk2a_total_mag_field_model = [utils.calculate_total_magnetic_field(*point)
                              for point in gk2a_89_model_list]
g17_total_mag_field_model = [utils.calculate_total_magnetic_field(*point)
                             for point in g17_89_model_list]

gk2a_total_mag_field_modelsub = [utils.calculate_total_magnetic_field(*point)
                                 for point in gk2a_89_subtr_list]
g17_total_mag_field_modelsub = [utils.calculate_total_magnetic_field(*point)
                                for point in g17_89_subtr_list]

gk2a_total_mag_field = [utils.calculate_total_magnetic_field(*point) for point
                        in gk2a_data_list]
g17_total_mag_field = [utils.calculate_total_magnetic_field(*point) for point
                       in g17_data_list]


mean_difference_g17_obsvsmodel, standard_deviation_g17_obsvsmodel = \
    utils.mean_and_std_dev(
    g17_total_mag_field_model, g17_total_mag_field)
mean_difference_gk2a_obsvsmodel, standard_deviation_gk2a_obsvsmodel = \
    utils.mean_and_std_dev(
    gk2a_total_mag_field_model, gk2a_total_mag_field)

print(f'g17 |B| (GSE) obsv vs {model_str} model')
print('bottom left sub plot')
print(f'Mean Difference: {mean_difference_g17_obsvsmodel} nT')
print(f'Standard Deviation: {standard_deviation_g17_obsvsmodel} nT')
print('---------------')
print(f'gk2a |B| (GSE) obsv vs {model_str} model')
print('bottom right sub plot')
print(f'Mean Difference: {mean_difference_gk2a_obsvsmodel} nT')
print(f'Standard Deviation: {standard_deviation_gk2a_obsvsmodel} nT')
print('---------------')

# plt.plot(gk2a_time_list, gk2a_total_mag_field_modelsub,
#          label=f'gk2a {model_str} removed')
# plt.plot(gk2a_time_list, gk2a_total_mag_field, label='gk2a gse')
# plt.legend()
# plt.title('GK2A |B|')
# plt.show()
#
# plt.plot(g17_time_list, g17_total_mag_field_modelsub, label=f'g17 {
# model_str} removed')
# plt.plot(g17_time_list, g17_total_mag_field, label='g17 gse')
# plt.legend()
# plt.title('G17 |B|')
# plt.show()


plotter.plot_components_vs_t89_with_color('G17', g17_data_list,
                                          g17_89_subtr_list, g17_time_list,
                                          model_str)
plotter.plot_components_vs_t89_with_color('GK2A', gk2a_data_list,
                                          gk2a_89_subtr_list, gk2a_time_list,
                                          model_str)

# plotter.plot_4_scatter_plots_with_color(
#     g17_total_mag_field, g17_total_mag_field_model, g17_time_list,
#     gk2a_total_mag_field, gk2a_total_mag_field_model, gk2a_time_list,
#     model_used=model_str,
#     output_file=None, best_fit=True, is_model_subtr=False)

# plotter.plot_4_scatter_plots_with_color(
#     g17_total_mag_field, g17_total_mag_field_modelsub, g17_time_list,
#     gk2a_total_mag_field,
#     gk2a_total_mag_field_modelsub, gk2a_time_list, model_used=model_str,
#     output_file=None,
#     best_fit=True, is_model_subtr=True)


mean_difference_subtrvssubtr, standard_deviation_subtrvssubtr = \
    utils.mean_and_std_dev(
        g17_total_mag_field_modelsub, gk2a_total_mag_field_modelsub)
mean_diff_modelvsmodel, stddev_modelvsmodel = utils.mean_and_std_dev(
    g17_total_mag_field_model, gk2a_total_mag_field_model)
# print(f'(g17 - {model_str} model) vs (gk2a - {model_str} model)')
# print('top left plot, model removed from data')
# print(f'Mean Difference: {mean_difference_subtrvssubtr} nT')
# print(f'Standard Deviation: {standard_deviation_subtrvssubtr} nT')
# print('---------------')
print(f'(g17 {model_str}) vs (gk2a {model_str})')
print('top left plot, just estimated model vs model')
print(f'Mean Difference: {mean_diff_modelvsmodel} nT')
print(f'Standard Deviation: {stddev_modelvsmodel} nT')
print('---------------')

mean_difference_g17_obsvsmodel_sub, standard_deviation_g17_obsvsmodel_sub = \
    utils.mean_and_std_dev(
        g17_total_mag_field_modelsub, g17_total_mag_field)
mean_difference_gk2a_obsvsmodel_sub, standard_deviation_gk2a_obsvsmodel_sub = \
    utils.mean_and_std_dev(
        gk2a_total_mag_field_modelsub, gk2a_total_mag_field)

print(f'g17 |B| (GSE) obsv vs g17 |B| with {model_str} removed')
print('bottom left sub plot, model removed')
print(f'Mean Difference: {mean_difference_g17_obsvsmodel_sub} nT')
print(f'Standard Deviation: {standard_deviation_g17_obsvsmodel_sub} nT')
print('---------------')
print(f'gk2a |B| (GSE) obsv vs gk2a |B| with {model_str} removed')
print('bottom right sub plot, model removed')
print(f'Mean Difference: {mean_difference_gk2a_obsvsmodel_sub} nT')
print(f'Standard Deviation: {standard_deviation_gk2a_obsvsmodel_sub} nT')
print('---------------')

# Use the function to calculate stats
# hourly_stats = utils.calc_stats(gk2a_time_list,
# gk2a_total_mag_field_modelsub, g17_total_mag_field_modelsub)
# hourly_stats = utils.calc_stats(gk2a_time_list,
# gk2a_total_mag_field_modelsub, g17_total_mag_field_modelsub, 'H')
# print(hourly_stats)


# TODO: add if __name__ == '__main__' to avoid running on import

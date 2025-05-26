from py.e.eval_linear_regresion import get_plot_prop, std_dev_and_residuals
from py.u.utils_data_plotting import dict_plotter, title_generator_refactor, get_root_dir_path
from py.calc.generate_samples import sample_generation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator
import os
from pathlib import Path
import re
import pandas as pd


def code_comparison(first_file_path:str, second_file_path:str, filter_key:str, angle:int, steel_grade:int, m_el_perc:float, n_perc:float, nrd_direction:str) -> None:



    first_data_set = sample_generation(first_file_path, nrd_direction, m_el_perc, n_perc, steel_grade, angle)

    second_data_set = sample_generation(second_file_path, nrd_direction, m_el_perc, n_perc, steel_grade, angle)

    if not first_data_set or  not second_data_set:
        print(f'Comparison is stopped data cant be generated')
        return

    f_c_stand = first_data_set[0].conn_setup.code_standard
    s_c_stand = second_data_set[0].conn_setup.code_standard


    conn_type:str = first_data_set[0].conn_setup.conn_type
    steel_grade:str = str(round(first_data_set[0].conn_setup.steel_grade, 0) / 1e6)
    angle_of_conn:str = str(first_data_set[0].conn_setup.c_angle)


    parent_path_lin_reg = Path(get_root_dir_path()/ 'plots' / 'code_to_code'/ 'lin_reg'/ 'overleaf' /
                       (f_c_stand + ' '
                        + s_c_stand + ' '
                        + conn_type + ' '
                        + f' steel S{steel_grade}'
                        + f' angle {angle}'
                        + f' n {n_perc}'
                        + f' m {m_el_perc}'))

    parent_path = Path(get_root_dir_path()/ 'plots' / 'code_to_code'/ 'detailed'/
                       (f_c_stand + ' '
                        + s_c_stand + ' '
                        + conn_type + ' '
                        + f' steel S{steel_grade}'
                        + f' angle {angle}'
                        + f' n {n_perc}'
                        + f' m {m_el_perc}'))

    same_setup = []

    # Create a dictionary for faster lookups
    first_code_dict = {sample.my_sql_key: sample for sample in first_data_set}

    # Iterate through new_code and compare with old_code using dictionary lookup
    for second in second_data_set:
        first = first_code_dict.get(second.my_sql_key)
        if first:
            data_to_compare = {
                'name': second.my_sql_key,
                'd0': second.conn_setup.chord.d,
                't0': second.conn_setup.chord.t,
                'd1': second.conn_setup.conn_member.d,
                't1': second.conn_setup.conn_member.t,
                "fy": second.conn_setup.steel_grade,
                'angle': second.conn_setup.c_angle,
                'comparison': (first.results.Nrd / second.results.Nrd),
                'betta': (second.conn_setup.conn_member.d / second.conn_setup.chord.d),
                "gamma": (second.conn_setup.chord.d / (2 * second.conn_setup.chord.t)),
                'conn_type': second.conn_setup.conn_type,
                'first_code_res': first.results.Nrd,
                'second_code_res':second.results.Nrd

            }
            same_setup.append(data_to_compare)


    code_to_compare, plot_res_label = title_generator_refactor(f_c_stand, s_c_stand, conn_type, steel_grade, angle_of_conn, m_el_perc, n_perc, nrd_direction)

    #dict_plotter(same_setup, filter_key, code_to_compare, plot_res_label, parent_path)

    code_lin_reg(same_setup, parent_path_lin_reg, f_c_stand, s_c_stand, conn_type, angle, steel_grade, m_el_perc, n_perc)

    return


def code_lin_reg(dict_calculated:list[dict], parent_path:Path,first_code:str, second_code: str, conn_type: str, angle:int, steel_grade:str, m_el_perc:float, n_perc:float):

    plot_style: dict = get_plot_prop()
    conn_type = re.sub(r"[_]", " ", conn_type)
    first_code = re.sub(r"[_]", " ", first_code)
    second_code = re.sub(r"[_]", " ", second_code)

    b_data = 0

    index: int = -1

    first_code_list = []
    second_code_list = []

    for i in dict_calculated:
        index += 1
        comparison = i['comparison']

        first_code_list.append(round((i['first_code_res'] / 1e3), 1))
        second_code_list.append(round((i['second_code_res'] / 1e3), 1))

        b_data += comparison

    b = b_data / (index + 1)

    idea_y = np.array(first_code_list)
    analy_x = np.array(second_code_list)

    # Sort the data by analy_x
    sorted_indices = np.argsort(analy_x)
    analy_x_sorted = analy_x[sorted_indices]
    idea_y_sorted = idea_y[sorted_indices]

    lin_reg = np.polyfit(analy_x_sorted, idea_y_sorted, 1)[0]

    analy_x_sorted_reshaped = analy_x_sorted.reshape(-1, 1)
    lin_reg, _, _, _ = np.linalg.lstsq(analy_x_sorted_reshaped, idea_y_sorted, rcond=None)

    slope_list = [
        #b,
        lin_reg[0]]

    for slope in slope_list:

        statistical_res = std_dev_and_residuals(analy_x_sorted, idea_y_sorted, slope)

        # Generate a regression line starting from 0 (y = mx)
        x_line = np.linspace(0, max(analy_x_sorted), 100)  # X values for the line
        y_line = slope * x_line  # Y values based on the slope

        plt.figure(figsize=(8, 5))

        # Scatter plot using the dictionary style
        plt.plot(analy_x_sorted, idea_y_sorted, plot_style["scatter"]["marker"],
                 label=f"Resistance [kN], number of the calculations: {(len(analy_x_sorted))}",
                 color=plot_style["scatter"]["color"],
                 markersize=plot_style["scatter"]["markersize"],
                 markeredgecolor=plot_style["scatter"]["markeredgecolor"],
                 markeredgewidth=plot_style["scatter"]["markeredgewidth"])

        # Regression line using the dictionary style
        plt.plot(x_line, y_line,
                 label=(f"Linear Regression Line (slope={slope:.2f}, "
                        f"$R^2$ = {statistical_res['r_squared']:.3f} )"
                        ),
                 color=plot_style["regression_line"]["color"],
                 linewidth=plot_style["regression_line"]["linewidth"],
                 linestyle=plot_style["regression_line"]["linestyle"])

        ax = plt.gca()
        ax.grid(plot_style["grid"])

        x_max_resistance = int(np.max(analy_x_sorted))
        y_max_resistance = int(np.max(idea_y_sorted))
        lim_max_resistance = max(x_max_resistance, y_max_resistance)

        # Determine axis limits and tick spacing (locator) based on the range:
        if lim_max_resistance >= 4000:
            # For very high values, round up to the next thousand.
            lim_max_resistance = ((lim_max_resistance // 1000) + 1) * 1000
            locator = MultipleLocator(1000)
        elif 1500 <= lim_max_resistance < 4000:
            # For intermediate values:
            # Option 1: you might want to round up to a friendly number:
            lim_max_resistance = ((lim_max_resistance // 250) + 1) * 250
            locator = MultipleLocator(250)
        elif 500 <= lim_max_resistance < 1500:
            # For moderately high values:
            lim_max_resistance = ((lim_max_resistance // 125) + 1) * 125
            locator = MultipleLocator(125)
        elif 250 <= lim_max_resistance < 500:
            lim_max_resistance = 600  # fixed upper limit for this range
            locator = MultipleLocator(100)
        elif 0 <= lim_max_resistance < 250:
            lim_max_resistance = 250
            locator = MultipleLocator(50)

        # Set axis limits and tick locators:
        ax.set_xlim(0, lim_max_resistance)
        ax.set_ylim(0, lim_max_resistance)
        ax.xaxis.set_major_locator(locator)
        ax.yaxis.set_major_locator(locator)

        # Adding labels and title
        plt.xlabel(f'{second_code} {conn_type} (kN)')
        plt.ylabel(f'{first_code} {conn_type} (kN)')
        steel_grade_int = int(float(steel_grade))

        if slope == b:
            plot_name = f'Relationship between {first_code} and  {second_code} {conn_type} S{(steel_grade)} {angle}, slope is b'

        else:
            plot_name = (
                f"Relation {first_code} and {second_code}, {conn_type}, "
                f"S{steel_grade_int if steel_grade_int is not None else ''}, "
                f"{angle if angle is not None else angle}°, load $m_{{el}}$: "
                f"{str(m_el_perc*100) + '%' if m_el_perc is not None else ''}, "
                f"n: {str(n_perc*100) + '%' if n_perc is not None else ''}"
            )

        plt.title(plot_name)

        # Adding grid and legend
        plt.grid(True)
        plt.legend(loc="upper left")

        absolute_path = parent_path

        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)

        df = pd.DataFrame({
            'Fpr EN': analy_x_sorted,
            'EN': idea_y_sorted,

        })

        df.to_excel((parent_path / 'excel.xlsx'), index=False)


        plot_name = re.sub(r"[$:{}%]", "", plot_name)

        plot_name = re.sub(r"[ ]", "_", plot_name)

        plot_save_name = (absolute_path /f'{plot_name}.png')


        plt.savefig(plot_save_name, dpi=300)
        print(f"Lin reg filename {plot_name} is printed")
        plt.close()

    return


if __name__ == '__main__':

    # angles = [30,45]
    # steels = [235]
    # n_percs = [-0.8 ]
    # conn_types = ['CHS_X']
    #
    #
    # for angle in angles:
    #     for steel in steels:
    #         for perc in n_percs:
    #             for conn_type in conn_types:
    #
    #                 f_path = os.path.join('../../Code_Config_yaml/EN' , (conn_type + '.yaml'))
    #                 s_path = os.path.join('../../Code_Config_yaml/Fpr_EN' , (conn_type + '.yaml'))
    #
    #                 code_comparison(f_path, s_path, 'd0', angle, steel, 0, perc, '-')

    code_comparison('../../Code_Config_yaml/EN/CHS_T_and_Y.yaml', '../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 'd0', 45, 460, 0, (-0.8), '-')
import copy

import matplotlib.pyplot as plt
import numpy as np
import os

from eval_res_to_diff_code import calc_res_from_calculated, dict_generator
from matplotlib.ticker import MultipleLocator
from pathlib import Path
from typing import  Union

from src.calc.base_classes import MainCalculationInfo
from src.e.eval_res_to_diff_code import duplicates_filtering
from src.u.utilis_plastic_strain_investigation import plot_comparison_with_plastic_strains, \
    plot_analyzes_percentage_histogram
from src.u.utils_data_plotting import get_root_dir_path, params_for_plot_pdf_save
import re



def get_plot_prop():
    # Define plot styling settings as a dictionary
    plot_style = {
    "scatter": {
        "color": "purple",  # Blue color for scatter points
        "marker": "o",  # Circle marker
        "markersize": 4,
        "markeredgecolor": 'black',
        'markeredgewidth': 0.25
    },
    "regression_line": {
        "color": "red",  # Red color for regression line
        "linewidth": 2,
        "linestyle": "-"  # Solid line style for regression line
    },
    "axis_labels": {
        "fontsize": 10,
        "fontweight": None
    },
    "title": {
        "fontsize": 9,
        "fontweight": None,
        "pad": 10
    },
    "ticks": {
        "fontsize": 9
    },
    "legend": {
        "loc": "upper left",
        "fontsize": 9
    },
    "grid": True  # Grid is turned off
    }

    return plot_style

def std_dev_and_residuals(analy_x: np.array, idea_y: np.array, slope:Union[np.ndarray|float]) -> dict:

    sorted_indices = np.argsort(analy_x)
    analy_x_sorted = analy_x[sorted_indices]
    idea_y_sorted = idea_y[sorted_indices]

    # to be valid also for b
    lin_reg = np.array(slope)

    # Calculate residuals (difference between actual and predicted values)
    residuals = idea_y_sorted - (lin_reg * analy_x_sorted)

    # Standard deviation of the residuals
    std_dev_residuals = np.std(residuals)

    # Total variance (sum of squared differences from the mean)
    total_variance = np.sum((idea_y_sorted - np.mean(idea_y_sorted)) ** 2)

    # Residual variance (sum of squared residuals)
    residual_variance = np.sum(residuals ** 2)

    # R² (Coefficient of Determination)
    r_squared = 1 - (residual_variance / total_variance)

    # Store results in a dictionary
    result_dict = {
        "std_dev_residuals": std_dev_residuals,
        "r_squared": r_squared,
        "slope": lin_reg
    }

    # Return the result dictionary
    return result_dict


def get_different_color(file_path: str, plot_prop:dict):

    code_standard = Path(file_path).parent.name

    if code_standard == "EN":
        plot_prop['scatter']['color'] = 'blue'

    elif code_standard == "AISC":
        plot_prop['scatter']['color'] = 'yellow'

    elif code_standard == 'Fpr_EN':
        plot_prop['scatter']['color'] = 'lime'

    else:
        raise KeyError(f"Incorect code standard: {code_standard}, color setting imposiable")


    return plot_prop


def linear_regression_refactor(file_path:str, parent_path:Path, **query_params):

    plot_pdf_parameters = params_for_plot_pdf_save()

    plot_prop:dict = get_plot_prop()

    plot_style = get_different_color(file_path, plot_prop)

    # Initialize sum and index for averaging comparison value
    b_data = 0
    index: int = -1

    idea = []
    analytical = []
    chord_lps = []
    conn_member_lps = []

    # Use dynamic kwargs to pass filters into the calculation function.
    # calc_res_from_calculated will also inject required parameters based on file_path.
    calculated_all:list[MainCalculationInfo] = calc_res_from_calculated(file_path, **query_params)
    calculated:list[MainCalculationInfo] = duplicates_filtering(calculated_all)

    strange_list:list[MainCalculationInfo] = []
    min_comp: float = float('inf')

    for result in calculated:
        r_cbfem = result.idea_results.Nrd_idea
        r_hand = result.results.Nrd


        if (r_cbfem/r_hand) < 1.0:
            strange_list.append(copy.deepcopy(result))

        if (r_cbfem/r_hand) < min_comp:
            min_comp = (r_cbfem/r_hand)
            min_comp_result = copy.deepcopy(result)

    #plot_comparison_with_plastic_strains(calculated)
    plot_analyzes_percentage_histogram(calculated)




    if not calculated:
        print("Warning: No calculated results available. Skipping data generation.")
        return

    dict_calculated:list[dict] = dict_generator(calculated)




    first_code = "CBFEM"
    code_standard: str = calculated[0].conn_setup.code_standard
    conn_type: str = calculated[0].conn_setup.conn_type
    angle_of_conn: str = str(calculated[0].conn_setup.c_angle)

    # Extract filtering parameters from query_params for labeling.
    # These values might be None if not provided.
    angle_query = query_params.get("angle")
    # If steel_grade is passed, or if get_data_dynamic remapped it to "steel", try to use it.
    steel_grade_query = query_params.get("steel_grade") or query_params.get("steel")
    m_perc_query = query_params.get("m_perc")
    n_perc_query = query_params.get("n_perc")
    nrd_direction_query = query_params.get("nrd_direction")

    # Loop through calculated data to fill arrays and compute the average 'comparison'
    for i in dict_calculated:
        index += 1
        comparison = i["comparison"]
        idea.append(round(i["idea_res"] / 1e3, 5))
        analytical.append(round(i["analy_res"] / 1e3, 5))
        chord_lps.append(round(i['max_chord_lps_cbfem'],5))
        conn_member_lps.append(round(i['max_conn_member_lps_cbfem'], 5))
        b_data += comparison

    # Average comparison value
    b = b_data / (index + 1)

    # Convert lists to numpy arrays
    idea_y = np.array(idea)
    analy_x = np.array(analytical)
    np_chord_lps = np.array(chord_lps)
    np_conn_member_lps = np.array(conn_member_lps)


    average_chord_lps = np_chord_lps.mean()
    average_conn_member_lps = np_conn_member_lps.mean()

    # Sort the data by analytical resistance for plotting
    sorted_indices = np.argsort(analy_x)
    analy_x_sorted = analy_x[sorted_indices]
    idea_y_sorted = idea_y[sorted_indices]
    np_chord_lps_sorted = np_chord_lps[sorted_indices]
    np_conn_member_lps_sorted = np_conn_member_lps[sorted_indices]



    analy_x_sorted_reshaped = analy_x_sorted.reshape(-1, 1)
    lin_reg_slope, _, _, _ = np.linalg.lstsq(analy_x_sorted_reshaped, idea_y_sorted, rcond=None)



    # Linear regression from np.polyfit returns coefficients; take the slope.
    lin_reg_slope_test = np.polyfit(analy_x_sorted, idea_y_sorted, 1)[0]


    # Compare the two slopes: b and lin_reg.
    slope_list = [b, lin_reg_slope[0]]

    # For each slope, generate and save a plot.
    for plot_slope in slope_list:
        # Generate regression line data: starting at 0 and extending to the maximum analytical value.
        x_line = np.linspace(0, max(analy_x_sorted), 100)
        y_line = plot_slope * x_line

        number_of_points = len(analy_x_sorted)
        statistical_res = std_dev_and_residuals(analy_x_sorted, idea_y_sorted, plot_slope)

        plt.figure(figsize=(8, 5))

        # Scatter plot using the dictionary style
        plt.plot(analy_x_sorted, idea_y_sorted, plot_style["scatter"]["marker"],
                label=f"Resistance [kN], number of the calculations: {number_of_points}",
                color=plot_style["scatter"]["color"],
                markersize=plot_style["scatter"]["markersize"],
                markeredgecolor=plot_style["scatter"]["markeredgecolor"],
                markeredgewidth=plot_style["scatter"]["markeredgewidth"] )

        # Regression line using the dictionary style
        plt.plot(x_line, y_line,
                label=(f"Linear Regression Line (slope={plot_slope:.2f}, "
                       f"$R^2$ = {statistical_res['r_squared']:.3f} ), "
                       f"A. lps chord = {(average_chord_lps * 100):.3f}% ), "
                       f"A. brace = {(average_conn_member_lps * 100):.3f}% ), "),
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


        # Remove underscores in code_standard and conn_type for nicer labels.
        for j, item in enumerate([code_standard, conn_type]):
            if j == 0:
                code_standard = item.replace("_", " ")
            else:
                conn_type = item.replace("_", " ")

        # Generate the plot title dynamically.
        # We use the queried values if provided, otherwise they could be omitted or defaulted.
        if plot_slope == b:
            plot_name = (
                f"Relationship between CBFEM and Analytical {code_standard} {conn_type}, "
                f"S{int(steel_grade_query) if steel_grade_query is not None else ''}, "
                f"{angle_query if angle_query is not None else angle_of_conn}°, load $m_{{el}}$: "
                f"{str(m_perc_query*100) + '%' if m_perc_query is not None else ''}, "
                f"n: {str(n_perc_query*100) + '%' if n_perc_query is not None else ''} , slope is b"
            )
        else:
            plot_name = (
                f"Relationship between CBFEM and Analytical {code_standard} {conn_type}, "
                f"S{int(steel_grade_query) if steel_grade_query is not None else ''}, "
                f"{angle_query if angle_query is not None else angle_of_conn}°, load $m_{{el}}$: "
                f"{str(m_perc_query) + '' if m_perc_query is not None else ''}, "
                f"n: {str(n_perc_query) + '' if n_perc_query is not None else ''}, slope is lin_reg"
            )

        folder_name = (
            f"_CBFEM_and_{code_standard}_{conn_type}_"
            f"S{int(steel_grade_query) if steel_grade_query is not None else ''}_"
            f"{angle_query if angle_query is not None else angle_of_conn}_"
            f"load_{m_perc_query}_{n_perc_query}"
        )

        # plt.xlabel(f"{code_standard} {conn_type} [kN]")
        # plt.ylabel(f"IDEA Conn {conn_type} [kN]")
        # plt.title(plot_name, fontsize=8)
        # plt.grid(True)
        # plt.legend(loc="upper left")

        # Set labels and title using the dictionary
        ax.set_xlabel(f"{code_standard} {conn_type} [kN]", fontsize=plot_style["axis_labels"]["fontsize"],
                      fontweight=plot_style["axis_labels"]["fontweight"])
        ax.set_ylabel(f"IDEA Conn {conn_type} [kN]", fontsize=plot_style["axis_labels"]["fontsize"],
                      fontweight=plot_style["axis_labels"]["fontweight"])
        ax.set_title(plot_name, fontsize=plot_style["title"]["fontsize"], pad=plot_style["title"]["pad"],
                     fontweight=plot_style["title"]["fontweight"])

        # Set tick label sizes
        ax.tick_params(axis='both', which='major', labelsize=plot_style["ticks"]["fontsize"])

        # Legend styling
        ax.legend(loc=plot_style["legend"]["loc"], fontsize=plot_style["legend"]["fontsize"])

        # Tight layout for clean spacing
        plt.tight_layout()


        # Prepare the output directory and save the plot.
        absolute_path = parent_path
        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)

        # Remove unwanted characters from the plot name for a valid filename.
        safe_plot_name = re.sub(r"[$:{}%]", "", plot_name)

        safe_plot_name = re.sub(r"[ ]", "_", safe_plot_name)
        plt.savefig((absolute_path / f"{safe_plot_name}.png"), dpi=300)
        plt.close()

    return




if __name__ == "__main__":
    #generate_plots('EN',"CHS_K",45,235e6, 'd0')
    print('script')

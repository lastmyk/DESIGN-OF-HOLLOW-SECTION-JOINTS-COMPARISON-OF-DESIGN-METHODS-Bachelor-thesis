import gc
import os
import numpy as np
from fontTools.ttLib.woff2 import bboxFormat
from matplotlib.ticker import MultipleLocator
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from collections import Counter
from pathlib import Path
import re

def latexized_plot_name(plot_name:str) -> str:
    replacements = {
        r'\bm el\b': r'$m_{el}$ =',
        r'\bn\b': r'n ='
    }

    # General replacements
    for pattern, replacement in replacements.items():
        plot_name = re.sub(pattern, replacement, plot_name)

    # Final cleanup for proper LaTeX formatting
    latex_name = rf'{plot_name}'

    return latex_name



def get_max_temperature_per_xy(x, y, temperature):
    """
    Creates a hash map to store the maximum temperature for each unique (x, y) pair.

    Parameters:
        x (np.array): X-coordinates
        y (np.array): Y-coordinates
        temperature (np.array): Temperature values

    Returns:
        unique_x (np.array): Unique x values
        unique_y (np.array): Unique y values
        max_temps (np.array): Corresponding max temperatures
    """

    hash_map = {}

    for i in range(len(x)):
        key = (x[i], y[i])  # Create a unique key from (x, y)
        if key in hash_map:
            hash_map[key] = max(hash_map[key], temperature[i])  # Store max temperature
        else:
            hash_map[key] = temperature[i]

    # Extract results
    unique_x = np.array([key[0] for key in hash_map.keys()])
    unique_y = np.array([key[1] for key in hash_map.keys()])
    max_temps = np.array(list(hash_map.values()))

    print(f'Number of the reduced data from dataset is {len(unique_x) - len(x)}')

    return unique_x, unique_y, max_temps


def calculate_bounds(temperatures):
    temperatures = np.round(temperatures, 6)

    # Get the unique temperatures and their counts
    temp_counts = Counter(temperatures)

    # Extract the unique temperatures (sorted)
    unique_temps = sorted(temp_counts.keys())
    # If there is only one unique temperature
    if len(unique_temps) == 1:
        # If only one unique temperature, create bounds with a small gap
        min_temp = unique_temps[0]
        max_temp = min_temp + 0.01  # Adding a small gap
        bounds = np.array([min_temp, max_temp])  # At least two values

    else:
        # Calculate the differences between consecutive temperatures
        temp_diffs = np.diff(unique_temps)

        # Find the maximum difference
        max_diff = np.max(temp_diffs)

        # Determine the division based on the max difference
        if max_diff < 0.05:
            division = 0.025
        elif max_diff < 0.1:
            division = 0.05
        elif max_diff < 0.2:
            division = 0.1
        else:
            division = 0.25

        # Adjust division further based on the number of unique temperatures
        num_unique_temps = len(unique_temps)

        if num_unique_temps < 5:
            division = max(division, 0.1)  # Use larger division if few unique temps
        elif num_unique_temps < 15:
            division = max(division, 0.05)  # Moderate division for medium range
        else:
            division = max(division, 0.01)  # Smaller division for more unique temps

        # Find the min and max temperature
        min_temp = min(unique_temps)
        max_temp = max(unique_temps)

        # Otherwise, use np.arange for multiple values
        bounds = np.arange(min_temp, max_temp + division, division)
        bounds[-1] = max_temp

    return bounds


def params_for_plot_pdf_save()-> dict:
    params = {
        'format': "pdf",
        'bbox_inches': "tight"}

    return params


def plot_data_3D(x_betta, y_res, y_gamma, thickness, plot_name, conn_type: str, temparature_label: str, parent_path: Path | None):

    latex_plot_name = latexized_plot_name(plot_name)

    params_plot_pdf = params_for_plot_pdf_save()

    # Convert input lists to numpy arrays.
    x = np.array(x_betta)
    # y_gamma will be plotted on the z-axis now.
    gamma = np.array(y_gamma)
    temperature = np.array(y_res)
    # thickness will be plotted on the y-axis.
    t_val = np.array(thickness)

    ###### This part ensures the colorbar size matches your 2D plots.
    _, _, max_temps = get_max_temperature_per_xy(x, gamma, temperature)

    # Sort the data by the aggregated temperature (ascending)
    sorted_indices = np.argsort(temperature)
    x_sorted = x[sorted_indices]
    gamma_sorted = gamma[sorted_indices]
    thickness_sorted = t_val[sorted_indices]
    temperature_sorted = np.round(temperature[sorted_indices], 6)

    # Define your custom colormap (blue -> green -> yellow -> red)
    colors = ['blue', 'green', 'yellow', 'red']
    bounds = calculate_bounds(max_temps)
    cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=len(bounds))
    norm = BoundaryNorm(boundaries=bounds, ncolors=cmap.N, clip=True)

    # Create a 3D plot.
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    fig.set_size_inches(6.4, 4.8)
    #ax.set_position([0.05, 0.1, 0.4, 0.8])  # Adjust position to fit colorbar

    # Create the 3D scatter plot with swapped y and z:
    # • x coordinate remains x_sorted.
    # • y coordinate now uses thickness_sorted.
    # • z coordinate now uses gamma_sorted.
    sc = ax.scatter(x_sorted, thickness_sorted, gamma_sorted,
                    c=temperature_sorted, cmap=cmap, norm=norm,
                    s=temperature_sorted * 100, label='Temperature', alpha=0.7)

    # Add shadow projection on the x-y plane (z fixed at 0)
    ax.scatter(x_sorted, thickness_sorted, zs=0, zdir='z',
               c='gray', alpha=0.15, s=temperature_sorted * 50, marker='o')

    # Add the colorbar.
    color_bar = fig.colorbar(sc, ax=ax, boundaries=bounds, ticks=bounds, shrink=0.7)
    color_bar.set_label(temparature_label)
    color_bar.ax.set_yticklabels([f"{round(val, 3)}" for val in color_bar.get_ticks()])

    # Update axis labels to reflect the new coordinate mapping:
    # x remains β, y now shows t₁ (thickness), and z shows γ.
    ax.set_xlabel(r'$\mathrm{β}$ = $\mathrm{\dfrac{d_1}{d_0}}$ [-]', fontsize=8)
    ax.set_ylabel(r'$\mathrm{t_1}$ [mm]', fontsize=8)
    ax.set_zlabel(r'$\mathrm{γ}$ = $\mathrm{\dfrac{d_0}{2 \cdot t_0}}$ [-]', fontsize=8)

    # Change the font size of the axis tick labels.
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=8)
    ax.tick_params(axis='z', labelsize=8)

    y_plot_lim = max_y_lim(y_gamma)

    # Adjust limits as needed.
    # For thickness now plotted on the y-axis:
    ax.set_ylim(max(8, np.max(thickness_sorted)), 2)
    ax.yaxis.set_major_locator(MultipleLocator(2))
    # For gamma now plotted on the z-axis (adjust the limit as appropriate):
    ax.set_zlim(0, y_plot_lim)

    ax.invert_xaxis()

    # Set the view angle
    ax.view_init(elev=15, azim=105)

    # Set title and layout adjustments.
    fig.suptitle(latex_plot_name, fontsize=8)
    fig.tight_layout()

    # Save the plot to the corresponding directory.
    script_dir = get_root_dir_path()
    absolute_path:Path = script_dir / "plots" / conn_type

    if parent_path is not None:
        absolute_path = parent_path

    if not os.path.exists(absolute_path):
        os.makedirs(absolute_path)

    safe_plot_name = re.sub(r"[$:{}%\\]", "", plot_name)

    plt.savefig(os.path.join(absolute_path, f"{safe_plot_name}3D.pdf"), **params_plot_pdf)
    #plt.savefig(os.path.join(absolute_path, f"{safe_plot_name}3D.png"), dpi=300)

    plt.close(fig)
    gc.collect()

    return


def get_root_dir_path() -> Path:
    from pathlib import Path

    # Get the absolute path of the current script
    script_dir = Path(__file__).resolve()

    # Move up two levels to reach the project root
    project_dir = script_dir.parents[2]


    return project_dir


def plot_data(x_betta,y_res, y_gamma, plot_name, conn_type:str, temparature_label:str, parent_path: Path | None):

    latex_plot_name = latexized_plot_name(plot_name)
    params_plot_pdf = params_for_plot_pdf_save()

    x = np.array(x_betta)
    y = np.array(y_gamma)
    temperature = np.array(y_res)

    unique_x, unique_y, max_temps = get_max_temperature_per_xy(x, y, temperature)


    sorted_indices = np.argsort(max_temps) # Sort by temperature (ascending)

    x = unique_x[sorted_indices]
    y = unique_y[sorted_indices]
    temperature = max_temps[sorted_indices]

    temperature = np.round(temperature, 6)

    # Define your custom color map: blue -> green -> yellow -> red
    colors = ['blue', 'green', 'yellow', 'red']

    bounds = calculate_bounds(temperature)

    cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=len(bounds))

    # Normalize the data to fit the boundaries
    norm = BoundaryNorm(boundaries=bounds, ncolors=cmap.N, clip=True)

    # Create figure and axis for the first y-axis (temperature appearance, but y-axis position for other_data)
    fig, ax1 = plt.subplots()

    sc = ax1.scatter(x, y, c=temperature, cmap=cmap, norm=norm, s=temperature*100,
                     label='Temperature', alpha=0.7)

    # # Add colorbar to the plot
    cbar = plt.colorbar(sc, ax=ax1, boundaries=bounds, ticks=bounds)
    cbar.set_label(temparature_label)

    # Format the colorbar ticks to show as percentages
    cbar.ax.set_yticklabels([f"{round(x,3)}" for x in cbar.get_ticks()])

    # Set labels for the axes
    ax1.set_xlabel(r'$\mathrm{β}$ = $\mathrm{\dfrac{d_1}{d_0}}$ [-]')
    ax1.set_ylabel(r'$\mathrm{γ}$ = $\mathrm{\dfrac{d_0}{2 \cdot t_0}}$  [-]', color='black')
    ax1.tick_params(axis='y', labelcolor='black')

    y_plot_lim = max_y_lim(y_gamma)

    # Set y-axis limits from 0 to 50
    ax1.set_ylim(0, y_plot_lim)

    # Set title and show plot
    fig.suptitle(latex_plot_name,fontsize=8)
    fig.tight_layout()



    script_dir:Path = get_root_dir_path()
    absolute_path:Path = script_dir / "plots" / conn_type

    if parent_path is not None:
        absolute_path = parent_path


    if not os.path.exists(absolute_path):
        os.makedirs(absolute_path)

    safe_plot_name = re.sub(r"[$:{}%]", "", plot_name)

    plt.savefig((absolute_path / f"{safe_plot_name}.pdf"), **params_plot_pdf)
    #plt.savefig((absolute_path / f"{safe_plot_name}.png"), dpi=300)

    plt.close(fig)
    gc.collect()

    return


def max_y_lim(y_gamma:list):
    y_plot_lim = max(30, int(max(y_gamma)))

    if 30 < y_plot_lim < 40:
        y_plot_lim = 40

    elif 40 < y_plot_lim < 50:
        y_plot_lim = 50

    return y_plot_lim


def dict_plotter(data:list[dict], key_to_filter:str, comparison_descr:str, desc_label:str, parent_path: Path|None) -> None:

    for i in data:
        validate_dict(i, i['conn_type'])

    unique_types = set()

    for i in data:
        unique_types.add(i[key_to_filter])


    subsets = {}  # Dictionary to store the subsets

    for unique_type in unique_types:
        # Filter data based on the current unique type


        subsetx = [i for i in data if i[key_to_filter] == unique_type]
        subsets[unique_type] = subsetx  # Store the subset in the dictionary


    for subset in subsets.items():

        plot_name = f"{comparison_descr} - N CHS chord d = {str(round((subset[0]*1e3),1))} mm"
        plot_name = plot_name.replace("/", "_")
        plot_name = plot_name.replace('_', ' ')
        print(plot_name + '\n'*2)

        x_betta = []
        y_gamma = []
        y_res = []
        brace_ths = []

        strength_case = []

        max_name = None
        max_comp = float('-inf')

        min_name = None
        min_comp = float('+inf')


        for j in subset[1]:

            if j['comparison'] > max_comp:
                max_name:str = j['name']
                max_comp:float = j['comparison']

            if j['comparison'] < min_comp:
                min_name:str = j['name']
                min_comp:float = j['comparison']



            res_analy = j["comparison"]

            betta = j['betta']

            gamma = j['gamma']

            brace_th = (j['t1'] * 1e3)

            j["x_betta"] = betta

            j["y_gamma"] = gamma

            j["y_res"] = res_analy

            x_betta.append(betta)
            y_gamma.append(gamma)
            y_res.append(res_analy)
            brace_ths.append(brace_th)

        print(f'Max res is {max_comp} for conn {max_name}\n')
        print(f'Min res is {min_comp} for conn {min_name}\n')
        max_name = max_name.replace('/', '_')
        min_name = min_name.replace('/', '_')
        print(f'Max res is {max_comp} for conn {max_name}\n')
        print(f'Min res is {min_comp} for conn {min_name}\n')

        plot_data_3D(x_betta, y_res, y_gamma, brace_ths, plot_name, comparison_descr, desc_label, parent_path)

        plot_data(x_betta, y_res, y_gamma, plot_name, comparison_descr, desc_label, parent_path)


    return


def validate_dict(input_dict:dict, conn_type:str) -> None:
    if conn_type[:3] == 'CHS':

        required_keys = {'d0', 't0', 'd1', 't1', 'fy', 'angle', 'comparison', 'betta', 'gamma', 'name'}
    else:
        required_keys = {'b0', 'h0', 't0', 'b1', 'h1', 't1', 'fy', 'angle', 'comparison', 'betta', 'gamma', 'name'}

    mising_keys = required_keys - input_dict.keys()

    if mising_keys:

        raise KeyError(f"Missing required keys: {mising_keys}. Evaluation impossible")


def title_generator_refactor(
    first_code: str,
    second_code: str,
    conn_type: str = None,
    steel_grade: str = None,
    angle_of_conn: str = None,
    m_perc: float = None,
    n_perc: float = None,
    nrd_direction: str = None
) -> tuple[str, str]:
    """
    Generate a dynamic title and label based on the provided parameters.
    Only the non-None parameters will be included in the title.

    Parameters:
      first_code (str): Identifier for the first code.
      second_code (str): Identifier for the second code.
      conn_type (str, optional): Connection type.
      n_p (str, optional): A string representing a percentage (as used in the plot).
      steel_grade (str, optional): Steel grade information.
      angle_of_conn (str, optional): Angle of the connection.
      m_perc (float, optional): m_el percentage.
      n_perc (float, optional): n percentage.
      nrd_direction (str, optional): NRD direction, included only if second_code equals "CHS_T_and_Y".

    Returns:
      tuple[str, str]: A tuple containing the generated title and a temperature label.
    """
    # Start with the basic comparison title
    if second_code == 'Fpr_EN':
        second_code = 'Fpr_EN_1993-1-8'
    elif second_code == 'EN':
        second_code = 'EN_1993-1-8'
    elif second_code == 'AISC':
        second_code = 'AISC 360-22'
    else:
        raise KeyError(f'Title cant be generated, incorrect design code {second_code}')


    title_parts = [f"{first_code} vs {second_code},"]

    # Append the parameters only if they are provided
    if conn_type:
        title_parts.append(conn_type + ',')
    if steel_grade:
        title_parts.append(f"S {steel_grade}" + ',')
    if angle_of_conn:
        title_parts.append(f"{angle_of_conn}°"  + ',')
    if m_perc is not None:
        title_parts.append(f"m_el {m_perc}"  + ',')
    if n_perc is not None:
        title_parts.append(f"n {n_perc}"  + ',')
    if nrd_direction and second_code == "CHS_T_and_Y":
        title_parts.append(f"Nrd_direction is {nrd_direction}")

    # Join parts with a single space
    code_to_compare = " ".join(title_parts)

    # Create a temperature label (you can extend this logic if needed)
    temparature_label = f"{first_code} / {second_code} [-]"
    temparature_label = temparature_label.replace("_", " ")

    return code_to_compare, temparature_label

def main():
    print('script utils_data_plotting.src is running ')


if __name__ == '__main__':
    main()

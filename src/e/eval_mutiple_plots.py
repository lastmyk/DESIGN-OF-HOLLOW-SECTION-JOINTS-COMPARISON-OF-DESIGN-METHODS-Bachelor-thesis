from src.e.eval_res_to_diff_code import dict_generator, calc_res_from_calculated
from src.u.utils_data_plotting import get_root_dir_path
from src.calc.base_classes import MainCalculationInfo
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def idea_res_to_code(file_path:str, file_pathxx:str, file_pathkk:str,) -> None:

    calculated:list[MainCalculationInfo] = calc_res_from_calculated(file_path, angle=45)

    calculatedXX:list[MainCalculationInfo] = calc_res_from_calculated(file_pathxx, angle=45)

    calculatedKK:list[MainCalculationInfo] = calc_res_from_calculated(file_pathkk, angle=45)

    data_for_plotting:list[dict] = dict_generator(calculated)

    data_for_plottingx:list[dict] = dict_generator(calculatedXX)

    data_for_plottingk:list[dict] = dict_generator(calculatedKK)

    dataset_titles = ['CHS T & Y', 'CHS X', 'CHS K']

    box_stat_plotter(data_for_plotting, data_for_plottingx, data_for_plottingk, titles=dataset_titles)

    violin_plotter(data_for_plotting, data_for_plottingx, data_for_plottingk, titles=dataset_titles)

    return


def set_axis_style(ax, labels):
    """Set custom tick labels and limits for the x-axis."""
    ax.set_xticks(np.arange(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    ax.set_xlim(0.25, len(labels) + 0.75)
    ax.set_xlabel('Data Groups')


def violin_plotter(*datasets, titles=None):


    if not datasets:
        raise ValueError("At least one dataset must be provided.")

    # Check that titles, if provided, match the number of datasets.
    if titles is not None:
        if len(titles) != len(datasets):
            raise ValueError(
                f"Number of titles provided ({len(titles)}) does not match the number of datasets ({len(datasets)}).")
    else:
        titles = [f"Dataset {i + 1}" for i in range(len(datasets))]

    # Extract 'comparison' values from each dataset.
    data_for_plot = []
    for dataset in datasets:
        data_values = [item['comparison'] for item in dataset]
        data_for_plot.append(data_values)

    # Create the figure and a single set of axes.
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create the violin plot without default statistics.
    ax.violinplot(data_for_plot)

    # Set overall title and axis labels.
    ax.set_title('Comparison Violin Plot EN to IDEA Conn')
    ax.set_ylabel('Comparison Values')

    # Apply x-axis style with provided titles.
    set_axis_style(ax, titles)

    # Add horizontal grid lines and adjust y-axis limits.
    ax.yaxis.grid(True)
    ax.set_ylim(0.8, 4)

    # Save the plot to file.
    script_dir: Path = get_root_dir_path()
    absolute_path = script_dir / 'plots' / 'Violin_statics'
    absolute_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(absolute_path / 'CONN_type_Fpr_AISC.png', dpi=300)

    plt.close(fig)
    return None


def box_stat_plotter(*datasets, titles=None):
    """
    Plots a box plot for an arbitrary number of datasets.

    Each dataset should be a list of dictionaries with a 'comparison' key.

    :param datasets: Positional arguments, each is a list of dicts (each dict must contain a 'comparison' key).
    :param titles: Optional list of titles (one per dataset) to label each box. If not provided,
                   default labels 'Dataset 1', 'Dataset 2', ... are used.
    """
    if not datasets:
        raise ValueError("At least one dataset must be provided.")

    # If titles are provided, check that their count matches the number of datasets.
    if titles is not None:
        if len(titles) != len(datasets):
            raise ValueError(
                f"Number of titles provided ({len(titles)}) does not match the number of datasets ({len(datasets)}).")
    else:
        # Generate default titles if none provided.
        titles = [f"Dataset {i + 1}" for i in range(len(datasets))]

    # Extract 'comparison' values from each dataset.
    data_for_plot = []
    for dataset in datasets:
        data_values = [item['comparison'] for item in dataset]
        data_for_plot.append(data_values)

    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 6))

    meanlineprops = dict(linestyle='--', linewidth=2.5, color='purple')

    # Create the box plot with custom tick labels from titles.
    ax.boxplot(data_for_plot, tick_labels=titles,meanprops=meanlineprops, meanline=True, showmeans=True)

    # Set overall title and axis labels.
    ax.set_title('Comparison Box Plot EN to IDEA Conn')
    ax.set_xlabel('Data Groups')
    ax.set_ylabel('Comparison Values')

    # Add horizontal grid lines and adjust y-axis limits.
    ax.yaxis.grid(True)
    ax.set_ylim(0.8, 4)

    # Save the plot to file.
    script_dir: Path = get_root_dir_path()
    absolute_path = script_dir / 'plots' / 'Box_statics'
    absolute_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(absolute_path / f'CONN_type_EN.png', dpi=300)

    plt.close(fig)

    return None


if __name__ == "__main__" :
    idea_res_to_code(r'../../Code_Config_yaml/AISC/CHS_T_and_Y.yaml', r'../../Code_Config_yaml/AISC/CHS_X.yaml', r'../../Code_Config_yaml/AISC/CHS_K.yaml')



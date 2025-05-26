import numpy as np
import matplotlib.pyplot as plt
from typing import List
from py.calc.base_classes import MainCalculationInfo


def plot_comparison_with_plastic_strains(strange_list: List[MainCalculationInfo]):
    """
    Visualizes relationship between FEA/hand calculation ratio and plastic strains

    Parameters:
    strange_list (List[MainCalculationInfo]): List of calculation results containing:
        - idea_results.Nrd_idea: FEA results
        - results.Nrd: Hand calculation results
        - idea_results.chord_strain: Plastic strain in chord member
        - idea_results.conn_member_strain: Plastic strain in connector member
    """
    # Extract data from objects
    r_cbfem = np.array([i.idea_results.Nrd_idea for i in strange_list])
    r_hand = np.array([i.results.Nrd for i in strange_list])
    ps_chord = np.array([i.conn_setup.chord.t * 1e3 for i in strange_list])
    ps_brace = np.array([i.conn_setup.conn_member.t *1e3 for i in strange_list])

    comparison = r_cbfem / r_hand

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot for chord member strain
    _create_strain_plot(ax1, ps_chord, comparison, 'Chord Member')

    # Plot for connector member strain
    _create_strain_plot(ax2, ps_brace, comparison, 'Brace Member')

    plt.tight_layout()
    plt.show()


def _create_strain_plot(ax, x_data, y_data, strain_location: str):
    """Helper function to create standardized strain comparison plot"""
    ax.scatter(x_data, y_data, alpha=0.6, edgecolors='w')

    # Add trend line
    coefs = np.polyfit(x_data, y_data, 1)
    trend_line = np.poly1d(coefs)
    ax.plot(x_data, trend_line(x_data), 'r--',
            label=f'Trend: y={coefs[0]:.2f}x + {coefs[1]:.2f}')

    # Add reference line
    ax.axhline(1, color='g', linestyle='-', label='1:1 Reference')

    # Formatting
    ax.set_xlabel(f'$t$ {strain_location} [mm]')
    ax.set_ylabel('FEA / Hand Calculation Ratio [-]')
    ax.set_title(f'Impact of {strain_location} thickness t')
    ax.legend()
    ax.grid(True)
    ax.set_ylim(bottom=0)  # Force positive scale



def plot_analyzes_percentage_histogram(strange_list: List[MainCalculationInfo]):
    """
    Plots a histogram of analysis percentages from idea_results.analyzes_percentage.

    Parameters:
    strange_list (List[MainCalculationInfo]): List of calculation results containing
        idea_results.analyzes_percentage, which is a list of percentages.
    """
    # Extract and flatten all analysis percentages
    all_percentages: np.array = np.array([i.results.res_dict['N_chord'] / i.conn_setup.chord.N_max for i in strange_list])
    #all_percentages:np.array = np.array([i.idea_results.analysis_perc for i in strange_list])

    # Create figure
    plt.figure(figsize=(10, 6))

    # Plot histogram
    plt.hist(all_percentages, bins=20, edgecolor='black', alpha=0.7, color='skyblue')

    # Add labels and title
    plt.xlabel(f'$N_{{0,E}} / N_{{0,R}}$ [-]')
    plt.ylabel('Number of calculated specimens')
    plt.title('Distribution of chord pre-loading')

    # Add grid and adjust layout
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()



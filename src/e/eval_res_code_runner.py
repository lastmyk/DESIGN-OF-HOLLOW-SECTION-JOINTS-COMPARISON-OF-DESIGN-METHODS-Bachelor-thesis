import os
import time

from src.e.eval_linear_regresion import linear_regression_refactor
from src.e.eval_res_to_diff_code import idea_res_to_code_refactor
from src.u.utils_data_plotting import get_root_dir_path
from pathlib import Path


def create_path_to_codes(conn_type:str,angle:int=None, steel_grade:int=None, m_perc:float=None, n_perc:float=None, nrd_direction:str=None)->dict:
    pathes = []
    codes = ['Fpr_EN', 'EN', 'AISC' ]
    for code in codes:

        path = os.path.join('../../Code_Config_yaml', code, conn_type + '.yaml')
        if not os.path.exists(path):
            KeyError(f'Incorrect connection type {conn_type}, path doesnt exist')
        pathes.append(path)

    # path to folder
    same_setup_folder_path = Path(get_root_dir_path() / 'plots' / 'cbfem' / 'lin_reg'/  'overleaf' /conn_type
                                  / (('S' + str(steel_grade)) + ' '
                                  + ('angle' + str(angle)) + ' '
                                  +('m ' + (str(m_perc))) + ' '
                                  +('n ' + str(n_perc)) + ' '
                                  +str(nrd_direction)))

    same_setup_detailed_folder_path = Path(get_root_dir_path() / 'plots' / 'cbfem' / 'detailed_plots'/ conn_type
                                  / (('S' + str(steel_grade)) + ' '
                                  + ('angle' + str(angle)) + ' '
                                  +('m ' + (str(m_perc))) + ' '
                                  +('n ' + str(n_perc)) + ' '
                                  +str(nrd_direction)))

    path_res = {
        'pathes': pathes,
        'parent': same_setup_folder_path,
        'parent_detailed':same_setup_detailed_folder_path

    }

    return path_res



def runner(conn_type:str, angle:int, steel_grade:int, m_perc:float, n_perc:float, nrd_direction:str) ->None:
    pathes:dict = create_path_to_codes(conn_type, angle, steel_grade, m_perc, n_perc, nrd_direction)

    time_a = time.time()

    # for path in pathes['pathes']:
    #     idea_res_to_code_refactor(path,
    #                               pathes['parent_detailed'],
    #                               angle=angle, steel=steel_grade, m_perc=m_perc, n_perc=n_perc, nrd_direction=nrd_direction)
    #
    #     print(f'1 Code detailed print running time is {time.time() - time_a} seconds ')

    for path in pathes['pathes']:
        linear_regression_refactor(
            path,
            pathes['parent'],
            angle=angle, steel=steel_grade, m_perc=m_perc, n_perc=n_perc, nrd_direction=nrd_direction)

    return


def global_lin_reg(conn_type: str, **query_params) -> None:
    """
    Run the full data generation and plotting workflow using dynamic parameters.

    Parameters:
      conn_type (str): The connection type identifier.
      **query_params: Additional filtering parameters such as:
          - angle (int)
          - steel_grade (int)
          - m_perc (float)
          - n_perc (float)
          - nrd_direction (str)
          ... as expected by idea_res_to_code_refactor and linear_regression_refactor.

    The function:
      1. Retrieves the relevant file paths via create_path_to_codes(conn_type).
      2. Generates IDEA code outputs using idea_res_to_code_refactor().
      3. Performs linear regression analysis and plotting using linear_regression_refactor().
    """
    # Ensure that the conn_type is included in the query parameters
    query_params["conn_type"] = conn_type

    # Get paths for processing based on the connection type.
    pathes = create_path_to_codes(conn_type,
                                  angle=query_params.get('angle', None),
                                  steel_grade=query_params.get('steel_grade', None),
                                  m_perc=query_params.get('m_perc', None),
                                  n_perc=query_params.get('n_perc', None),
                                  nrd_direction=query_params.get('nrd_direction', None))


    # Process each file path to perform linear regression and generate plots
    for path in pathes['pathes']:
        linear_regression_refactor(path, pathes['parent'], **query_params)

    return


if __name__ == '__main__':
    # Example usage with dynamic keyword parameters.'CHS_K' 'CHS_T_and_Y' 'CHS_X'

    # steels = [235, 355, 420, 550, 600]
    # n_percs = [0.8, 0.45, -0.45, -0.8]
    #
    # for steel in steels:
    #     for perc in n_percs:
    #         runner('CHS_T_and_Y', angle=90, steel_grade=steel, m_perc=0, n_perc=perc, nrd_direction='-')

    # angles = [30,45,60,90]
    # steels = [235, 355, 420, 460, 550, 600]
    # m_percs = [0, -0.45, 0.45]
    # n_percs = [0, -0.45, -0.8, 0.45, 0.8]
    # conn_types = ['CHS_X', 'CHS_K', 'CHS_T_and_Y']
    #
    #
    # for angle in angles:
    #     for steel in steels:
    #         for mperc in m_percs:
    #              for nperc in n_percs:
    #                 for conn_type in conn_types:
    #                     runner(conn_type, angle=angle, steel_grade=steel, m_perc=mperc, n_perc=nperc, nrd_direction='-')

    runner('CHS_X', angle=30, steel_grade=420, m_perc=0, n_perc=-0.8, nrd_direction='-')




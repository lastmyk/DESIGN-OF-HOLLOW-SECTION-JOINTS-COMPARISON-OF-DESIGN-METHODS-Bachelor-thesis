from py.u.utilis_data_import import get_data_from_DB
import json
import os
from py.u.utils_data_plotting import dict_plotter, title_generator_refactor
from py.calc.generate_samples import code_calc, additional_excluding
from py.calc.base_classes import BaseGeometry, RectangleHollow, ConfigConn, ConnSetup, IdeaRes, MainCalculationInfo, \
    IdeaLoadingInfo
from typing import Any
import yaml
from pathlib import Path
import time


def get_data_dynamic(**query_params) -> list[dict]:
    """
    Build and execute a dynamic SQL query based on passed keyword parameters.

    Expected keys (if provided):
      - conn_type (str)  [Required]
      - angle (float)
      - steel (int)
      - m_perc (float)
      - n_perc (float)
      - nrd_direction (str)
    """
    query = (
        "SELECT "
        "i.name AS exp_key, "
        "i.capacity AS Analytical_Capacity, "
        "i.conn_type AS Connection_type, "
        "i.angle AS Angle_of_the_connected_m_and_chord, "
        "i.specification "
        "FROM idea_res i "
        "WHERE i.code_standard IS NOT NULL "
    )

    conditions = []
    params = []

    # Required parameter: conn_type
    if "conn_type" in query_params:
        conditions.append("i.conn_type = %s")
        params.append(query_params["conn_type"])
    else:
        raise ValueError("Missing required parameter: conn_type")

    # Optional parameters and filters:
    if "angle" in query_params and query_params["angle"] is not None:
        conditions.append("i.angle = %s")
        params.append(query_params["angle"])

    if "steel" in query_params and query_params["steel"] is not None:
        # Convert steel to integer expected by DB query
        steel_val = int(query_params["steel"] * 1e6)
        conditions.append("i.steel_grade BETWEEN %s - 1000 AND %s + 1000")
        params.extend([steel_val, steel_val])

    if "m_perc" in query_params and query_params["m_perc"] is not None:
        m_perc = query_params["m_perc"]
        if abs(m_perc) > 1:
            raise KeyError(f"m_perc too large: {m_perc}")
        conditions.append("i.m_perc = %s")
        params.append(int(m_perc * 100))

    if "n_perc" in query_params and query_params["n_perc"] is not None:
        n_perc = query_params["n_perc"]
        if abs(n_perc) > 1:
            raise KeyError(f"n_perc too large: {n_perc}")
        conditions.append("i.n_perc = %s")
        params.append(int(n_perc * 100))

    if "nrd_direction" in query_params and query_params["nrd_direction"] is not None:
        conditions.append("i.nrd_direction = %s")
        params.append(query_params["nrd_direction"])

    # Append all conditions to the base query
    if conditions:
        query += " AND " + " AND ".join(conditions)

    # Execute the dynamically built query.
    return get_data_from_DB(query, tuple(params), "gel_last_calc_idea")


def parse_to_class(cls, data):
    """
    Recursively parse a dictionary into dataclass instances.
    """
    # Handle dictionaries directly
    if isinstance(data, dict) and hasattr(cls, '__dataclass_fields__'):
        fieldtypes = {f.name: f.type for f in cls.__dataclass_fields__.values()}
        return cls(**{f: parse_to_class(fieldtypes[f], data[f]) for f in data})
    # Handle lists by inferring their item type
    elif isinstance(data, list):
        item_type = cls.__args__[0] if hasattr(cls, '__args__') else Any
        return [parse_to_class(item_type, item) for item in data]
    # For primitive types, return the data as is
    else:
        return data


def get_analysis_loading(data_fea_calc:list[dict], model_definition_filename:str) -> list[MainCalculationInfo]:

    connections = []
    with open(model_definition_filename, 'r') as f:
        model_definition = yaml.load(f, yaml.FullLoader)

    for single_calc in data_fea_calc:

        single_specification_str:str= single_calc['specification']

        single_specification = json.loads(single_specification_str)

        analysis_percentage = (
                single_specification['idea_results'].get('analysis_percentage') or
                single_specification['idea_results'].get('analysis_perc') or
                0  # Provide a default value if both keys are missing
        )

        conn_type = single_specification['conn_setup']['conn_type']

        actual_perc_n = single_specification['perc_chord_N'] * analysis_percentage
        actual_perc_m = single_specification['perc_chord_M'] * analysis_percentage

        nrd_direct = single_specification['conn_setup'].get('nrd_direction', '-')

        if conn_type[:3] == "RHS":

            conn_member = parse_to_class(RectangleHollow, single_specification['conn_setup']['conn_member'])
            chord = parse_to_class(RectangleHollow, single_specification['conn_setup']['chord'])

        else:
            conn_member = parse_to_class(BaseGeometry, single_specification['conn_setup']['conn_member'])
            chord = parse_to_class(BaseGeometry, single_specification['conn_setup']['chord'])

        idea_res = parse_to_class(IdeaRes, single_specification['idea_results'])

        steel_grade = single_specification['conn_setup']['steel_grade']
        steel_grade_str = single_specification['conn_setup']['steel_grade_str']
        c_angle = single_specification['conn_setup']['c_angle']

        config_yaml = ConfigConn(
            profiles_chord=model_definition["profiles"]['chord']['type'],
            profiles_conn_m=model_definition["profiles"]['connected_member']['type'],
            validity_conditions=model_definition['validity_conditions'],
            idea_conn_path=model_definition['idea_conn_path'],
            equations=model_definition['equations'],
            add_exlus_conds=model_definition.get('additional_exclusion', None)

        )

        conn_setup = ConnSetup(
            conn_type=model_definition["connection_type"],
            code_standard=model_definition["code_standard"],
            config_=config_yaml,
            nrd_direction=nrd_direct,
            steel_grade=steel_grade,
            steel_grade_str=steel_grade_str,
            c_angle=c_angle,
            conn_member=conn_member,
            chord=chord,

        )

        connection_info = MainCalculationInfo(
            conn_setup=conn_setup,
            perc_chord_N=actual_perc_n,
            perc_chord_M=actual_perc_m,
            idea_results=idea_res,
            my_sql_key=single_specification['my_sql_key']
        )

        connections.append(connection_info)


    return connections


def calc_res_from_calculated(file_path_new:str, **query_params) -> list[MainCalculationInfo] :

    # Remove the file extension
    without_extension = os.path.splitext(file_path_new)[0]

    # Extract the substring after the last '/'
    conn_type = os.path.basename(without_extension)

    query_params["conn_type"] = conn_type

    # get data from db
    data: list[dict] = get_data_dynamic(**query_params)

    if not data:
        return []
    #get raw data to class
    conn_prep:list[MainCalculationInfo] = get_analysis_loading(data, file_path_new)

    #calculate same as raw data from sample generation
    calculated = code_calc(conn_prep, 'post')

    #exclude if needed, based on config
    filtered_calc = additional_excluding(calculated)

    #filter if possible duplicates
    filtered_duplicates = duplicates_filtering(filtered_calc)

    return filtered_duplicates


def dict_generator(data:list[MainCalculationInfo]) -> list[dict]:

    dicts = []

    for i in data:

        if i.conn_setup.conn_type[:3] == 'CHS':

            data_dict = {
                'name': i.my_sql_key,
                't0': i.conn_setup.chord.t,
                'd0': i.conn_setup.chord.d,
                't1': i.conn_setup.conn_member.t,
                'd1': i.conn_setup.conn_member.d,
                'fy': i.conn_setup.steel_grade,
                'angle': i.conn_setup.c_angle,
                'comparison': ( i.idea_results.Nrd_idea / i.results.Nrd),
                'betta': (i.conn_setup.conn_member.d / i.conn_setup.chord.d),
                'gamma': (i.conn_setup.chord.d / (2 * i.conn_setup.chord.t)),
                'idea_res': i.idea_results.Nrd_idea,
                'analy_res': i.results.Nrd,
                'conn_type': i.conn_setup.conn_type,
                'max_chord_lps_cbfem': i.idea_results.chord_strain,
                'max_conn_member_lps_cbfem': i.idea_results.conn_member_strain,
                }
        else:
            data_dict = {
                'name': i.my_sql_key,
                't0': i.conn_setup.chord.t,
                'b0': i.conn_setup.chord.b,
                'h0': i.conn_setup.chord.h,
                't1': i.conn_setup.conn_member.t,
                'b1': i.conn_setup.conn_member.b,
                'h1': i.conn_setup.conn_member.b,
                'fy': i.conn_setup.steel_grade,
                'angle': i.conn_setup.c_angle,
                'comparison': ( i.idea_results.Nrd_idea / i.results.Nrd),
                'betta': i.results.res_dict['betta'],
                'gamma': i.results.res_dict['gamma'],
                'idea_res': i.idea_results.Nrd_idea,
                'analy_res': i.results.Nrd,
                'conn_type': i.conn_setup.conn_type

                }


        dicts.append(data_dict)


    return dicts




def idea_res_to_code_refactor(file_path: str, parent_path:Path, **query_params) -> None:
    """
    Generate plotting code from IDEA results using dynamic query parameters.

    Parameters:
      file_path (str): Path to the file; the basename without extension is used to derive 'conn_type'.
      **query_params: Dynamic filtering parameters, which may include:
          - angle (int)
          - steel_grade (int)  [if provided, remapped to 'steel']
          - m_perc (float)
          - n_perc (float)
          - nrd_direction (str)
          ... or any additional filtering key expected by calc_res_from_calculated.
          :param file_path:
          :param parent_path:
    """

    # Remove the file extension and extract the basename as 'conn_type'
    without_extension = os.path.splitext(file_path)[0]
    conn_type = os.path.basename(without_extension)
    query_params["conn_type"] = conn_type

    # If the parameter 'steel_grade' was passed, remap it to 'steel'
    if "steel_grade" in query_params:
        query_params["steel"] = query_params.pop("steel_grade")

    # Retrieve calculated results from the DB using dynamic parameters
    calculated = calc_res_from_calculated(file_path, **query_params)

    if not calculated:
        print('\n' + "Warning: No calculated results available. Skipping data generation." + '\n')
        return

    # Generate the data dictionary for plotting
    data_for_plotting = dict_generator(calculated)

    # Extract base parameters from the results for title generation
    first_code = 'CBFEM'
    second_code: str = calculated[0].conn_setup.code_standard

    # Retrieve additional optional parameters for the title from query_params
    m_perc: float = query_params.get("m_perc")
    n_perc: float = query_params.get("n_perc")
    nrd_direction = query_params.get("nrd_direction")
    steel_grade: str = str(query_params.get("steel"))
    angle_of_conn: str = str(query_params.get("angle"))


    # Generate the dynamic title and label; title_generator will omit parameters that are None.
    comparison_title, plot_res_label = title_generator_refactor(
        first_code, second_code, conn_type, steel_grade, angle_of_conn,
        m_perc, n_perc, nrd_direction
    )
    time_a = time.time()

    print('Start printing')

    # Plot the data using the generated title and label.
    dict_plotter(data_for_plotting, 'd0', comparison_title, plot_res_label, parent_path)

    print(f'Dict plotter running time is {time_a - time.time()} seconds')

    return


def duplicates_filtering(data: list[MainCalculationInfo]) -> list[MainCalculationInfo]:
    seen = set()  # To track unique conn_member values
    unique_data = []  # To store non-duplicate items

    for item in data:
        conn = item.conn_setup.chord.name + item.conn_setup.conn_member.name + str(item.perc_chord_M) +str(item.perc_chord_N) +str(item.conn_setup.c_angle) + item.conn_setup.steel_grade_str
        if conn not in seen:
            seen.add(conn)
            unique_data.append(item)

    return unique_data

if __name__ == "__main__" :
    idea_res_to_code_refactor(r'../../Code_Config_yaml/EN/CHS_X.yaml', angle=45, steel_grade=235, m_perc=-0.45, n_perc=-0.45, nrd_direction='-')




import time
import yaml
import numexpr
from dataclasses import asdict
from typing import Any, Union
import math
import json
import numexpr as ne
from itertools import product

from src.calc.base_classes import BaseGeometry, RectangleHollow, ConfigConn, ConnSetup, CodeRes, MainCalculationInfo
from src.calc.gen_sample_helper.code_check import get_css_class, get_steel_str
from src.calc.gen_sample_helper.csv_fetching import get_cross_sections



def get_steel_topology(base_geometries:list[Union[BaseGeometry, RectangleHollow]], steel_g:int) -> list[Union[
    BaseGeometry, RectangleHollow]]:

    """Add steel to conn, for c-s class definition"""

    steel_angle_samples = []

    steel_to_set = steel_g * 1e6
    steel_str = get_steel_str(steel_g)

    for base_geometry in base_geometries:

        # set steel to chord
        base_geometry.steel_grade = steel_to_set
        base_geometry.steel_grade_str = steel_str

        steel_angle_samples.append(base_geometry)


    return steel_angle_samples


def generate_samples(model_definition_filename:str, nrd_direction:str,m_el_perc:float, n_perc:float, steel_g:int) -> list[
    ConnSetup]:

    with open(model_definition_filename, 'r') as f:
        model_definition:dict = yaml.load(f, yaml.FullLoader)

    code_stand = model_definition['code_standard']


    chord_type = model_definition['profiles']['chord']['type']

    chord_samples = get_cross_sections(chord_type)

    chord_css = get_steel_topology(chord_samples, steel_g)

    assign_css_class(chord_css, code_stand, chord_type, m_el_perc, n_perc)


    connected_member_type = model_definition['profiles']['connected_member']['type']

    connected_member_samples = get_cross_sections(connected_member_type)

    connected_member_css = get_steel_topology(connected_member_samples, steel_g)

    assign_css_class(connected_member_css, code_stand, chord_type, m_el_perc, n_perc)


    # check conditions
    conditions = model_definition['validity_conditions']

    config_yaml = ConfigConn(
        profiles_chord=model_definition["profiles"]['chord']['type'],
        profiles_conn_m=model_definition["profiles"]['connected_member']['type'],
        validity_conditions=model_definition['validity_conditions'],
        idea_conn_path=model_definition['idea_conn_path'],
        equations=model_definition['equations'],
        add_exlus_conds=model_definition.get('additional_exclusion', None)
    )

    ### find out if compression of chord or connected member need to be checked
    mem_compr = 1 if (n_perc < 0) or (m_el_perc < 0)  else 0

    # list of validated css in connection
    list_of_validated = []

    # list of excluded because criteria of the code
    list_of_excluded = []

    # Combine conditions into a single expression
    combined_expr = " & ".join(f"({cond})" for cond in conditions)


    for one_chord, one_connected_member  in product(chord_css,connected_member_css):

        main_class = ConnSetup(
            conn_type=model_definition["connection_type"],
            code_standard=model_definition["code_standard"],
            config_=config_yaml,
            nrd_direction=nrd_direction

        )
        main_class.chord = one_chord
        main_class.conn_member = one_connected_member

        all_conditions_satisfied = True

        condition_to_check = {

            "chord_d": main_class.chord.d,
            "chord_t": main_class.chord.t,

            "connected_m_d": main_class.conn_member.d,
            "connected_m_t": main_class.conn_member.t,

            "d_0": main_class.chord.d,
            "t_0": main_class.chord.t,

            "d_1": main_class.conn_member.d,
            "t_1": main_class.conn_member.t,

            "b_0": main_class.chord.get_base('b', 0),
            "h_0": main_class.chord.get_base('h', 0),

            "b_1": main_class.conn_member.get_base('b',0),
            "h_1": main_class.conn_member.get_base('h',0),

            'nrd_dir':mem_compr,

            'csc_chord': main_class.chord.css_class,
            'csc_conn_mem': main_class.conn_member.css_class,

        }

        # #This code for debugging if cond is set correct in Yaml
        #
        # for cond in conditions:
        #
        #     cond_results = numexpr.evaluate(cond, condition_to_check)
        #
        #     if not cond_results:
        #
        #         exclude_reason = f'Exclude reason is {cond}'
        #         main_class.exclude_reason = exclude_reason
        #
        #         all_conditions_satisfied = False
        #         break
        #
        #     if all_conditions_satisfied is True:
        #
        #         list_of_validated.append(main_class)


        # Evaluate combined conditions once
        if ne.evaluate(combined_expr, condition_to_check):
            list_of_validated.append(main_class)

        else:
            main_class.exclude_reason = f"Combined condition failed: {combined_expr}"
            list_of_excluded.append(main_class)

    return list_of_validated


def get_stl_and_angle_conn(generated_samples:list[ConnSetup], steel_gg: int, angle_gg: float) -> list[ConnSetup] :

    """Add steel and angle to connection"""

    steel_angle_samples = []

    steel_to_set = steel_gg * 1e6
    steel_str = get_steel_str(steel_gg)
    angle: float = angle_gg

    for geometry_sample in generated_samples:

        # set steel to main class
        geometry_sample.c_angle = angle
        geometry_sample.steel_grade = steel_to_set
        geometry_sample.steel_grade_str = steel_str

        steel_angle_samples.append(geometry_sample)


    return steel_angle_samples


def assign_css_class(mat_samples:list[Union[BaseGeometry, RectangleHollow]], code_standard:str, cs_type:str, m_el_perc:float, n_perc:float)-> None :



    for mat_sample in mat_samples:

        mat_sample.css_class = get_css_class(mat_sample, code_standard, cs_type, m_el_perc, n_perc)

    return


def get_loading(steel_angle_samples:list[ConnSetup], M_el_percantage:float, N_percantage:float) -> list[
    MainCalculationInfo]:

    loaded_samples = []


    for steel_angle_sample in steel_angle_samples:

        load_sample = MainCalculationInfo(
            conn_setup=steel_angle_sample,
            perc_chord_M=M_el_percantage,
            perc_chord_N=N_percantage
        )

        loaded_samples.append(load_sample)



    return loaded_samples



def yaml_calculator(equations:dict[str:Any], variables:dict[str,float]) -> dict[str, float] :

    calculated_eqations = {}
    for equation, calc in equations.items():

        try:
            # Evaluate the expression using numexpr
            result = ne.evaluate(calc, local_dict=variables)
            # Store the evaluated result in variables
            variables[equation] = result.item()
            calculated_eqations[equation] = result.item()
        except Exception as e1:
            er1 = (f"numexpr failed for {calc}: {e1}, falling back to eval()")

            try:
                # Evaluate the expression using numexpr
                result = eval(calc, {}, variables)
                # Store the evaluated result in variables
                variables[equation] = result
                calculated_eqations[equation] = result
            except Exception as e2:
                er2 = f"eval() also failed for {calc}: {e2}"

                raise ValueError(f"Both evaluation methods failed for '{calc}'.\n"
                                 f"numexpr error: {er1}\n"
                                 f"eval error: {er2}")

    if "math" in variables:
        del variables['math']


    return variables


def code_calc(prepared_samples:list[MainCalculationInfo], calculation_phase:str) ->list[MainCalculationInfo]:

    """
    Code calc of the tubes connection acc. to EN or AISC or Fpr_EN
    :param prepared_samples:
    :return:
    """
    code_calculated_samples = []

    for prepared_sample in prepared_samples:

        equations = prepared_sample.conn_setup.config_.equations

        variables_for_calc = {
            'b_0': prepared_sample.conn_setup.chord.get_base("b", 0),
            'h_0': prepared_sample.conn_setup.chord.get_base("h", 0),
            't_0': prepared_sample.conn_setup.chord.t,
            'd_0': prepared_sample.conn_setup.chord.d,
            'csc_chord':prepared_sample.conn_setup.chord.css_class,

            'b_1': prepared_sample.conn_setup.conn_member.get_base("b", 0),
            'h_1': prepared_sample.conn_setup.conn_member.get_base("h", 0),
            't_1': prepared_sample.conn_setup.conn_member.t,
            'd_1': prepared_sample.conn_setup.conn_member.d,
            'csc_conn_memb': prepared_sample.conn_setup.conn_member.css_class,

            'thetta_1': prepared_sample.conn_setup.c_angle,
            'fy_0': prepared_sample.conn_setup.steel_grade,

            'A_0': prepared_sample.conn_setup.chord.A,
            'W_0': prepared_sample.conn_setup.chord.W_el,
            'W_0_pl':prepared_sample.conn_setup.chord.W_pl,
            'I_0': prepared_sample.conn_setup.chord.I,

            'A_1': prepared_sample.conn_setup.conn_member.A,
            'W_1': prepared_sample.conn_setup.conn_member.W_el,
            'W_1_pl': prepared_sample.conn_setup.conn_member.W_pl,
            'I_1': prepared_sample.conn_setup.conn_member.I,

            'N_chord': prepared_sample.N_chord,
            'M_chord': prepared_sample.M_chord,
            'math': math,

            'd_0_end_length': prepared_sample.end_length_idea,
            'N_cbfem': 0,
            'perc_analyz': 0,
            'n_dir': prepared_sample.conn_setup.nrd_direction
            
        }

        if calculation_phase == 'post':
            variables_for_calc |= {
                'N_cbfem': prepared_sample.idea_results.Nrd_idea,
                'd_0_end_length': prepared_sample.end_length_idea,
                'perc_analyz':prepared_sample.idea_results.analysis_perc,
            }

        hand_calc_results = yaml_calculator(equations, variables_for_calc)

        detailed_result = CodeRes(
            Nrd=hand_calc_results['Nrd'],
            kp_my_sql_key=hand_calc_results['kp_my_sql_key'],
            res_dict=hand_calc_results,
        )

        prepared_sample.results = detailed_result


        code_calculated_samples.append(prepared_sample)

    return code_calculated_samples


def assign_my_sql_key(loaded_samples:list[MainCalculationInfo]) -> None :

    for loaded_sample in loaded_samples:

        code = loaded_sample.conn_setup.code_standard

        conn_type = loaded_sample.conn_setup.conn_type

        chord_name = loaded_sample.conn_setup.chord.name

        connected_member_name = loaded_sample.conn_setup.conn_member.name

        kp = str(loaded_sample.perc_chord_N)

        m_perc = str(loaded_sample.perc_chord_M)

        n_perc = str(loaded_sample.perc_chord_N)

        loaded_sample.my_sql_key = f'{conn_type}_{chord_name}_{connected_member_name}_m_{m_perc}_n_{n_perc}'


    return None


def additional_excluding(calculated_samples:list[MainCalculationInfo]) ->list[MainCalculationInfo]:

    not_excluded = []

    for calculated_sample in calculated_samples:

        results_validity = True

        if  calculated_sample.results.Nrd > calculated_sample.conn_setup.conn_member.N_max :

            results_validity = False

        if calculated_sample.conn_setup.config_.add_exlus_conds:

            for additional_excl_condition in calculated_sample.conn_setup.config_.add_exlus_conds:

                data_to_check:dict = calculated_sample.results.res_dict

                cond_res = numexpr.evaluate(additional_excl_condition, data_to_check)

                if not cond_res:

                    exculde_reason = f'Exclude reason is {additional_excl_condition}'

                    calculated_sample.exclude_reason = exculde_reason

                    results_validity = False
                    break



        if results_validity is True:

            not_excluded.append(calculated_sample)



    return not_excluded


def sample_generation(config_path:str, nrd_sign:str, m_el_perc:float, n_perc:float, steel_g:int, angle_conn: float) -> list[
    MainCalculationInfo]:

    # recording of the data need to added

    time_start = time.time()

    samples:list[ConnSetup] = generate_samples(config_path, nrd_sign, m_el_perc, n_perc, steel_g)

    prepared_samples = get_stl_and_angle_conn(samples, steel_g, angle_conn)

    loaded_samples:list[MainCalculationInfo] = get_loading(prepared_samples, m_el_perc, n_perc)

    assign_my_sql_key(loaded_samples)

    css_excluded = (loaded_samples)

    code_calculated = code_calc(css_excluded, 'pre')

    nrd_valid_samples = additional_excluding(code_calculated)

    time_finish = time.time()

    script_speed = time_finish - time_start

    print(f'Script generate_sample speed is {script_speed}' + '\n')

    print(f'Length of excluded connections due cross section class and N_max brace resistancce   {len(nrd_valid_samples)- len(code_calculated)}'+ '\n')

    print(f'Length of valid connections {len(nrd_valid_samples)}'+ '\n')


    return nrd_valid_samples


def main():

    data_generated = sample_generation(r'../../Code_Config_yaml/EN/CHS_X.yaml', '-', 0, -0.45, 355, 45)


if __name__ == "__main__":
    main()




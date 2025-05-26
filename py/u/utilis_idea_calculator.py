import math
from typing import Any
from ideastatica_connection_api import ConMprlCrossSection, ConMember

import py.calc.gen_sample_helper.csv_fetching
from .utilis_data_import import dict_for_db_recoding, add_to_db_single
from py.calc.generate_samples import yaml_calculator
from py.calc.base_classes import IdeaLoad, MainCalculationInfo


def get_result(raw_results, name: str) -> float:
    deserved_res = None

    if name != "buckling":
        # iteration through dicts
        for outer_key, inner_dicts in raw_results['summary'].items():
            for inner_key, value in inner_dicts.items():
                if name == value:
                    deserved_res = inner_dicts['checkValue']
                    break
        if deserved_res is None or deserved_res < 0:
            return 0
        return float(deserved_res)
    else:
        # iteration through dicts
        for outer_key, inner_dicts in raw_results['summary'].items():
            for inner_key, value in inner_dicts.items():
                if name == value:
                    if inner_dicts['checkValue'] != 0:
                        deserved_res = inner_dicts['checkValue']
                        break
                    elif inner_dicts['limit'] != 0:
                        deserved_res = inner_dicts['limit']
                        break

        if deserved_res is None or deserved_res < 0:
            return 0
        return float(deserved_res)


def get_member_id(members_idea:list[ConMember], model_beam_name:str) -> int|None:
    for m in range(len(members_idea)):
        if members_idea[m].name == model_beam_name:
            member_id = members_idea[m].id
            return member_id  # Return immediately if a match is found

    # If we finish the loop without finding a match, raise an exception
    raise ValueError(f"Member name '{model_beam_name}' not found in the model")


def get_member_loading_id(member_loadings, member_id, position:str) -> int|None:
    for item in range(len(member_loadings)):
        if member_loadings[item].member_id == member_id and member_loadings[item].position == position:
            num_in_list = item
            return num_in_list

    raise ValueError(f"Member id '{member_id}' or load position {position}  not found in the model")


def get_loading(api_client, project_id, api_member, project_item, model_name: str, force: str, position: str,
                model_project_item: int) -> float:
    # Instance for load effect
    api_load = api_client.load_effect
    # Call info for all connection item
    all_load_effects = api_load.get_load_effects(project_id, model_project_item)
    # assuming that there is only one load case in .ideaCon
    load_effect = all_load_effects[0]
    # list of loading on the member
    members_list = load_effect.member_loadings

    members = api_member.get_members(project_id, project_item)

    # get member id acc. to name of member
    member_id = get_member_id(members, model_name)
    # get number in list acc. to name and loaded end
    num_in_list = get_member_loading_id(members_list,member_id,position)

    # Iterate through member end
    member_end = members_list[num_in_list]

    # Iterate trough load effect: n, vz, vy, mz, my, mx
    n_value = getattr(member_end.section_load, force)
    return n_value


def my_range(start, end, step):
    while start <= end:
        yield start
        start += step


def exclude_from_eval(calculation:MainCalculationInfo, db_writing:int, lps:float) -> bool:

    res_validity = True
    # Define exclusion criteria and reasons in a list of tuples
    exclusion_criteria = [
        (calculation.idea_results.analysis_perc >= 1.0,
         f"analysis percentage {calculation.idea_results.analysis_perc} is higher than 1"),

        (calculation.results.Nrd_recalc > calculation.conn_setup.conn_member.N_max,
         f"Nrd_recalc {calculation.results.Nrd_recalc} > N_max {calculation.conn_setup.conn_member.N_max}"),

        (calculation.idea_results.min_weld_parts > calculation.idea_results.weld_parts,
         f"min_weld_parts {calculation.idea_results.min_weld_parts} > weld_parts {calculation.idea_results.weld_parts}"),

        (calculation.idea_results.conn_member_strain > calculation.idea_results.chord_strain and calculation.idea_results.conn_member_strain > (lps / 2),
         f"Connected member strain {round(calculation.idea_results.conn_member_strain,4)} >  chord strain {round(calculation.idea_results.chord_strain,4)} and connected member strain {round(calculation.idea_results.conn_member_strain,4)} > (lps/2) {lps/2}")
    ]

    # Check each exclusion criterion
    for condition, reason in exclusion_criteria:
        if condition:
            print(f'connection{calculation.my_sql_key} is excluded because {reason}')
            res_validity = False

            calculation.conn_setup.exclude_reason = reason
            prep_excluded_to_db = dict_for_db_recoding(calculation, "excluded_from_eval")

            if db_writing != 0:
                add_to_db_single("excluded_from_eval", prep_excluded_to_db)
            else:
                print("Excluded Not recorded to db")

            break  # Exit the loop on the first exclusion reason

    return res_validity


def recalculate_kp(sample: MainCalculationInfo) -> dict[str, Any]:

    recalc_equations = sample.conn_setup.config_.equations

    N_chord_new = (sample.N_chord * sample.idea_results.analysis_perc)

    M_chord_new = (sample.M_chord * sample.idea_results.analysis_perc)

    hand_calc_res = {
        'b_0': sample.conn_setup.chord.get_base("b", 0),
        'h_0': sample.conn_setup.chord.get_base("h", 0),
        't_0': sample.conn_setup.chord.t,
        'd_0': sample.conn_setup.chord.d,
        'csc_chord': sample.conn_setup.chord.css_class,

        'b_1': sample.conn_setup.conn_member.get_base("b", 0),
        'h_1': sample.conn_setup.conn_member.get_base("h", 0),
        't_1': sample.conn_setup.conn_member.t,
        'd_1': sample.conn_setup.conn_member.d,
        'csc_conn_memb': sample.conn_setup.conn_member.css_class,

        'thetta_1': sample.conn_setup.c_angle,
        'fy_0': sample.conn_setup.steel_grade,

        'A_0': sample.conn_setup.chord.A,
        'W_0': sample.conn_setup.chord.W_el,
        'W_0_pl': sample.conn_setup.chord.W_pl,
        'I_0': sample.conn_setup.chord.I,

        'A_1': sample.conn_setup.conn_member.A,
        'W_1': sample.conn_setup.conn_member.W_el,
        'W_1_pl': sample.conn_setup.conn_member.W_pl,
        'I_1': sample.conn_setup.conn_member.I,

        'N_chord': N_chord_new,
        'M_chord': M_chord_new,
        'math': math,
    }

    recalculated_code_res = yaml_calculator(recalc_equations, hand_calc_res)


    return recalculated_code_res


def set_css_id(api_member, project_id, project_item, api_material, beam_name_in_idea_model: str, css_profile: str,
               steel: str, project_id_: str) -> ConMember :

    members = api_member.get_members(project_id, project_item)

    chord_css_set:ConMprlCrossSection = ConMprlCrossSection(
        materialName=steel,
        mprlName=css_profile
    )

    api_material.add_cross_section(project_id, chord_css_set)

    actual_css = api_material.get_cross_sections(project_id)

    chord_css_id = [css['id'] for css in actual_css if css['name'] == css_profile]

    chord_member = [item for item in members if item.name == beam_name_in_idea_model]

    chord_member[0].cross_section_id = chord_css_id[0]

    update_css = api_member.update_member(project_id, project_item, chord_member[0])

    return update_css


def assign_new_load_effects(api_loading, project_id, project_item, chord: ConMember, conn_m: ConMember,
                            info_hand_calc: MainCalculationInfo) -> None:

    all_load_effects = api_loading.get_load_effects(project_id, project_item)

    load_id = all_load_effects[0].id

    new_chord_loading = [item for item in all_load_effects[0].member_loadings if item.member_id == chord.id]

    new_connected_m_loading = [item for item in all_load_effects[0].member_loadings if item.member_id == conn_m.id]

    for i in new_connected_m_loading:
        for force, value in i.section_load:
            if force == "n":
                setattr(i.section_load, "n", info_hand_calc.idea_loading.conn_member_end.n)
            elif hasattr(i.section_load, force):
                setattr(i.section_load, force, 0)


    for i in new_chord_loading:
        if i.position == "End":

            for force, value in i.section_load:

                if force == "n":
                    i.section_load.n = info_hand_calc.idea_loading.chord_end.n
                elif force == "my":
                    i.section_load.my = info_hand_calc.idea_loading.chord_end.my
                elif force == "vz":
                    i.section_load.vz = info_hand_calc.idea_loading.chord_end.vz


                else:

                    if hasattr(i.section_load, force):
                        setattr(i.section_load, force, 0)

        # begin is left

        elif i.position == "Begin":

            for force, value in i.section_load:

                if force == "n":
                    i.section_load.n = info_hand_calc.idea_loading.chord_begin.n
                elif force == "my":
                    i.section_load.my = info_hand_calc.idea_loading.chord_begin.my
                elif force == "vz":
                    i.section_load.vz = info_hand_calc.idea_loading.chord_begin.vz

                else:
                    if hasattr(i.section_load, force):
                        setattr(i.section_load, force, 0)

    api_loading.update_load_effect(project_id, project_item, all_load_effects[0])

    return None


def assign_new_load_chord(api_loading, project_id, project_item, chord: ConMember,
                          info_hand_calc: MainCalculationInfo) -> None:

    all_load_effects = api_loading.get_load_effects(project_id, project_item)

    load_id = all_load_effects[0].id

    new_chord_loading = [item for item in all_load_effects[0].member_loadings if item.member_id == chord.id]

    for i in new_chord_loading:
        if i.position == "End":

            for force, value in i.section_load:

                if force == "n":
                    i.section_load.n = info_hand_calc.idea_loading.chord_end.n
                elif force == "my":
                    i.section_load.my = info_hand_calc.idea_loading.chord_end.my
                elif force == "vz":
                    i.section_load.vz = info_hand_calc.idea_loading.chord_end.vz


                else:

                    if hasattr(i.section_load, force):
                        setattr(i.section_load, force, 0)

        # begin is left

        elif i.position == "Begin":

            for force, value in i.section_load:

                if force == "n":
                    i.section_load.n = info_hand_calc.idea_loading.chord_begin.n
                elif force == "my":
                    i.section_load.my = info_hand_calc.idea_loading.chord_begin.my
                elif force == "vz":
                    i.section_load.vz = info_hand_calc.idea_loading.chord_begin.vz

                else:
                    if hasattr(i.section_load, force):
                        setattr(i.section_load, force, 0)

    api_loading.update_load_effect(project_id, project_item, all_load_effects[0])

    return None


def assign_new_load_connected_m(api_loading, project_id, project_item, conn_m: ConMember, conn_member_end: IdeaLoad) -> None:

    all_load_effects = api_loading.get_load_effects(project_id, project_item)

    load_id = all_load_effects[0].id

    new_connected_m_loading = [item for item in all_load_effects[0].member_loadings if item.member_id == conn_m.id]

    for i in new_connected_m_loading:
        for force, value in i.section_load:
            if force == "n":
                setattr(i.section_load, "n", conn_member_end.n)
            elif hasattr(i.section_load, force):
                setattr(i.section_load, force, 0)

    api_loading.update_load_effect(project_id, project_item, all_load_effects[0])

    return None





def get_plate_strain(actual_division_of_the_chs:int, chs_divis_conn_member:int, plates_all_data: dict[str, dict]) -> (float, float):

    if len(plates_all_data) == 2:

        for key_dict, dict in plates_all_data.items():

            chs_number:int = len(dict['items'])

            if 'chord' == dict['name']:
                chord_strain_act  = dict['maxStrain']

            elif 'connected_m' == dict['name'] :

                conn_member_strain_act = dict['maxStrain']
            else:
                print("")

        return chord_strain_act, conn_member_strain_act

    elif  4 > len(plates_all_data) > 2:
        max_strain_conn_member = 0

        for key_dict, dict in plates_all_data.items():

            chs_number: int = len(dict['items'])

            if 'chord' == dict['name']:
                chord_strain_act = dict['maxStrain']
                continue

            conn_mem_str = dict['maxStrain']

            if conn_mem_str > max_strain_conn_member:

                max_strain_conn_member = conn_mem_str

        conn_member_strain_act = max_strain_conn_member

        return chord_strain_act, conn_member_strain_act



if __name__ == '__main__':

    print('script utilis_idea_calculator.py is running')
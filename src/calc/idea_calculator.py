import copy
from collections import Counter

import ideastatica_connection_api
import ideastatica_connection_api.ideastatica_client as idea_client
import os
import json
from src.u.utilis_idea_calculator import get_result, get_loading, exclude_from_eval, recalculate_kp, set_css_id, \
    assign_new_load_effects, assign_new_load_chord, assign_new_load_connected_m, get_plate_strain
from src.u.utilis_data_import import get_data_from_DB, valid_recording
from src.u.utils_data_plotting import get_root_dir_path
from src.calc.base_classes import IdeaRes, MainCalculationInfo
from idea_load_generator import run_load_generator
import math
import time
import subprocess
from pathlib import Path
import random

def idea_calculator(prepared_for_idea:MainCalculationInfo, db_writing:int) -> MainCalculationInfo :

    baseUrl = "http://localhost:5000"

    config_yaml = prepared_for_idea.conn_setup.config_

    chord_info = prepared_for_idea.conn_setup.chord

    connected_member_info = prepared_for_idea.conn_setup.conn_member


    # Defining the host is optional and defaults to http://localhost
    # See configuration.src for a list of all supported configuration parameters.
    configuration = ideastatica_connection_api.Configuration(
        host=baseUrl
    )
    # to run script from elsewhere, but need to explicitly fill the path
    # dir_path = os.path.dirname(os.path.realpath(__file__))
    #project_file_path = os.path.join(dir_path,"idea_model" ,"chs_y.ideaCon")

    # to run script from project directory
    script_dir:Path = get_root_dir_path()
    project_file_path = (script_dir/ config_yaml.idea_conn_path)



    # Enter a context with an instance of the API client
    with idea_client.IdeaStatiCaClient(configuration, project_file_path) as api_client:

        # get project data
        project_id = api_client.project_id

        project_data = api_client.project.get_project_data(project_id)


        # Get API for connections in the project
        api_conn = api_client.connection

        # Get member connection API
        api_member = api_client.member

        api_material = api_client.material

        api_parameter = api_client.parameter

        # get api loading

        api_loading = api_client.load_effect

        # Get list of all connections in the project
        connections = api_conn.get_connections(project_id)

        api_project = api_client.project

        # Get code setup
        code_setup = api_project.get_setup(project_id)

        if prepared_for_idea.conn_setup.conn_type[:3] == "RHS":

            actual_division_of_the_chs = (getattr(code_setup,"division_of_arcs_of_rhs") + 1) * 4

        else:
            actual_division_of_the_chs = getattr(code_setup, 'division_of_surface_of_chs')

        if  0 < prepared_for_idea.conn_setup.steel_grade < 420e6:

            limit_plasti_strain_actual = getattr(code_setup,'limit_plastic_strain')

        else:
            limit_plasti_strain_actual = getattr(code_setup,'hss_limit_plastic_strain')

        # loop for calc all cons in .ideaCon file
        i = -1
        for conn in connections:

            print(f"Calc of {chord_info.name} and {connected_member_info.name}")

            i = i + 1
            project_item = connections[i].id

            new_chord = set_css_id(api_member, project_id, project_item, api_material, "chord", chord_info.name,
                                   chord_info.steel_grade_str, project_id)

            debug = api_material.get_cross_sections(project_id)

            members_debug = api_member.get_members(project_id, project_item)

            new_connected_m = set_css_id(api_member, project_id, project_item, api_material, 'connected_m',
                                         connected_member_info.name, connected_member_info.steel_grade_str, project_id)

            # actual_parameter = api_parameter.get_parameters(project_id, project_item)
            #
            # for param in actual_parameter:
            #     if param.key == 'angle':
            #         param.value = 60
            #
            #         upd = {
            #             f"{param.key}": param.value
            #         }
            #
            #
            # param_upd = api_parameter.update_parameters(project_id, project_item, [upd])


            if prepared_for_idea.conn_setup.conn_type == "CHS_X":
                second_connected_m = set_css_id(api_member, project_id, project_item, api_material, 'connected_m_2',
                                                connected_member_info.name, connected_member_info.steel_grade_str,
                                                project_id)

                assign_new_load_chord(api_loading, project_id, project_item, new_chord, prepared_for_idea)

                assign_new_load_connected_m(api_loading, project_id, project_item, new_connected_m,
                                            prepared_for_idea.idea_loading.conn_member_end)

                assign_new_load_connected_m(api_loading, project_id, project_item, second_connected_m,
                                            prepared_for_idea.idea_loading.conn_member_end)

            elif prepared_for_idea.conn_setup.conn_type == "CHS_T_and_Y" or prepared_for_idea.conn_setup.conn_type == "RHS_T_and_Y" :
                assign_new_load_effects(api_loading, project_id, project_item, new_chord, new_connected_m,
                                        prepared_for_idea)

            elif prepared_for_idea.conn_setup.conn_type == "CHS_K":
                second_connected_m = set_css_id(api_member, project_id, project_item, api_material, 'connected_m_2',
                                                connected_member_info.name, connected_member_info.steel_grade_str,
                                                project_id)

                assign_new_load_chord(api_loading, project_id, project_item, new_chord, prepared_for_idea)

                assign_new_load_connected_m(api_loading, project_id, project_item, new_connected_m,
                                            prepared_for_idea.idea_loading.conn_member_end)

                assign_new_load_connected_m(api_loading, project_id, project_item, second_connected_m,
                                            prepared_for_idea.idea_loading.conn_member_2_end)

            #members_debug2 = api_member.get_members(project_id, project_item)

            actual_force = get_loading(api_client, project_id, api_member, project_item, 'connected_m', "n", "End",
                                       project_item)


            # get calculation API for the active project
            api_calc = api_client.calculation

            # run stress-strain CBFEM analysis for the connection id = 1
            calcParams = ideastatica_connection_api.ConCalculationParameter()
            calcParams.connection_ids = [project_item]


            time_1 =time.time()
            # get detailed results
            results_text = api_calc.get_raw_json_results(project_id, calcParams)
            #print(f"Raw results 2: {results_text}")
            time_2 = time.time()
            time_of_solver_run = round(time_2 - time_1, 5)


            # this assume only one weld in the connection for x ok k there need more comprehensive solution
            raw_results:dict = json.loads(results_text[0])


            plates_all_data:dict[str,dict] = raw_results['plates']
            results_summary_all_data:dict[str,dict] = raw_results['summary']

            d0 = prepared_for_idea.conn_setup.chord.d
            d1 = prepared_for_idea.conn_setup.conn_member.d


            if prepared_for_idea.conn_setup.conn_type == 'RHS_T_and_Y':
                d0 = prepared_for_idea.conn_setup.chord.b
                d1 = prepared_for_idea.conn_setup.conn_member.b
                chs_divis_conn_member = int(4 * (getattr(code_setup,"division_of_arcs_of_rhs") + 1))

            else:
                chs_divis_conn_member = int((d1 / d0) * actual_division_of_the_chs)


            chord_strain_act, conn_member_strain_act = get_plate_strain(actual_division_of_the_chs, chs_divis_conn_member, plates_all_data)


            welds_all_data = raw_results['welds']

            first_weld_item = next(iter(welds_all_data.items()))

            actual_weld_parts = len(first_weld_item[1]['items'])

            if len(welds_all_data) > 1:

                weld_part = 0

                for i, k in welds_all_data.items():
                    weld_ac = len(k['items'])

                    if weld_ac > weld_part:
                        weld_part = weld_ac

                print(f'Min weld parts from the hole conn is {weld_part}')

                actual_weld_parts = weld_part

            min_weld_parts = int(math.floor(((d1 / d0) * actual_division_of_the_chs)))

            weld_parts_tolerance = int(math.floor(max((min_weld_parts * 0.1), 4)))

            min_weld_parts_tolerated = min_weld_parts - weld_parts_tolerance

            # get results check based on name,for example if bolt isnt present value 0 is returned

            summary_res_analysis = get_result(raw_results, "Analysis")
            summary_res_plates = get_result(raw_results, 'Plates') * 100
            summary_res_bolts = get_result(raw_results, "Bolts") * 100
            summary_res_welds = get_result(raw_results, "Welds") * 100
            # get buckling factor acc. to load resistance
            # BUCKLING factor is calculated acc.to actual forces, that are set in model

            plate_strain = summary_res_plates
            print(f'Plates = {summary_res_plates} %')

            weld_ut = summary_res_welds
            print(f'Welds = {summary_res_welds} %')

            bolt_ut = summary_res_bolts
            print(f'Bolts = {summary_res_bolts} %')

            capacity_idea = abs(summary_res_analysis * actual_force)

            print(f'Capacity in N = {capacity_idea}')

            # analysis percent in format 84.56 %
            print(f'Analysis : {summary_res_analysis*100}%')

            # plate material
            if summary_res_plates != 0:
                plates = raw_results.get("plates", {})
                for key, pl in plates.items():
                    if pl.get("maxStrain") == summary_res_plates/100:
                        # given value of Plates_mat is in MPa
                        plates_mat = float(pl.get("materialFy"))
                        break
            else:
                plates_mat = str(0)

            prepared_for_idea.idea_results = IdeaRes(
                Nrd_idea=capacity_idea,
                fy=plates_mat,
                analysis_perc=summary_res_analysis,
                division_of_the_chs=actual_division_of_the_chs,
                weld_parts=actual_weld_parts,
                min_weld_parts=min_weld_parts_tolerated,
                chord_strain= chord_strain_act,
                conn_member_strain=conn_member_strain_act

            )


            recalc_res = recalculate_kp(prepared_for_idea)

            prepared_for_idea.results.Nrd_recalc = recalc_res["Nrd"]

            prepared_for_idea.results.kp_my_sql_key_recalc = recalc_res["kp_my_sql_key"]

            prepared_for_idea.results.n_chord_new = recalc_res['N_chord']

            prepared_for_idea.results.m_chord_new = recalc_res['M_chord']

            prepared_for_idea.results.res_dict_recalc = recalc_res

            unq_filename = prepared_for_idea.my_sql_key + '_angle_' + str(prepared_for_idea.conn_setup.c_angle) +  '_steel_' + prepared_for_idea.conn_setup.steel_grade_str
            unq_filename = unq_filename.replace("/", "_")

            res_validity = exclude_from_eval(prepared_for_idea, db_writing, limit_plasti_strain_actual)

            valid_recording(prepared_for_idea, db_writing, res_validity)

            if prepared_for_idea.conn_setup.exclude_reason is not None:

                reason = prepared_for_idea.conn_setup.exclude_reason
                reason = reason.replace("/", "_")
                reason = reason.replace(">", "_")
                reason = reason.replace("<", "_")
                unq_filename = unq_filename + "_excluded" + f"{reason}"


            download_file_path:Path = get_root_dir_path() / 'idea_model' / 'calculated' / f'{unq_filename}.ideaCon'


            download_project = api_project.download_project(project_id, fileName=download_file_path)



            print(f'Time of the solver run: {time_of_solver_run}s')

            print()
            print()

        # close the active project on the backend
        api_project.close_project(project_id)

        return prepared_for_idea


def calc_runner(filename:str, should_record:int, nrd_direction:str, m_perc:float, n_perc:float, steel_g:int, angle_conn: float):

    query_actual_calculated = (
        "SELECT "
        "a.specification "
        "FROM analytical_res a "
        "WHERE a.conn_type = %s"
    )

    #calculated_json = get_data_from_DB(query_actual_calculated, params, "actual_for_calc")

    hand_calc_results:list[MainCalculationInfo] = run_load_generator(filename,0,nrd_direction, m_perc, n_perc,steel_g, angle_conn)

    # aa:list[MainCalculationInfo] = []
    #
    # for i in hand_calc_results:
    #     if i.conn_setup.chord.d == 0.1778 and i.conn_setup.chord.t == 0.0125 and i.conn_setup.conn_member.d == 0.1683 and i.conn_setup.conn_member.t == 0.010:
    #         aa.append(i)
    #
    # hand_calc_results = aa
    random.seed(42)

    random.shuffle(hand_calc_results)

    hand_calc_results = random.sample(hand_calc_results, min(1000, len(hand_calc_results)))
    debug = (Counter(item.conn_setup.chord.d for item in hand_calc_results))

    code_standard = hand_calc_results[0].conn_setup.code_standard
    conn_type = hand_calc_results[0].conn_setup.conn_type
    angle =  hand_calc_results[0].conn_setup.c_angle
    steel = hand_calc_results[0].conn_setup.steel_grade


    query_last_calc_idea = (
        "SELECT "
        "i.name AS exp_key, "
        "i.capacity AS Analytical_Capacity, "
        "i.conn_type AS Connection_type, "
        "i.angle AS Angle_of_the_connected_m_and_chord, "
        "i.specification "
        "FROM idea_res i "
        "WHERE i.conn_type = %s "
        "AND i.angle = %s "
        "AND i.steel_grade BETWEEN %s - 1000 AND %s + 1000 "
        "AND i.m_perc = %s "
        "AND i.n_perc = %s "
        "AND i.nrd_direction = %s "
    )

    query_last_excluded = (
        "SELECT "
        "e.name AS exp_key, "
        "e.capacity AS Analytical_Capacity, "
        "e.conn_type AS Connection_type, "
        "e.angle AS Angle_of_the_connected_m_and_chord, "
        "e.specification "
        "FROM excluded_from_eval e "
        "WHERE e.conn_type = %s "
        "AND e.angle = %s "
        "AND e.steel_grade BETWEEN %s - 1000 AND %s + 1000 "
        "AND e.m_perc = %s "
        "AND e.n_perc = %s "
        "AND e.nrd_direction = %s "
    )

    params_last_excluded = (
        conn_type,
        angle,
        steel,
        steel,
        int(m_perc*100),
        int(n_perc*100),
        nrd_direction
    )

    print()
    print()

    calculated_in_db_idea = get_data_from_DB(query_last_calc_idea,params_last_excluded,"gel_last_calc_idea")

    calculated_in_db_excluded = get_data_from_DB(query_last_excluded, params_last_excluded, "gel_last_calc_excluded")

    calculated_in_db_idea.extend(calculated_in_db_excluded)

    print(f"Number of samples for calculation {len(hand_calc_results)}")

    if calculated_in_db_idea:
        existing_keys = {i['exp_key'] for i in calculated_in_db_idea}
        hand_calc_results[:] = [j for j in hand_calc_results if j.my_sql_key not in existing_keys]

    print(f"Number of needed calculation {len(hand_calc_results)}")


    if not hand_calc_results:
        print('\n' * 2 + f'Skipping calculation, desired calc is available' + '\n' * 2)

        return print(f'Calculation done, {filename}, S{steel}, angle {angle}, n {n_perc}, m {m_perc}')

    file_path = r"C:\Program Files\IDEA StatiCa\StatiCa24.1_bakalarka\net6.0-windows\IdeaStatiCa.ConnectionRestApi.exe"

    api_run = subprocess.Popen(file_path,creationflags=subprocess.CREATE_NEW_CONSOLE)

    print("Waiting for the API service to start...")
    time.sleep(15)

    print("Service should now be running.")

    idea_calculated = []

    for hand_calc_res in hand_calc_results:

        calculation: MainCalculationInfo = idea_calculator(hand_calc_res, should_record)

        idea_calculated.append(calculation)

    api_run.kill()

    print(f'Calculation done, {filename}, S{steel}, angle {angle}, n {n_perc}, m {m_perc}')

    return idea_calculated


if __name__ == "__main__":

    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, -0.45, 355, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, -0.45, 420, 90)
    #
    #
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, -0.8, 235, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, -0.8, 355, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, -0.8, 420, 90)
    #
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, 0.45, 355, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, 0.45, 420, 90)
    #
    #
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, 0.8, 235, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, 0.8, 355, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_T_and_Y.yaml', 1, '-', 0, 0.8, 420, 90)
    # ######################################################################################################################################################
    # # #chs k
    # #calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, -0.45, 355, 30)
    # # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, -0.45, 420, 30)
    # #
    # #
    # # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, -0.8, 235, 30)
    # # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, -0.8, 355, 30)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, -0.8, 420, 30)
    #
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, 0.45, 355, 30)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, 0.45, 420, 30)
    #
    #
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, 0.8, 235, 30)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, 0.8, 355, 30)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_K.yaml', 1, '-', 0, 0.8, 420, 30)
    # ######################################################################################################################################################
    #chs k

    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, 0.45, 355, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, 0.45, 420, 90)
    #
    #
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, 0.8, 235, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, 0.8, 355, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, 0.8, 420, 90)
    #
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, -0.8, 235, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, -0.8, 355, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, -0.8, 420, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, -0.8, 550, 90)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, -0.8, 600, 90)

    calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 1, '-', 0, -0.8, 420, 30)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 0, '-', 0, -0.8, 355, 30)
    # calc_runner(r'../../Code_Config_yaml/Fpr_EN/CHS_X.yaml', 0, '-', 0, -0.8, 420, 30)



    print('calc 1 done')


import math
from generate_samples import sample_generation
from py.calc.base_classes import IdeaLoad, IdeaLoadingInfo, MainCalculationInfo


def assign_idea_load_chs_t_and_y(hand_calc_results:list[MainCalculationInfo]) -> None:

    excluded = []

    for hand_calc_res in hand_calc_results[:]:

        nrd_code = hand_calc_res.results.Nrd

        n_connected_member_max = hand_calc_res.conn_setup.conn_member.N_max

        force_scale_factor = min(1.8, ((n_connected_member_max*0.95)/nrd_code))

        angle = hand_calc_res.conn_setup.c_angle

        nrd_scaled = nrd_code * force_scale_factor

        vertical_reaction = (nrd_scaled * math.sin(( angle * math.pi) / 180.0 )) / 2

        horizontal_reaction = ( nrd_scaled * math.cos(( angle * math.pi) / 180.0 ))

        if hand_calc_res.conn_setup.nrd_direction == '-':

            end_moment: float = hand_calc_res.M_chord + (vertical_reaction * hand_calc_res.end_length_idea)

        else:
            end_moment: float = hand_calc_res.M_chord - (vertical_reaction * hand_calc_res.end_length_idea)

            # forces if + direction of the end connected member
            horizontal_reaction = horizontal_reaction * -1
            vertical_reaction = vertical_reaction * -1
            nrd_scaled = nrd_scaled * -1


        n_chord = hand_calc_res.N_chord

        m_chord = hand_calc_res.M_chord

        if abs(end_moment) > hand_calc_res.conn_setup.chord.M_max_el:

            hand_calc_res.conn_setup.exclude_reason = f'end_moment{end_moment} > hand_calc_res.M_chord{hand_calc_res.M_chord}'

            excluded.append(hand_calc_res)
            hand_calc_results.remove(hand_calc_res)
            continue

        elif ((abs(end_moment)/hand_calc_res.conn_setup.chord.M_max_pl + abs((-n_chord + horizontal_reaction))/ hand_calc_res.conn_setup.chord.N_max) >=0.95):

            hand_calc_res.conn_setup.exclude_reason = f'end_moment utilization {abs(end_moment)/hand_calc_res.conn_setup.chord.M_max_el} + normal chord_begin utilization {abs((-n_chord + horizontal_reaction))/ hand_calc_res.conn_setup.chord.N_max} > 0.95 '

            excluded.append(hand_calc_res)
            hand_calc_results.remove(hand_calc_res)
            continue

        elif ((abs(end_moment)/hand_calc_res.conn_setup.chord.M_max_pl + abs(n_chord)/ hand_calc_res.conn_setup.chord.N_max) >=0.95):

            hand_calc_res.conn_setup.exclude_reason = f'end_moment utilization {abs(end_moment)/hand_calc_res.conn_setup.chord.M_max_el} + normal chord_end utilization {abs(n_chord)/ hand_calc_res.conn_setup.chord.N_max} > 0.95 '

            excluded.append(hand_calc_res)
            hand_calc_results.remove(hand_calc_res)
            continue


        connected_member_calc = IdeaLoad(
            n=round(-nrd_scaled, 3),
            position="End"
        )



        chord_begin_calc =IdeaLoad(
            n=round((-n_chord + horizontal_reaction), 3),
            vz=round(vertical_reaction, 3),
            my=round(-m_chord, 3),
            position="Begin",
        )

        chord_end_calc =IdeaLoad(
            n=round(n_chord, 3),
            vz=round(vertical_reaction, 3),
            my=round(m_chord, 3),
            position="End",
        )

        idea_load = IdeaLoadingInfo(
            force_scale_factor=force_scale_factor,
            vertical_reaction=vertical_reaction,
            chord_end=chord_end_calc,
            chord_begin=chord_begin_calc,
            conn_member_end=connected_member_calc,
            force='n',
            beam_name_idea="connected_m",
            position="End"
        )

        hand_calc_res.idea_loading = idea_load
    print(f'Excluded due to end moment failure is {len(excluded)}')

    return None


def assign_idea_load_chs_x(hand_calc_results:list[MainCalculationInfo]) -> None:

    excluded = []

    for hand_calc_res in hand_calc_results[:]:

        nrd_code = hand_calc_res.results.Nrd

        n_connected_member_max = hand_calc_res.conn_setup.conn_member.N_max

        force_scale_factor = min(3.0, ((n_connected_member_max*0.95)/nrd_code))

        nrd_scaled = nrd_code * force_scale_factor

        n_chord = hand_calc_res.N_chord

        m_chord = hand_calc_res.M_chord
        vertical_reaction = 0.0


        connected_member_calc = IdeaLoad(
            n=round(-nrd_scaled, 3),
            position="End"
        )

        chord_begin_calc =IdeaLoad(
            n=round((-n_chord ), 3),
            my=round(-m_chord, 3),
            position="Begin",
        )

        chord_end_calc =IdeaLoad(
            n=round(n_chord, 3),
            my=round(m_chord, 3),
            position="End",
        )

        idea_load = IdeaLoadingInfo(
            force_scale_factor=force_scale_factor,
            vertical_reaction=vertical_reaction,
            chord_end=chord_end_calc,
            chord_begin=chord_begin_calc,
            conn_member_end=connected_member_calc,
            force='n',
            beam_name_idea="connected_m",
            position="End"
        )

        hand_calc_res.idea_loading = idea_load

    return None


def assign_idea_load_chs_k(hand_calc_results:list[MainCalculationInfo]) -> None:


    for hand_calc_res in hand_calc_results[:]:

        nrd_code = hand_calc_res.results.Nrd

        angle = hand_calc_res.conn_setup.c_angle

        n_connected_member_max = hand_calc_res.conn_setup.conn_member.N_max

        force_scale_factor = min(3.0, ((n_connected_member_max*0.95)/nrd_code))

        nrd_scaled = nrd_code * force_scale_factor

        n_chord = hand_calc_res.N_chord

        m_chord = hand_calc_res.M_chord
        vertical_reaction = 0.0

        horizontal_reaction = (nrd_scaled * math.cos((angle * math.pi) / 180.0))


        connected_member_1_calc = IdeaLoad(
            n=round(nrd_scaled, 3),
            position="End"
        )

        connected_member_2 = IdeaLoad(
            n=round(-nrd_scaled, 3),
            position="End"
        )


        chord_begin_calc =IdeaLoad(
            n=round((-n_chord - 2 * horizontal_reaction ), 3),
            my=round(-m_chord, 3),
            position="Begin",
        )

        chord_end_calc =IdeaLoad(
            n=round(n_chord, 3),
            my=round(m_chord, 3),
            position="End",
        )

        idea_load = IdeaLoadingInfo(
            force='n',
            beam_name_idea="connected_m",
            position="End",
            force_scale_factor=force_scale_factor,
            vertical_reaction=vertical_reaction,
            chord_end=chord_end_calc,
            chord_begin=chord_begin_calc,
            conn_member_end=connected_member_1_calc,
            conn_member_2_end=connected_member_2
        )

        hand_calc_res.idea_loading = idea_load

    return None


def run_load_generator(idea_path:str, should_record_excluded:int, nrd_direction:str, m_perc:float, n_perc:float, steel_g:int, angle_conn: float) -> list[MainCalculationInfo] :

    generated_data = sample_generation(idea_path,nrd_direction, m_perc, n_perc, steel_g, angle_conn)

    conn_type = generated_data[0].conn_setup.conn_type


    if conn_type == "CHS_T_and_Y" or conn_type == "RHS_T_and_Y":

        assign_idea_load_chs_t_and_y(generated_data)

    elif conn_type == "CHS_X":

        assign_idea_load_chs_x(generated_data)

    elif conn_type == "CHS_K":

        assign_idea_load_chs_k(generated_data)


    return generated_data



if __name__ == '__main__':

    calculated = run_load_generator()




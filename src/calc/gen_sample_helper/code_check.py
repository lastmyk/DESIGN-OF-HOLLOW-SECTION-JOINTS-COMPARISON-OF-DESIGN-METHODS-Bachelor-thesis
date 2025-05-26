from typing import Union

from src.calc.base_classes import BaseGeometry, RectangleHollow


def get_css_class(mat_sample:Union[BaseGeometry, RectangleHollow], code_standard:str, cs_type:str, m_el_perc:float, n_perc:float) -> int:

    """Cross-section class acc.to code standard defining stability class in general, based on slenderness and material

    """
    if cs_type == 'CHS':

        d = mat_sample.d
        t = mat_sample.t
        fy = mat_sample.steel_grade

        if code_standard == 'EN':

            epsilon = (235 / (fy /1e6)) ** 0.5

            if (d / t) <= 50 * (epsilon ** 2):
                cross_section_class = 1

            elif (50 * (epsilon ** 2)) < (d / t) <= (70 * (epsilon ** 2)):
                cross_section_class = 2

            elif (70 * (epsilon ** 2)) < (d / t) <= (90 * (epsilon ** 2)):
                cross_section_class = 3
            # fake class
            elif (90 * (epsilon ** 2)) < (d / t) <= (250 * (epsilon ** 2)):
                cross_section_class = 4

            else:
                raise f"Incorrect input, check your variables t {t}, d {d}, fy {fy}"

        elif code_standard == 'Fpr_EN':

            epsilon = (235 / (fy /1e6)) ** 0.5

            if (d / t) <= 50 * (epsilon ** 2):
                cross_section_class = 1

            elif (50 * (epsilon ** 2)) < (d / t) <= (70 * (epsilon ** 2)):
                cross_section_class = 2

            elif (70 * (epsilon ** 2)) < (d / t) <= (90 * (epsilon ** 2)):
                cross_section_class = 3
            # fake class
            elif (90 * (epsilon ** 2)) < (d / t) <= (1000 * (epsilon ** 2)):
                cross_section_class = 4

            else:
                raise f"Incorrect input, check your variables t {t}, d {d}, fy {fy}"

        elif code_standard == 'AISC':

            epsilon = (235 / (fy /1e6)) ** 0.5

            if (d / t) <= 50 * (epsilon ** 2):
                cross_section_class = 1

            elif (50 * (epsilon ** 2)) < (d / t) <= (70 * (epsilon ** 2)):
                cross_section_class = 2

            elif (70 * (epsilon ** 2)) < (d / t) <= (90 * (epsilon ** 2)):
                cross_section_class = 3
            # fake class
            elif (90 * (epsilon ** 2)) < (d / t) <= (250 * (epsilon ** 2)):
                cross_section_class = 4

            else:
                raise f"Incorrect input, check your variables t {t}, d {d}, fy {fy}"

        else:
            raise ValueError(f"Incorrect code standard {code_standard}")


    elif cs_type == 'RHS':

        b = mat_sample.b
        h = mat_sample.h
        t = mat_sample.t
        fy = mat_sample.steel_grade

        ri = t

        ch = h - 2*t - 2*ri

        cb = b - 2*t - 2*ri

        c = max(cb, ch)

        if n_perc != 0 and m_el_perc != 0:

            raise ValueError(f'For RHS m_el: {m_el_perc} and n: {n_perc} cant be applied together')

        elif m_el_perc == 0 and n_perc == 0:
            raise ValueError(f'Cant determinate correctly cross section class')

        elif n_perc != 0:

            if code_standard == 'EN':

                epsilon = (235 / (fy / 1e6)) ** 0.5

                if (c / t) <= 33 * (epsilon ** 2):
                    cross_section_class = 1

                elif (33 * (epsilon ** 2)) < (c / t) <= (38 * (epsilon ** 2)):
                    cross_section_class = 2

                elif (38 * (epsilon ** 2)) < (c / t) <= (42 * (epsilon ** 2)):
                    cross_section_class = 3

                else:
                    cross_section_class = 4

            elif code_standard == 'Fpr_EN':

                epsilon = (235 / (fy / 1e6)) ** 0.5

                if (c / t) <= 33 * (epsilon ** 2):
                    cross_section_class = 1

                elif (33 * (epsilon ** 2)) < (c / t) <= (38 * (epsilon ** 2)):
                    cross_section_class = 2

                elif (38 * (epsilon ** 2)) < (c / t) <= (42 * (epsilon ** 2)):
                    cross_section_class = 3

                else:
                    cross_section_class = 4

            elif code_standard == 'AISC':

                epsilon = (235 / (fy / 1e6)) ** 0.5

                if (c / t) <= 33 * (epsilon ** 2):
                    cross_section_class = 1

                elif (33 * (epsilon ** 2)) < (c / t) <= (38 * (epsilon ** 2)):
                    cross_section_class = 2

                elif (38 * (epsilon ** 2)) < (c / t) <= (42 * (epsilon ** 2)):
                    cross_section_class = 3

                else:
                    cross_section_class = 4
            else:
                raise ValueError(f"Incorrect code standard {code_standard}")

        elif m_el_perc != 0:

            if code_standard == 'EN':

                epsilon = (235 / (fy / 1e6)) ** 0.5

                if (c / t) <= 72 * (epsilon ** 2):
                    cross_section_class = 1

                elif (72 * (epsilon ** 2)) < (c / t) <= (83 * (epsilon ** 2)):
                    cross_section_class = 2

                elif (83 * (epsilon ** 2)) < (c / t) <= (124 * (epsilon ** 2)):
                    cross_section_class = 3

                else:
                    cross_section_class = 4

            elif code_standard == 'Fpr_EN':

                epsilon = (235 / (fy / 1e6)) ** 0.5

                if (c / t) <= 72 * (epsilon ** 2):
                    cross_section_class = 1

                elif (72 * (epsilon ** 2)) < (c / t) <= (83 * (epsilon ** 2)):
                    cross_section_class = 2

                elif (83 * (epsilon ** 2)) < (c / t) <= (124 * (epsilon ** 2)):
                    cross_section_class = 3

                else:
                    cross_section_class = 4

            elif code_standard == 'AISC':

                epsilon = (235 / (fy / 1e6)) ** 0.5

                if (c / t) <= 72 * (epsilon ** 2):
                    cross_section_class = 1

                elif (72 * (epsilon ** 2)) < (c / t) <= (83 * (epsilon ** 2)):
                    cross_section_class = 2

                elif (83 * (epsilon ** 2)) < (c / t) <= (124 * (epsilon ** 2)):
                    cross_section_class = 3

                else:
                    cross_section_class = 4

            else:
                raise ValueError(f"Incorrect code standard {code_standard}")

        else:
            raise ValueError(f'Incorrect loading check m {m_el_perc} or n {n_perc}')

    else:
        raise ValueError(f"Incorrect cross-section type {cs_type}")


    return int(cross_section_class)


def get_steel_str(steel_grd:int) -> str:

    if steel_grd == 235:
        stl_str = 'S 235'
    elif steel_grd == 355:
        stl_str = 'S 355'
    elif steel_grd == 420:
        stl_str = 'S 420 N/NL'
    elif steel_grd == 460:
        stl_str = 'S 460 N/NL'
    elif steel_grd == 550:
        stl_str = 'S 550 Q/QL/QL1'
    elif steel_grd == 600:
        stl_str = 'S 600 MC'
    elif steel_grd == 700:
        stl_str = 'S 700 MC'

    else:
        raise KeyError(f'Incorrect steel grade {steel_grd}')

    return stl_str

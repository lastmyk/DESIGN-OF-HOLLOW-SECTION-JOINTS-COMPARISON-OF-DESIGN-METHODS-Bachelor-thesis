import csv
from typing import Union

from py.calc.base_classes import BaseGeometry, RectangleHollow


def get_cs_params_csv(file_path: str, cs_type:str) -> list[Union[BaseGeometry, RectangleHollow]]:
    if cs_type == 'CHS':
        with open(file_path, mode='r') as file:
            reader = csv.reader(file, delimiter=';')

            # Skip the first 9 rows if headers are on the 10th row
            for _ in range(9):
                next(reader)

            headers = next(reader)  # Assume the 10th row contains headers

            # Skip the next 4 rows to start reading from the 14th line
            for _ in range(3):
                next(reader)

            csv_array = []


            for row in reader:

                cs_proper = BaseGeometry(
                    name=row[0],

                    ElementID=row[1],

                    # converting to the meters
                    d=(round((float(row[2].replace(",", "."))), 5) / 1e3),

                    t=(float(row[3].replace(",", ".")) / 1e3),

                    Fabrication=row[4],

                    cs_type=cs_type
                )


                csv_array.append(cs_proper)

    elif cs_type == 'RHS':

        with open(file_path, mode='r') as file:
            reader = csv.reader(file, delimiter=';')

            # Skip the first 9 rows if headers are on the 10th row
            for _ in range(9):
                next(reader)

            headers = next(reader)  # Assume the 10th row contains headers

            # Skip the next 4 rows to start reading from the 14th line
            for _ in range(3):
                next(reader)

            csv_array = []

            for row in reader:
                cs_proper = RectangleHollow(
                    name=row[0],

                    ElementID=row[1],

                    # converting to the meters
                    d=float(0),

                    t=(float(row[4].replace(",", ".")) / 1e3),

                    Fabrication=row[6],

                    cs_type=cs_type,

                    b=(round((float(row[2].replace(",", "."))), 5) / 1e3),
                    h=(round((float(row[3].replace(",", "."))), 5) / 1e3),

                    A_provided=(float(row[7].replace(",", "."))),

                    Iy_provided=(float(row[10].replace(",", "."))),

                    Iz=(float(row[11].replace(",", "."))),

                    W_el_y_provided=(float(row[12].replace(",", "."))),

                    W_el_z=(float(row[13].replace(",", "."))),

                    It=(float(row[15].replace(",", "."))),

                    W_pl_y_provided=(float(row[18].replace(",", "."))),

                    W_pl_z=(float(row[19].replace(",", "."))),

                    Avy=(float(row[21].replace(",", "."))),

                    Avz=(float(row[22].replace(",", "."))),


                )

                csv_array.append(cs_proper)

    else:
        raise KeyError(f'Incorrect cross section type {cs_type}')

    return csv_array


def get_cross_sections(css_type:str) -> list[Union[BaseGeometry, RectangleHollow]]:
    if css_type == "CHS":
        cross_sections = get_cs_params_csv(r'../../csv_cross_section/Circular hollow_CHS(cf).csv', css_type)
    elif css_type == "RHS":
        cross_sections = get_cs_params_csv(r'../../csv_cross_section/Rectangular hollow_SHS.csv', css_type)
    else:
        raise f"Invalid cross section type {css_type}"

    return cross_sections

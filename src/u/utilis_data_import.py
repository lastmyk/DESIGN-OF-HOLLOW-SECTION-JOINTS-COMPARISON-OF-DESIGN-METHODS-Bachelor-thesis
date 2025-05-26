import csv
import json
import os
from dataclasses import asdict
from datetime import datetime
import mysql.connector
import yaml
from mysql.connector import pooling
from .utils_data_plotting import get_root_dir_path
from pathlib import Path

from src.calc.base_classes import MainCalculationInfo


# Function to get the current time in MySQL format
def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_data_from_DB(query:str, params, csv_name:str):



    # Establish a database connection
    cred_filename = '../../db_credentials/db_credentials.yaml'
    with open(cred_filename, 'r') as f:
        credentials = yaml.load(f, yaml.FullLoader)

    connection = mysql.connector.connect(
        host=credentials['mysql_server'],
        database=credentials['mysql_database'],
        user=credentials['mysql_user'],
        password=credentials['mysql_password'],
    )

    # Create a cursor object with dictionary cursor
    cursor = connection.cursor(dictionary=True)

    try:
        # Print the query and parameters for debugging
        print(f"Executing query: {query}"  + '\n')
        print(f"With parameters: {params}" + '\n')

        query_for_log = query
        for p in params:
            query_for_log = query_for_log.replace('%s', repr(p), 1)
        print(f"Interpolated query:\n{query_for_log}" + '\n')

        # If params is None, replace it with an empty tuple
        params = params or ()

        # Execute the query with parameters
        cursor.execute(query, params)

        # Fetch all results as dictionaries
        results = cursor.fetchall()
        print(f"Number of the resutls fetched from the DB is {len(results)}" + '\n')

        if results:
            # Write into csv
            try:

                script_dir:Path = get_root_dir_path()
                absolute_path:Path = script_dir / 'csv_output'

                if not os.path.exists(absolute_path):
                    os.makedirs(absolute_path)

                csv_file_abs_path:Path = absolute_path / f'{csv_name}.csv'

                with open(csv_file_abs_path, mode='w', newline='') as csv_file:
                    writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(results[0].keys())
                    for row in results:
                        writer.writerow(row.values())
            except PermissionError:
                print("Close the CSV file before running the code.")
        else:
            print("No results found for the given query and parameters.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        results = None

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()

    return results


def add_to_db_pool(table_name:str, info:list[dict]) -> None:

    cred_filename = '../../db_credentials/db_credentials.yaml'
    with open(cred_filename, 'r') as f:
        credentials = yaml.load(f, yaml.FullLoader)


    time_of_calc = get_current_time()

    #
    # name = info["name"]
    #
    # conn_type = info["conn_type"]
    #
    # capacity = info["capacity"]
    #
    # angle = info["angle"]
    #
    # steel_grade = info["steel_grade"]
    #
    # specification = info["specification"]

    # Create a connection pool
    pool = pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,  # Number of reusable connections in the pool
        host=credentials['mysql_server'],
        database=credentials['mysql_database'],
        user=credentials['mysql_user'],
        password=credentials['mysql_password'],
    )

    data_list = []
    for i in info:
        info = i["db_params"]
        data = (
            info["name"],
            info['code_standard'],
            info["conn_type"],
            info["capacity"],
            info["angle"],
            info["steel_grade"],
            get_current_time(),  # Add the current timestamp
            info["specification"],# Serialized JSON
            info['m_perc'],
            info['n_perc']
        )
        data_list.append(data)


    column_names = "name, code_standard, conn_type, capacity, angle, steel_grade, time_of_calc, specification, m_perc, n_perc"

    connection = pool.get_connection()

    if not connection.is_connected():
        raise Exception('Not connected to db.')

    cursor = connection.cursor()



    query = (

            f"INSERT INTO mykola_lastovetskyi_bachelor_thesis.{table_name}"
             
             f" ({column_names}) "
             
             f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

             )

    # Use executemany for batch insertion
    cursor.executemany(query, data_list)

    # Commit the transaction once
    connection.commit()

    print(f"Time of recording to DB : {time_of_calc}")

    cursor.close()
    connection.close()


def add_to_db_single(table_name:str, info:dict) -> None:
    cred_filename = '../../db_credentials/db_credentials.yaml'
    with open(cred_filename, 'r') as f:
        credentials = yaml.load(f, yaml.FullLoader)

    connection = mysql.connector.connect(
        host=credentials['mysql_server'],
        database=credentials['mysql_database'],
        user=credentials['mysql_user'],
        password=credentials['mysql_password'],
    )

    if not connection.is_connected():
        raise Exception('Not connected to db.')


    calc_time = get_current_time()

    cursor = connection.cursor()

    column_names = "name, code_standard, conn_type, capacity, angle, steel_grade, nrd_direction, time_of_calc, specification, m_perc, n_perc"

    name = info["name"]

    conn_type = info["conn_type"]

    code_standard = info['code_standard']

    capacity = info["capacity"]

    angle = info["angle"]

    steel_grade = info["steel_grade"]

    nrd_direction = info["nrd_direction"]

    specification = info["specification"]

    m_perc = info['m_perc']

    n_perc = info['n_perc']

    data = (
        name,
        code_standard,
        conn_type,
        capacity,
        angle,
        steel_grade,
        nrd_direction,
        calc_time,
        specification,
        m_perc,
        n_perc
    )


    query = (
             f"INSERT INTO mykola_lastovetskyi_bachelor_thesis.{table_name}"
             f" ({column_names}) "
             "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    cursor.execute(query, data)

    print(f"Time of recording to DB : {calc_time}")

    connection.commit()


def dict_for_db_recoding(sample:MainCalculationInfo, table_to_send:str) -> dict:

    if sample.conn_setup.exclude_reason is None and table_to_send =='idea_res':
        capacity_idea = sample.idea_results.Nrd_idea

    elif sample.conn_setup.exclude_reason is None and table_to_send =='updated_analy_res':
        capacity_idea = sample.results.Nrd_recalc

    else:
        capacity_idea = sample.conn_setup.exclude_reason

    name = sample.my_sql_key
    conn_type = sample.conn_setup.conn_type
    angle = sample.conn_setup.c_angle
    steel = sample.conn_setup.steel_grade
    code = sample.conn_setup.code_standard
    specification = json.dumps(asdict(sample))
    m_perc:int = int(sample.perc_chord_M*100)
    n_perc:int = int(sample.perc_chord_N*100)
    nrd_direct = str(sample.conn_setup.nrd_direction)

    prepared_dict = {
        'name':name,
        'code_standard': code,
        'conn_type': conn_type,
        'capacity': capacity_idea,
        'angle': angle,
        'steel_grade': steel,
        'nrd_direction':nrd_direct,
        'specification': specification,
        'm_perc': m_perc,
        'n_perc': n_perc
    }

    return prepared_dict


def get_last_calc(conn_type:str, query):


    csv_name = "get_last_calc"

    data = get_data_from_DB(query, None, csv_name)

    for i in data[:]:

        if i['Connection_type'] != conn_type:
            data.remove(i)



    return data


def valid_recording(calculation:MainCalculationInfo, db_writing:int, res_validity:bool) -> None:

    # If valid, record the calculation results in the respective tables
    if res_validity:

        if db_writing != 0:
            # prep_recalc = dict_for_db_recoding(calculation, "updated_analy_res")
            # add_to_db_single("updated_analy_res", prep_recalc)
            # print(f'connection{calculation.my_sql_key} is valid and recorded to updated resdb')

            prep_idea = dict_for_db_recoding(calculation, "idea_res")
            add_to_db_single("idea_res", prep_idea)
            print(f'connection{calculation.my_sql_key} is valid and recorded to idea res')
        else:
            print("Successfully calculated Not recorded to db")

    return

def main():
    print('script is utilis_data_import.src is running')

if __name__ == '__main__':
    main()
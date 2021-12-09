import sqlite3
from google.cloud import storage 
import pandas as pd
import numpy as np
from datetime import datetime
import mysql.connector
import sys
import os

#### Establish Connection ###
import yaml
with open('gcloud.yaml') as stream:
    info_dict = yaml.safe_load(stream)
    db_username = info_dict.get('cloud_sql_vars')[0]["CLOUD_SQL_USERNAME"]
    db_password = info_dict.get('cloud_sql_vars')[1]["CLOUD_SQL_PASSWORD"]
    db_database = info_dict.get('cloud_sql_vars')[2]['CLOUD_SQL_DATABASE_NAME']
    db_connection = info_dict.get('cloud_sql_vars')[3]['CLOUD_SQL_CONNECTION_NAME']
if db_password is None:
    exit("No password set for Cloud SQL. Exiting...")

def connect():

    if os.environ.get('GAE_ENV') == 'standard':
        # If deployed, use the available connection pool.
        try:
            cnx = mysql.connector.connect(
                unix_socket='/cloudsql/{}'.format(db_connection),
                user=db_username,
                password=db_password,
                database=db_database)
        except Exception as e:
            print("Error: ", e)
    else:
        cnx = mysql.connector.connect(user=db_username, password=db_password, host='35.229.85.24', database=db_database)

    #### Connection Established ####
    print("Connection Established")

    #### Execute query ####

    

    return cnx

if __name__ == "__main__":
    connect(0,0,0)
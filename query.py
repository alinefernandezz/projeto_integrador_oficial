# pip install mysql-connector-python
# pip install streamlit -m run dash.py

import mysql.connector
import pandas as pd

def conexao(query):
    conn = mysql.connector.connect(
        host = "projetointegrador-ana.mysql.database.azure.com",
        port = "3306",
        user = "ana",
        password = "senai@134",
        db = "bd_medidorAna"
    )

    dataframe = pd.read_sql(query, conn)

    conn.close()

    return dataframe
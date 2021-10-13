import traceback
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
import json
from tabulate import tabulate
from tqdm import tqdm
import datetime as dt
import pandas as pd
import glob
import uuid


# https://github.com/geovanneoliveira/LVF-pipeline/blob/main/data%20processing/0%20-%20Data%20Processing%20Flow.ipynb

class Teste(Resource): 

    def importjson(self):
        # @TODO tornar mais genérico
        file = f"{current_app.config.get('PRE_PROCESSING_RAW')}/Fluxo_de_Entradas-XYZ-KWQ.json"

        with open(file) as jsonFile:
            json_object = json.load(jsonFile)
            jsonFile.close()

        data = []
        data = json_object['data']['entrace_flow']['data']

        df = pd.DataFrame(data)
        return df
    
    def removeNA(self, df):
        return df.dropna() # Remove all not a number

    def renameCol(self, df, col, new_col):
        return df.rename(columns={col:new_col}) # Rename Column    
    
    def save_file(self, df):
        payload = request.get_json()

        if 'path' in payload:
            return payload['path']

        file_id = uuid.uuid4()
        path = f"{current_app.config.get('PRE_PROCESSING_RAW')}/{file_id}.csv"

        df.to_csv(path, index=False)

        return path

    def convertDate(self, df, col = 'Key'):

        week = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]
        date_format = '%Y-%m-%dT%H:%M:%S'

        df = df.sort_values(by=col, key=lambda value: pd.to_datetime(value, format=date_format))
        
        df.insert(0, 'Data', df[col])
        df.insert(1, 'Hora', -1)
        df.insert(1, 'Dia', -1)
        df.drop(columns=col, inplace = True)

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            df.loc[index, 'Data'] = dt.datetime.strptime(row['Data'], date_format).strftime('%d/%m/%Y')
            df.loc[index, 'Dia'] = week[dt.datetime.strptime(row['Data'], date_format).weekday()]
            df.loc[index, 'Hora'] = dt.datetime.strptime(row['Data'], date_format).hour

        return df

    # @jwt_required
    def post(self):
        try:
            df = self.importjson()
            
            df = self.removeNA(df)

            df = self.renameCol(df, 'value', 'Quantidade de Entradas')
            df = self.convertDate(df, 'key')

            # @TODO: Implementar aqui função de salvar o arquivo igual ao PrePRocessing.py
            # salvar um arquivo flow_dataset.xlsx
            df = df.to_json()

            return df
        except:
            traceback.print_exc()
            return None, 500

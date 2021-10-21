import traceback
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
import json
from tabulate import tabulate
from tqdm import tqdm
import datetime as dt
import pandas as pd
from utils import preprocessing_utils


# https://github.com/geovanneoliveira/LVF-pipeline/blob/main/data%20processing/0%20-%20Data%20Processing%20Flow.ipynb

class PreprocessingFlow(Resource): 

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
    
    def convertDate(self, df, col = 'Key'):

        date_format = '%Y-%m-%dT%H:%M:%S'

        df = df.sort_values(by=col, key=lambda value: pd.to_datetime(value, format=date_format))
        
        df.insert(0, 'Data', df[col])
        df.insert(1, 'Hora', -1)
        df.insert(1, 'Dia', -1)
        df.drop(columns=col, inplace = True)

        for index, row in df.iterrows():
            df.loc[index, 'Data'] = dt.datetime.strptime(row['Data'], date_format).strftime('%d/%m/%Y')
            df.loc[index, 'Dia'] = preprocessing_utils.WEEK[dt.datetime.strptime(row['Data'], date_format).weekday()]
            df.loc[index, 'Hora'] = dt.datetime.strptime(row['Data'], date_format).hour

        return df

    # @jwt_required
    def post(self):
        try:
            df = self.importjson()

            df = preprocessing_utils.remove_na(df)
            df = preprocessing_utils.rename_col(df, 'value', 'Quantidade de Entradas')
            df = self.convertDate(df, 'key')
            path = f"{current_app.config.get('PRE_PROCESSING_RAW')}/flow_dataset.csv"
            preprocessing_utils.save_file(df, path)
            json = df.to_json()

            return json
        except:
            traceback.print_exc()
            return None, 500

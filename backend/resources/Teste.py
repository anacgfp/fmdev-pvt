import traceback
from flask_restful import Resource
from flask_jwt_extended import jwt_required
import json
from tabulate import tabulate
from tqdm import tqdm
import datetime as dt
import pandas as pd
import glob

# https://github.com/geovanneoliveira/LVF-pipeline/blob/main/data%20processing/0%20-%20Data%20Processing%20Flow.ipynb

class Teste(Resource):
    file = "/content/Fluxo_de_Entradas-OUT-MAI.json"

    def importjson(self, file=file):
        with open(file) as jsonFile:
            jsonObject = json.load(jsonFile)
            jsonFile.close()

        data = []
        data = jsonObject['data']['entrace_flow']['data']

        df = pd.DataFrame(data)
        return df
    
    def removeNA(self, df):
        return df.dropna() # Remove all not a number

    def renameCol(self, df, col, new_col):
        return df.rename(columns={col:new_col}) # Rename Column

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
            # print('Original dataset ' + str(df.shape) + '\n')
            # print(tabulate(df.head(), headers='keys', tablefmt='psql'))
            
            df = self.removeNA(df)
            # print('Remove N/A ' + str(df.shape))

            df = self.renameCol(df, 'value', 'Quantidade de Entradas')
            df = self.convertDate(df, 'key')
            # print('\n\nConvert Date' + str(df.shape) + '\n')

            # print(tabulate(df.head(), headers='keys', tablefmt='psql'))
            # @TODO: Implementar aqui função de salvar o arquivo igual ao PrePRocessing.py
            df.to_excel('flow_dataset.xlsx', index=False)

            return df
        except:
            traceback.print_exc()
            return None, 500

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
from utils import preprocessing_utils



# https://github.com/geovanneoliveira/LVF-pipeline/blob/main/data%20processing/0%20-%20Data%20Processing%20Sales.ipynb

class PreprocessingSales(Resource):
      
    def append_files(self, files):
        df = pd.DataFrame()
        for path in files:
            sheet = pd.read_excel(path, engine='openpyxl')
            store_name = path.split("-")[1]  # Get file name
            sheet.insert(1, "Name", store_name) # Add new column with store name
            df = df.append(sheet, ignore_index=True)
        return df

    def selectColumns(self, df, columns): 
        return df[columns] # Select columns 


    def removeNA(self, df):
        return df.dropna() # Remove all not a number

    def convertDate(self, df, col = 'Date'):
        date_format = '%Y/%m/%d %H:%M:%S'
        date_std_format = '%d/%m/%Y'
        df = df.sort_values(by=col, key=lambda value: pd.to_datetime(value, format=date_format))

        df.insert(0, 'Data', df[col])
        df.insert(1, 'Hora', -1)
        df.insert(1, 'Dia', -1)
        df.drop(columns=col, inplace = True)

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            df.loc[index, 'Data'] = row['Data'].strftime(date_std_format)
            df.loc[index, 'Dia'] = preprocessing_utils.WEEK[row['Data'].weekday()]
            df.loc[index, 'Hora'] = row['Data'].hour

        return df

    def generateTickets(self, df):
        res = pd.DataFrame(columns=['Data', 'Dia', 'Hora', 'Loja', 'Quantidade de Tickets', 'Ticket Médio'])

        df.reset_index(inplace=True, drop=True) # reset index

        days = df['Data'].unique() # all days uniques from dataset

        total = days.shape[0] # count uniques days

        for date in tqdm(days, total=total): # iterate all days from dataset

            for hour in range(0, 24): # iterate each hour

                tmp = df[ (df['Data'] == date) & (df['Hora'] == hour) ] # temporary set filtered

                stores = tmp['Name'].unique() # stores into this interval

                for store in stores: # iterate all stores

                    aux = tmp[tmp['Name'] == store] # filter by store in aux dataframe

                    counter = aux.shape[0] # counter of registers
                    avg = round(aux['Total'].sum() / aux.shape[0],2) # calculate ticket average
                
                    res = res.append({'Data':date, 'Dia':aux['Dia'].head(1).values[0], 'Hora':hour, 'Loja':store, 'Quantidade de Tickets':counter, 'Ticket Médio': avg}, ignore_index=True) # appending into a new dataframe
            
        return res # return a new dataframe
    
    
    # @jwt_required
    def post(self):
        try:
            files_path = f"{current_app.config.get('PRE_PROCESSING_RAW')}/sales/*.*"
            files = preprocessing_utils.read_files(files_path)
            df = self.append_files(files)
            df = self.selectColumns(df, ['Name', 'Total', 'Date'])
            df = self.removeNA(df)
            df = self.convertDate(df, 'Date')
            df = self.generateTickets(df)
            
            path = f"{current_app.config.get('PRE_PROCESSING_RAW')}/sales_dataset.xlsx"
            preprocessing_utils.save_file(df, path)

            return 'ok'
        except:
            traceback.print_exc()
            return None, 500

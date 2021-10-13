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

class PreprocessingWifi(Resource):
    
    def read_files(self):
        files_path = f"{current_app.config.get('PRE_PROCESSING_RAW')}/sales/*.*"

        files = glob.glob(files_path)
        print((str)(len(files)) + " files were loaded")
        return files
    
    def appendFiles(self, files):
        df = pd.DataFrame() # New Dataframe

        for path in files: # Loop
            sheet = pd.read_excel(path) # Read File
            df = df.append(sheet, ignore_index=True) # Append in the large Dataframe
        return df
    
    def selectColumns(self, df, columns): 
        return df[columns]


    def removeNA(self, df):
        return df.dropna() # Remove all not a number


    def removeAgeInconsistencies(self, df):
        df = df[df['Idade'] != 'Anos'] # Remove undefined 'Idade'

        for index, row in df.iterrows(): # Remove suffix 'Anos' and transform to number
            df.loc[index, 'Idade'] = int(row['Idade'].split(' ')[0])

            df = df[df['Idade'] < 100] # Remove anomalies 'Idade' more than 100 years

        return df


    def removeGenderIncosistencies(self, df):
        df = df[df['Gênero'] != 'Gênero não informado'] # Remove undefined 'Gênero não informado'

        return df


    def convertDate(self, df, col = 'Data Login'):

        week = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]

        df = df.sort_values(by='Data Login', key=lambda value: pd.to_datetime(value, format='%d/%m/%Y %H:%M:%S'))

        df.rename(columns={col: 'Data'}, inplace = True)
        df.insert(1, 'Hora', -1)
        df.insert(1, 'Dia', -1)

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            df.loc[index, 'Data'] = dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M:%S').strftime('%d/%m/%Y')
            df.loc[index, 'Dia'] = week[dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M:%S').weekday()]
            df.loc[index, 'Hora'] = dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M:%S').hour
            df.loc[index, 'Tempo Online'] = self.getStandardizeTime(row['Tempo Online'])

        return df

    def getStandardizeTime(self, time):

        if '-' in time:
            time = '0h0m1s'

        elif 'm' not in time and 'h' not in time:
            time = '0h0m' + time
    
        elif 'm' not in time:
            time = time.split('h')[0] + 'h0m' + time.split('h')[1]

        elif 'h' not in time:
            time = '0h' + time
        
        return dt.datetime.strptime(time,'%Hh%Mm%Ss').strftime('%H:%M:%S')
    
    def sumTimeOfRepeatedRows(self, df):

        df.reset_index(inplace=True) # reset index

        days = df['Data'].unique() # all days uniques from dataset

        total = days.shape[0] # count uniques days

        for date in tqdm(days, total=total): # iterate all days from dataset

            for hour in range(0, 24): # iterate each hour

                tmp = df[ (df['Data'] == date) & (df['Hora'] == hour) ] # temporary set filtered
                
                repeated = tmp['Mac Address'].value_counts()[tmp['Mac Address'].value_counts() > 1].index # get repeated mac by MAC ADDRESS
                
            if repeated.empty: # check if there no repeated row
                continue
            
            for mac in repeated: # if there are, iterate by each mac

                itens = tmp[ tmp['Mac Address'] == mac ] # get itens repeated 

                baseItem = itens.iloc[0] # get the baseline item
                
                totalTime = dt.datetime.strptime(baseItem['Tempo Online'], '%H:%M:%S') # get the baseline time

                itens = itens.iloc[1:] # remove the first row
                
                for index, item in itens.iterrows(): # iterate by others rows
            
                    totalTime = (totalTime - dt.datetime.strptime('00:00:00', '%H:%M:%S') + dt.datetime.strptime(item['Tempo Online'], '%H:%M:%S')) # sum all time 

                    df.loc[index,'index'] = -1 # set row as deprecated
                
                baseItem['Tempo Online'] = totalTime.strftime('%H:%M:%S') # set a sum of time
                
                df.iloc[baseItem.name] = baseItem # update a baseline element in original dataset

        df.drop(df.index[df['index'] == -1], inplace=True) # drop deprecated rows 

        df.drop(columns=['index', 'Mac Address'], axis=1, inplace=True) # remove deprecated columns
        
        df.reset_index(drop=True ,inplace=True) # reset index
        
        return df # return DataFrame
    
    
    def DatetimeToSeconds(self, df):
        for index, row in df.iterrows():
            t = dt.datetime.strptime(row['Tempo Online'], '%H:%M:%S')
            df.loc[index, 'Tempo Online'] = int(dt.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second).total_seconds())
        
        return df

    def binarizeGender(self, df):
        df.loc[df['Gênero'] == 'Feminino', 'Gênero'] = 0 
        df.loc[df['Gênero'] == 'Masculino', 'Gênero'] = 1
        return df
    
    # @jwt_required
    def post(self):
        try:
            # @TODO: Implementar aqui função de salvar o arquivo igual ao PrePRocessing.py
            files = self.read_files()
            df = self.appendFiles(files)
            df = self.selectColumns(df, ['Data Login', 'Gênero', 'Idade', 'Tempo Online', 'Mac Address'])
            df = self.removeNA(df)
            df = self.removeAgeInconsistencies(df)
            df = self.removeGenderIncosistencies(df)
            df = self.convertDate(df, 'Data Login')
            df = self.sumTimeOfRepeatedRows(df)
            
            df = self.DatetimeToSeconds(df)
            df1 = self.df.copy()
            df = self.binarizeGender(df)
            
            # salvar esses arquivos aqui, e retornar um objeto com os dois
            # df1.to_excel('Wifi_dataset_with_gender.xlsx', index=False)
            # df.to_excel('Wifi_dataset.xlsx', index=False)

            df1 = df1.to_json()
            df = df.to_json()
            return_object = {
                'wifiWithGender': df1, 
                'wifiWithoutGender': df
            }


            # @TODO: Implementar aqui função de salvar o arquivo igual ao PrePRocessing.py
            return return_object
        except:
            traceback.print_exc()
            return None, 500
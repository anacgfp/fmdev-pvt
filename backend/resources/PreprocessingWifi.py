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

class PreprocessingWifi(Resource):
    data_login = 'Data Login'
    gender = 'Gênero'
    online_time = 'Tempo Online'
    
    def removeAgeInconsistencies(self, df):
        df = df[df['Idade'] != 'Anos'] # Remove undefined 'Idade'

        for index, row in df.iterrows(): # Remove suffix 'Anos' and transform to number
            df.loc[index, 'Idade'] = int(row['Idade'].split(' ')[0])

        df = df[df['Idade'] < 100] # Remove anomalies 'Idade' more than 100 years
        return df


    def removeGenderIncosistencies(self, df):
        df = df[df[self.gender] != 'Gênero não informado'] # Remove undefined 'Gênero não informado'
        return df

    def convertDate(self, df, col = data_login):
        df = df.sort_values(by='Data Login', key=lambda value: pd.to_datetime(value, format='%d/%m/%Y %H:%M:%S'))

        df.rename(columns={col: 'Data'}, inplace = True)
        df.insert(1, 'Hora', -1)
        df.insert(1, 'Dia', -1)

        for index, row in tqdm(df.iterrows(), total=df.shape[0]):
            df.loc[index, 'Data'] = dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M:%S').strftime('%d/%m/%Y')
            df.loc[index, 'Dia'] = preprocessing_utils.WEEK[dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M:%S').weekday()]
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
                
                totalTime = dt.datetime.strptime(baseItem[self.online_time], '%H:%M:%S') # get the baseline time

                itens = itens.iloc[1:] # remove the first row
                
                for index, item in itens.iterrows(): # iterate by others rows
            
                    totalTime = (totalTime - dt.datetime.strptime('00:00:00', '%H:%M:%S') + dt.datetime.strptime(item[self.online_time], '%H:%M:%S')) # sum all time 

                    df.loc[index,'index'] = -1 # set row as deprecated
                
                baseItem[self.online_time] = totalTime.strftime('%H:%M:%S') # set a sum of time
                
                df.iloc[baseItem.name] = baseItem # update a baseline element in original dataset

        df.drop(df.index[df['index'] == -1], inplace=True) # drop deprecated rows 

        df.drop(columns=['index', 'Mac Address'], axis=1, inplace=True) # remove deprecated columns
        
        df.reset_index(drop=True ,inplace=True) # reset index
        
        return df # return DataFrame
    
    
    def DatetimeToSeconds(self, df):
        for index, row in df.iterrows():
            t = dt.datetime.strptime(row[self.online_time], '%H:%M:%S')
            df.loc[index, self.online_time] = int(dt.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second).total_seconds())
        
        return df

    def binarizeGender(self, df):
        df.loc[df[self.gender] == 'Feminino', self.gender] = 0 
        df.loc[df[self.gender] == 'Masculino', self.gender] = 1
        return df
    
    # @jwt_required
    def post(self):
        try:
            files_path = f"{current_app.config.get('PRE_PROCESSING_RAW')}/wifi/*.*"
            try:
                files = preprocessing_utils.read_files(files_path)
            except:
                return 'Error reading files', 500
            df = preprocessing_utils.append_files(files)

            columns_to_select = [self.data_login, self.gender, 'Idade', self.online_time, 'Mac Address']
            df = preprocessing_utils.select_columns(df, columns_to_select)
            df = preprocessing_utils.remove_na(df)
            df = self.removeAgeInconsistencies(df)
            df = self.removeGenderIncosistencies(df)
            df = self.convertDate(df, self.data_login)
            df = self.sumTimeOfRepeatedRows(df)
            
            df = self.DatetimeToSeconds(df)
            df1 = df.copy()
            path1 = f"{current_app.config.get('PRE_PROCESSING_RAW')}/Wifi_dataset_with_gender.csv"
            preprocessing_utils.save_file(df1, path1)
            path2 = f"{current_app.config.get('PRE_PROCESSING_RAW')}/Wifi_dataset.csv"
            df = self.binarizeGender(df)
            preprocessing_utils.save_file(df, path2)

            return 'ok'
        except:
            traceback.print_exc()
            return None, 500
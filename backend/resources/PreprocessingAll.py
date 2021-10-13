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
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()  # for plot styling
import numpy as np
from sklearn.cluster import KMeans
import collections


class PreprocessingAll(Resource):
    seg_names = {
        1 : 'Âncoras',
        2 : 'Serviços',
        3 : 'Vestuário',
        4 : 'Artigos do Lar',
        5 : 'Artigos Diversos',
        6 : 'Alimentação'
    }
    
    def read_files(self):

        dir_wifi = f"{current_app.config.get('PRE_PROCESSING_RAW')}/Wifi_dataset.xlsx"
        dir_sales = f"{current_app.config.get('PRE_PROCESSING_RAW')}/sales_dataset.xlsx"
        dir_flow = f"{current_app.config.get('PRE_PROCESSING_RAW')}/flow_dataset.xlsx"
        dir_segments = f"{current_app.config.get('PRE_PROCESSING_RAW')}/segmentos.csv"

        return dir_wifi, dir_sales, dir_flow, dir_segments
    
    def openCsvFile(self, dir):
        return pd.read_csv(dir, sep=';', encoding = "ISO-8859-1")

    def openDataframe(self, dir):
        return pd.read_excel(dir)
    
    def concatFlowAndWifi(self, dfF, dfW):
        res = pd.DataFrame(columns=['Data', 'Dia', 'Hora', 'Quantidade de Entradas', 'Gênero', 'Idade', 'Tempo Online']) #new dataframe

        res['Data'], res['Dia'], res['Hora'], res['Quantidade de Entradas'] = dfF['Data'], dfF['Dia'], dfF['Hora'], dfF['Quantidade de Entradas'] # get values from baseline

        days = dfF['Data'].unique() # All days uniques

        total = days.shape[0] # count uniques days

        for date in tqdm(days, total=total): # iterate all days from data

            for hour in range(0, 24): # iterate each hour

                tmp = dfW[ (dfW['Data'] == date) & (dfW['Hora'] == hour) ] # temporary set filtered

                if tmp.empty: # check if there some element into dataframe
                    continue
            
                filter_ = (res['Data'] == date) & (res['Hora'] == hour) #filter for new dataframe
            
                res.loc[filter_,'Gênero'] =  tmp['Gênero'].mode()[0] #insert Gênero mode

                res.loc[filter_,'Idade'] = tmp['Idade'].median() #insert Idade median

                res.loc[filter_,'Tempo Online'] = tmp['Tempo Online'].median() #insert Tempo Online median
        
        return res
    
    def concatFWAndSales(self, dfFW, dfS):
        res = pd.DataFrame(columns=['Data', 'Dia', 'Hora', 'Quantidade de Entradas', 'Gênero', 'Idade', 'Tempo Online', 'Loja', 'Quantidade de Tickets', 'Ticket Médio']) #new dataframe
        days = dfFW['Data'].unique() # All days uniques
        total = days.shape[0] # count uniques days
        for date in tqdm(days, total=total): # iterate all days from data
            for hour in range(0, 24): # iterate each hour
                aux = dfFW[ (dfFW['Data'] == date) & (dfFW['Hora'] == hour)] # aux to populate fields
                tmp = dfS[ (dfS['Data'] == date) & (dfS['Hora'] == hour) ] # temporary set filtered
                if tmp.empty: # check if there some element into dataframe
                    res = res.append({ 
                        'Data': aux['Data'].head(1).values[0],
                        'Dia': aux['Dia'].head(1).values[0],
                        'Hora': aux['Hora'].head(1).values[0],
                        'Quantidade de Entradas': aux['Quantidade de Entradas'].head(1).values[0],
                        'Gênero': aux['Gênero'].head(1).values[0],
                        'Idade': aux['Idade'].head(1).values[0],
                        'Tempo Online': aux['Tempo Online'].head(1).values[0],
                        }, ignore_index=True) # get values from dfFW
                else:
                    for _, row in tmp.iterrows(): # iterate each store
                        res = res.append({ 
                            'Data': aux['Data'].head(1).values[0],
                            'Dia': aux['Dia'].head(1).values[0],
                            'Hora': aux['Hora'].head(1).values[0],
                            'Quantidade de Entradas': aux['Quantidade de Entradas'].head(1).values[0],
                            'Gênero': aux['Gênero'].head(1).values[0],
                            'Idade': aux['Idade'].head(1).values[0],
                            'Tempo Online': aux['Tempo Online'].head(1).values[0],
                            'Loja': row['Loja'],
                            'Quantidade de Tickets': row['Quantidade de Tickets'],
                            'Ticket Médio': row['Ticket Médio']
                            }, ignore_index=True) # get values from dfFW
        
        return res #return new dataframe
    
    def transposeStores(self, df):

        res = pd.DataFrame(columns=['Data', 'Dia', 'Hora', 'Quantidade de Entradas', 'Gênero', 'Idade', 'Tempo Online']) #new dataframe

        # res['Data'], res['Dia'], res['Hora'], res['Quantidade de Entradas'] = df['Data'], df['Dia'], df['Hora'], df['Quantidade de Entradas'] # get values from baseline

        days = df['Data'].unique() # All days uniques

        total = days.shape[0] # count uniques days

        for date in tqdm(days, total=total): # iterate all days from data

            for hour in range(0, 24): # iterate each hour

                tmp = df[ (df['Data'] == date) & (df['Hora'] == hour) ] # temporary set filtered

                if tmp.empty: # check if there some element into dataframe
                    continue

                obj = {} # Object to append

                first = None # get first element

                for index, row in tmp.iterrows(): # iterate each store

                    if first == None:
                        first = True

                        obj = {
                            'Data': tmp['Data'].head(1).values[0],
                            'Dia': tmp['Dia'].head(1).values[0],
                            'Hora': tmp['Hora'].head(1).values[0],
                            'Quantidade de Entradas': tmp['Quantidade de Entradas'].head(1).values[0],
                            'Gênero': tmp['Gênero'].head(1).values[0],
                            'Idade': tmp['Idade'].head(1).values[0],
                            'Tempo Online': tmp['Tempo Online'].head(1).values[0]
                        }
       
                    obj.update({
                    row['Loja'] + '.Quantidade de Tickets' : row['Quantidade de Tickets'],
                    row['Loja'] + '.Ticket Médio' : row['Ticket Médio']
                    })

                res = res.append(obj, ignore_index=True)    

        return res.fillna(0) #return new dataframe
    
    def calculeTotalofHour(self, df):

        aux = df.iloc[:,7:-1] # get all without identificators

        for index, row in aux.iterrows(): # iterate in lines
        
            total = 0 # init value equals zero

            for i in range(0,len(row),2): # iterate in columns
                total = total + (row[i] * row[1+i]) # Calculate Σ(Q. Ticket. * Avg Ticket)

            df.loc[index,'Total'] = total # insert value in new column

        return df
    
    def kmeansClustering(self, n_clusters, col1, col2):
        X = df[[col1, col2]] # New set to clustering 

        kmeans = KMeans(n_clusters=n_clusters) # init
        kmeans.fit(X) # train
        y_kmeans = kmeans.predict(X) # predict

        plt.scatter(X[col1], X[col2], c=y_kmeans, s=50, cmap='viridis') # Plot Graph
        plt.savefig('kmeansClustering' + n_clusters + col1 + col2 + '.png')

        centers = kmeans.cluster_centers_
        plt.scatter(centers[:, 0], centers[:, 1], c='black', s=200 , alpha=0.5) # Plot centers
        plt.savefig('kmeansClustering' + n_clusters + col1 + col2 + 'centers' + '.png')

        return y_kmeans
    
    # @jwt_required
    def post(self):
        try:
            # @TODO: Implementar aqui função de salvar o arquivo igual ao PrePRocessing.py
            dir_wifi, dir_sales, dir_flow, dir_segments = self.read_files()
            dfWifi = self.openDataframe(dir_wifi)
            dfSales = self.openDataframe(dir_sales)
            dfFlow = self.openDataframe(dir_flow)
            seg = self.openCsvFile(dir_segments)


            dfFW = self.concatFlowAndWifi(dfFlow, dfWifi)
            df = self.concatFWAndSales(dfFW, dfSales)
            df.dropna(inplace=True)
            df = self.transposeStores(df)
            df = self.calculeTotalofHour(df)
            df.boxplot(['Total'])
            plt.savefig('boxplot_total.png')
            y_kmeans = self.kmeansClustering(2, 'Hora', 'Total')
            
            for index, row in df.iterrows():
                if y_kmeans[index]  == 1:
                    df.drop(index=(index), inplace=True)

            df.reset_index(drop=True, inplace=True)
            df.boxplot(['Total'])
            plt.savefig('boxplot_total_without_outliers.png')





            # problema na importação
            # profile = ProfileReport(df, title='Report',html={'style':{'full_width':True}})
            
            # df.to_excel('level1_dataset.xlsx', index=False)




            # @TODO: Implementar aqui função de salvar o arquivo igual ao PrePRocessing.py
            return "a"
        except:
            traceback.print_exc()
            return None, 500
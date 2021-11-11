import glob
import pandas as pd
from tqdm import tqdm
import xlrd
import csv
import json
import datetime as dt

def save_file(df, path):
    df.to_csv(path, index=False, encoding='utf8')
    return path

def remove_na(df):
    return df.dropna()  # Remove all not a number

def rename_col(df, col, new_col):
    return df.rename(columns={col: new_col})  # Rename Column

def read_files(files_path):
    files = glob.glob(files_path)
    print((str)(len(files)) + " files were loaded")
    return files

def append_files(files, type=''):
    df = pd.DataFrame()
    for path in files:
        sheet = pd.read_excel(path)
        df = df.append(sheet, ignore_index=True)
    return df

def select_columns(df, columns): 
    return df[columns]

# constants
WEEK = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]

# flow preprocessing
def import_json(path):
    with open(path) as jsonFile:
        json_object = json.load(jsonFile)
        jsonFile.close()

    data = []
    data = json_object['data']['entrace_flow']['data']

    df = pd.DataFrame(data)
    return df

def convert_date_flow(df, col = 'Key'):

    date_format = '%Y-%m-%dT%H:%M:%S'

    df = df.sort_values(by=col, key=lambda value: pd.to_datetime(value, format=date_format))
        
    df.insert(0, 'Data', df[col])
    df.insert(1, 'Hora', -1)
    df.insert(1, 'Dia', -1)
    df.drop(columns=col, inplace = True)

    for index, row in df.iterrows():
        df.loc[index, 'Data'] = dt.datetime.strptime(row['Data'], date_format).strftime('%d/%m/%Y')
        df.loc[index, 'Dia'] = WEEK[dt.datetime.strptime(row['Data'], date_format).weekday()]
        df.loc[index, 'Hora'] = dt.datetime.strptime(row['Data'], date_format).hour

    return df

#end flow preprocessing

# wifi pre processing

data_login = 'Data Login'
gender = 'Gênero'
online_time = 'Tempo Online'

def remove_age_inconsistencies(df):
    df = df[df['Idade'] != 'Anos'] # Remove undefined 'Idade'

    for index, row in df.iterrows(): # Remove suffix 'Anos' and transform to number
        df.loc[index, 'Idade'] = int(row['Idade'].split(' ')[0])

    df = df[df['Idade'] < 100] # Remove anomalies 'Idade' more than 100 years
    return df

def remove_gender_inconsistencies(df):
    df = df[df[gender] != 'Gênero não informado'] # Remove undefined 'Gênero não informado'
    return df

def get_standardize_time(time):
    if '-' in time:
        time = '0h0m1s'

    elif 'm' not in time and 'h' not in time:
        time = '0h0m' + time
    
    elif 'm' not in time:
        time = time.split('h')[0] + 'h0m' + time.split('h')[1]

    elif 'h' not in time:
        time = '0h' + time        
    return dt.datetime.strptime(time,'%Hh%Mm%Ss').strftime('%H:%M:%S')

def convert_date_wifi(df, col = data_login):
    df = df.sort_values(by='Data Login', key=lambda value: pd.to_datetime(value, format='%d/%m/%Y %H:%M:%S'))

    df.rename(columns={col: 'Data'}, inplace = True)
    df.insert(1, 'Hora', -1)
    df.insert(1, 'Dia', -1)

    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        df.loc[index, 'Data'] = dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M:%S').strftime('%d/%m/%Y')
        df.loc[index, 'Dia'] = WEEK[dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M:%S').weekday()]
        df.loc[index, 'Hora'] = dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M:%S').hour
        df.loc[index, 'Tempo Online'] = get_standardize_time(row['Tempo Online'])
    return df

def sum_time_repeated_rows(df):
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

def datetime_to_seconds(df):
    for index, row in df.iterrows():
        t = dt.datetime.strptime(row[online_time], '%H:%M:%S')
        df.loc[index, online_time] = int(dt.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second).total_seconds())
        
    return df

def binarize_gender(df):
    df.loc[df[gender] == 'Feminino', gender] = 0 
    df.loc[df[gender] == 'Masculino', gender] = 1
    return df

def append_files_sales(files):
    df = pd.DataFrame()
    for path in files:
        sheet = pd.read_excel(path)
        store_name = path.split("-")[1].replace('я', '´')  # Get file name
        sheet.insert(1, "Name", store_name) # Add new column with store name
        df = df.append(sheet, ignore_index=True)
    return df

def convert_date_sales(df, col = 'Date'):
    date_format = '%d/%m/%Y %H:%M'
    date_std_format = '%d/%m/%Y'
    df = df.sort_values(by=col, key=lambda value: pd.to_datetime(value, format=date_format))

    df.insert(0, 'Data', df[col])
    df.insert(1, 'Hora', -1)
    df.insert(1, 'Dia', -1)
    df.drop(columns=col, inplace = True)

    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        df.loc[index, 'Data'] = dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M').strftime('%d/%m/%Y')
        df.loc[index, 'Dia'] = WEEK[dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M').weekday()]
        df.loc[index, 'Hora'] = dt.datetime.strptime(row['Data'],'%d/%m/%Y %H:%M').hour

    return df

def generate_tickets(df):
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

# def csv_from_excel(file, csvPath):
#     wb = xlrd.open_workbook(file)
#     sh = wb.sheet_by_name('Sheet1')
#     your_csv_file = open(csvPath, 'w')
#     wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

#     for rownum in range(sh.nrows):
#         wr.writerow(sh.row_values(rownum))

#     your_csv_file.close()

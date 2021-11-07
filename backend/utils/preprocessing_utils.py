import glob
import pandas as pd
import xlrd
import csv

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
        # if type=='csv':
        #     csvPath = path.split('.')[0] + '.csv'
        #     if csvPath != path:
        #         csv_from_excel(path, csvPath)
        #     sheet = pd.read_csv(csvPath, encoding = 'utf8')
        # else:
        sheet = pd.read_excel(path)
        df = df.append(sheet, ignore_index=True)
    return df

def select_columns(df, columns): 
    return df[columns]

# constants
WEEK = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]


# def csv_from_excel(file, csvPath):
#     wb = xlrd.open_workbook(file)
#     sh = wb.sheet_by_name('Sheet1')
#     your_csv_file = open(csvPath, 'w')
#     wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

#     for rownum in range(sh.nrows):
#         wr.writerow(sh.row_values(rownum))

#     your_csv_file.close()

import glob
import pandas as pd

def save_file(df, path):
    df.to_csv(path, index=False)
    return path

def remove_na(df):
    return df.dropna()  # Remove all not a number

def rename_col(df, col, new_col):
    return df.rename(columns={col: new_col})  # Rename Column

def read_files(files_path):
    files = glob.glob(files_path)
    return files

def append_files(files):
    df = pd.DataFrame()
    for path in files:
        sheet = pd.read_excel(path, engine='openpyxl')
        df = df.append(sheet, ignore_index=True)
    return df

def select_columns(df, columns): 
    return df[columns]

# constants
WEEK = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]

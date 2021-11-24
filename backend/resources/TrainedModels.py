import json
import joblib
import traceback
from matplotlib import pyplot as plt
from numpy.core.numeric import NaN
import pandas as pd
from pycaret.classification import *
from utils import utils
from flask_restful import Resource
from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required
from flask import jsonify
import base64
import os
from flask import send_file


# retorna os modelos treinados
class TrainedModels(Resource):
    
    # @jwt_required
    def post(self):
        try:
            period = request.args.get('period')
            feature = request.args.get('feature')
            
            experimentosDir = f"{current_app.config.get('TRAIN_MODELS')}/Experimentos"
            param1 = ['Dia', 'Hora']
            param2 = ['ALL', 'FS']
            if period not in param1 or feature not in param2:
                return {"msg": "Periodo ou feature Invalido"}, 500
            param3 = ['Total (T+1)', 'Total (T+2)', 'Total (T+3)']

            objeto_retorno = {}
            for index, t in enumerate(param3):
                try:
                    path = f"{experimentosDir}/{period}/{feature}/{t}/results.csv" 
                    df = pd.read_csv(path) 
                except:
                    continue
                objeto_retorno[t] = []
                for _, row in df.iterrows():
                    obj = {}
                    obj['Accuracy'] = round(row['Accuracy'], 3)
                    obj['Recall'] = round(row['Recall'], 3)
                    obj['Prec'] = round(row['Prec'], 3)
                    obj['F1'] = round(row['F1'], 3)
                    obj['Kappa'] = round(row['Kappa'], 3)
                    obj['MCC'] = round(row['MCC'], 3)
                    obj['Name'] = row['Name'] if row['Name'] else ""
                    obj['Model'] = row['Model'] if row['Model'] else ""
                    obj['initials'] = row['Unnamed: 0'] if row['Unnamed: 0'] else ""
                    obj['itemIdx'] = str(index + 1)
                    objeto_retorno[t].append(obj)
            return jsonify(objeto_retorno)
        except:
            traceback.print_exc()
            return None, 500
    
class TrainedModelsImages(Resource):    
    # @jwt_required
    def post(self):
        try:
            period = request.args.get('period')
            feature = request.args.get('feature')
            time = request.args.get('time') #can be 1, 2, 3
            time_types = ['Total (T+1)', 'Total (T+2)', 'Total (T+3)']
            initials = request.args.get('initials')
            
            basePath = f"{current_app.config.get('TRAIN_MODELS')}/Experimentos/{period}/{feature}/{time_types[int(time)-1]}"
            path = f"{basePath}/{initials}_confusion_matrix.png"
            param1 = ['Dia', 'Hora']
            param2 = ['ALL', 'FS']
            if period not in param1 or feature not in param2 or time not in ['1', '2', '3']:
                return {"msg": "Periodo ou feature Invalido"}, 500
            image = open(path, 'rb')
            image_read = image.read()
            image_64_encode = base64.encodebytes(image_read) #encodestring also works aswell as decodestring
            img_str = image_64_encode.decode('utf-8') # str

            return img_str
        except:
            traceback.print_exc()
            return None, 500
        
class TrainedModelPipeline(Resource):    
    # @jwt_required
    def post(self):
        try:
            period = request.args.get('period')
            feature = request.args.get('feature')
            time = request.args.get('time') #can be 1, 2, 3
            time_types = ['Total (T+1)', 'Total (T+2)', 'Total (T+3)']
            initials = request.args.get('initials')
            
            basePath = f"{current_app.config.get('TRAIN_MODELS')}/Experimentos/{period}/{feature}/{time_types[int(time)-1]}"
            path = f"{basePath}/{initials}.pkl"
            param1 = ['Dia', 'Hora']
            param2 = ['ALL', 'FS']
            if period not in param1 or feature not in param2 or time not in ['1', '2', '3']:
                return {"msg": "Periodo ou feature Invalido"}, 500
            return send_file(path, attachment_filename='model.pkl')

        except:
            traceback.print_exc()
            return None, 500
        
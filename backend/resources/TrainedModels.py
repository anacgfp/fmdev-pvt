import json
import joblib
import traceback
from numpy.core.numeric import NaN
import pandas as pd
from utils import utils
from flask_restful import Resource
from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required
from flask import jsonify
import base64

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
                path = f"{experimentosDir}/{period}/{feature}/{t}/results.csv" 
                df = pd.read_csv(path) 
                objeto_retorno[t] = []
                for _, row in df.iterrows():
                    obj = {}
                    obj['Accuracy'] = row['Accuracy'] if row['Accuracy'] else ""
                    obj['Recall'] = row['Recall'] if row['Recall'] else ""
                    obj['Prec'] = row['Prec'] if row['Prec'] else ""
                    obj['F1'] = row['F1'] if row['F1'] else ""
                    obj['Kappa'] = row['Kappa'] if row['Kappa'] else ""
                    obj['MCC'] = row['MCC'] if row['MCC'] else ""
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

            path = f"{current_app.config.get('TRAIN_MODELS')}/Experimentos/{period}/{feature}/{time_types[int(time)-1]}/{initials}.png"
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
        
        


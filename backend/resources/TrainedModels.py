import json
import joblib
import traceback
import pandas as pd
from utils import utils
from flask_restful import Resource
from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required

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
            for t in param3:
                path = f"{experimentosDir}/{period}/{feature}/{t}/results.csv" 
                df = pd.read_csv(path) 
                obj = {}
                objeto_retorno[t] = []
                for index, row in df.iterrows():
                    obj['Accuracy'] = row['Accuracy']
                    obj['AUC'] = row['AUC']
                    obj['Recall'] = row['Recall']
                    obj['Prec'] = row['Prec']
                    obj['F1'] = row['F1']
                    obj['Kappa'] = row['Kappa']
                    obj['MCC'] = row['MCC']
                    objeto_retorno[t].append(obj)
                # 'Name', 'Model', TODO
            return objeto_retorno
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

            return send_file(path, mimetype='image/png')
        except:
            traceback.print_exc()
            return None, 500
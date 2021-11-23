import traceback
import numpy as np
import pandas as pd
from pycaret.classification import *  
from utils import preprocessing_utils
from flask import jsonify
from flask_restful import Resource
from flask import request, current_app
from flask_jwt_extended import jwt_required
import seaborn as sns
from tqdm import tqdm
import datetime as dt
import matplotlib.pyplot as plt
from sklearn.metrics import plot_confusion_matrix
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import StratifiedKFold
from scipy.stats import wilcoxon
from sklearn.model_selection import train_test_split
from sklearn import metrics
from pycaret.utils import enable_colab
from sklearn.metrics import confusion_matrix, accuracy_score
import itertools as it
import os
import warnings
warnings.filterwarnings("ignore")

class Train(Resource):
    def read_paths(self):
        dia = f"{current_app.config.get('PRE_PROCESSING_RAW')}/pre_processed/Dia.csv"
        hora = f"{current_app.config.get('PRE_PROCESSING_RAW')}/pre_processed/Hora.csv"

        return dia, hora

    def featureSelection(self, df, TARGET_NAME, fee = 0.30):
        #Using Pearson Correlation
        cor = df.corr()

        #Correlation with output variable
        cor_target = abs(cor[TARGET_NAME])

        #Selecting highly correlated features
        relevant_features = cor_target[cor_target>fee]
        df = df.filter(list(relevant_features.index))

        return df
    
    def creatingModel(self, train, TARGET_NAME, TRAIN_SIZE, FEATURES_NAME):    
        # Using 70% train and 30% validate
        cls = setup(data= train,
                    target=TARGET_NAME,
                    train_size=TRAIN_SIZE,
                    data_split_stratify = False,
                    normalize=True,
                    normalize_method='minmax',
                    numeric_features=FEATURES_NAME,
                    silent=True)
        return cls
    
    def tuningModels(self, models_trained, METRIC_TRAIN):
        print('tuned')
        models = pd.DataFrame(columns=['initials','name','model','score'])
        for model in models_trained.itertuples():
            tuned = tune_model(model.model, optimize = METRIC_TRAIN, n_iter=30, verbose= False )
            models.loc[models.shape[0]] = [ model.initials, model.name, tuned, pull()[METRIC_TRAIN].Mean ]
        models.sort_values(by=['score'], ascending=False, inplace=True, ignore_index=True)
        return models


    def trainingModels(self, METRIC_TRAIN, THRESHOLD):
        print('training')

        models_list = compare_models(sort=METRIC_TRAIN, n_select=13)
        # Select N Best Models
        table = pull()
        models_trained = pd.DataFrame(columns=['initials','name','model','score'])

        for (index, line), model in zip(table.iterrows(), models_list):
            if line[METRIC_TRAIN] > THRESHOLD:
                models_trained.loc[models_trained.shape[0]] = [ index, line.Model, model, line[METRIC_TRAIN] ]

        return models_trained
    

    def wilcoxonTest(self, train, models, TARGET_NAME, METRIC_WILCOXON):
        print('wilcoxon')
        # Get Train Data

        X_train = train.drop([TARGET_NAME], axis=1)
        Y_train = train[TARGET_NAME]


        # Run Cross Validation 
        cv_results = {}

        kfold = StratifiedKFold(n_splits=30, random_state=42, shuffle=True)
        for model in models.itertuples():
            cv_results[model.initials] = cross_val_score(model.model, X_train, Y_train, cv=kfold, scoring=METRIC_WILCOXON)

        # Run Wilcoxon Test

        initials_names = list(models.initials)
        wilcoxon_test = pd.DataFrame(columns=initials_names, index=initials_names)

        for name1 in cv_results:
            for name2 in cv_results:
                if name1!=name2:
                    stat, p = wilcoxon(cv_results[name1], cv_results[name2])
                    if p > 0.05:
                    #print('As distribuições são semelhantes (=): ',name1,'x',name2,'stat=%.3f p=%.3f' % (stat, p))
                        wilcoxon_test.loc[name1,name2] = '='
                    else:
                    #print('As distribuições são diferentes  (≠): ',name1,'x',name2,'stat=%.3f p=%.3f' % (stat, p))
                        wilcoxon_test.loc[name1,name2] = '≠'

        for idx in initials_names:
            if idx not in initials_names: continue

            cut = wilcoxon_test[idx].where(wilcoxon_test[idx].str.contains('=')).dropna().index.tolist()
            initials_names = [x for x in initials_names if not x in cut]
        
        return models[models.initials.isin(initials_names)]

    def normalize(self, df, target):
        print('normalize')
        result = df.copy()
        for feature_name in df.columns.difference([target]):
            max_value = df[feature_name].max()
            min_value = df[feature_name].min()
            result[feature_name] = (df[feature_name] - min_value) / ((max_value - min_value) if not (max_value - min_value) == 0 else 1)
        return result
 
    def testingModels(self, models, test, dir_, TARGET_NAME):
        print('testing models')
        # Get Test Data
        test_normalized = self.normalize(test, TARGET_NAME)

        X_test = test_normalized.drop([TARGET_NAME], axis=1).values
        Y_test = test_normalized[TARGET_NAME].values
        
        # Generate Confusion Matrix
        for model in models.itertuples():
            plot_confusion_matrix(model.model, X_test, Y_test,
                                display_labels=['Low','Medium','High'],
                                cmap=plt.cm.Blues,
                                normalize='true')
            plt.grid(False)
            plt.title(model.name)
            plt.savefig(dir_+model.initials+'_confusion_matrix.png')
            plt.close()
            
        # Metrics for Test
        initials_names = list(models.initials)
        test_metrics = pd.DataFrame(columns=['Name', 'Model', 'Accuracy','AUC','Recall','Prec','F1','Kappa','MCC'], index=initials_names)

        for model in models.itertuples():
            y_pred = model.model.predict(X_test)
            save_model(model.model, dir_ + model.initials)
            aux = None
            try :
                y_pred_proba = model.model.predict_proba(X_test)
                aux = metrics.roc_auc_score(Y_test, y_pred_proba, average='weighted', multi_class='ovr')
            except Exception as _ :
                aux = 'N/A'
                
            test_metrics.loc[model.initials, 'Name'] = model.name
            test_metrics.loc[model.initials, 'Model'] = model.model
            test_metrics.loc[model.initials, 'Accuracy'] = metrics.accuracy_score(Y_test, y_pred)
            test_metrics.loc[model.initials, 'AUC'] = aux
            test_metrics.loc[model.initials, 'Recall'] = metrics.recall_score(Y_test, y_pred, average='macro')
            test_metrics.loc[model.initials, 'Prec'] = metrics.precision_score(Y_test, y_pred,  average='weighted')
            test_metrics.loc[model.initials, 'F1'] = metrics.f1_score(Y_test, y_pred, average='weighted')
            test_metrics.loc[model.initials, 'Kappa'] = metrics.cohen_kappa_score(Y_test, y_pred)
            test_metrics.loc[model.initials, 'MCC'] = metrics.matthews_corrcoef(Y_test, y_pred)

        test_metrics.sort_values(by=['F1'], ascending=False, inplace=True)
        return test_metrics


    def saveList(self, L, dir_):
        with open(dir_+'Features.txt', 'w') as f:
            for item in L:
                f.writelines(str(item)+'\n')
            f.close()


    # @jwt_required
    def post(self):
        try:
            dia, hora = self.read_paths()
            dic = { 
                'dataset' : [dia.split('.')[0], hora.split('.')[0]],
                'feature' : ['ALL', 'FS'],
                'target' : ['Total (T+1)','Total (T+2)','Total (T+3)']
            }          

            PARAMS = it.product(*(dic[idx] for idx in dic))
            # Declaration of Constants
            TARGETS = ['Total (T+1)','Total (T+2)','Total (T+3)']
            TEST_SIZE = 0.3
            TRAIN_SIZE = 0.7
            METRIC_TRAIN = 'F1'
            METRIC_WILCOXON = 'f1_weighted'
            THRESHOLD = 0.6
            
            lista = []
            # Execute
            a = []
            for param in PARAMS:
                # Get params
                type_time = param[0].split('/')[-1]
                dir_ = f"{current_app.config.get('TRAIN_MODELS')}/Experimentos/{type_time}/{param[1]}/{param[2]}/"
                os.makedirs(dir_, exist_ok=True)
                df = pd.read_csv(param[0]+'.csv')
                TARGET_NAME = param[2]
                df.drop(columns=[x for x in TARGETS if x != TARGET_NAME], axis=1, inplace=True)
                FEATURES_NAME = list(df.columns.difference([TARGET_NAME]))

                # Init Modeling
                if param[1] == 'FS':
                    df = self.featureSelection(df, TARGET_NAME)
                    FEATURES_NAME = list(df.columns.difference([TARGET_NAME]))
                    self.saveList(FEATURES_NAME, dir_)

                train, test = train_test_split(df, test_size=TEST_SIZE, random_state=42)
                try :
                    cls = self.creatingModel(train, TARGET_NAME, TRAIN_SIZE, FEATURES_NAME)

                    models_trained = self.trainingModels(METRIC_TRAIN, THRESHOLD)
                    lista.append(models_trained.shape)
                    models_trained.to_csv(dir_+'trained.csv', index=False)

                    models_tuned = self.tuningModels(models_trained, METRIC_TRAIN)
                    models_tuned.to_csv(dir_+'tuned.csv', index=False)

                    models_hyp = self.wilcoxonTest(train, models_tuned, TARGET_NAME, METRIC_WILCOXON)
                    models_hyp.to_csv(dir_+'hypothesis.csv', index=False)

                    results = self.testingModels(models_hyp, test, dir_, TARGET_NAME)
                    results.to_csv(dir_+'results.csv', index=True)
                except Exception as _ :
                    print('Error')

            return 'OK'
        except:
            traceback.print_exc()
            return {"msg": "Error on POST Train"}, 500
        
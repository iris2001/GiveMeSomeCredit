#!/usr/bin/env python
# coding: utf-8
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedShuffleSplit
import xgboost as xgb
#*****************************************************************************************
#Use XGboost model Only:
#1.load data (training and test) and preprocessing data(replace NA,98,96,0(age) with NaN)
#2.split training data into training_new  and test_new (for validation model)

#3.Build XGBoost model using the training_new data:
#   a. handle missing values and imbalanced data distribution
#   b. perform parameter tuning using grid search with CrossValidation
#   c. output the best model and make predictions for test data
#*****************************************************************************************

#*****************************************************************************************
# a few tools
#*****************************************************************************************

#*****************************************************************************************
# func to create a new dict using  keys and values
# input: keys =[]and values=[]
# output: dict{}
#*****************************************************************************************
def creatDictKV(keys, vals):
    lookup = {}
    if len(keys) == len(vals):
        for i in range(len(keys)):
            key = keys[i]
            val = vals[i]
            lookup[key] = val
    #print lookup
    return lookup

#*************************************************************************
#compute AUC
# input: y_true =[] and y_score=[]
# output: auc
#*************************************************************************
def computeAUC(y_true, y_score):

    auc = roc_auc_score(y_true, y_score)
    print "auc= ", auc
    return auc

#*************************************************************************
#compute classWeight for unbalanced binary data
# input: label=[]
# output:classWeight=#neg/#pos
#*************************************************************************
def computeClassWeight(label):
    label = label.tolist()
    #label=list(label)
    sum_wpos = label.count(1)
    sum_wneg = label.count(0)

    # print weight statistics
    print ('weight statistics: wpos=%g, wneg=%g, ratio=%g' % \
           (sum_wpos, sum_wneg, sum_wneg / sum_wpos))
    return  sum_wneg / sum_wpos
#*****************************************************************************************


#*****************************************************************************************
# Real Stuff:
#*****************************************************************************************


def main():
    #*************************************************************************************
    #1.load data (training and test) and preprocessing data(replace NA,98,96,0(age) with NaN)
    #read data using pandas
    #replace 98, 96 with NAN for NOTime30-59,90,60-90
    #replace  0 with NAN for age
    #*************************************************************************************
    colnames = ['ID', 'label', 'RUUnsecuredL', 'age', 'NOTime30-59', \
                'DebtRatio', 'Income', 'NOCredit', 'NOTimes90', \
                'NORealEstate', 'NOTime60-89', 'NODependents']
    col_nas = ['', 'NA', 'NA', 0, [98, 96], 'NA', 'NA', 'NA',\
               [98, 96], 'NA', [98, 96], 'NA']
    col_na_values = creatDictKV(colnames, col_nas)

    dftrain = pd.read_csv("cs-training.csv", names=colnames,\
                            na_values=col_na_values, skiprows=[0])
    train_id = [int(x) for x in dftrain.pop("ID")]
    y_train = np.asarray([int(x)for x in dftrain.pop("label")])
    x_train = dftrain.as_matrix()

    dftest = pd.read_csv("cs-test.csv", names=colnames,\
                            na_values=col_na_values, skiprows=[0])
    test_id = [int(x) for x in dftest.pop("ID")]
    y_test = np.asarray(dftest.pop("label"))
    x_test = dftest.as_matrix()

    #*************************************************************************************
    #2.split training data into training_new  and test_new (for validation model)
    # to keep the class ratio using StratifiedShuffleSplit to do the split
    #*************************************************************************************

    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.33333, random_state=0)
    for train_index, test_index in sss.split(x_train, y_train):
        print("TRAIN:", train_index, "TEST:", test_index)
        x_train_new, x_test_new = x_train[train_index], x_train[test_index]
        y_train_new, y_test_new = y_train[train_index], y_train[test_index]

    y_train = y_train_new
    x_train = x_train_new

    #*************************************************************************************
    #3.Build XGboost model using the training_new data:
    #   a. handle missing values and imbalanced data distribution
    #*************************************************************************************
    #  Initialize the model:
    #   a. handle missing values and imbalanced data distribution
    #      -handle missing values by setting papameter"missing=NaN"
    #      -deal with imbalanced data distribution by:
    #       1.scale_pos_weight=149974/10026=13
    #       2. max_delta_step=1
    #*************************************************************************************
    pos_weight = computeClassWeight(y_train)
    param_dist = {"objective":"binary:logistic", \
                "n_estimators":500, \
                "scale_pos_weight":pos_weight, \
                "max_delta_step":1, \
                "subsample":0.8, \
                "colsample_bytree":0.8, \
                "seed":27, \
                "eval_metric":"auc", "missing":'NaN'}
    clf = xgb.XGBClassifier(param_dist)
    #*************************************************************************************
    #   b. perform parameter tuning using grid search with CrossValidation in 4 steps:
    #        Control overfitting by tuning 1-3
    #         1.control model complexity : max_depth, min_child_weight and gamma
    #         2.add randomness to make training robust to noise: subsample, colsample_bytree
    #         3.Tuning Regularization Parameters:reg_alpha,reg_lambda
    #         4.Lower the learning rate and decide the optimal parameters .
    #*************************************************************************************
    #param_test = { 'max_depth':range(3,10,2), 'min_child_weight':range(1,6,2) }
    #param_test = { 'max_depth':[3,4,5],\
	#           'min_child_weight':[6,8,10,12],\
	#           'gamma':[i/10.0 for i in range(0,5)] }
    #param_test = { 'max_depth':[4],\
	#           'min_child_weight':[8],\
	#           'gamma':[i/10.0 for i in range(0,5)] }
    #param_test = { 'max_depth':[4],\
	#           'min_child_weight':[6],\
	#           'gamma':[0] }
    #param_test = { 'max_depth':[4],\
	#           'min_child_weight':[6],\
	#           'gamma':[0] ,'reg_alpha':[0.001, 0.005, 0.01, 0.05]}
    #param_test = { 'max_depth':[4],\
	#           'min_child_weight':[6],\
	#           'gamma':[0] ,'reg_alpha':[0.001,0.002]}
    #param_test = { 'max_depth':[4],\
	#           'min_child_weight':[6],\
	#           'gamma':[0] ,'reg_alpha':[0.001],\
	#           'subsample':[0.6,0.7,0.8,0.9],\
	#           'colsample_bytree':[i/10.0 for i in range(6,10)] }
    #param_test = { 'max_depth':[4],\
	#           'min_child_weight':[6],\
	#           'gamma':[0] ,'reg_alpha':[0.001],\
	#           'subsample':[0.6],\
	#           'colsample_bytree':[0.7] }
    #param_test = { 'max_depth':[4],\
	#           'min_child_weight':[6],\
	#           'gamma':[0] ,'reg_alpha':[0.001],\
	#           'subsample':[0.6],\
	#           'colsample_bytree':[0.7],\
	#           'learning_rate':[0.1,0.02,0.05,0.08] }
    #param_test = { 'max_depth':[3,4,5,6],\
	#           'min_child_weight':[2,4,6,8],\
	#           'gamma':[0,0.1,0.3,0.5],\
        #           'reg_alpha':[0.001,0.005,0.01,0.05],\
	#           'subsample':[0.6,0.7,0.8,0.9],\
	#           'colsample_bytree':[0.6,0.7,0.8,0.9],\
	#           'learning_rate':[0.1,0.02,0.05,0.08] }
    #*************************************************************************************
    #this is the best parameter after tuning
    #*************************************************************************************
    param_test = {'max_depth':[4], \
                    'min_child_weight':[6], \
                    'gamma':[0,0.1], \
                    'reg_alpha':[0.001], \
                    'subsample':[0.6], \
                    'colsample_bytree':[0.7], \
                    'learning_rate':[0.1]}

    grid_search = GridSearchCV(clf, param_grid=param_test, scoring='roc_auc',\
                                n_jobs=-1, iid=False, cv=10)

    #*************************************************************************************
    #   c. output the best model and make predictions for test data
    #       - Use best parameter to build model with training_new data
    #*************************************************************************************
    grid_search.fit(x_train, y_train)
    print "the best parameter:", grid_search.best_params_
    print "the best score:", grid_search.best_score_
    #   #print "the parameters used:",grid_search.get_params

    #*************************************************************************************
    #   To see how fit the model with the training_new data
    #       -Use the model trained to make predication for train_new data
    #*************************************************************************************
    predicted_probs_train = grid_search.predict_proba(x_train)
    predicted_probs_train = [x[1] for  x in predicted_probs_train]
    computeAUC(y_train, predicted_probs_train)

    #*************************************************************************************
    #   To see how well the model performs with the test_new data
    #    -Use the model trained to make predication for validataion data (test_new)
    #*************************************************************************************
    predicted_probs_test_new = grid_search.predict_proba(x_test_new)
    predicted_probs_test_new = [x[1] for x in predicted_probs_test_new]
    computeAUC(y_test_new, predicted_probs_test_new)

    #*************************************************************************************
    #  use the model to predict for test and output submission file
    #*************************************************************************************
    predicted_probs_test = grid_search.predict_proba(x_test)
    predicted_probs_test = ["%.9f" % x[1] for x in predicted_probs_test]
    submission = pd.DataFrame({'ID':test_id, 'Probabilities':predicted_probs_test})
    submission.to_csv("xgboost_benchmark.csv", index=False)

#*************************************************************************************
if __name__ == "__main__":
    main()


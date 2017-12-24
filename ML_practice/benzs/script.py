# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load in 

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import matplotlib.pyplot as plt
from pylab import savefig

# Input data files are available in the "../input/" directory.
# For example, running this (by clicking run or pressing Shift+Enter) will list the files in the input directory

from subprocess import check_output
print(check_output(["ls", "../input"]).decode("utf8"))

# preprocessing/decomposition
from sklearn.preprocessing import StandardScaler, OneHotEncoder, MinMaxScaler
from sklearn.decomposition import PCA

# Keras is a deep learning library that wraps the efficient numerical libraries Theano and TensorFlow.
# It provides a clean and simple API that allows you to define and evaluate deep learning models in just a few lines of code.from keras.models import Sequential, load_model
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, BatchNormalization, Activation
from keras.wrappers.scikit_learn import KerasRegressor
from keras.callbacks import EarlyStopping, ModelCheckpoint
# define custom R2 metrics for Keras backend
from keras import backend as K
# to tune the NN
from keras.constraints import maxnorm
from keras.optimizers import SGD, Adam

# model evaluation
from sklearn.model_selection import cross_val_score, KFold, train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error

# feature selection
from sklearn.feature_selection import f_regression, mutual_info_regression, VarianceThreshold

# define path to save model
import os
model_path = 'keras_model.h5'

# turn run_de to True if you want to run the decomposition.
run_de = False

# to make results reproducible
# seed = 42

# Read datasets
train = pd.read_csv('../input/train.csv')
test = pd.read_csv('../input/test.csv')

train_for_analysis = train.copy()
test_for_analysis = test.copy()

# save IDs for submission
id_test = test['ID'].copy()

###########################
# DATA ANALYSIS
###########################

# glue datasets together
total = pd.concat([train_for_analysis, test_for_analysis], axis=0)
print('initial shape: {}'.format(total.shape))

# binary indexes for train/test set split
is_train = ~total.y.isnull()

# find all categorical features
cf = total.select_dtypes(include=['object']).columns

# make one-hot-encoding convenient way - pandas.get_dummies(df) function
dummies = pd.get_dummies(
    total[cf],
    drop_first=False # you can set it = True to ommit multicollinearity (crucial for linear models)
)

print('oh-encoded shape: {}'.format(dummies.shape))

# get rid of old columns and append them encoded
total = pd.concat(
    [
        total.drop(cf, axis=1), # drop old
        dummies # append them one-hot-encoded
    ],
    axis=1 # column-wise
)

print('appended-encoded shape: {}'.format(total.shape))

# recreate train/test again, now with dropped ID column
train_for_analysis, test_for_analysis = total[is_train].drop(['ID'], axis=1), total[~is_train].drop(['ID', 'y'], axis=1)

# drop redundant objects
del total

train_no_y = train_for_analysis.drop('y', axis=1).copy()
train_y = train_for_analysis.y
        
# Analyze Categorical
# F-test and mutual information on Categorical Features
# F-test captures only linear dependency, mutual information can capture any kind of dependency between variables and it rates
f_test, _ = f_regression(train_no_y.values[:,1:8], train_y)
f_test /= np.max(f_test)
    
mi = mutual_info_regression(train_no_y.values[:,1:8], train_y)
mi /= np.max(mi)
    
fig_ftest = plt.figure(figsize=(30, 10))
for i in range(7):
    plt.subplot(1, 7, i + 1)
    plt.scatter(train_no_y.values[:, i], train_y.values)
    plt.xlabel("$x_{}$".format(i + 1), fontsize=14)
    if i == 0:
        plt.ylabel("$y$", fontsize=14)
    plt.title("F-test={:.2f}, MI={:.2f}".format(f_test[i], mi[i]),
              fontsize=16)
fig_ftest.savefig("f_test_mutual_info_regression.png")

###########################
# DATA PREPARATION
###########################

# Transform Categorical Features in Numerical

mean_x0 = train[['X0', 'y']].groupby(['X0'], as_index=False).median()
mean_x0.columns = ['X0', 'mean_x0']

train = pd.merge(train, mean_x0, on='X0', how='outer')

mean_x1 = train[['X1', 'y']].groupby(['X1'], as_index=False).median()
mean_x1.columns = ['X1', 'mean_x1']

train = pd.merge(train, mean_x1, on='X1', how='outer')

mean_x2 = train[['X2', 'y']].groupby(['X2'], as_index=False).median()
mean_x2.columns = ['X2', 'mean_x2']

train = pd.merge(train, mean_x2, on='X2', how='outer')

mean_x3 = train[['X3', 'y']].groupby(['X3'], as_index=False).median()
mean_x3.columns = ['X3', 'mean_x3']

train = pd.merge(train, mean_x3, on='X3', how='outer')

mean_x4 = train[['X4', 'y']].groupby(['X4'], as_index=False).median()
mean_x4.columns = ['X4', 'mean_x4']

train = pd.merge(train, mean_x4, on='X4', how='outer')

mean_x5 = train[['X5', 'y']].groupby(['X5'], as_index=False).median()
mean_x5.columns = ['X5', 'mean_x5']

train = pd.merge(train, mean_x5, on='X5', how='outer')

mean_x6 = train[['X6', 'y']].groupby(['X6'], as_index=False).median()
mean_x6.columns = ['X6', 'mean_x6']

train = pd.merge(train, mean_x6, on='X6', how='outer')

mean_x8 = train[['X8', 'y']].groupby(['X8'], as_index=False).median()
mean_x8.columns = ['X8', 'mean_x8']

train = pd.merge(train, mean_x8, on='X8', how='outer')

train = train.drop(['ID','X0','X1','X2','X3','X4','X5','X6','X8'], axis=1).copy()

print(train.head(100))

test = pd.merge(test, mean_x0, on='X0', how='left')

test['mean_x0'].fillna(test['mean_x0'].dropna().median(), inplace=True)

test = pd.merge(test, mean_x1, on='X1', how='left')

test['mean_x1'].fillna(test['mean_x1'].dropna().median(), inplace=True)

test = pd.merge(test, mean_x2, on='X2', how='left')

test['mean_x2'].fillna(test['mean_x2'].dropna().median(), inplace=True)

test = pd.merge(test, mean_x3, on='X3', how='left')

test['mean_x3'].fillna(test['mean_x3'].dropna().median(), inplace=True)

test = pd.merge(test, mean_x4, on='X4', how='left')

test['mean_x4'].fillna(test['mean_x4'].dropna().median(), inplace=True)

test = pd.merge(test, mean_x5, on='X5', how='left')

test['mean_x5'].fillna(test['mean_x5'].dropna().median(), inplace=True)

test = pd.merge(test, mean_x6, on='X6', how='left')

test['mean_x6'].fillna(test['mean_x6'].dropna().median(), inplace=True)

test = pd.merge(test, mean_x8, on='X8', how='left')

test['mean_x8'].fillna(test['mean_x8'].dropna().median(), inplace=True)

test = test.drop(['ID','X0','X1','X2','X3','X4','X5','X6','X8'], axis=1).copy()

print(test.head(100))

# check shape
print('\nTrain shape: {}\nTest shape: {}'.format(train.shape, test.shape))

#########################
# DECOMPOSITION
#########################
if run_de:
    
    # PCA
    pca = PCA(iterated_power='auto', n_components=None, random_state=None, svd_solver='auto')
    pca.fit(train_no_y)
    # The pca.explained_variance_ratio_ returned are the variances from principal components. 
    # You can use them to find how many dimensions (components) your data could be better transformed by pca. 
    # You can use a threshold for that (e.g, you count how many variances are greater than 0.5, among others).
    print(pca.explained_variance_)
    
    # After that, you can transform the data by PCA using the number of dimensions (components) that are equal to principal components higher than the threshold used. 
    # The data reduced to these dimensions are different from the data on dimensions in original data.
    pca.n_components = 380
    pca_results_train = pca.fit_transform(train_no_y)
    pca_results_test = pca.fit_transform(test)
  
    '''
    # Append decomposition components to datasets
    for i in range(1, n_comp+1):
        train_no_y['pca_' + str(i)] = pca_results_train[:,i-1]
        test['pca_' + str(i)] = pca_results_test[:, i-1]
    '''
    # If you are using sigmoid activation functions, rescale your data to values between 0-and-1. 
    # If you’re using the Hyperbolic Tangent (tanh), rescale to values between -1 and 1.
    
    min_max_scaler = MinMaxScaler(feature_range=(0, 1))
    # standard_scaler = StandardScaler()
    train_decomposed_no_y = min_max_scaler.fit_transform(pca_results_train)
    test_decomposed = min_max_scaler.fit_transform(pca_results_test)
    print('\nTrain shape after Decomposition: {}\nTest shape after Decomposition: {}'.format(train_decomposed_no_y.shape, test_decomposed.shape))
    print(train_decomposed_no_y)
    
#########################################################################################################################################
# GENERATE MODEL
# The Keras wrappers require a function as an argument. 
# This function that we must define is responsible for creating the neural network model to be evaluated.
# Below we define the function to create the baseline model to be evaluated. 
# The network uses good practices such as the rectifier activation function for the hidden layer. 
# No activation function is used for the output layer because it is a regression problem and we are interested in predicting numerical 
# values directly without transform.# The efficient ADAM optimization algorithm is used and a mean squared error loss function is optimized. 
# This will be the same metric that we will use to evaluate the performance of the model. 
# It is a desirable metric because by taking the square root gives us an error value we can directly understand in the context of the problem.
##########################################################################################################################################

def r2_keras(y_true, y_pred):
    SS_res =  K.sum(K.square( y_true - y_pred )) 
    SS_tot = K.sum(K.square( y_true - K.mean(y_true) ) ) 
    return ( 1 - SS_res/(SS_tot + K.epsilon()) )
    
# Base model architecture definition.
# Dropout is a technique where randomly selected neurons are ignored during training. 
# They are dropped-out randomly. This means that their contribution to the activation.
# of downstream neurons is temporally removed on the forward pass and any weight updates are
# not applied to the neuron on the backward pass.
# More info on Dropout here http://machinelearningmastery.com/dropout-regularization-deep-learning-models-keras/
# BatchNormalization, Normalize the activations of the previous layer at each batch, i.e. applies a transformation 
# that maintains the mean activation close to 0 and the activation standard deviation close to 1.
# 'input_dims' inputs -> ['input_dims' -> 'input_dims' -> 'input_dims'//2 -> 'input_dims'//4] -> 1
def model():
    model = Sequential()
    #input layer
    model.add(Dense(input_dims, input_dim=input_dims, kernel_constraint=maxnorm(5)))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dropout(0.4)) # Reduce Overfitting With Dropout Regularization
    # hidden layers
    model.add(Dense(input_dims,kernel_constraint=maxnorm(5)))
    model.add(BatchNormalization())
    model.add(Activation(act_func))
    model.add(Dropout(0.4))
    
    model.add(Dense(input_dims//2,kernel_constraint=maxnorm(5)))
    model.add(BatchNormalization())
    model.add(Activation(act_func))
    model.add(Dropout(0.4))
    
    model.add(Dense(input_dims//4))
    model.add(Activation(act_func))
  
    # output layer (y_pred)
    model.add(Dense(1, activation='linear'))
    # Use a large learning rate with decay and a large momentum. Increase your learning rate by a factor of 10 to 100 and use a high momentum value of 0.9 or 0.99
    # sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    # adam = Adam(lr=0.01, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.0)
    # compile this model
    model.compile(loss='mean_squared_error', # one may use 'mean_absolute_error' as alternative
                  optimizer='adam',
                  metrics=[r2_keras] # you can add several if needed
                 )
    
    # Visualize NN architecture
    print(model.summary())
    return model
    
# initialize input dimension

if run_de:
    # Decomposition
    input_dims = train_decomposed_no_y.shape[1]
else:
    # No Decomposition
    input_dims = train.shape[1]-1
    
#activation functions for hidden layers
act_func = 'tanh' # could be 'relu', 'sigmoid', ...tanh

# make np.seed fixed
# np.random.seed(seed)

# initialize estimator, wrap model in KerasRegressor
estimator = KerasRegressor(
    build_fn=model, 
    nb_epoch=300, 
    batch_size=20,
    verbose=1
)

# X, y preparation
if run_de:
     # Decomposition
     X, y = train_decomposed_no_y, train_y
     X_test = test_decomposed
     print('\nTrain shape Decomposition: {}\nTest shape Decomposition: {}'.format(X.shape, X_test.shape))
else:    
     # No Decomposition
     X, y = train.drop('y', axis=1).copy().values, train.y.values
     X_test = test.values
     print('\nTrain shape No Feature Selection: {}\nTest shape No Feature Selection: {}'.format(X.shape, X_test.shape))

# train/validation split
X_tr, X_val, y_tr, y_val = train_test_split(
    X, 
    y, 
    test_size=0.2#, 
    #random_state=seed
)

# prepare callbacks
callbacks = [
    EarlyStopping(
        monitor='val_loss', 
        patience=10,
        verbose=1),
    ModelCheckpoint(
        model_path, 
        monitor='val_loss', 
        save_best_only=True, 
        verbose=0)
]

# fit estimator
history = estimator.fit(
    X_tr, 
    y_tr, 
    epochs=100, # increase it to 20-100 to get better results
    validation_data=(X_val, y_val),
    verbose=2,
    callbacks=callbacks,
    shuffle=True
)

# list all data in history
print(history.history.keys())

# summarize history for R^2
fig_acc = plt.figure(figsize=(10, 10))
plt.plot(history.history['r2_keras'])
plt.plot(history.history['val_r2_keras'])
plt.title('model accuracy')
plt.ylabel('R^2')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()
fig_acc.savefig("model_accuracy.png")

# summarize history for loss
fig_loss = plt.figure(figsize=(10, 10))
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()
fig_loss.savefig("model_loss.png")

# if best iteration's model was saved then load and use it
if os.path.isfile(model_path):
    estimator = load_model(model_path, custom_objects={'r2_keras': r2_keras})

# check performance on train set
print('MSE train: {}'.format(mean_squared_error(y_tr, estimator.predict(X_tr))**0.5)) # mse train
print('R^2 train: {}'.format(r2_score(y_tr, estimator.predict(X_tr)))) # R^2 train

# check performance on validation set
print('MSE val: {}'.format(mean_squared_error(y_val, estimator.predict(X_val))**0.5)) # mse val
print('R^2 val: {}'.format(r2_score(y_val, estimator.predict(X_val)))) # R^2 val
pass

# predict results
res = estimator.predict(X_test).ravel()
print(res)

# create df and convert it to csv
output = pd.DataFrame({'id': id_test, 'y': res})
output.to_csv('keras-baseline.csv', index=False)
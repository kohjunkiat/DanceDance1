import os
import numpy as np
from numpy import mean
from numpy import std
from numpy import dstack
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import TimeDistributed
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras.models import load_model
from keras.utils import to_categorical
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import itertools


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
data_processed_path = os.path.join(PROJECT_DIR, 'data', 'keras_datasets')

labels = [
    'hunchback', 'cowboy', 'crab', 'chicken', 'raffles', 'runningman', 'doublepump', 'snake',
    'mermaid', 'jamesbond', 'ultimate'
]


def get_callbacks(name_weights, patience_lr):
    mcp_save = ModelCheckpoint(name_weights, save_best_only=True, monitor='val_loss', mode='min')
    reduce_lr_loss = ReduceLROnPlateau(monitor='loss', factor=0.1, patience=patience_lr, verbose=1, epsilon=1e-4, mode='min')
    return [mcp_save, reduce_lr_loss]


def get_model(trainX, trainy, model_path=None):
    # define model
    verbose, epochs, batch_size = 2, 40, 96
    n_timesteps, n_features, n_outputs = trainX.shape[1], trainX.shape[2], trainy.shape[1]

    # reshape data into time steps of sub-sequences
    n_steps, n_length = 4, 4
    trainX = trainX.reshape((trainX.shape[0], n_steps, n_length, n_features))
    if os.path.isfile(model_path):
        model = load_model(model_path)
    else:
        model = Sequential()
        model.add(
            TimeDistributed(Conv1D(filters=64, kernel_size=2, activation='relu'), input_shape=(None, n_length, n_features)))
        model.add(TimeDistributed(Conv1D(filters=64, kernel_size=2, activation='relu')))
        model.add(TimeDistributed(Dropout(0.5)))
        model.add(TimeDistributed(MaxPooling1D(pool_size=1)))
        model.add(TimeDistributed(Flatten()))
        model.add(LSTM(100))
        model.add(Dropout(0.5))
        model.add(Dense(100, activation='relu'))
        model.add(Dense(n_outputs, activation='softmax'))
        model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    print(model.summary())
    return model


# load a single file as a numpy array
def load_file(filepath):
    dataframe = pd.read_csv(filepath)
    return dataframe.values


# load a list of files and return as a 3d numpy array
def load_group(filenames, prefix=''):
    loaded = list()
    for name in filenames:
        data = load_file(prefix + name)
        loaded.append(data)
    # stack group so that features are the 3rd dimension
    loaded = dstack(loaded)
    return loaded


# load a dataset group, such as train or test
def load_dataset_group(group, prefix=''):
    filepath = group + '\\'
    # load all 18 files as a single array
    filenames = list()
    # acceleration
    filenames += [
        'acc_x1.csv', 'acc_y1.csv', 'acc_z1.csv', 'acc_x2.csv', 'acc_y2.csv', 'acc_z2.csv', 'acc_x3.csv', 'acc_y3.csv',
        'acc_z3.csv'
    ]
    # body gyroscope
    filenames += [
        'gyro_x1.csv', 'gyro_y1.csv', 'gyro_z1.csv', 'gyro_x2.csv', 'gyro_y2.csv', 'gyro_z2.csv', 'gyro_x3.csv',
        'gyro_y3.csv', 'gyro_z3.csv'
    ]
    # load input data
    X = load_group(filenames, filepath)
    # load class output
    y = load_file(filepath + 'labels.csv')

    return X, y


# load the dataset, returns train and test X and y elements
def load_dataset(prefix=''):
    # load all train
    trainX, trainy = load_dataset_group(os.path.join(PROJECT_DIR, 'data', 'keras_datasets'))

    return trainX, trainy


# fit and evaluate a model
def evaluate_model(model, trainX, trainy, testX, testy):
    # define model
    verbose, epochs, batch_size = 0, 25, 96
    n_timesteps, n_features, n_outputs = trainX.shape[1], trainX.shape[2], trainy.shape[1]

    # reshape data into time steps of sub-sequences
    n_steps, n_length = 4, 4
    testX = testX.reshape((testX.shape[0], n_steps, n_length, n_features))

    # evaluate model
    _, accuracy = model.evaluate(testX, testy, batch_size=batch_size, verbose=0)
    return accuracy


def train_model(trainX, trainy):
    # define model
    verbose, epochs, batch_size = 2, 60, 96
    n_timesteps, n_features, n_outputs = trainX.shape[1], trainX.shape[2], trainy.shape[1]
    print(n_features)
    print(n_timesteps)

    # reshape data into time steps of sub-sequences
    n_steps, n_length = 4, 4
    trainX = trainX.reshape((trainX.shape[0], n_steps, n_length, n_features))
    # define model
    model = Sequential()
    model.add(TimeDistributed(Conv1D(filters=64, kernel_size=3, activation='relu'), input_shape=(None, n_length, n_features)))
    model.add(TimeDistributed(Conv1D(filters=64, kernel_size=3, activation='relu')))
    model.add(TimeDistributed(Dropout(0.5)))
    model.add(TimeDistributed(MaxPooling1D(pool_size=2)))
    model.add(TimeDistributed(Flatten()))
    model.add(LSTM(100, stateful=True))
    model.add(Dropout(0.5))
    model.add(Dense(100, activation='relu'))
    model.add(Dense(n_outputs, activation='softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    print(model.summary())
    # fit network
    model.fit(trainX, trainy, epochs=epochs, batch_size=batch_size, verbose=verbose)

    return model


# summarize scores
def summarize_results(scores):
    print(scores)
    m, s = mean(scores), std(scores)
    print('Accuracy: %.3f%% (+/-%.3f)' % (m, s))


# Generator for the implementation of cross validation
def get_generator_values(X_train_cv, y_train_cv, batch):
    batch_list_x = []
    batch_list_y = []
    while 1:  # run forever, so you can generate elements indefinitely
        for n in range(len(X_train_cv)):
            batch_list_x.append(X_train_cv[n])
            batch_list_y.append(y_train_cv[n])
            if len(batch_list_x) == batch:
                yield (np.array(batch_list_x), np.array(batch_list_y))
                batch_list_x = []
                batch_list_y = []


data_x, data_y = load_dataset()
print(len(data_x[0][0]))
trainX, testX, trainY, testY = train_test_split(data_x, data_y, test_size=0.2, random_state=42)

trainY = to_categorical(trainY)
testY = to_categorical(testY)
print(trainX.shape, trainY.shape)
print(testX.shape, testY.shape)

# # Training normal, without validating with cross validation
# model = train_model(trainX, trainY)
# model_dir = os.path.join(PROJECT_DIR, 'models')
# model_filepath = os.path.join(model_dir, 'onesecondmodel.h5')
# model.save(model_filepath)
# model = load_model(model_filepath)
#
# score = evaluate_model(model, trainX, trainY, testX, testY)
# score = score * 100.0
# print('%.3f' % score)


#Training with Cross Validation of kFold = 5
# Instantiate the cross validator
kfold_splits = 5
seed = 7
skf = StratifiedKFold(n_splits=kfold_splits, shuffle=True, random_state=seed)
for train_idx, val_idx in skf.split(trainX, trainY.argmax(1)):
    X_train_cv = trainX[train_idx]
    y_train_cv = trainY[train_idx]
    X_valid_cv = trainX[val_idx]
    y_valid_cv = trainY[val_idx]
    print(len(X_train_cv))
    model_path = os.path.join(PROJECT_DIR, 'models', "cnnlstmmodel16(2mins).h5")
    callbacks = get_callbacks(name_weights=model_path, patience_lr=10)
      # define model
    verbose, epochs, batch_size = 2, 40, 96
    n_timesteps, n_features, n_outputs = X_train_cv.shape[1], X_train_cv.shape[2], y_train_cv.shape[1]

    # reshape data into time steps of sub-sequences
    n_steps, n_length = 4, 4
    X_train_cv = X_train_cv.reshape(X_train_cv.shape[0], n_steps, n_length, n_features)
    X_valid_cv = X_valid_cv.reshape(X_valid_cv.shape[0], n_steps, n_length, n_features)
    generator = get_generator_values(X_train_cv, y_train_cv, batch_size)

    model = get_model(trainX, trainY, model_path)
    model.fit_generator(
        generator,
        steps_per_epoch=len(X_train_cv) / batch_size,
        epochs=15,
        shuffle=True,
        verbose=2,
        validation_data=(X_valid_cv, y_valid_cv),
        callbacks=callbacks)

    print(model.evaluate(X_valid_cv, y_valid_cv))


# To test performance of the trained model
model_path = os.path.join(PROJECT_DIR, 'models', 'cnnlstmmodel16(2mins).h5')
model = load_model(model_path)
print(len(testX))
print(testX[0])

n_features = 18
# reshape data into time steps of sub-sequences
n_steps, n_length = 4, 4
test_samples = testX.reshape(29176, n_steps, n_length, n_features)
results = model.predict(test_samples, batch_size=96, verbose=0)
print(len(results))
score = evaluate_model(model, trainX, trainY, testX, testY)
score = score * 100.0
print('%.3f' % score)
rounded_predictions = []
for i in results:
    rounded_predictions.append(np.argmax(i))
conf_mat = confusion_matrix(testY.argmax(1), rounded_predictions)
print(conf_mat)


# To show the confusion matrix in a figure
def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()


# Plot non-normalized confusion matrix
plt.figure()
plot_confusion_matrix(conf_mat, classes=labels,
                      title='Confusion matrix, without normalization')
#
# # Plot normalized confusion matrix
# plt.figure()
# plot_confusion_matrix(cnf_matrix, classes=labels, normalize=True,
#                       title='Normalized confusion matrix')
#
plt.show()

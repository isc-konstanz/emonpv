# Just disables the warning, doesn't enable AVX/FMA
import sys
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from pathlib import Path

import numpy as np
import pandas as pd
from keras.models import Model, model_from_json, Sequential
from keras.layers import Input, Dense, Flatten, LeakyReLU
from keras.layers.convolutional import Conv1D
from keras.callbacks import TensorBoard, History, EarlyStopping


def to_cyclic_feature(df, feature, num):
    df[feature + '_x'] = np.sin(2.0 * np.pi * df[feature] / num)
    df[feature + '_y'] = np.cos(2.0 * np.pi * df[feature] / num)
    return df.drop(feature, axis=1)


class Learning():
    
    def __init__(self, load=False, name='model', **kwargs):
        ## net params
        self.num_layers = 3
        self.num_neurons = 100
        self.filter_size = 32
        self.kernel_size = 2
        self.batch_size = 1024
        self.const_features = ['latitude', 'longitude', 'altitude', 'modules_per_string', 'strings_per_inverter', 'tilt',
                          'azimuth', 'albedo', 'Technology', 'BIPV', 'A_c', 'N_s', 'pdc0', 'gamma_pdc']
        self.dyn_features = ['Wind Direction_x', 'Wind Direction_y', 'Total Cloud Cover', 'Low Cloud Cover', 'Medium Cloud Cover',
                        'High Cloud Cover', 'Wind Speed', 'Total Precipitation',
                        'Snow Fraction', 'Mean Sea Level Pressure', 'DIF - backwards', 'DNI - backwards', 'Shortwave Radiation',
                        'Temperature', 'Relative Humidity', 'Hour_x', 'Hour_y', 'Month_x', 'Month_y']               
        self.target_features = ['power']
        self.act_fct = 'relu'
        self.loss_fct = 'mae'
        self.optim = 'adam'
        self.metrics = []#'mse']
        self.history = History()
        #self.val_history = History()

        ## data params
        self.filename = '../datasets/full_data_5_systems.csv'
        if not os.path.exists('../datasets/'):
            os.makedirs('../datasets/')
        self.timesteps = 5
        self.num_sys = 5
        self.shape = (self.timesteps + 1, len(self.const_features + self.dyn_features + self.target_features) + 1)
        
        ## training params
        self.callbacks = [self.history, EarlyStopping(patience=10, restore_best_weights=True)]
        self.verbose = 1
        self.epochs = 200
        self.forecast_horizon = 24
        self.sliding_window = 120
        self.save_dir = '../learning/'
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        self.get_model(load, name)


    # create or load model
    def get_model(self, load=False, name='model'):
        if load:
            # load json and create model
            json_file = open(self.save_dir + name + '.json', 'r')
            model_json = json_file.read()
            json_file.close()
            self.model = model_from_json(model_json)
            # load weights into new model
            self.model.load_weights(self.save_dir + name + '.h5')
            print("Loaded model from disk")
        else:
            self.model = Sequential()
            self.model.add(Conv1D(self.filter_size, self.kernel_size, input_shape=self.shape, activation=self.act_fct, dilation_rate=1, padding='causal', kernel_initializer='he_uniform'))
            for n in range(self.num_layers):
                self.model.add(Conv1D(self.filter_size, self.kernel_size, activation=self.act_fct, dilation_rate=2**(n+1), padding='causal', kernel_initializer='he_uniform'))
            self.model.add(Flatten())
            self.model.add(Dense(self.num_neurons, activation=self.act_fct, kernel_initializer='he_uniform'))
            self.model.add(Dense(self.num_neurons, activation=self.act_fct, kernel_initializer='he_uniform'))
            self.model.add(Dense(self.num_neurons, activation=self.act_fct, kernel_initializer='he_uniform'))
            self.model.add(Dense(len(self.target_features)))
            self.model.add(LeakyReLU(alpha=0.001))

        self.model.compile(loss=self.loss_fct, optimizer=self.optim, metrics=self.metrics)
    
    
    # create historical datasets
    def create_historical_dataset(self):
        fname = self.save_dir + 'data_step' + str(self.timesteps)

        if Path(fname + '.npz').exists():
            print('Loading preprocessed dataset ...')
            with np.load(fname + '.npz') as datafile:
                self.trainX = datafile['trainX']
                self.trainY = datafile['trainY']
                self.testX = datafile['testX']
                self.testY = datafile['testY']
                self.pvlib = datafile['pvlib']
                self.idx = datafile['idx']
        else:
            print('Data preprocessing ...')
            dataframe = pd.read_csv(self.filename, skipinitialspace=True).set_index(['time', 'SystemID'])
            dataframe = np.array_split(dataframe, self.num_sys)
            pvlibs = []
            trainXs = []
            trainYs = []
            testXs = []
            testYs = []
            idxs = []
            for s in range(self.num_sys):
                df = dataframe[s]
                pvlibs.append(df.power_pvlib)
                dataset = df[self.const_features + self.dyn_features + self.target_features]
        
                dataset['forecast_horizon'] = 0
                p = dataset[self.target_features]
                dataset = dataset.drop(self.target_features, axis=1)
                for f in self.target_features:
                    dataset[f] = p[f]
                dataset = dataset.dropna()

                x = []
                for i in range(self.timesteps+1, len(dataset)+1):
                    sys.stdout.write("System %i/%i: %5i/%i                \r" % (s+1, self.num_sys, i, len(dataset)))
                    sys.stdout.flush()
                    d = dataset.iloc[i-self.timesteps-1:i].copy()
                    d.iloc[-1, -len(self.target_features):] = -1
                    x.append(d.values)
                x = np.array(x)
                y = dataset[self.target_features].iloc[self.timesteps:]
                split = dataset[:('2015-10-11 00:00:00', s)].iloc[self.timesteps+1:].shape[0]
                trainX, testX = x[:split], x[split:]
                trainY, testY = y.iloc[:split].values, y.iloc[split:].values
                idx = y.iloc[split:].index
                
                trainXs.append(trainX)
                trainYs.append(trainY)
                testXs.append(testX)
                testYs.append(testY)
                idxs.append(idx)
                
            a = np.stack(trainYs, axis=1)
            self.trainY = a.reshape(a.shape[0]*a.shape[1], a.shape[2])

            a = np.stack(trainXs, axis=1)
            self.trainX = a.reshape(a.shape[0]*a.shape[1], a.shape[2], a.shape[3])

            a = np.stack(testYs, axis=1)
            self.testY = a.reshape(a.shape[0]*a.shape[1], a.shape[2])

            a = np.stack(testXs, axis=1)
            self.testX = a.reshape(a.shape[0]*a.shape[1], a.shape[2], a.shape[3])

            a = np.stack(pvlibs, axis=1)
            self.pvlib = a.reshape(a.shape[0]*a.shape[1], 1)[-len(testY)-self.forecast_horizon*self.num_sys:]

            a = np.stack(idxs, axis=1)
            self.idx = a.reshape(a.shape[0]*a.shape[1])

            np.savez(fname, trainX=self.trainX, trainY=self.trainY, testX=self.testX, testY=self.testY, pvlib=self.pvlib, idx=self.idx)
            print('Saved to ' + fname + '.npz       ')
        print('Preprocessing done.')
    
    
    # create input for prediction
    def create_input(self, weather, system, location):
        df = weather.rename(columns={'temp_air': 'Temperature', 'wind_speed': 'Wind Speed', 'humidity_rel': 'Relative Humidity',
                       'pressure_sea': 'Mean Sea Level Pressure', 'ghi': 'Shortwave Radiation', 'dni': 'DNI - backwards',
                       'dhi': 'DIF - backwards', 'total_clouds': 'Total Cloud Cover', 'low_clouds': 'Low Cloud Cover',
                       'mid_clouds': 'Medium Cloud Cover', 'high_clouds': 'High Cloud Cover', 'rain': 'Total Precipitation',
                       'snow': 'Snow Fraction', 'wind_direction': 'Wind Direction'})
        df['Hour'] = pd.to_datetime(df.index).hour.values
        df['Month'] = pd.to_datetime(df.index).month.values
        df = to_cyclic_feature(df, 'Hour', 24)
        df = to_cyclic_feature(df, 'Month', 12)
        df = to_cyclic_feature(df, 'Wind Direction', 360)
        
        df['latitude'] = location.latitude
        df['longitude'] = location.longitude
        df['altitude'] = location.altitude
        df['modules_per_string'] = system.modules_per_string
        df['strings_per_inverter'] = system.strings_per_inverter
        df['tilt'] = system.surface_tilt
        df['azimuth'] = system.surface_azimuth
        df['albedo'] = system.albedo
        t = 3 #CIGS
        if system.module_parameters['Technology'] == "Mono-c-Si": t = 0
        elif system.module_parameters['Technology'] == "Multi-c-Si": t = 1
        elif system.module_parameters['Technology'] == "Thin Film": t = 2
        df['Technology'] = t
        b = 1
        if system.module_parameters['BIPV'] == 'N': b = 0
        df['BIPV'] = b
        df['A_c'] = system.module_parameters['A_c']
        df['N_s'] = system.module_parameters['N_s']
        df['pdc0'] = system.module_parameters['pdc0']
        df['gamma_pdc'] = system.module_parameters['gamma_pdc']
        df = df[pd.Timestamp.now('UTC') - pd.to_timedelta(self.timesteps, unit='h'):] # take only the last self.timesteps
        df['forecast_horizon'] = 0
        df['power'] = -1
        df['power'].iloc[:self.timesteps] = -1 # TODO: set the correct measurements for the last self.timesteps here
        
        input = df[self.const_features + self.dyn_features + ['forecast_horizon'] + self.target_features].values
        return input, df.index.values[self.timesteps:]
    
    
    # pre-train model with historical data
    def pre_train_model(self):
        print('Start pretraining ...')    
        self.train_model(self.trainX, self.trainY)
        print('Done.')
        self.save_model('pretrained')
    
    
    # train model with new data
    def train_model(self, X, y):
        val_idx = int(len(y) / 10.0)
        self.model.fit(X[val_idx:], y[val_idx:], self.batch_size, self.epochs, self.verbose, self.callbacks, validation_data=(X[:val_idx], y[:val_idx]))

        
    # predict with new data
    def predict(self, X):
        # initialize values for lagged power columns
        p = []
        for l in range(self.timesteps):
            p.append(X[l][-1])
        predictions = []
        ts = []
        for f in range(len(X) - self.timesteps):
            # build input vector for future timestep
            t = np.array([X[f:f+self.timesteps+1]])
            if t.size > 0:
                for l in range(self.timesteps-1):
                    t[0][l,-1] = p[l]
                    p[l] = p[l+1]
                t[0][-2,-1] = p[-1]
                t[0][:,-2] = f
                ts.append([t, -1])

                # make prediction for input new vector
                p[-1] = self.model.predict(t, self.batch_size).item(0)
                predictions.append(p[-1])

        return ts, pd.DataFrame(predictions)

    
    # save model
    def save_model(self, name='model'):
        # serialize model to JSON
        model_json = self.model.to_json()
        with open(self.save_dir + name + '.json', 'w') as json_file:
            json_file.write(model_json)
        # serialize weights to HDF5
        self.model.save_weights(self.save_dir + name + '.h5')
        print("Saved model to disk")

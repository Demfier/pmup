from keras.models import model_from_json
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from matplotlib.pyplot import specgram
import keras
from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Embedding
from keras.layers import LSTM
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.layers import Input, Flatten, Dropout, Activation
from keras.layers import Conv1D, MaxPooling1D, AveragePooling1D
from keras.models import Model
from keras.callbacks import ModelCheckpoint
from sklearn.metrics import confusion_matrix
import pandas as pd
from keras.utils import np_utils
from sklearn.preprocessing import LabelEncoder

def audio_dep(file):
    json_file = open('./model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights("./Emotion_Voice_Detection_Model.h5")
    # print(loaded_model)
    #livedf= pd.DataFrame(columns=['feature'])
    X, sample_rate = librosa.load(file, res_type='kaiser_fast',duration=3,sr=22050*2)
    sample_rate = np.array(sample_rate)
    mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=40),axis=0)

    if len(mfccs) > 216:
        mfccs = mfccs[:216]
    else:
        mfccs = np.concatenate((mfccs, np.asarray([0 for x in range(216-len(mfccs))])))

    livedf2 = mfccs

    livedf2 = pd.DataFrame(data=livedf2)

    livedf2 = livedf2.stack().to_frame().T

    twodim = np.expand_dims(livedf2, axis=2)

    livepreds = loaded_model.predict(twodim, batch_size=32, verbose=0)
    # 1,3,6,8- happy
    # 0, 2,4,5,7,9- sad

    livepreds1 = livepreds.argmax(axis=1)
    liveabc = livepreds1.astype(int).flatten()[0]

    #print(liveabc)

    h= livepreds[0][1] + livepreds[0][3]  + livepreds[0][6]  + livepreds[0][8]
    s= sum(livepreds[0])-h
    r= 1-(s/h)

    return(r)
    # if liveabc in [1,3,6,8]:
    #     return("happy", livepreds[0][liveabc], r)
    # else:
    #     return("sad", livepreds[0][liveabc], r)

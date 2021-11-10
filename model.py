import numpy as np
from database import Database
from keras.models import Model, load_model
from keras.layers import Dense, Input, concatenate
import keras
from settings import *


def getMatchData():
    data = Database.getMatchData()
    dataType = np.dtype(
        [
            ("matchId", str, 14),
            ("100-1", int),
            ("100-2", int),
            ("100-3", int),
            ("100-4", int),
            ("100-5", int),
            ("200-1", int),
            ("200-2", int),
            ("200-3", int),
            ("200-4", int),
            ("200-5", int),
            ("sideWon", int),
        ]
    )
    arr = np.asarray(data)
    return arr


def splitData(arr):
    nRows = len(arr)
    dataSplit = int(nRows * TRAINING_SPLIT)
    trainData = arr[:dataSplit]
    testData = arr[dataSplit:]
    return trainData, testData

def getDataBuckets(arr):
    trainData, testData = splitData(arr)
    xTrain = [trainData[:,[1,2,3,4,5]], trainData[:,[6,7,8,9,10]]]
    xTrain = np.asarray(xTrain)
    xTrain = xTrain.astype(int)
    
    yTrain = trainData[:,[11]]
    yTrain = np.asarray(yTrain)
    yTrain = yTrain.astype(int)
    
    xTest = [testData[:,[1,2,3,4,5]], testData[:,[6,7,8,9,10]]]
    xTest = np.asarray(xTest)
    xTest = xTest.astype(int)
    
    yTest = testData[:,[11]]
    yTest = np.asarray(yTest)
    yTest = yTest.astype(int)
    return xTrain, yTrain, xTest, yTest

def createModel():
    arr = getMatchData()
    
    xTrain, yTrain, xTest, yTest = getDataBuckets(arr)
    
    blueInput = Input(shape=(5,), name="blueTeam")
    dense = Dense(64, activation="relu")
    x = dense(blueInput)
    x = Dense(64, activation="relu")(x)
    outputs = Dense(10)(x)
    
    redInput = Input(shape=(5,), name="redTeam")
    dense2 = Dense(64, activation="relu")
    x2 = dense2(redInput)
    x2 = Dense(64, activation="relu")(x2)
    
    concat = concatenate([x,x2])
    outputs = Dense(10)(concat)

    model = Model(inputs=[blueInput, redInput], outputs=outputs)
    
    m = 256
    n_epoch = 25
    
    model.compile(optimizer='Nadam',
              loss='binary_crossentropy', 
            )

    model.fit(list(xTrain), yTrain, epochs=n_epoch, batch_size=m, shuffle=True)
    model.save(MODEL_DIR)
    
def loadModel():
    model = load_model(MODEL_DIR)
    return model


if __name__ == "__main__":
    arr = getMatchData()
    
    xTrain, yTrain, xTest, yTest = getDataBuckets(arr)
    if (CREATE_NEW_MODEL):
        createModel()
        
    model = loadModel()
    
    testInput = [xTest[0], xTest[1]]
    
    testOut = model.predict(testInput)
    print(f"Predicted={testOut}, actual={yTest[0]}")
    pass

    
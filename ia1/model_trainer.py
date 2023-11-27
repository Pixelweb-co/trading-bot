import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential

print("model traning")

# Cargar los datos históricos
df = pd.read_csv('historical_data.csv', index_col=0)
prediction_window = 5
fibonacci_length = 5

def fibonacci(sequence_length):
    if sequence_length == 1:
        return [1]
    elif sequence_length == 2:
        return [1, 1]
    else:
        fib_sequence = [1, 1]
        while len(fib_sequence) < sequence_length:
            next_fib = fib_sequence[-1] + fib_sequence[-2]
            fib_sequence.append(next_fib)
        return fib_sequence



#fibonnaci
fib_sequence = fibonacci(fibonacci_length)
for i in range(len(fib_sequence)):
    df[f"fib_{i+1}"] = df["close"].shift(i) - fib_sequence[i]

# Crear columna para la predicción
df["prediction"] = df["close"].shift(-prediction_window)

print("Número de columnas:", len(df.columns))
# Seleccionar los datos de entrada y salida
X = df.drop(['close'], axis=1)
y = df['close']

# Dividir los datos en conjuntos de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Crear el modelo de aprendizaje automático
model = Sequential()
model.add(Dense(32, input_dim=10, activation='relu'))
model.add(Dense(1, activation='linear'))
model.compile(loss='mse', optimizer='adam')

# Entrenar el modelo
model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test, y_test))

# Guardar el modelo en un archivo HDF5
model.save('model.h5')

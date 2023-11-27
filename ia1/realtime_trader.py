import time
import datetime
import numpy as np
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from tensorflow.keras.models import load_model
import subprocess

API = IQ_Option("xxxxxx@gmail.com", "xxxxxx")
API.connect()  # Conectar a IQOption
goal = "EURUSD-OTC" 
balance_type = "PRACTICE"
API.change_balance(balance_type)

print("entrenando...")
subprocess.run(['python3', 'data_collector.py'])
subprocess.run(['python3', 'model_trainer.py'])

model = load_model('model.h5')


# Configurar los parámetros de la estrategia
asset_name = 'EURUSD'
timeframe = '60'
amount = 1
direction = ''
expiration_time = 2
polling_time=3
bets = []
trade = False

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


step = 0

while True:
    hora_actual = datetime.datetime.now()

    if hora_actual.second == 0 and step == 5:
        print("entrenando...")
        trade = False
        subprocess.run(['python3', 'data_collector.py'])
        subprocess.run(['python3', 'model_trainer.py'])
        model = load_model('model.h5')
        step = 0

    if hora_actual.second == 45 and trade == False:
        # Obtener las velas más recientes
        candles = API.get_candles(goal, 60, 5, time.time())
        df = pd.DataFrame(candles, columns=['from', 'open', 'close', 'min', 'max', 'volume'])
        #fibonnaci
        fib_sequence = fibonacci(fibonacci_length)
        for i in range(len(fib_sequence)):
            df[f"fib_{i+1}"] = df["close"].shift(i) - fib_sequence[i]

        # Crear columna para la predicción
        df["prediction"] = df["close"].shift(-prediction_window)

        print("Número de columnas:", len(df.columns))

        df.set_index('from', inplace=True)
        df.index = pd.to_datetime(df.index, unit='s')
         # Seleccionar los datos de entrada
        X = df.drop(['close'], axis=1)

        # Utilizar el modelo para predecir el precio de cierre
        y_pred = model.predict(X)

        # Tomar una decisión de compra o venta en función de la predicción
        if y_pred[-1] > np.mean(y_pred[:-1]):
            print("Comprar")
            result, id = API.buy(amount, asset_name, 'call', expiration_time)
            print('Operación de compra abierta con ID:', id)
            trade = True
        else:
            print("Vender")
            result, id = API.buy(amount, asset_name, 'put', expiration_time)
            print('Operación de compra abierta con ID:', id)
            trade = True
        # Esperar a que finalice la operación
        if 'id' in locals():
            print("Esperando finalice la operacion")
            if trade:
                time.sleep(2)
            
                print("trdeing seg ",datetime.datetime.now().second)
            
                tempo = datetime.datetime.now().second
                while(tempo != 0): #wait till 1 to see if win or lose
                    tempo = datetime.datetime.now().second
                    #print("tempo ",tempo)
                    if tempo == 30:
                        print("validando estado precio")    

                betsies = API.get_optioninfo(1)
                #print(betsies)
                betsies = betsies['msg']['result']['closed_options']
                    
                for bt in betsies:
                    bets.append(bt['win'])
                win = bets[-1:]
                print(win)
                if win == ['win']:
                   print(f'win')
                   #bet_money = 1
                        
                elif win == ['lose']:
                   print(f'lose')
                   #bet_money = bet_money * martingale # martingale V3
                        
                else:
                   print(f'none')
                   bets.append(0)
                   #print(bet_money)
                trade = False        
        step = step + 1            
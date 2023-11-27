from iqoptionapi.stable_api import IQ_Option
import pandas as pd
import time

print("data collector")

API = IQ_Option("xxxxxx@gmail.com", "xxxxxx")
API.connect()  # Conectar a IQOption
goal = "EURUSD-OTC"
balance_type = "PRACTICE"
API.change_balance(balance_type)

# Configurar los parámetros de la estrategia
asset_name = 'EURUSD-OTC'
timeframe = '60'
amount = 10
direction = ''
expiration_time = 2
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


# Obtener las velas históricas
candles = API.get_candles(goal, int(timeframe), 2000, time.time())
df = pd.DataFrame(candles, columns=['from', 'open', 'close', 'min', 'max', 'volume'])
df.set_index('from', inplace=True)
df.index = pd.to_datetime(df.index, unit='s')

#fibonnaci
fib_sequence = fibonacci(fibonacci_length)
for i in range(len(fib_sequence)):
    df[f"fib_{i+1}"] = df["close"].shift(i) - fib_sequence[i]

# Crear columna para la predicción
df["prediction"] = df["close"].shift(-prediction_window)

# Almacenar los datos en un archivo CSV
df.to_csv('historical_data.csv')

import time
from iqoptionapi.stable_api import IQ_Option
import numpy as np
import talib
import datetime
import pandas as pd
from colorama import init, Fore, Style

# Inicializar colorama
init()

API=IQ_Option("xxxxxx@gmail.com", "xxxxxx")
API.connect() # Conectar a IQ Option
goal = "EURUSD"
balance_type = "PRACTICE"
API.change_balance(balance_type)

# Configurar los parámetros de la estrategia
asset_name = "EURUSD"
timeframe = "1"
amount = 10
direction = ""
expiration_time = 2

# Obtener las velas más recientes
def get_candles():
    candles = API.get_candles(goal, int(timeframe), 100, time.time())
    if candles is None:
        return None
    df = pd.DataFrame(candles)
    df.set_index('from', inplace=True)
    df.index = pd.to_datetime(df.index, unit='s')
    close_prices = df['close'].astype(float)
    
    
    return close_prices,df

while True:
    hora_actual = datetime.datetime.now()
    if hora_actual.second == 56:
        print("Obteniendo velas...")
        close_prices, df = get_candles()
        if close_prices is None:
            continue

        high_prices =df['max'].astype(float)
        low_prices = df['min'].astype(float)

        # Calcular los niveles de soporte y resistencia
        pivot = (close_prices[-1] + close_prices[-2] + close_prices[-3]) / 3
        r1 = (2 * pivot) - close_prices[-3]
        r2 = pivot + (close_prices[-3] - close_prices[-4])
        r3 = close_prices[-1] + 2 * (pivot - close_prices[-3])
        s1 = (2 * pivot) - close_prices[-3]
        s2 = pivot - (close_prices[-3] - close_prices[-4])
        s3 = close_prices[-1] - 2 * (close_prices[-3] - pivot)


        # Calcular los indicadores técnicos
        ema20 = talib.EMA(close_prices, timeperiod=20)
        ema50 = talib.EMA(close_prices, timeperiod=50)
        rsi = talib.RSI(close_prices, timeperiod=14)
        macd, macd_signal, macd_hist = talib.MACD(close_prices)
        stoch_k, stoch_d = talib.STOCH(high=high_prices, low=low_prices, close=close_prices)
        cci = talib.CCI(high=high_prices, low=low_prices, close=close_prices, timeperiod=14)
        aroon_down, aroon_up = talib.AROON(high=high_prices, low=low_prices, timeperiod=14)

        # Verificar si se cumple la condición de entrada
        if close_prices[-1] > r1 and close_prices[-2] <= r1 and ema20[-1] > ema50[-1] and ema20[-2] <= ema50[-2] and rsi[-1] > 60 and macd[-1] > macd_signal[-1] and stoch_k[-1] < 80 and cci[-1] > 0 and aroon_up[-1] > aroon_down[-1]:
            direction = "put"
        elif close_prices[-1] < s1 and close_prices[-2] >= s1 and ema20[-1] < ema50[-1] and ema20[-2] >= ema50[-2] and rsi[-1] < 40 and macd[-1] < macd_signal[-1] and stoch_k[-1] > 20 and cci[-1] < 0 and aroon_down[-1] > aroon_up[-1]:
            direction = "call"
        
        print("cci ",cci[-1])

        print("stk ", stoch_k[-1])
        print("std ", stoch_d[-1])


        # Abrir la operación si se cumple la condición de entrada
        if direction:
            print(Fore.GREEN + "Abrir operación: {} {} - Monto: {} - Vencimiento: {} minutos".format(asset_name, direction.upper(), amount, expiration_time) + Style.RESET_ALL)
            result, id = API.buy(amount, asset_name, direction, expiration_time)
            print(result)




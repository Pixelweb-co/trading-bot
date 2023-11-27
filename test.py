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
API.connect()#connect to iqoption
goal="EURUSD"
balance_type="PRACTICE"
API.change_balance(balance_type)

# Configurar los parámetros de la estrategia
asset_name = 'EURUSD'
timeframe = '60'
amount = 10
direction = ''
expiration_time = 2

# Configurar los parámetros del oscilador estocástico
period_k = 14
period_d = 3
overbought = 80
oversold = 20

# Configurar los parámetros de la nube Ichimoku
tenkan_period = 9
kijun_period = 26
senkou_period = 52

def ichimoku_cloud(high, low, tenkan_period, kijun_period, senkou_period):
    # Calcular las líneas Tenkan-sen y Kijun-sen
    tenkan_sen = talib.EMA(high, timeperiod=tenkan_period) + talib.EMA(low, timeperiod=tenkan_period)
    tenkan_sen /= 2.0
    kijun_sen = talib.EMA(high, timeperiod=kijun_period) + talib.EMA(low, timeperiod=kijun_period)
    kijun_sen /= 2.0

    # Calcular la línea Senkou Span A
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(tenkan_period)

    # Calcular la línea Senkou Span B
    senkou_span_b = ((talib.EMA(high, timeperiod=senkou_period) + talib.EMA(low, timeperiod=senkou_period)) / 2).shift(kijun_period)

    return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b


# Obtener los datos de precios en tiempo real
while True:
    hora_actual = datetime.datetime.now()
    #print(hora_actual.second)
    if hora_actual.second == 49:
        print("obteniendo velas")

        # Obtener las velas más recientes
        candles = API.get_candles(goal, int(timeframe), 100, time.time())
        if candles is None:
            continue
        df = pd.DataFrame(candles)
        df.set_index('from', inplace=True)
        df.index = pd.to_datetime(df.index, unit='s')
    # Validar los datos recibidos
        if df.empty or len(df) < senkou_period:
            continue

        # Obtener los precios de cierre de las velas más recientes
        close_prices = df['close'].astype(float)

        # Calcular los niveles de Ichimoku Cloud
        tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b = ichimoku_cloud(
            df['max'].astype(float), 
            df['min'].astype(float), 
            tenkan_period, kijun_period, senkou_period
        )

        # Calcular los niveles de Fibonacci
        high = np.max(close_prices[-senkou_period:])
        low = np.min(close_prices[-senkou_period:])
        diff = high - low
        fib_23 = high - diff * 0.236
        fib_38 = high - diff * 0.382
        fib_50 = high - diff * 0.5
        fib_61 = high - diff * 0.618
        fib_78 = high - diff * 0.786

        # Calcular la diferencia entre el precio actual y los niveles de Fibonacci
        fib_diff_23 = abs(close_prices[-1] - fib_23)
        fib_diff_38 = abs(close_prices[-1] - fib_38)
        fib_diff_50 = abs(close_prices[-1] - fib_50)
        fib_diff_61 = abs(close_prices[-1] - fib_61)
        fib_diff_78 = abs(close_prices[-1] - fib_78)

        # Imprimir las diferencias entre el precio actual y los niveles de Fibonacci
        print('Diferencia con nivel de Fibonacci 23.6%:', fib_diff_23)
        print('Diferencia con nivel de Fibonacci 38.2%:', fib_diff_38)
        print('Diferencia con nivel de Fibonacci 50.0%:', fib_diff_50)
        print('Diferencia con nivel de Fibonacci 61.8%:', fib_diff_61)
        print('Diferencia con nivel de Fibonacci 78.6%:', fib_diff_78)

        # Determine the closest Fibonacci level
        min_diff = min(fib_diff_23, fib_diff_38, fib_diff_50, fib_diff_61, fib_diff_78)

        if min_diff == fib_diff_23:
            print(Fore.GREEN +"The current price is closest to the Fibonacci 23.6% level.")
        elif min_diff == fib_diff_38:
            print(Fore.CYAN  +"The current price is closest to the Fibonacci 38.2% level.")
        elif min_diff == fib_diff_50:
            print(Fore.BLUE  +"The current price is closest to the Fibonacci 50.0% level.")
        elif min_diff == fib_diff_61:
            print(Fore.YELLOW  +"The current price is closest to the Fibonacci 61.8% level.")
        else:
            print(Fore.RED  +"The current price is closest to the Fibonacci 78.6% level.")

        print(Style.RESET_ALL)    
        print('seg: ',hora_actual.second)
    if hora_actual.second == 55:
       
        # Verificar si el precio cruza alguno de los niveles de Fibonacci
        if close_prices[-1] > fib_61 and close_prices[-2] <= fib_61:
            # Abrir una operación de compra
            result, id = API.buy(amount, asset_name, 'call', expiration_time)
            print('Operación de compra abierta con ID:', id)

        elif close_prices[-1] < fib_38 and close_prices[-2] >= fib_38:
            # Abrir una operación de venta
            result, id = API.buy(amount, asset_name, 'put', expiration_time)
            print('Operación de venta abierta con ID:', id)
        

API.disconnect()
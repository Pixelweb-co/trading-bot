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
balance_type="REAL"
API.change_balance(balance_type)

# Configurar los parámetros de la estrategia
asset_name = 'EURUSD'
timeframe = '60'
amount = 6
direction = ''
expiration_time = 1


while True:
    hora_actual = datetime.datetime.now()
    if hora_actual.second == 49:
        print("Obteniendo velas")

        # Obtener las velas más recientes
        candles = API.get_candles(goal, int(timeframe), 100, time.time())
        if candles is None:
            continue
        df = pd.DataFrame(candles)
        df.set_index('from', inplace=True)
        df.index = pd.to_datetime(df.index, unit='s')

        # Obtener los precios de cierre de las velas más recientes
        close_prices = df['close'].astype(float)

        # Calcular los niveles de retroceso de Fibonacci
        highest = np.max(close_prices)
        lowest = np.min(close_prices)
        diff = highest - lowest
        level_0_0 = highest
        level_23_6 = highest - (0.236 * diff)
        level_38_2 = highest - (0.382 * diff)
        level_50_0 = highest - (0.5 * diff)
        level_61_8 = highest - (0.618 * diff)
        level_76_4 = highest - (diff * 0.764)

        level_100_0 = lowest

        # Calcular la diferencia entre el precio actual y los niveles de Fibonacci
        fib_diff_23 = abs(close_prices[-1] - level_23_6)
        fib_diff_38 = abs(close_prices[-1] - level_38_2)
        fib_diff_50 = abs(close_prices[-1] - level_50_0)
        fib_diff_61 = abs(close_prices[-1] - level_61_8)
        fib_diff_74 = abs(close_prices[-1] - level_76_4)

        # Imprimir las diferencias entre el precio actual y los niveles de Fibonacci
        print('Diferencia con nivel de Fibonacci 23.6%:', fib_diff_23)
        print('Diferencia con nivel de Fibonacci 38.2%:', fib_diff_38)
        print('Diferencia con nivel de Fibonacci 50.0%:', fib_diff_50)
        print('Diferencia con nivel de Fibonacci 61.8%:', fib_diff_61)
        print('Diferencia con nivel de Fibonacci 78.6%:', fib_diff_74)

        # Determine the closest Fibonacci level
        min_diff = min(fib_diff_23, fib_diff_38, fib_diff_50, fib_diff_61, fib_diff_74)

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

    if hora_actual.second == 56:
        # Verificar si se hace operación según la estrategia
        
        if close_prices[-1] <= level_23_6 and close_prices[-2] > level_23_6:
            direction = "call"
            confirmed = False
        elif close_prices[-1] >= level_61_8 and close_prices[-2] < level_61_8:
             direction = "put"
             confirmed = False   
        else:
            direction = ""
            confirmed = True
        print("validando...",direction)

        # Realizar operación si se cumple la condición de entrada
        if direction != "" :
            print(Fore.GREEN +"Se cumple la condición de entrada:", direction)
            check, id = API.buy(amount, asset_name, direction, expiration_time)
            print(Fore.CYAN +"Operación realizada con id:", id)
            
            print(Style.RESET_ALL)    
        check, id = API.buy(amount, asset_name, 'put', expiration_time)
        # Esperar a que finalice la operación
        if 'id' in locals():
                status, result = API.check_win(id)
                if status:
                    print('Operación finalizada con resultado:', result)
                    break
                time.sleep(1)


API.disconnect()

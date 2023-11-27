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


while True:
    hora_actual = datetime.datetime.now()
    #print(hora_actual.second)
    if hora_actual.second == 49:
        print("obteniendo velas")

        # Obtener las velas más recientes
        candles = API.get_candles(goal, int(timeframe), 75, time.time())
        if candles is None:
            continue
        df = pd.DataFrame(candles)
        df.set_index('from', inplace=True)
        df.index = pd.to_datetime(df.index, unit='s')
    

        # Obtener los precios de cierre de las velas más recientes
        close_prices = df['close'].astype(float)
        open_prices = df['open'].astype(float)
        #validar estrategia en tiempo real


        print('seg: ',hora_actual.second)
    if hora_actual.second == 55:
       
        #verificar si se hace operacion segun la estrategia aqui


        # Esperar a que finalice la operación
        if 'id' in locals():
            while True:
                status, result = API.check_win_v3(id)
                if status:
                    print('Operación finalizada con resultado:', result)
                    break
                time.sleep(1)


API.disconnect()
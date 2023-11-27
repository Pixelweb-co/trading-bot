import time
from iqoptionapi.stable_api import IQ_Option
import datetime
import pandas as pd
from colorama import init, Fore, Style
import talib

# Inicializar colorama
init()

API=IQ_Option("egbmaster2007@gmail.com","16287318ed")
API.connect()# Conectarse a IQ Option
goal="EURUSD"
balance_type="PRACTICE"
API.change_balance(balance_type)

# Configurar los parámetros de la estrategia
asset_name = 'EURUSD-OTC'
timeframe = '60'
amount = 10
direction = ''
expiration_time = 2

while True:
    hora_actual = datetime.datetime.now()
    if hora_actual.second == 49:
        print("Obteniendo velas")

        # Obtener las velas más recientes
        candles = API.get_candles(goal, int(timeframe), 10, time.time())
        if candles is None:
            continue
        df = pd.DataFrame(candles)
        
        df.set_index('from', inplace=True)
        df.index = pd.to_datetime(df.index, unit='s')

        # Obtener los precios de cierre de las velas más recientes
        close_prices = df['close'].astype(float)

        # Calcular los indicadores necesarios
        df['hammer'] = talib.CDLHAMMER(df['open'], df['max'], df['min'], df['close'])
        df['morning_star'] = talib.CDLMORNINGSTAR(df['open'], df['max'], df['min'], df['close'])
        df['evening_star'] = talib.CDLEVENINGSTAR(df['open'], df['max'], df['min'], df['close'])
        # Calcular las Bandas de Bollinger
        upper_band, middle_band, lower_band = talib.BBANDS(
            close_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )

        # Buscar patrones de martillo
        last_candle = df.iloc[-1]
        
        # Obtener el precio de cierre de la última vela
        last_close_price = close_prices[-1]
        
        if last_candle['hammer'] > 0:
            
            print(Fore.GREEN + 'Se encontró un patrón de vela martillo' + Style.RESET_ALL)
            # Aquí puedes agregar la lógica para realizar una operación basada en el patrón de martillo
        elif last_candle['morning_star'] > 0:
            print(df)
            print(Fore.GREEN + 'Se encontró un patrón de Estrella de la Mañana' + Style.RESET_ALL)
            # Aquí puedes agregar la lógica para realizar una operación basada en el patrón de Estrella de la Mañana
            result, id = API.buy(amount, asset_name, 'call', expiration_time)
            print('Operación de compra abierta con ID:', id)
            trade = True

        elif last_candle['evening_star'] > 0:
            print(df)
            print(Fore.GREEN + 'Se encontró un patrón de Estrella de la Tarde' + Style.RESET_ALL)
            # Aquí puedes agregar la lógica para realizar una operación basada en el patrón de Estrella de la Tarde
            result, id = API.buy(amount, asset_name, 'put', expiration_time)
            print('Operación de compra abierta con ID:', id)
            trade = True

                # Estrategia de Bandas de Bollinger
        if last_close_price > upper_band:
            print(df)
            print(Fore.GREEN + 'Precio por encima de la Banda Superior de Bollinger. Realizar operación de venta' + Style.RESET_ALL)
            # Aquí puedes agregar la lógica para realizar una operación de venta basada en la estrategia de Bandas de Bollinger
            result, id = API.buy(amount, asset_name, 'put', expiration_time)
            print('Operación de venta abierta con ID:', id)
        elif last_close_price < lower_band:
            print(df)
            print(Fore.GREEN + 'Precio por debajo de la Banda Inferior de Bollinger. Realizar operación de compra' + Style.RESET_ALL)
            # Aquí puedes agregar la lógica para realizar una operación de compra basada en la estrategia de Bandas de Bollinger
            result, id = API.buy(amount, asset_name, 'call', expiration_time)
            print('Operación de compra abierta con ID:', id)
        
        print('seg:', hora_actual.second)
        
    if hora_actual.second == 55:
        # Verificar si se hace operación según la estrategia aquí
        pass

    # Esperar a que finalice la operación
    if 'id' in locals():
        while True:
            status, result = API.check_win_v3(id)
            if status:
                print('Operación finalizada con resultado:', result)
                break
            time.sleep(1)

API.disconnect()

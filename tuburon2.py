import time
from iqoptionapi.stable_api import IQ_Option
import numpy as np
import talib
import datetime
import pandas as pd
from colorama import init, Fore, Style
from scipy.signal import argrelextrema

# Inicializar colorama
init()

API = IQ_Option("xxxxxx@gmail.com", "xxxxxx")
API.connect()  # Conectarse a IQ Option
goal = "EURUSD-OTC"
balance_type = "PRACTICE"
API.change_balance(balance_type)

# Configurar los parámetros de la estrategia
asset_name = goal
timeframe = '60'
amount = 10
direction = ''
expiration_time = 4


def calculate_indicators(candles):
    # Calcular indicadores
    close_prices = candles['close'].astype(float)

    # Calcular ZigZag
    zigzag = argrelextrema(close_prices.values, np.greater)[0]

    # Calcular medias móviles
    sma20 = talib.SMA(close_prices, timeperiod=20)
    sma50 = talib.SMA(close_prices, timeperiod=50)

    # Calcular RSI
    rsi = talib.RSI(close_prices, timeperiod=14)

    # Calcular bandas de Bollinger
    upper_band, middle_band, lower_band = talib.BBANDS(close_prices, timeperiod=20, nbdevup=2, nbdevdn=2)

    # Calcular MACD
    macd, macd_signal, _ = talib.MACD(close_prices)

    return zigzag, sma20, sma50, rsi, upper_band, middle_band, lower_band, macd, macd_signal


def print_indicator_values(zigzag, sma20, sma50, rsi, upper_band, middle_band, lower_band, macd, macd_signal):
    print(f"{Fore.CYAN}Indicador ZigZag: {zigzag}")
    print(f"{Fore.GREEN}Dirección: {Fore.YELLOW}{zigzag[-1] > zigzag[-2]}")
    print(f"{Fore.GREEN}Media Móvil 20 períodos: {sma20}")
    print(f"{Fore.GREEN}Dirección: {Fore.YELLOW}{sma20.iloc[-1] > sma20.iloc[-2]}")
    print(f"{Fore.YELLOW}Media Móvil 50 períodos: {sma50}")
    print(f"{Fore.GREEN}Dirección: {Fore.YELLOW}{sma50.iloc[-1] > sma50.iloc[-2]}")
    print(f"{Fore.MAGENTA}RSI: {rsi}")
    print(f"{Fore.GREEN}Dirección: {Fore.YELLOW}{rsi[-1] > rsi[-2]}")
    print(f"{Fore.BLUE}Banda de Bollinger Superior: {upper_band}")
    print(f"{Fore.GREEN}Dirección: {Fore.YELLOW}{df['close'].iloc[-1] > upper_band.iloc[-1]}")
    print(f"{Fore.RED}Banda de Bollinger Media: {middle_band}")
    print(f"{Fore.GREEN}Dirección: {Fore.YELLOW}{df['close'].iloc[-1] > middle_band.iloc[-1]}")
    print(f"{Fore.YELLOW}Banda de Bollinger Inferior: {lower_band}")
    print(f"{Fore.GREEN}Dirección: {Fore.YELLOW}{df['close'].iloc[-1] > lower_band.iloc[-1]}")
    print(f"{Fore.CYAN}MACD: {macd}")
    print(f"{Fore.GREEN}Dirección: {Fore.YELLOW}{macd[-1] > macd_signal[-1]}")
    print(Style.RESET_ALL)


def detect_reversals(zigzag, sma20, sma50, rsi, upper_band, middle_band, lower_band, macd, macd_signal):
    if (
        zigzag[-1] > zigzag[-2] and
        sma20.iloc[-1] > sma20.iloc[-2] and
        sma50.iloc[-1] > sma50.iloc[-2] and
        rsi[-1] > rsi[-2] and
        df['close'].iloc[-1] > upper_band.iloc[-1] and
        macd[-1] > macd_signal[-1]
    ):
        return 'call'
    elif (
        zigzag[-1] < zigzag[-2] and
        sma20.iloc[-1] < sma20.iloc[-2] and
        sma50.iloc[-1] < sma50.iloc[-2] and
        rsi[-1] < rsi[-2] and
        df['close'].iloc[-1] < lower_band.iloc[-1] and
        macd[-1] < macd_signal[-1]
    ):
        return 'put'
    else:
        return ''


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

        # Calcular indicadores
        zigzag, sma20, sma50, rsi, upper_band, middle_band, lower_band, macd, macd_signal = calculate_indicators(df)

        # Mostrar valores de los indicadores y su dirección
        print_indicator_values(zigzag, sma20, sma50, rsi, upper_band, middle_band, lower_band, macd, macd_signal)

        # Detectar retrocesos según la estrategia
        direction = detect_reversals(zigzag, sma20, sma50, rsi, upper_band, middle_band, lower_band, macd, macd_signal)

        print('Seg:', hora_actual.second)

    if hora_actual.second == 55:
        # Verificar si se debe realizar una operación según la estrategia
        if direction != '':
            print('Realizar operación:', direction)

            # Realizar la operación
            id = API.buy(amount, asset_name, direction, expiration_time)
            print('Operación enviada:', id)

        # Esperar a que finalice la operación
        if 'id' in locals():
            while True:
                status, result = API.check_win_v3(id)
                if status:
                    print('Operación finalizada con resultado:', result)
                    break
                time.sleep(1)

API.disconnect()

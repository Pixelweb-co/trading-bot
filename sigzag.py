import time
from iqoptionapi.stable_api import IQ_Option
import numpy as np
import datetime
import pandas as pd
from colorama import init, Fore, Style
import talib
import os
import platform
import logging
#logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(message)s')
#import speech_recognition as sr
#import requests
#import pyttsx3
import pymongo
# Establecer conexión con la base de datos
client = pymongo.MongoClient('mongodb://admin:Nosotros123@localhost:27017/')
db = client['tradingbot']
collection = db['operaciones']


# Comprobar si la colección ya existe
if 'operaciones' not in db.list_collection_names():
    # Crear la colección
    db.create_collection('operaciones')
    print('La colección "operaciones" ha sido creada.')

# Crear el índice único para el campo 'id' en la colección 'operaciones'
collection.create_index('id', unique=True)

# Definir el modelo de operación
operacion_modelo = {
    'id': {'type': int, 'unique': True},
    'direction': str,
    'timestamp': float,
    'stochastic': float,
    'close_price': float,
    'result': str,
    'zigzag': float,
    'MA_FAST': float,
    'MA_SLOW': float,
    'aroon_up': float,
    'aroon_down': float,
    'upper_band': float,
    'lower_band': float,
    'RSI': float,
    'amount': float
}


# Inicializar colorama

init()

API = IQ_Option("xxxxxx@gmail.com", "xxxxxx")
API.connect()  # Conectar a IQ Option
goal = "EURUSD-OTC"
balance_type = "PRACTICE" # REAL / PRACTICE
API.change_balance(balance_type)

profit=API.get_all_profit()
# Configurar los parámetros de la estrategia
asset_name =  goal
timeframe = '60'
amount = 1
direction = ''
expiration_time = 2
trade = False
showResume = True
bet_money = amount #QUANTITY YOU WANT TO BET EACH TIME

total_ganado = 0
total_perdido = 0

martingale = 2
nro_martingale = 2
actual_martingale = 0

bid = True
bets = []
# Lista para almacenar las operaciones realizadas
operaciones_realizadas = []

# Configuración de la biblioteca de síntesis de voz
#engine = pyttsx3.init()

#def speak(text):
#    engine.say(text)
#    engine.runAndWait()

def limpiar_consola():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def obtener_operaciones():
    
            betsies = API.get_optioninfo_v2(2)
            print(betsies)
            betsies = betsies['msg']['closed_options']
                
            for bt in betsies:
                print("operacion")
                bets.append(bt['win'])
                win = bets[-1:]
                print(win)

valor_total_ganado = 0
valor_total_perdido = 0
amount_init = 10

valor_cuenta = API.get_balance()


def header():
    limpiar_consola()
    print(Fore.BLUE + (f'| Robot trading v1 | Valor en cuenta: $ {str(valor_cuenta)} | Beneficio : {profit["CADCHF"]["turbo"]} | Operaciones ganadas: {str(total_ganado)} | Operaciones perdidas: {str(total_perdido)} | Valor operacion actual : $ {str(amount)} | Divisas: {asset_name}') + Style.RESET_ALL)
    print("\n")
    print(Fore.YELLOW + (f'| Valor inversion asignado : $ {amount_init} | Ganancias : $ {str(valor_total_ganado)} | Perdidas: $ {str(valor_total_perdido)} | Saldo: {str(valor_total_ganado - valor_total_perdido)}') + Style.RESET_ALL)
    print("\n")
    

def calcular_pivot_points(high_prices, low_prices, close_prices):
    pivots = {}
    pivots['R2'] = max(high_prices[-3:]) 
    pivots['R1'] = ((2 * close_prices[-1]) - low_prices[-1]) 
    pivots['P'] = ((high_prices[-1] + low_prices[-1] + close_prices[-1]) / 3) 
    pivots['S1'] = ((2 * close_prices[-1]) - high_prices[-1]) 
    pivots['S2'] = min(low_prices[-3:]) 
    return pivots

def calcular_niveles_fibonacci(high_prices, low_prices):
    niveles = {}
    rango = max(high_prices) - min(low_prices)
    niveles['0%'] = max(high_prices)
    niveles['23.6%'] = max(high_prices) - 0.236 * rango
    niveles['38.2%'] = max(high_prices) - 0.382 * rango
    niveles['50%'] = max(high_prices) - 0.5 * rango
    niveles['61.8%'] = max(high_prices) - 0.618 * rango
    niveles['100%'] = min(low_prices)
    return niveles


def calcular_soporte_resistencia_cercano(high_prices, low_prices, close_prices):
    niveles_fibonacci = calcular_niveles_fibonacci(high_prices, low_prices)
    puntos_pivot = calcular_pivot_points(high_prices, low_prices, close_prices)
    ultimo_precio_cierre = close_prices[-1]

    cercania = {}

    # Buscar el nivel de Fibonacci más cercano
    niveles = list(niveles_fibonacci.keys())
    for i in range(len(niveles)):
        nivel = niveles[i]
        if ultimo_precio_cierre >= niveles_fibonacci[nivel]:
            cercania['Nivel Fibonacci'] = nivel
            break

    # Buscar el punto pivot (soporte o resistencia) más cercano
    puntos = list(puntos_pivot.keys())
    for i in range(len(puntos)):
        punto = puntos[i]
        if ultimo_precio_cierre >= puntos_pivot[punto]:
            cercania['Punto Pivot'] = punto
            break

    return cercania


def zigzag(data, percentage=1):
    reference = np.full_like(data['max'], np.nan)
    reference[0] = data['max'][0]

    is_direction_up = np.full_like(data['max'], True)
    htrack = np.full_like(data['max'], np.nan)
    ltrack = np.full_like(data['max'], np.nan)

    reverse_range = reference * (percentage / 100)

    for i in range(1, len(data)):
        if is_direction_up[i]:
            htrack[i] = max(data['max'][i], htrack[i-1])
            if data['close'][i] < (htrack[i-1] - reverse_range[i-1]):
                is_direction_up[i] = False
                reference[i] = htrack[i]
                # Verificar si alcanzó el máximo y comenzó a bajar
                if data['close'][i] == htrack[i]:
                    return -1
        else:
            ltrack[i] = min(data['min'][i], ltrack[i-1])
            if data['close'][i] > (ltrack[i-1] + reverse_range[i-1]):
                is_direction_up[i] = True
                reference[i] = ltrack[i]
                # Verificar si alcanzó el mínimo y comenzó a subir
                if data['close'][i] == ltrack[i]:
                    return 1

    return 0




def detectar_tope(candles):
    highs = candles['max'].astype(float)
    lows = candles['min'].astype(float)
    close_prices = candles['close'].astype(float)

    # Algoritmo personalizado para detectar topos en base a los precios de cierre
    zigzag = []
    up = True  # Indicador de dirección ascendente
    last_zigzag = None

    for i in range(len(close_prices)):
        if i == 0:
            zigzag.append(close_prices[i])
        else:
            if up:
                if close_prices[i] > highs[i - 1]:
                    zigzag.append(close_prices[i])
                    last_zigzag = 1
                    up = False
                else:
                    if close_prices[i] < lows[i - 1]:
                        zigzag.append(close_prices[i])
                        last_zigzag = -1
            else:
                if close_prices[i] < lows[i - 1]:
                    zigzag.append(close_prices[i])
                    last_zigzag = -1
                    up = True
                else:
                    if close_prices[i] > highs[i - 1]:
                        zigzag.append(close_prices[i])
                        last_zigzag = 1

    return last_zigzag


def calcular_estocastico(high_prices, low_prices, close_prices, fastk_period=14, slowk_period=3, slowd_period=3):
    # Calcular el máximo y mínimo de los últimos fastk_period períodos
    max_high = max(high_prices[-fastk_period:])
    min_low = min(low_prices[-fastk_period:])
    
    # Calcular los valores del estocástico K para cada período
    k_values = [(close - min_low) / (max_high - min_low) for close in close_prices[-fastk_period:]]
    
    # Calcular el promedio móvil simple de slowk_period períodos del estocástico K para obtener el estocástico D
    d_values = sum(k_values[-slowk_period:]) / slowk_period
    
    return k_values, d_values

id = 0
estrategia = 'none'

header()
while True:
    hora_actual = datetime.datetime.now()

    if hora_actual.hour >= 15 and hora_actual.minute == 5 or hora_actual.hour <= 19 and hora_actual.minute == 5:
        goal = "EURUSD-OTC"
    
    if hora_actual.hour >= 15 and hora_actual.minute == 5 or hora_actual.hour <= 19 and hora_actual.minute == 5:
        goal = "EURUSD"

    if hora_actual.second == 50 or hora_actual.second == 28:
        #print(f'reset {hora_actual.second} activo: {goal} hora: {hora_actual.hour} minuto: {hora_actual.minute}')
        trade = False
        showResume = True
    
    
    if  hora_actual.second == 59 and showResume == True:
        header() 
        showResume = False
        print(Fore.BLUE + "Obteniendo velas \n ______________________________________" + Style.RESET_ALL)

        # Obtener las velas más recientes
        candles = API.get_candles(goal, int(timeframe), 100, time.time())
        if candles is None:
            continue
        df = pd.DataFrame(candles)
        df.set_index('from', inplace=True)
        df.index = pd.to_datetime(df.index, unit='s')

        # Calcular los indicadores
        close_prices = round(df['close'].astype(float), 6)
        high_prices = df['max'].astype(float)
        low_prices = df['min'].astype(float)

        # Indicador Estocástico
        stoch_signal = talib.STOCH(high_prices, low_prices, close_prices, fastk_period=19)[1]
        
        k, d = calcular_estocastico(high_prices, low_prices, close_prices)
        print("Estocástico K:", str(k[-1]))
        print("Estocástico D:", d)

        # Calcular los niveles de Fibonacci
        levels_fibonacci = calcular_niveles_fibonacci(df['max'].astype(float), df['min'].astype(float))


        # Encontrar en qué rango Fibonacci se encuentra el último precio de cierre
        for nivel, valor in levels_fibonacci.items():
            if close_prices[-1] >= valor:
                rango = nivel
                break

        print("El último precio de cierre se encuentra en el rango Fibonacci:", rango)

        # Calcular el indicador Average True Range (ATR)
        atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)

        # Media Móvil Exponencial (EMA)
        ema_5 = talib.EMA(close_prices, timeperiod=5)
        ema_20 = talib.EMA(close_prices, timeperiod=50)

        ma2 = talib.MA(close_prices, timeperiod=2)
        ma5 = talib.MA(close_prices, timeperiod=5)

        # Obtener los dos últimos valores de cada media móvil
        last_ma2_values = ma2[-2:]
        last_ma5_values = ma5[-2:]

        # Calcular la diferencia porcentual entre los dos últimos valores de cada media móvil
        percentage_difference = abs((last_ma2_values[1] - last_ma5_values[1]) / last_ma5_values[1]) * 100

        # Imprimir el resultado
        print("La cercanía de la media móvil de 2 períodos a la media móvil de 5 períodos es del", percentage_difference, "%")

        # Imprimir el resultado de la cercanía
        print("La cercanía de la media móvil de 2 períodos a la media móvil de 5 períodos es del", percentage_difference, "%")

        # Verificar si las medias móviles se cruzaron
        if last_ma2_values[0] < last_ma5_values[0] and last_ma2_values[1] > last_ma5_values[1]:
            print("Las medias móviles se cruzaron: MA2 ha cruzado por encima de MA5")
            print("Cambio a tendencia alcista")
        elif last_ma2_values[0] > last_ma5_values[0] and last_ma2_values[1] < last_ma5_values[1]:
            print("Las medias móviles se cruzaron: MA2 ha cruzado por debajo de MA5")
            print("Cambio a tendencia bajista")
        else:
            print("No ha ocurrido un cruce de medias móviles")



        # Indicador Aroon
        aroon_up, aroon_down = talib.AROON(high_prices, low_prices, timeperiod=14)

        # RSI de 6 períodos
        rsi_6 = talib.RSI(close_prices, timeperiod=14)

        # Detectar tope con el indicador ZigZag personalizado
        tope = detectar_tope(df)
        #tope = zigzag(df)
        # Realizar la comprobación de ruptura de resistencia o soporte
        pivot_points = calcular_pivot_points(high_prices, low_prices, close_prices)
        upper_band, middle_band, lower_band = talib.BBANDS(close_prices, timeperiod=30)

        
        # Imprimir el último precio de cierre
        last_close_price = close_prices.iloc[-1]
        print(Fore.YELLOW + 'Último precio de cierre: ' + str(last_close_price) + Style.RESET_ALL)
        
        print(Fore.YELLOW + 'Precio cierre anterior: '+str(round(df['close'][-2].astype(float), 6)) + Style.RESET_ALL)
        

        # Calcular la volatilidad promedio
        average_volatility = atr.mean()

        # Comparar la volatilidad promedio con los umbrales para determinar el estado de la volatilidad
        low_threshold = average_volatility * 0.5
        high_threshold = average_volatility * 1.5

        if atr[-1] < low_threshold:
            print("Baja volatilidad")
        elif atr[-1] > high_threshold:
            print("Alta volatilidad")
        else:
            print("Volatilidad normal")

        volume = df['volume'].astype(float)

        # Calcular el promedio de volumen
        average_volume = volume.mean()

        # Comparar el volumen actual con el promedio para determinar su estado
        low_threshold = average_volume * 0.5
        high_threshold = average_volume * 1.5

        if volume[-1] < low_threshold:
            print("Bajo volumen")
        elif volume[-1] > high_threshold:
            print("Alto volumen")
        else:
            print("Volumen normal")


        cercania = calcular_soporte_resistencia_cercano(high_prices, low_prices, close_prices)
        print("cercania a soporte resistencia fb ",cercania)


        #reistencias y soportes
        print('Resistencia: ',pivot_points['R2'])
        print('Soporte: ',pivot_points['S2'])

        print('UpperBand : ',(round(upper_band[-1],6)) - 0.000116)
        print('LowerBand: ',(round(lower_band[-1],6)) - 0.000052)



        # Imprimir los valores de los indicadores
        print('Estocástico:', int(stoch_signal[-1]))
        print('EMA de 5 períodos:', ema_5[-1])
        print('EMA de 20 períodos:', ema_20[-1])
        print('Aroon Up:', aroon_up[-1])
        print('Aroon Down:', aroon_down[-1])
        print('ZigZag:', tope)
        print('RSI',rsi_6[-1])

         # Mostrar los niveles de Fibonacci
        print('Niveles de Fibonacci:')
        for nivel, valor in levels_fibonacci.items():
            print(f'{nivel}: {valor}')

        #bollinger up rota
        if close_prices.iloc[-2] > (round(upper_band[-2],6)) - 0.000116:
            print(Fore.MAGENTA +'Precio anterior ha roto bolinger up '+ Style.RESET_ALL)
        if close_prices.iloc[-2] < (round(lower_band[-2],6)) - 0.000052:
            print(Fore.MAGENTA +'Precio anterior ha roto bolinger down '+ Style.RESET_ALL)
        # direccion RSI
        if rsi_6[-1] > rsi_6[-2]:
            print(Fore.GREEN +'Rsi subiendo'+ Style.RESET_ALL)
        else:
            print(Fore.RED +'Rsi bajando'+ Style.RESET_ALL)

        # direccion RSI
        if stoch_signal[-1] > stoch_signal[-2]:
            print(Fore.GREEN +'Stocastico subiendo'+ Style.RESET_ALL)
        else:
            print(Fore.RED +'Stocastico bajando'+ Style.RESET_ALL)
        
        # direccion aroon
        if aroon_down[-1] > aroon_up[-1]:
            print(Fore.GREEN +'Las fuerza es alcista'+ Style.RESET_ALL)
        else:
            print(Fore.RED +'Las fuerza es bajista'+ Style.RESET_ALL)


        # Indicar si el precio está subiendo o bajando según las medias móviles
        if ema_5[-1] > ema_20[-1]:
            print(Fore.GREEN +'Las medias móviles indican que el precio está subiendo'+ Style.RESET_ALL)
        else:
            print(Fore.RED +'Las medias móviles indican que el precio está bajando'+ Style.RESET_ALL)

        # Comprobar el cruce de medias móviles
        if ema_5[-2] < ema_20[-2] and ema_5[-1] > ema_20[-1] and aroon_down[-1] < aroon_up[-1] and aroon_up[-1] > 70:
            print(Fore.YELLOW +'¡Se produjo un cruce alcista de medias móviles!'+ Style.RESET_ALL)
            #speak('¡Se produjo un cruce alcista de medias móviles!')
            if not trade:
                direction = 'call'
                estrategia = 'cruceMedias'
                id = API.buy(amount, asset_name, direction, expiration_time)
                
                if direction == 'put':
                        print(Fore.RED + 'Operación de venta realizada '+str(hora_actual.second)+ Style.RESET_ALL)
                else:
                        print(Fore.GREEN +'Operación de compra realizada'+str(hora_actual.second)+ Style.RESET_ALL)

                trade = True

        elif ema_5[-2] > ema_20[-2] and ema_5[-1] < ema_20[-1] and aroon_down[-1] > aroon_up[-1] and aroon_up[-1] < 30:
                print(Fore.BLUE +'¡Se produjo un cruce bajista de medias móviles!'+ Style.RESET_ALL)
                #speak('¡Se produjo un cruce bajista de medias móviles!')
                direction = 'put'
                estrategia = 'cruceMedias'
                id = API.buy(amount, asset_name, direction, expiration_time)
                
                if direction == 'put':
                        print(Fore.RED + 'Operación de venta realizada '+str(hora_actual.second)+ Style.RESET_ALL)
                else:
                        print(Fore.GREEN +'Operación de compra realizada'+str(hora_actual.second)+ Style.RESET_ALL)

                trade = True

        
        # Validar la estrategia en tiempo real y determinar la dirección de la operación
        if tope is not None:
           
            # Confirmar la estrategia con los indicadores
            if  tope == -1 and rsi_6[-1] > rsi_6[-2]  and stoch_signal[-1] > stoch_signal[-2]:  
                print(Fore.LIGHTMAGENTA_EX +"Extrategia zigzag vende"+ Style.RESET_ALL)  

            if tope == 1 and rsi_6[-1] < rsi_6[-2]  and stoch_signal[-1] < stoch_signal[-2]:  
                print(Fore.LIGHTMAGENTA_EX +"Extrategia zigzag compra"+ Style.RESET_ALL)  

            
            if tope == -1 and rsi_6[-1] > rsi_6[-2] and stoch_signal[-1] > stoch_signal[-2]:
                print(Fore.LIGHTMAGENTA_EX + 'venta'+ Style.RESET_ALL)
                # Hacer operación de venta o compra durante 4 minutos
                direction = 'put'  # Dirección de la operación de venta
                estrategia = 'zigzag'
                
                if not trade:
                    #speak('¡Operacion creada por estrategia de zigzag !')
                    id = API.buy(amount, asset_name, direction, expiration_time)
                    

                    if direction == 'put':
                        print(Fore.RED + 'Operación de venta realizada '+str(hora_actual.second)+ Style.RESET_ALL)
                    else:
                        print(Fore.GREEN +'Operación de compra realizada'+str(hora_actual.second)+ Style.RESET_ALL)

                    trade = True
                    time.sleep(5)

            if tope == 1 and rsi_6[-1] < rsi_6[-2] and stoch_signal[-1] < stoch_signal[-2]:
                print(Fore.LIGHTMAGENTA_EX + 'compra'+ Style.RESET_ALL)
                # Hacer operación de venta o compra durante 4 minutos
                direction = 'call'  # Dirección de la operación de venta
                estrategia = 'zigzag'
                if not trade:
                    #speak('¡Operacion creada por estrategia de zigzag !')
                    id = API.buy(amount, asset_name, direction, expiration_time)
                    

                    if direction == 'put':
                        print(Fore.RED + 'Operación de venta realizada '+str(hora_actual.second)+ Style.RESET_ALL)
                    else:
                        print(Fore.GREEN +'Operación de compra realizada'+str(hora_actual.second)+ Style.RESET_ALL)

                    trade = True
                    time.sleep(5)

        
        # # Mostrar las últimas 10 operaciones realizadas
        # if hora_actual.second == 20:
        #     print('Últimas 10 operaciones realizadas:')
        #     for operacion in operaciones_realizadas[-10:]:
        #         print('Dirección:', operacion['direction'])
        #         print('Timestamp:', operacion['timestamp'])
        #         print('Estocástico:', operacion['stochastic'])
        #         print('Precio de cierre:', operacion['close_price'])
        #         print('Resultado:', operacion['result'])
        #         print('-------------------')

        
            if (
                tope == 1 and close_prices[-1] > pivot_points['R1'] and close_prices[-1] > levels_fibonacci['61.8%'] and stoch_signal[-1] > stoch_signal[-2] and stoch_signal[-1] < 20
            ):
                print(Fore.GREEN + 'Ruptura de resistencia detectada compra' + Style.RESET_ALL)
                # Realizar operación de compra
                direction = 'call'
                estrategia = 'pivot'
                id = API.buy(amount, asset_name, direction, expiration_time)
                
                trade = True

            elif (
                tope == -1 and close_prices[-1] > pivot_points['S1'] and close_prices[-1] < levels_fibonacci['38.2%'] and stoch_signal[-1] < stoch_signal[-2] and stoch_signal[-1] > 80
            ):
                strpv = str(pivot_points['S2'])
                print(f'cp: {str(close_prices[-1])} s2: {strpv} blw: {str((round(lower_band[-1],6)) - 0.000052)}')
                print(Fore.CYAN + 'Ruptura de soporte detectada venta' + Style.RESET_ALL)
                # Realizar operación de venta
                direction = 'put'
                estrategia = 'pivot'
                id = API.buy(amount, asset_name, direction, expiration_time)
                
                trade = True


            if(trade == True):
                operacion = {
                        'id':str(id[1]),
                        'direction': direction,
                        'estrategia':estrategia,
                        'result': '',
                        'timestamp': time.time(),
                        'stochastic': stoch_signal[-1],
                        'close_price': last_close_price,
                        'winmoney':0,
                        'zigzag':tope,
                        'MA_FAST':ema_5[-1],
                        'MA_SLOW':ema_20[-1],
                        'aroon_up': aroon_up[-1],
                        'aroon_down': aroon_down[-1],
                        'upper_band':(round(upper_band[-1],6)) - 0.000116,
                        'lower_band':(round(lower_band[-1],6)) - 0.000052,
                        'RSI':rsi_6[-1],
                        'amount':amount
                    }
                
                
                time.sleep(20)
                tempo = datetime.datetime.now().second
                i=0
                
                print("operacion en curso ",operacion)
                while(tempo != 1): #wait till 1 to see if win or lose
                    tempo = datetime.datetime.now().second    
                    header()
                    print(operacion)
                    print("Esperando operacion...",abs(tempo - 60))
                        
                    if i < expiration_time -1  and tempo == 59 :
                        time.sleep(2)
                        i = i + 1
                        print(". ",i)
                        
                    else:
                        tempo = datetime.datetime.now().second    
                    time.sleep(1)    
                
                header()        
                print("Resultado operacion id: ",id)
                amount_result = 0
                betsies = API.get_optioninfo_v2(2)
                betsies = betsies['msg']['closed_options']
                bets = []

                for bt in betsies:
                    bets.append(bt)

                win = bets[0]['win']

                if win == 'win':
                    #print(bets[0]['win_amount'])
                    amount_result = (float(bets[0]['win_amount']) - amount)
                    print("ganado : ",amount_result)
                    #speak(f'ganado {amount_result} dolares')
                    operacion['winmoney'] = amount_result
                    valor_total_ganado = round(valor_total_ganado + amount_result,2)
                    

                    if total_ganado > amount_init  :
                        print("aumento de la inversion a 2")
                        amount = amount * 2
                    else:
                        amount = 1


                elif win == 'loose':
                    amount_result = amount_result - amount
                    print("perdido : ",amount_result)                
                    #speak(f'perdido {amount_result} dolares')

                    valor_total_perdido = valor_total_perdido + amount

                
                #print(win)
                if win == 'win':
                    #print(f'Balance : {get_balance(iq)}')
                    
                    total_ganado = total_ganado + 1

                elif win == 'loose':
                    
                    #print(f'Balance : {get_balance(iq)}')
                    if  actual_martingale < nro_martingale:
                        print("aplica martingala la siguiente operacion para recuperar esta")
                        amount = amount * martingale # martingale V3
                        actual_martingale = actual_martingale + 1
                    else:
                        amount = bet_money
                        actual_martingale = 0
                    total_perdido = total_perdido + 1    

                else:
                    #print(f'Balance : {get_balance(iq)}')
                    bets.append(0)
                    print("valor inversion ",amount)
                operacion['result'] = win
                
                print(operacion)
                collection.insert_one(operacion)
                operaciones_realizadas.append(operacion)
                
                trade = False    
            
                
                print(f'Total ganado: $ {valor_total_ganado}')
                print(f'Total perdido: $ {valor_total_perdido}')
                
            else:
                print("\n Buscando estrategias... \n")
            
            print("Esperando siguiente vela en: ", str(datetime.datetime.now().second )+' Segundos...')

API.disconnect()

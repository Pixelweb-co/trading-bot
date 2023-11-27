import time
import pandas as pd
import plotly.graph_objects as go
from iqoptionapi.stable_api import IQ_Option
from flask import Flask, render_template

app = Flask(__name__)

API = IQ_Option("egbmaster2007@gmail.com", "16287318ed")
API.connect()

goal = "EURUSD-OTC"
timeframe = '1m'

@app.route('/')
def index():
    return render_template('candles.html')

@app.route('/candles')
def get_candles():
    candles = API.get_candles(goal, int(timeframe), 1000, time.time())
    df = pd.DataFrame(candles)
    df.set_index('from', inplace=True)
    df.index = pd.to_datetime(df.index, unit='s')
    df['mid'] = (df['close'] + df['open']) / 2
    
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['max'],
        low=df['min'],
        close=df['close']
    )])
    
    fig.update_layout(title='Gráfico de Velas Japonesas', yaxis_title='Precio')
    
    return fig.to_html(full_html=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

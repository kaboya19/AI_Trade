# %%
import pandas as pd
import numpy as np
import catboost
from catboost import CatBoostRegressor

from datetime import datetime

import pandas as pd, numpy as np

import yfinance as yf

# %%
son=pd.read_excel("FiyatPenceresi.Xlsx")
endeks=son.iloc[-1,:]
son=son.iloc[:-1,:]
hisseler=son["Kod"].values
hisseler=np.array(hisseler)
for i in range(len(hisseler)):
    hisseler[i]=hisseler[i]+".IS"

# %%
df=pd.DataFrame()
for hisse in hisseler:
    hisse_verileri = yf.download(hisse,start="2010-01-01")  # Örnek tarih aralığı
    hisse_kapanis = hisse_verileri[['High','Low','Open','Close','Volume']]
    hisse_kapanis["Hisse"]=hisse
    hisse_kapanis.loc[hisse_kapanis["Close"] > hisse_kapanis["High"], "High"] = hisse_kapanis["Close"]
    hisse_kapanis.loc[hisse_kapanis["Close"] < hisse_kapanis["Low"], "Low"] = hisse_kapanis["Close"]

    df=pd.concat([df,hisse_kapanis],axis=0)
df

# %%
df["Volume"]=df["Volume"]*df["Close"]

# %%
data=df.copy()

# %%
df["Close"]=np.round(df["Close"],2)
df["High"]=np.round(df["High"],2)
df["Low"]=np.round(df["Low"],2)
df["Open"]=np.round(df["Open"],2)

# %%
df.columns=['High', 'Low', 'Open', 'Adj Close', 'Volume', 'Hisse']

# %%
df["Kademe"] = np.where(df["Adj Close"] < 20, 0.01,
                np.where(df["Adj Close"] < 50, 0.02,
                    np.where(df["Adj Close"] < 100, 0.05,
                        np.where(df["Adj Close"] < 250, 0.1,
                            np.where(df["Adj Close"] < 500, 0.25,
                                np.where(df["Adj Close"] < 1000, 0.5,
                                    np.where(df["Adj Close"] < 2500, 1, 2.5)
                                )  # Buradaki parantez eksikti.
                            )
                        )
                    )
                )
            )


# %%
df["Tavan"]=((((df["Adj Close"].shift(1))*1.1)/df["Kademe"]).fillna(0).astype(int))*df["Kademe"]
df["Tavan"]=np.round(df["Tavan"],2)

# %%
df["Tavan Kontrol"]=np.where((df["Tavan"]==df["Adj Close"]),1,0)

# %%
import pandas_ta as ta

df["SMA 5"]=df["Adj Close"].rolling(5).mean()
df["SMA 10"]=df["Adj Close"].rolling(5).mean()
df["SMA 200"]=df["Adj Close"].rolling(5).mean()

# RSI
df["RSI"] = ta.rsi(df["Adj Close"],14)

# Bağıl Hacim
df["Bağıl Hacim"] = df["Volume"] / df["Volume"].rolling(10).mean()



# ADX, DMI, Aroon
adx_data = ta.adx(df["High"], df["Low"], df["Adj Close"], 14)
df["ADX"], df["DMIP"], df["DMIN"] = adx_data.iloc[:, 0], adx_data.iloc[:, 1], adx_data.iloc[:, 2]




def calculate_stoch_rsi(data, rsi_period=14, stochastic_period=14, k_period=3, d_period=3):
    rsi = ta.rsi(data["Adj Close"], rsi_period)
    stoch_rsi = (rsi - rsi.rolling(window=stochastic_period).min()) / (rsi.rolling(window=stochastic_period).max() - rsi.rolling(window=stochastic_period).min())
    stoch_rsi_k = stoch_rsi.rolling(window=k_period).mean() * 100
    stoch_rsi_d = stoch_rsi_k.rolling(window=d_period).mean()
    data['StochRSI_%K'] = stoch_rsi_k
    data['StochRSI_%D'] = stoch_rsi_d
    return data

df = calculate_stoch_rsi(df)


def calculate_macd(data, short_period=12, long_period=26, signal_period=9):
    data['EMA_12'] = ta.ema(data['Adj Close'], short_period)
    data['EMA_26'] = ta.ema(data['Adj Close'], long_period)
    data['MACD'] = data['EMA_12'] - data['EMA_26']
    data['Signal_Line'] = ta.ema(data['MACD'], signal_period)
    data['MACD_above_Signal'] = (data['MACD'] > data['Signal_Line']).astype(float)
    return data

df = calculate_macd(df)



# Diğer Göstergeler
df["DD"] = ((df["Adj Close"] / df["High"]) - 1) * 100
df["Range"] = ((df["High"] - df["Low"]) / df["Adj Close"]) * 100

df["MOM"] = ta.mom(df["Adj Close"], 10)



df["Driehaus Momentum"] = ((df["Bağıl Hacim"] > 2) & (df["RSI"] > 50) & (df["MOM"] > 1) & (df["Adj Close"] > df["SMA 5"]) & (df["Adj Close"] > df["SMA 10"]) & (df["Adj Close"] > df["SMA 200"])).astype(int)
df["MACD Yukarı Kesen"] = ((df["Bağıl Hacim"] > 1.5) & (df["MACD"] > 0) & (df["MACD_above_Signal"] == 1)).astype(int)
df["ADXDMI20"] = ((df["Bağıl Hacim"] > 1.3) & (df["ADX"] > 20) & (df["DMIP"] > df["DMIN"])).astype(int)
df["MACD+Stoch"] = ((df["Bağıl Hacim"] > 1.3) & (df["StochRSI_%K"] > df["StochRSI_%D"]) & (df["MACD_above_Signal"] == 1)).astype(int)




# %%
import pandas_ta as ta
import ta as ta1

df['MACD_Signal'] = df["Signal_Line"]
df['MACD_Diff'] = ta1.trend.macd_diff(df['Adj Close'])
df['ROC'] = ta.roc(df["Adj Close"],12)



# %%
df["Return"]=100*((df["Open"]/df["Adj Close"].shift(2))-1)
df["Return"]=df["Return"].shift(-2)
df["Date"]=pd.to_datetime(df.index)
df


# %%
endeks1=yf.download(tickers="XU100.IS",end="2020-07-27")/100
endeks2=yf.download(tickers="XU100.IS",start="2020-07-27")
endeks=pd.concat([endeks1,endeks2],axis=0)
df["Endeks"]=endeks["Adj Close"]
df["Endeks Return"]=100*((df["Endeks"]/df["Endeks"].shift(1))-1)
df["Endeks Return Lag"]=100*((df["Endeks"].shift(1)/df["Endeks"].shift(2))-1)
df["Return Lag"]=((df["Adj Close"]/df["Adj Close"].shift(1))-1)*100


# %%
df=df.sort_index()

# %%
target_data = {
    "2024-02-13": "PATEK.IS",
    "2024-02-15": "BORSK.IS",
    "2024-02-22": "LMKDC.IS",
    "2024-02-29": "ALVES.IS",
    "2024-03-04": "ARTMS.IS",
    "2024-03-05": "MOGAN.IS",
    "2024-03-11": ["BARMA.IS", "INVES.IS", "EDATA.IS"],
    "2024-03-21": "ODINE.IS",
    "2024-04-26": "RGYAS.IS",
    "2024-05-02": ["OBAMS.IS", "ENTRA.IS"],
    "2024-05-09": "LILAK.IS",
    "2024-05-10": "KOTON.IS",
    "2024-05-16": "ALTNY.IS",
    "2024-05-17": "KOCMT.IS",
    "2024-05-23": "HRKET.IS",
    "2024-05-27": "PEHOL.IS",
    "2024-05-28": "ONRYT.IS",
    "2024-05-29": "OZYSR.IS",
    "2024-06-04": "ALKLC.IS",
    "2024-06-06": "YIGIT.IS",
    "2024-06-07": "HOROZ.IS"
}
for date, stocks in target_data.items():
    if isinstance(stocks, list):
        for stock in stocks:
            df.loc[(df.index == date) & (df["Hisse"] == stock), "Tavan Kontrol"] = 1
    else:
        df.loc[(df.index == date) & (df["Hisse"] == stocks), "Tavan Kontrol"] = 1
son=df.loc["2024-06-10":]
ilk=df.loc[:"2024-06-07"]
ilk=ilk[(ilk["Return"]<21) & (ilk["Return"]>-19)]
result=pd.concat([ilk,son],axis=0)

# %%
df=df.sort_index()

yasak=["YYAPI","EMNIS","TETMT","RODRG","BRKO","AYES","EUKYO","YGYO","BALAT","SONME","SNKRN","KSTUR","DERIM","UZERB","MARKA","MMCAS","YAYLA"]
for i in range(len(yasak)):
    yasak[i]=yasak[i]+".IS"
result=result.dropna()
result = result[~result['Hisse'].isin(["ISATR.IS","ISBTR.IS"])]
result = result[~result['Hisse'].isin(yasak)]
result=result[result["Tavan Kontrol"]==0]
result=result.sort_index()


# %%
params = {'iterations': 406,
 'depth': 8,
 'learning_rate': 0.05908481614373525,
 'random_strength': 15,
 'bagging_temperature': 0.48897432777080385,
 'border_count': 163,
 'l2_leaf_reg': 9}
model=CatBoostRegressor(**params,task_type="GPU",random_seed=42)
model.load_model("xtumyson.bin")

# %%
test=result.loc["2024-01-02":]
X_test=test[['Endeks Return','Return Lag','Range','RSI','Volume','Bağıl Hacim','DD','High', 'Low', 'Open', 'Adj Close','StochRSI_%K','MACD','ROC','MACD_Signal','MOM']]
tahminler=pd.DataFrame(test["Return"])
tahminler=tahminler.set_index(X_test.index)
tahminler["Tahmin"]=model.predict(X_test)
tahminler.columns=["Gerçek","Tahmin"]
tahminler["Hisse"]=test["Hisse"]
tahminler["Tavan"]=test["Tavan Kontrol"]
tahminler=tahminler[tahminler["Tavan"]==0]
top_5_rows = tahminler.groupby(level=0).apply(lambda x: x.nlargest(3, columns=['Tahmin'])).dropna()
topkar=(top_5_rows.groupby('Date')["Gerçek"].mean().iloc[:-2].cumsum()/2)

# %%
endeks1=yf.download(tickers="XU100.IS",start="2024-01-01",end="2024-06-10")
endeks1["Getiri"]=0
for i in range(len(endeks1)):
    endeks1["Getiri"].iloc[i]=100*((endeks1["Adj Close"].iloc[i]/endeks1["Adj Close"].iloc[0])-1)
endeks1=endeks1.fillna(0)


# %%
returns=top_5_rows.groupby('Date')["Gerçek"].mean().iloc[:-2].dropna()/2
returns=returns/100
returns=pd.DataFrame(returns)
returns["Kar"]=np.where((returns>0),1,0)


# %%
endeks1["Return"]=(endeks1["Adj Close"]/endeks1["Adj Close"].shift(1))-1


# %%
trade=pd.read_excel("trade.xlsx")
sonuclar=trade[["Kar(%).1","Endeks(%)"]].dropna()
sonuclar=sonuclar.set_index(yf.download(tickers="XU100.IS",start="2024-04-08").index)
endeks=yf.download(tickers="XU100.IS",start="2024-04-08")
endeks["Getiri"]=100*((endeks["Adj Close"]/endeks["Adj Close"].shift(1))-1)
endeks["Getiri"]=endeks["Getiri"].fillna(0)


import matplotlib.pyplot as plt
plt.style.use("fivethirtyeight")
plt.figure(figsize=(15,8))
plt.title("Canlıda Elde Edilen Sonuçlar")
plt.plot(sonuclar["Kar(%).1"].cumsum(),label="Model Getirisi")
plt.plot(sonuclar["Endeks(%)"].cumsum(),label="BIST100 Dışı Getiri")
plt.plot(endeks["Getiri"].cumsum(),label="BIST100 Getiri")
plt.legend()

# %%
import matplotlib.pyplot as plt
import io
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import telegram

# Bot token'ınızı buraya yapıştırın
BOT_TOKEN = '6994011653:AAH8kaRmhMqfHyp634PiaTP1ri63onS56Nk'
# Kanal kullanıcı adı ya da ID'si
CHANNEL_ID = '6356198553'  # ya da '-1001234567890' formatında kanal ID'si

# Bot nesnesini oluşturun
bot = telegram.Bot(token=BOT_TOKEN)

# /start komutu için callback fonksiyonu
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Bu botu kullanarak şunları yapabilirsiniz: \n/start - Başlangıç mesajı\n/canlisonuclar\n/backtest\n/stats')

# /help komutu için callback fonksiyonu
def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Bu botu kullanarak şunları yapabilirsiniz: \n/start - Başlangıç mesajı\n/canlisonuclar\n/backtest\n/stats')

# Gelen mesajları yakalama ve yanıt verme fonksiyonu
def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)

def canlisonuclar(update: Update, context: CallbackContext) -> None:
    plt.style.use("fivethirtyeight")
    plt.figure(figsize=(15,8))
    plt.title("Canlıda Elde Edilen Sonuçlar")
    plt.plot(sonuclar["Kar(%).1"].cumsum(),label="Model Getirisi")
    plt.plot(sonuclar["Endeks(%)"].cumsum(),label="BIST100 Dışı Getiri")
    plt.plot(endeks["Getiri"].cumsum(),label="BIST100 Getiri")
    plt.legend()

    # Grafiği byte dizisine kaydetme
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Grafiği Telegram'a gönderme
    update.message.reply_photo(photo=buf)

HTML_FILE_PATH = 'stochk_macd_roc_macdsignal_mom_endeks.html'

def backtest(update: Update, context: CallbackContext) -> None:
    # HTML dosyasını açma ve Telegram'a gönderme
    with open(HTML_FILE_PATH, 'rb') as file:
        update.message.reply_document(document=file, filename='report.html')
TXT_FILE_PATH = 'stats.txt'

def stats(update: Update, context: CallbackContext) -> None:
    # TXT dosyasını açma ve içeriğini okuma
    try:
        with open(TXT_FILE_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
            update.message.reply_text(content)
    except Exception as e:
        update.message.reply_text(f"Dosya okunurken bir hata oluştu: {e}")




def main() -> None:
    # Updater nesnesini oluşturun ve bot token'ını ekleyin
    updater = Updater(BOT_TOKEN)

    # Dispatcher nesnesi ile komutları ekleyin
    dispatcher = updater.dispatcher

    # /start ve /help komutları için handler'ları ekleyin
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("canlisonuclar", canlisonuclar))
    dispatcher.add_handler(CommandHandler("backtest", backtest))
    dispatcher.add_handler(CommandHandler("stats", stats))

    # Botu başlatın
    updater.start_polling()

    # Botu çalışır durumda tutun
    updater.idle()

if __name__ == '__main__':
    main()

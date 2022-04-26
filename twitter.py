# Autenticación con Twitter y seguimiento con Twitter Streaming API
import os
from collections import Counter, OrderedDict
from rx import create, operators
from tweepy import OAuthHandler, Stream, StreamListener
from tkinter import *
import json
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import sys
import matplotlib.pyplot as plt
import numpy


UsernameExcel = list()
TextExcel = list()
LocationExcel = list()
DateExcel = list()
DataDispositivo = list()
DataDescripcion = list()
DataLink = list()
RawText=list()


def insert_tweet(tweet, text):

    if tweet['sentiment'] < -0.05:
        mood = 'negativo'
    elif tweet['sentiment'] > 0.05:
        mood = 'positivo'
    else:
        mood = 'neutral'
    text.insert(END, f'{tweet["text"]}\n', mood)


def parse_tweet(t):

    username = t["user"]["name"] if 'user' in t else 'Anónimo'

    text = t["text"]

    if "retweeted_status" in t:

        if 'extended_tweet' in t["retweeted_status"]:
            usuario = t["retweeted_status"]["user"]["name"]
            text = "RT @" + usuario + " " + t["retweeted_status"]["extended_tweet"]["full_text"]

    if 'extended_tweet' in t:
        text = t["extended_tweet"]["full_text"]

    location = t["user"]["location"]
    date = t["created_at"]
    rts = t["retweet_count"]
    favoritos = t["favorite_count"]
    dispositivo = t["source"]

    dispositivo = dispositivo.split('"')
    dispositivo = dispositivo[4]
    dispositivo = re.sub("\</a|\>", "", dispositivo)

    description = t["user"]["description"]
    link = "https://twitter.com/twitter/statuses/" + str(t["id"])

    analizador = SentimentIntensityAnalyzer()

    '''

    if t["user"]["lang"]!='en':
        translator = Translator()
        ar = translator.translate(text).text
        sentimiento= analizador.polarity_scores(ar)['compound']

    else:

    '''
    sentimiento = analizador.polarity_scores(text)['compound']

    if sentimiento < -0.05:

        RawText.append(text)

        if text not in TextExcel:
            UsernameExcel.append(username)
            TextExcel.append(text)
            LocationExcel.append(location)
            DateExcel.append(date)
            DataDispositivo.append(dispositivo)
            DataDescripcion.append(description)
            DataLink.append(link)




    return {
        'text': f'Usuario: {username} \nLocalizacion: {location}\nFecha: {date} \nTweet: {text}\nRTs: {rts}\nFavoritos: {favoritos}\n'
                f'Dispositivo: {dispositivo}\nDescripcion: {description}\nLink del tweet: {link}\nSentimiento:{sentimiento}',
        'sentiment': sentimiento
    }


def mi_observable(keywords):

    consumer_key = "consumerkey"
    access_token = "accesstoken"
    consumer_secret = "consumersecret"
    access_token_secret = "accesstokensecret"

    def observe_tweets(o, s):
        class TweetListener (StreamListener):
            def on_data(self, data):
                o.on_next(data)

            def on_error(self, status):
                o.on_error(status)

        listener = TweetListener()
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        global stream
        stream = Stream(auth, listener)
        stream.filter(track=keywords, is_async=True, languages=['en'])


    return create(observe_tweets)


class App:
    def __init__(self):
        self.__contador = 0
        self.window = Tk()
        self.window.title('BÚSQUEDA DE TWEETS')
        self.window.resizable(False, False)
        Label(text='Término de búsqueda').grid(column=0, row=0)
        Button(text='Buscar', width=35, command=self.search).grid(column=0, row=1, columnspan=1)
        Button(text='Terminar', width=35, command=self.terminarButton).grid(column=1, row=1, columnspan=1)
        self.entry = Entry()
        self.entry.grid(column=1, row=0)
        self.txt = Text(bg='#ffffff')
        self.txt.grid(row=2, column=0, columnspan=2)
        self.txt.tag_config('negativo', background='white', foreground='red')
        self.txt.tag_config('neutral', background='white', foreground='black')
        self.txt.tag_config('positivo', background='white', foreground='green')
        self.window.mainloop()

    def search(self):
        mi_observable([self.entry.get()]).pipe(
            operators.map(lambda txt: json.loads(txt)),
            operators.map(lambda d: parse_tweet(d))
        ).subscribe(on_next=lambda t: insert_tweet(t, self.txt), on_error=lambda e: print(e))

    def terminarButton(self):
        stream.disconnect()
        #self.window.quit()


def mime_init(from_addr, recipients_addr, subject, body):
    """
    :param str from_addr:           The email address you want to send mail from
    :param list recipients_addr:    The list of email addresses of recipients
    :param str subject:             Mail subject
    :param str body:                Mail body
    :return:                        MIMEMultipart object
    """

    msg = MIMEMultipart()

    msg['From'] = from_addr
    msg['To'] = ','.join(recipients_addr)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    return msg


def send_email(user, password, from_addr, recipients_addr, subject, body, files_path=None, server='smtp.gmail.com'):
    """
    :param str user:                Sender's email userID
    :param str password:            sender's email password
    :param str from_addr:           The email address you want to send mail from
    :param list recipients_addr:    List of (or space separated string) email addresses of recipients
    :param str subject:             Mail subject
    :param str body:                Mail body
    :param list files_path:         List of paths of files you want to attach
    :param str server:              SMTP server (port is choosen 587)
    :return:                        None
    """

    #   assert isinstance(recipents_addr, list)
    FROM = from_addr
    TO = recipients_addr if isinstance(recipients_addr, list) else recipients_addr.split(' ')
    PASS = password
    SERVER = server
    SUBJECT = subject
    BODY = body
    msg = mime_init(FROM, TO, SUBJECT, BODY)

    for file_path in files_path or []:
        with open(file_path, "rb") as fp:
            part = MIMEBase('application', "octet-stream")
            part.set_payload((fp).read())
            # Encoding payload is necessary if encoded (compressed) file has to be attached.
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(file_path))
            msg.attach(part)

    if SERVER == 'localhost':  # send mail from local server
        # Start local SMTP server
        server = smtplib.SMTP(SERVER)
        text = msg.as_string()
        server.send_message(msg)
    else:
        # Start SMTP server at port 587
        server = smtplib.SMTP(SERVER, 587)
        server.starttls()
        # Enter login credentials for the email you want to sent mail from
        server.login(user, PASS)
        text = msg.as_string()
        # Send mail
        server.sendmail(FROM, TO, text)

    server.quit()


def mail_datos():

    user = 'user'
    password = 'password'
    from_addr = 'twitterosintdata@gmail.com'
    recipients_addr = ['twitterosintdata@gmail.com']
    subject = 'SMTP mail test'
    body = 'Hello from SMTP'
    file_path = ['tweets.xlsx', 'localizaciones_grafica.png', 'text_grafica.png','dispositivos_grafica.png']

    send_email(user, password, from_addr, recipients_addr, subject, body, file_path)


def pasarExcel():

    for i in range(0, len(LocationExcel) - 1):

        if LocationExcel[i] is None:
            LocationExcel[i] = 'No se ha proporcionado una ubicación'

        if DataDescripcion[i] is None:
            DataDescripcion[i] = 'No se ha proporcionado una descripcion'


    d = (
        {"Usuario": UsernameExcel, "Tweet": TextExcel, "Ubicación": LocationExcel, "Fecha": DateExcel,
         "Dispositivo": DataDispositivo, "Descripcion": DataDescripcion, "Link": DataLink}
    )

    df = pd.DataFrame(data=d)

    df.to_excel('tweets.xlsx', index=False, header=True)


def graficas():

    localizaciones = Counter(LocationExcel)
    tweets = Counter(RawText)
    dispositivos=Counter(DataDispositivo)

    resultadoLocalizacion = {}
    resultadoText = {}
    resultadoDispositivos={}

    for clave in localizaciones:
        valor = localizaciones[clave]
        resultadoLocalizacion[clave] = valor

    sortedDict1 = OrderedDict(sorted(resultadoLocalizacion.items(), key=lambda x: x[1], reverse=True))

    for clave in tweets:
        valor = tweets[clave]
        resultadoText[clave] = valor

    sortedDict2 = OrderedDict(sorted(resultadoText.items(), key=lambda x: x[1], reverse=True))

    for clave in dispositivos:
        valor = dispositivos[clave]
        resultadoDispositivos[clave] = valor

    sortedDict3 = OrderedDict(sorted(resultadoDispositivos.items(), key=lambda x: x[1], reverse=True))

    if len(sortedDict1) >= 10:

        for i in range(len(sortedDict1) - 10):
            sortedDict1.popitem()

    if len(sortedDict2) >= 5:

        for i in range(len(sortedDict2) - 5):
            sortedDict2.popitem()

    if len(sortedDict3) >= 5:

        for i in range(len(sortedDict3) - 5):
            sortedDict3.popitem()

    s = pd.Series(sortedDict1)
    print(s)

    ss = pd.Series(sortedDict2)
    print(ss)

    sss = pd.Series(sortedDict3)
    print(sss)


    df = pd.DataFrame(s)
    df2 = pd.DataFrame(ss)
    df3=pd.DataFrame(sss)

    dfhola= numpy.log10(df)

    dfhola.plot(kind='bar', title='Localizaciones mas repetidas')
    plt.savefig('localizaciones_grafica', bbox_inches='tight')

    df2.plot(kind='bar', title='Tweets mas repetidos')
    plt.savefig('text_grafica', bbox_inches='tight')

    df3.plot(kind='bar', title='Dispositivos')
    plt.savefig('dispositivos_grafica', bbox_inches='tight')


    plt.show()


if __name__ == '__main__':

    App()
    pasarExcel()
    graficas()
    mail_datos()




# Autenticación con Twitter y seguimiento con Twitter Streaming API
import rx


from rx import create, operators
from tweepy import OAuthHandler, Stream, StreamListener
from tkinter import *
import json
from googletrans import Translator
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

UsernameExcel = list()
TextExcel = list()
LocationExcel = list()
DateExcel = list()
DataDispositivo=list()
DataDescripcion=list()
DataLink=list()


def insert_tweet(tweet,text):

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
            usuario=t["retweeted_status"]["user"]["name"]
            text ="RT @" + usuario + t["retweeted_status"]["extended_tweet"]["full_text"]

    if 'extended_tweet' in t:
        text = t["extended_tweet"]["full_text"]

    location = t["user"]["location"]
    date = t["created_at"]
    rts = t["retweet_count"]
    favoritos = t["favorite_count"]
    dispositivo = t["source"]
    dispositivo=dispositivo.split('"')
    dispositivo=dispositivo[4]
    dispositivo = re.sub("\</a|\>", "", dispositivo)

    description=t["user"]["description"]
    link= "https://twitter.com/twitter/statuses/"+ str(t["id"])

    analizador = SentimentIntensityAnalyzer()

    if t["user"]["lang"]!='en':
        translator = Translator()
        ar = translator.translate(text).text
        sentimiento= analizador.polarity_scores(ar)['compound']

    else:

        sentimiento=analizador.polarity_scores(text)['compound']


    if sentimiento < -0.05:

        if text not in TextExcel:

            UsernameExcel.append(username)
            TextExcel.append(text)
            LocationExcel.append(location)
            DateExcel.append(date)
            DataDispositivo.append(dispositivo)
            DataDescripcion.append(description)
            DataLink.append(link)


    return {
        'text': f'Usuario: {username} \nLocalizacion: {location }\nFecha: {date} \nTweet: {text}\nRTs: {rts}\nFavoritos: {favoritos}\n'
                f'Dispositivo: {dispositivo}\nDescripcion: {description}\nLink del tweet: {link}\nSentimiento:{sentimiento}',
        'sentiment': sentimiento
    }

def mi_observable(keywords):

    consumer_key = "sWRtWGpLlv23MVVrnarKgYZIC"
    access_token = "2820286426-loksPpNPz2MLIuowV7WDDr7keEYk0S60XxASnuG"
    consumer_secret = "BZvea0H19Zp4V7xZxM7zGSO6FevKTMywzdZQfdM3iVrd0IeYHu"
    access_token_secret = "z8htgV2brDM307YzpcPYLUGLJo3aua7slsvPIY5F5i76u"

    def observe_tweets(o, s):
        class TweetListener (StreamListener):
            def on_data(self, data):
                o.on_next(data)

            def on_error(self, status):
                o.on_error(status)

        listener = TweetListener()
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
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

        Button(text='Buscar', width=35, command=self.searchButton).grid(column=0, row=1, columnspan=1)
        Button(text='Terminar', width=35, command=self.terminarButton).grid(column=1, row=1, columnspan=1)

        self.entry = Entry()
        self.entry.grid(column=1, row=0)

        self.txt = Text(bg='#ffffff')

        self.txt.grid(row=2, column=0, columnspan=2)

        self.txt.tag_config('negativo', background='white', foreground='red')
        self.txt.tag_config('neutral', background='white', foreground='black')
        self.txt.tag_config('positivo', background='white', foreground='green')

        self.window.mainloop()

    def searchButton(self):
        mi_observable([self.entry.get()]).pipe(
            operators.map(lambda txt: json.loads(txt)),
            operators.map(lambda d: parse_tweet(d))
        ).subscribe(on_next=lambda t:insert_tweet(t, self.txt), on_error=lambda e: print(e))

    def terminarButton(self):
        self.window.quit()


def envioMail():
    # Iniciamos los parámetros del script
    remitente = 'twitterosintdata@gmail.com'
    destinatarios = ['twitterosintdata@gmail.com']
    asunto = '[RPI] Correo de prueba'
    cuerpo = 'Este es el contenido del mensaje'
    ruta_adjunto = 'tweets.xlsx'
    nombre_adjunto = 'tweets.xlsx'

    # Creamos el objeto mensaje
    mensaje = MIMEMultipart()

    # Establecemos los atributos del mensaje
    mensaje['From'] = remitente
    mensaje['To'] = ", ".join(destinatarios)
    mensaje['Subject'] = asunto

    # Agregamos el cuerpo del mensaje como objeto MIME de tipo texto
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Abrimos el archivo que vamos a adjuntar
    archivo_adjunto = open(ruta_adjunto, 'rb')

    # Creamos un objeto MIME base
    adjunto_MIME = MIMEBase('application', 'octet-stream')
    # Y le cargamos el archivo adjunto
    adjunto_MIME.set_payload((archivo_adjunto).read())
    # Codificamos el objeto en BASE64
    encoders.encode_base64(adjunto_MIME)
    # Agregamos una cabecera al objeto
    adjunto_MIME.add_header('Content-Disposition', "attachment; filename= %s" % nombre_adjunto)
    # Y finalmente lo agregamos al mensaje
    mensaje.attach(adjunto_MIME)

    # Creamos la conexión con el servidor
    sesion_smtp = smtplib.SMTP('64.233.184.108')

    # Ciframos la conexión
    sesion_smtp.starttls()

    # Iniciamos sesión en el servidor
    sesion_smtp.login('twitterosintdata@gmail.com', 'mohoric99')

    # Convertimos el objeto mensaje a texto
    texto = mensaje.as_string()

    # Enviamos el mensaje
    sesion_smtp.sendmail(remitente, destinatarios, texto)

    # Cerramos la conexión
    sesion_smtp.quit()





def pasarExcel():

    for i in range(0,len(LocationExcel)-1):

        if LocationExcel[i] is None:
            LocationExcel[i] = 'No se ha proporcionado una ubicación'

        if DataDescripcion[i] is None:
            DataDescripcion[i] = 'No se ha proporcionado una descripcion'




    d = (
        {"Usuario": UsernameExcel, "Tweet": TextExcel, "Ubicación": LocationExcel, "Fecha": DateExcel, "Dispositivo": DataDispositivo, "Descripcion": DataDescripcion, "Link": DataLink}
    )

    df = pd.DataFrame(data=d)

    df.to_excel('tweets.xlsx', index=False, header=True)


if __name__ == '__main__':
    App()
    pasarExcel()
    envioMail()


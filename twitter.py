# Autenticación con Twitter y seguimiento con Twitter Streaming API
import rx
from rx import create, operators
from tweepy import OAuthHandler, Stream, StreamListener
from tkinter import *
import json
from textblob import TextBlob
from googletrans import Translator

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
    text = t["text"] if 'text' in t else ''
    location = t["user"]["location"]
    date = t["created_at"]

    translator = Translator()
    ar = translator.translate(text).text


    return {
        'text': f'Usuario: {username} \nLocalizacion: {location }\nFecha: {date} \nTweet: {text}\n\n',
        'sentiment': TextBlob(ar).sentiment.polarity

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
        stream.filter(track=keywords, is_async=True, languages=['en','es'])

    return create(observe_tweets)


class App:
    def __init__(self):
        self.__contador = 0
        self.window = Tk()
        self.window.title('BÚSQUEDA DE TWEETS')
        self.window.geometry('1920x1080')
        self.window.resizable(True, True)

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
        exit()


if __name__ == '__main__':
    App()




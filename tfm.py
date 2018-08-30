from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters ,ConversationHandler,RegexHandler)
import apiai, json
import sqlite3
import telegram as tg
import pandas as pd

CHOOSING, CANTIDAD, OFICINA, FIN = range(4)

columnas = ['id','edad','riesgo','cantidad','oficina']
df=pd.DataFrame(columns=columnas)
dictEdad = {"18-30":"¡Vaya jovencito! Ahora dime qué riesgo estás dispuesto a tomar.",
            "30-60":"MEdiana edad. Ahora dime qué riesgo estás dispuesto a tomar.",
            ">60": "La segunda juventud. Ahora dime qué riesgo estás dispuesto a tomar."}
dictRiesgo = {"Alto":"¡Vaya, veo que te va la marcha! Ahora dime qué cantidad te gustaría invertir.",
              "Medio":"Un punto medio, así me gusta. Ahora dime qué cantidad te gustaría invertir",
              "Bajo": "A mí también me gusta la tranquilidad. Ahora dime qué cantidad te gustaría invertir."}
dictCantidad = {"<5000":"Me gusta empezar con algo moderado. Dime, ¿Necesitarías una oficina para las gestiones?",
              "5000-20000":"Vaya, parece que quieres tomárte esto en serio. Dime, ¿Necesitarías una oficina para las gestiones?",
              ">20000": "Uuuf, veo que alguien ha trabajado duro y ahora está recogiendo los frutos.Dime, ¿Necesitarías una oficina para las gestiones?"}

def startCommand(bot, update,user_data):
	"""
	Función start. Se llama cuando el usuario introduce /start en el bot.
	Esta función pide la edad del usuario y guarda el id de usuario(único) en un DataFrame.
	"""
    df.set_value(update.message.chat_id, 'id', update.message.chat_id)
    reply_keyboard = [['18-30', '30-60'],
                  ['>60']]
    markup = tg.ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Tenemos que empezar por saber tu edad",
                     reply_markup=markup)
    return CHOOSING

def riesgo_choice(bot, update,user_data):
	"""
	Función Riesgo. Segunda etapa del flujo.
	Esta funcion recibe la edad del usuario y la almacena.
	Además, pide el nivel de riesgo deseado.
	"""
    df.set_value(update.message.chat_id,
                 'edad', update.message.text)
    respuesta = dictEdad[update.message.text]
    reply_keyboard = [['Alto', 'Medio'],
                  ['Bajo']]
    markup = tg.ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text=respuesta,
                     reply_markup=markup)
    return CANTIDAD

def cantidad_choice(bot, update,user_data):
	"""
	Función Cantidad. Tercera etapa de flujo. 
	Esta función recibe el nivel de riesgo del usuario y lo almacena.
	Además, pide la cantidad a invertir.
	"""
    df.set_value(update.message.chat_id,
                 'riesgo', update.message.text)
    respuesta = dictRiesgo[update.message.text]
    reply_keyboard = [['<5000', '5000-20000'],
                  ['>20000']]
    markup = tg.ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text=respuesta,
                     reply_markup=markup)
    return OFICINA
def oficina_choice(bot, update,user_data):
	"""
	Función oficina. Cuarta etapa del flujo.
	Esta función recibe la cantidad a invertir y la almacena.
	Además, da la opción de tener oficina.
	"""
    df.set_value(update.message.chat_id,
                 'cantidad', update.message.text)
    respuesta = dictCantidad[update.message.text]
    reply_keyboard = [['Sí', 'No']]
    markup = tg.ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text=respuesta,
                     reply_markup=markup)
    return FIN

def final_choice(bot, update,user_data):
	"""
	Función final. Final del flujo.
	Esta función alamacena la elección de oficina y
	responde con el mejor producto según las respuestas del usuario.
	"""
    df.set_value(update.message.chat_id,
                 'oficina', update.message.text)
    respuesta=str(df.iloc[0,0])
    bot.send_message(chat_id=update.message.chat_id,
                     text=respuesta,
                     reply_markup=markup)
    return ConversationHandler.END
    
def done(bot, update, user_data):
    update.message.reply_text("I learned these facts about you:")
    return ConversationHandler.END

def textMessage (bot, update):
	"""
	Función texto.
	Esta función tiene como objetivo conversar con el usuario.
	Utilizamos DialogFlow como agente.
	Guardamos todas las conversaciones en una base de datos.
	"""
    cnx = sqlite3.connect("Conversaciones.db") # Conectamos a la base de datos
    cursor = cnx.cursor()
    request = apiai.ApiAI ('TOKENDF').text_request() # Token para la API de DialogFlow
    request.lang = 'es' # Lenguaje del mensaje a enviar
    request.session_id = 'small-talk-63ecd' # ID de la sesión.
    request.query = update.message.text # Mandamos una consulta a la IA con el mensaje del usuario
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))
    response = responseJson['result']['fulfillment']['speech'] # Parseamos el JSON para obtener la respuesta del usuario
    msgusuario=update.message.text
    numero=str(update.message.chat_id)
    cursor.execute("INSERT INTO chats2 (id,usuario,bot) VALUES ('"+numero+"','"+msgusuario+"', '"+response+"')")
    cnx.commit()
    if response:
        bot.send_message(chat_id = update.message.chat_id, text = response)
    else:
        bot.send_message(chat_id = update.message.chat_id, text = 'Lo siento, no te he entendido. Recuerda que estoy aprendiendo.')

    
conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', startCommand, pass_user_data=True)],
        states={
            CHOOSING: [RegexHandler('^(18-30|30-60|>60|)$',
                                    riesgo_choice,
                                    pass_user_data=True),
                       ],
            CANTIDAD: [MessageHandler(Filters.text,
                                    cantidad_choice,
                                    pass_user_data=True)
                    ],
            OFICINA: [MessageHandler(Filters.text,
                                    oficina_choice,
                                    pass_user_data=True)
                    ],
            FIN: [MessageHandler(Filters.text,
                                    final_choice,
                                    pass_user_data=True)
                    ]

        },

        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    )  
     
updater = Updater(token='token:token')
dispatcher = updater.dispatcher
text_message_handler = MessageHandler(Filters.text,textMessage)
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(text_message_handler)
updater.start_polling(clean=True)
print('A toda madre')
updater.idle()

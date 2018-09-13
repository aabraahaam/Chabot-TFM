from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters ,ConversationHandler,RegexHandler)
import apiai, json
import sqlite3
updater = Updater(token='')
print("Connection to Telegram established; starting bot.")
dispatcher = updater.dispatcher
import telegram as tg
import pandas as pd

CHOOSING, CANTIDAD, OFICINA, FIN = range(4)
data = pd.read_csv("C:/Users/prueba/Downloads/Telegram Desktop/Productos.csv", sep= ";")
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
              ">20000": "Uuuf, veo que alguien ha trabajado duro y ahora está recogiendo los frutos. Dime, ¿Necesitarías una oficina para las gestiones?"}

def startCommand(bot, update,user_data):
    df.set_value(update.message.chat_id, 'id', update.message.chat_id)
    reply_keyboard = [['18-30', '30-60'],
                      ['>60']]
    markup = tg.ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Tenemos que empezar por saber tu edad",
                     reply_markup=markup)
    return CHOOSING

def riesgo_choice(bot, update,user_data):
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
    df.set_value(update.message.chat_id,
                 'cantidad', update.message.text)
    respuesta = dictCantidad[update.message.text]
    reply_keyboard = [['Sí', 'No']]
    markup = tg.ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text=respuesta,
                     reply_markup=markup)
    return final_choice

def final_choice(bot, update,user_data):
    df.set_value(update.message.chat_id,
                 'oficina', update.message.text)
    edad = df.query("id == "+str(update.message.chat_id)+"").iloc[0,1]
    riesgo = df.query("id == "+str(update.message.chat_id)+"").iloc[0,2]
    cantidad = df.query("id == "+str(update.message.chat_id)+"").iloc[0,3]
    oficina = df.query("id == "+str(update.message.chat_id)+"").iloc[0,4]
    respuesta = data.query("EDAD == '"+str(edad)+"' & RIESGO == '"+
                           str(riesgo)+"' & OFICINA == '"+str(oficina)+
                           "' & CANTIDAD == '"+str(cantidad)+"'").iloc[0,0]
    
    respuesta = "Hemos consultado la base de datos y el producto que mejor se adapta a sus necesidades es el " + str(respuesta)
    bot.send_message(chat_id=update.message.chat_id,
                     text=respuesta)
    return ConversationHandler.END
    
def done(bot, update, user_data):
    update.message.reply_text("I learned these facts about you:")
    return ConversationHandler.END

def textMessage (bot, update):
    cnx = sqlite3.connect("Conversaciones.db")
    cursor = cnx.cursor()
    request = apiai.ApiAI ('').text_request() # Token API to Dialogflow
    request.lang = 'es' # In which language will the request be sent
    request.session_id = 'small-talk-63ecd' # ID Sessions of the dialog (you need to learn the bot afterwards)
    request.query = update.message.text # We send a request to the AI with a message from the user
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))
    response = responseJson['result']['fulfillment']['speech'] # We parse JSON and pull out the answer
    #meter timestamp,update.message.text,response
    msgusuario=update.message.text
    numero=str(update.message.chat_id)
    cursor.execute("INSERT INTO chats2 (id,usuario,bot) VALUES ('"+numero+"','"+msgusuario+"', '"+response+"')")
    cnx.commit()
# If there is an answer from the bot - we send it to the user, if not - the bot did not understand it
    if response:
        bot.send_message(chat_id = update.message.chat_id, text = response)
    else:
        bot.send_message(chat_id = update.message.chat_id, text = 'No te entiendo, recuerda que estoy aprendiendo')

    
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
                    ]

        },

        fallbacks=[RegexHandler('^(Sí|No|)$', final_choice, pass_user_data=True)]
    )  

text_message_handler = MessageHandler(Filters.text,textMessage)    
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(text_message_handler)
updater.start_polling(clean=True)
print('Ejecutando')
updater.idle()

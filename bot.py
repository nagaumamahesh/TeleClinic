import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import os
import db
import notifbot
import time
from telebot import apihelper

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"), parse_mode=None)

ACTIONS = ["Schedule a doctor\'s appointment", "Call Ambulance", "Schedule a counsellor appointment", "Deliver food to room"]
markup = ReplyKeyboardMarkup(row_width=1)
for i in ACTIONS:
    markup.add(KeyboardButton(i))


def doctor_appointment(message: telebot.types.Message) -> None:
    bot.reply_to(message, "Done! Your appointment has been scheduled\nHead over to https://t.me/Noti_11_bot to get notified when the doctor is ready to see you")
    db.create_appointment(message.chat.id)


def deliver_food_to_room(message: telebot.types.Message) -> None:
    if db.is_patient_sick(message.chat.id):
        bot.reply_to(message, "Done! food will be sent to your room soon :)")
        notifbot.send_food_req_notif_to_warden(message.chat.id)
    else:
        bot.reply_to(message, "Sorry, you can't avail this feature when you're not sick")


def call_ambulance(message: telebot.types.Message) -> None:
    bot.reply_to(message, "Done! We'll share this information with the authorities and help will arrive soon")
    if not db.appointment_exists(message.chat.id):
        doctor_appointment(message)
    else:
        bot.reply_to(message, "You already have an appointment scheduled")
    notifbot.send_ambulance_notif(message.chat.id)


def counsellor_appointment(message: telebot.types.Message) -> None:
    bot.reply_to(message, "Done! Your appointment has been scheduled")
    notifbot.send_appointment_notif_to_counsellor(message.chat.id)


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message) -> None:
    if not db.patient_exists(message.chat.id):
        db.create_patient(message.chat.id)
        bot.reply_to(message, "Please register yourself using /register")
    else:
        bot.reply_to(message, "Welcome to healthbot, we are here to help you out :)", reply_markup=markup)


@bot.message_handler(commands=['register'])
def register(message: telebot.types.Message) -> None:
    if db.patient_has_registered(message.chat.id):
        bot.reply_to(message, "You are already registered. You do not have to register again", reply_markup=markup)
    else:
        bot.reply_to(message, '''Enter your details in the following format:\nName\nAge\nSex [M/F]\nRegistration Number\nHostel Block [A/B/C/D1/D2]\nRoom Number\nPhone Number''')


@bot.message_handler(func=lambda message: True)
def router(message: telebot.types.Message):
    try:
        if not db.patient_has_registered(message.chat.id):
            fields = message.text.split("\n")
            db.register_patient(message.chat.id, fields[0], int(fields[1]), fields[2], fields[3], fields[4], int(fields[5]),
                                int(fields[6]))
            bot.reply_to(message, "You are already registered, click on the button menu to continue", reply_markup=markup)
        if message.text == "Schedule a doctor's appointment":
            if not db.appointment_exists(message.chat.id):
                doctor_appointment(message)
            else:
                bot.reply_to(message, "You already have an appointment scheduled!")
            time.sleep(1)  # Add a delay between messages to avoid rate limiting
        elif message.text == "Deliver food to room":
            deliver_food_to_room(message)
            time.sleep(1)
        elif message.text == "Call Ambulance":
            call_ambulance(message)
            time.sleep(1)
        elif message.text == "Schedule a counsellor appointment":
            counsellor_appointment(message)
            time.sleep(1)
    except apihelper.ApiException as e:
        if "Too Many Requests" in str(e):
            print("Rate limit exceeded. Waiting and retrying...")
            time.sleep(5)  # Wait for 5 seconds and retry
            router(message)
        else:
            print(f"Error: {e}")


def polling():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)  # Wait for 5 seconds before attempting to reconnect


if __name__ == "__main__":
    polling()

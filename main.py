from registration_handlers import *
from riddle_handlers import *
from god_handlers import *


activate_registration_handlers()
activate_riddle_handlers()
activate_god_handlers()

print("Бот запущен!")
bot.polling()

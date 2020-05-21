import telebot
import random
import json
import threading

from telebot import types


with open("telegram-api-token.txt") as token_file:
    TELEGRAM_TOKEN = token_file.read().strip()

bot = telebot.TeleBot(TELEGRAM_TOKEN)

"""Просто колода карт"""

Cards=["♠6","♣6","♥6","♦6",
       "♠7","♣7","♥7","♦7",
       "♠8","♣8","♥8","♦8",
       "♠9","♣9","♥9","♦9",
       "♠1","♣1","♥1","♦1",
       "♠B","♣B","♥B","♦B",
       "♠D","♣D","♥D","♦D",
       "♠K","♣K","♥K","♦K",
       "♠T","♣T","♥T","♦T",
      ]



Value={
   "6":1,
   "7":2,
   "8":3,
   "9":4,
   "1":5,
   "B":6,
   "D":7,
   "K":8,
   "T":9,
}


turn={}
Coloda={} 
player_cards={}
players_in_game={}

""" Очень страшная переменная зависит от номера игрока (1-6) и от chat.id , она хранит информацию о игроке."""
players_of_the_game=[{} for i in range(10)]


Cozur={}

"""Просто две кучи карт одна для карт которые подбросили , другая для тех которыми побились."""
kycha={}
kycha_defence={}


Is_game={}
""" Принимает значения 1 и 2 : 1- ход начинается; 2- ход закончен и игрокам надо выдать карты."""
step={}



Is_over={}

"""Задержка между ходами, нужна если в случае чего надо отменить переход к слующему ходу"""
Timer={}

"""Хранит первое сообщения ,который пользователь написал боту"""
first_message={}

"""Принимает значение минимального козыря"""
mini={}


player_defender={}


@bot.message_handler(commands=["help"])
def help_player(message):
 try:  
         bot.send_message(message.chat.id,"Здравствуйте, я бот для игры в дурака.\nЯ работаю в несколько этапов:\n1)/create -для создания игры ,также выберется козырь.\n2)/join -после того как игра была создана к ней можно присоединиться и получить свои карты.\n3)/host- эта команда начинает игру, присоединяться к уже запущеной игре нельзя. ")
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")   
        

"""Создаёт новую игру , вместо create можно использовать start"""
@bot.message_handler(commands=["create"])
def new_game(message):
 try:   
      """Функция перемешывает колоду"""
      tosscards(message)

      """Изначально программа не знает кто ходит"""
      turn[message.chat.id]=0
      
      Is_over[message.chat.id]=False

      """Создаём колоду для определённого чата"""
      Coloda[message.chat.id]=""
      for i in range(0,36):
          Coloda[message.chat.id]+=Cards[i]

      bot.reply_to(message, "Игра создана!")
      """Выбераем козырь"""
      Choze_cozur(message)
      players_in_game[message.chat.id]=0
      
      """Обнуляем всех участников ,на случай если предыдущая игра не закончилась,а пользователи решили начать сначала новую игру. """
      To_zero(message)
      
      """ Игра не началась"""
      Is_game[message.chat.id]=False
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")     
        


"""На случай если новую игру не создали , но кто-то уже пытается в неё играть"""
@bot.message_handler(func =lambda message: (message.chat.id not in Is_over) or (Is_over[message.chat.id]==True))
def game_is_not_started(message):
 try:  
      bot.reply_to(message,"Создайте новую игру,пожалуйста!")
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")     


"""Срабатывает в случае окончания игры"""
def the_game_is_over(message):
 try:       
         bot.send_message(message.chat.id,"Игра окончена! Создайте новую игру,чтобы сыграть снова!")
         To_zero(message)
         Is_over[message.chat.id]=True
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")    
        


"""Функция ''регистрирует'' нового игрока"""
@bot.message_handler(commands=["join"])
def new_player(message):
 try:   
    """Нельзя присоединятся , если ты уже присоеденился ,если игра запущена (в неё уже играют) и если уже есть 6 игроков""" 
    if Is_in_game(message)==True:
        bot.reply_to(message,"Вы уже в игре.")
    elif Is_game[message.chat.id]==True:
        bot.reply_to(message,"Игра уже запущена, к ней нельзя присоедениться!")
    elif players_in_game[message.chat.id]==6:
        bot.reply_to(message,"В игре уже 6 человек ,больше нельзя.")   
    else:    
        players_in_game[message.chat.id]+=1   
        player_cards[message.from_user.id]=""
        """Функция выдаёт игроку его карты""" 
        Give_cards(message.from_user.id,message.chat.id)
        """Добавляем игрока"""
        Add_player(message)
        bot.reply_to(message,f"{message.from_user.first_name} вы успешно присоеденились к игре.")
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")  
        

"""На случай если пользователь не присоеденившийся к игре пытается в неё играть """
@bot.message_handler(func =lambda message: Is_in_game(message)==False)
def Not_in_game(message):
 try:     
    bot.reply_to(message,"Сначала присоеденитесь к игре!")
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")  
          

"""Показывает игроку его карты в виде клавиатуры"""
def show(user,chat):
 try:    
    global markup
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True,one_time_keyboard=False,selective=True,row_width=3)
    for i in range(0,len(player_cards[user])-1,6) :
        Card=player_cards[user][i]+player_cards[user][i+1]
        
        if (i+2<=len(player_cards[user])-1):
           Card2=player_cards[user][i+2]+player_cards[user][i+3]
        else:
            Card2=None

        if (i+4<=len(player_cards[user])-1):      
            Card3=player_cards[user][i+4]+player_cards[user][i+5]
        else:
            Card3=None  
        """Добавляем карты в столбик. Столбик рассчитан на 3 карты , но возможно прийдётся добавить только 1 или 2."""  
        Adding(Card,Card2,Card3)  
    
    """
    Добавляем вспомогательные клавиши. 
    В первом случае игрок ,который "обороняется" ,еще не назначен, т.к ход только начался. 
    поэтому мы добавляем клавишу "Взять" игроку ,чей ход следующий после этого:
        turn[chat] % players_in_game[chat]  + 1.
    Во втором случае "обороняющийся" уже назначен и мы добавляем клавишу уже ему.
    В третьем случае добавляем клавишу "Бито" для "атакующих"  
    """ 
    if (step[chat]==1) and (user==players_of_the_game[turn[chat]%players_in_game[chat]+1][chat].id) :
       markup.add("Взять")
    elif (step[chat]==2) and (user==player_defender[chat].id):
       markup.add("Взять")   
    else:
        markup.add("Бито")     

    """
    Существует два способа отправить клавиатуру конкретному человеку , а не всем в группе:
    1) С помошью ответа на конкретное сообщение,которым мы и пользуемся,отвечая на первое сообщение пользователя,
    которое хранится в first_message.
    2) Пользователи, которые были @упомянуты в поле text объекта Message; С этим способом я не разобрался:(
    """
    bot.reply_to(first_message[user],"Ваша клавиатура обновлена!",reply_markup=markup)         
 except Exception as e:
     bot.send_message(chat,"Случилась какая-то ошибка.") 


def Adding(Card,Card2,Card3):
 try:   
    """Т.к десятка в отличии от других карт имеет две цыфры она хранится в виде еденицы , 
    но пользователю её надо показать в виде 10 , поэтому ести карта равна 1 к ней надо прибавить 0.""" 
    if (Card!=None) and (Card[1]=="1") :
        Card+="0" 
    if (Card2!=None) and (Card2[1]=="1"):
        Card2+="0" 
    if (Card3!=None) and (Card3[1]=="1"):
        Card3+="0" 

    """Проверяем сколько карт нам надо добавить в очередной столбик :3 ,2 или 1."""
    if (Card3!=None):
        markup.add(Card,Card2,Card3)
    elif (Card2!=None):  
        markup.add(Card,Card2) 
    else:
        markup.add(Card)  

 except Exception as e:
     None


def Finish_turn(message):
    try:
       """Срабатывает если кто-то из игроков нажал "Бито" , т.к кто-то может быть еще чего-то хочет подкинуть
       функцию можно остановить.Для этого нужен таймер."""
       """Проверяем можем ли мы закончить ход ,если можем ,запускаем таймер, который через n секунд закончит ход.""" 
       if (Can_we_finish_turn(message)!=True):
         return 
       Timer[message.chat.id]=threading.Timer(10, the_game,args=[message]) 
       Timer[message.chat.id].start()   
       bot.send_message(message.chat.id,"Через 10 секунд ход будет окончен.")
    except Exception as e:
        return

    

def take_cards(message):
 try:   
    """Пытаемся остановить таймер """
    try:
       Timer[message.chat.id].cancel() 
    except Exception as e:
        None

    """Даём игроку все ранее сыгранные карты в этом ходу карты"""
    player_cards[message.from_user.id]+=kycha[message.chat.id]+kycha_defence[message.chat.id]
    """Обновляем клавиатуру игрока, пополняя её новыми картами."""
    show(message.from_user.id,message.chat.id)
    """Передаём ход следующему игроку"""
    Next_turn(message)
    """Переходим к слудующему шагу игры -выдече карт"""
    the_game(message)
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")     
 


@bot.message_handler(func=lambda message:(message.chat.id in Is_game) and (Is_game[message.chat.id]==True) and (step[message.chat.id]==2) and (message.from_user.id==player_defender[message.chat.id].id))
def Add_card_for_defence(message):
 try:   
    """10 хранится в программе в виде 1 , но игрок вводит обычную 10 ,поэтому мы отрезаем конечный ноль.""" 
    if (len(message.text)==3):
        message.text=message.text[:-1]  
    """Если игрок решил взять карты , мы запускаем  функцию take_cards"""   
    if (message.text=="Взять"):
        take_cards(message)
        return

    """Проверяем ,что игрок не мухлюет (кинул карту ,которая есть в его колоде и которой он может биться.)"""    
    if (Is_everything_alright_defence(message)==False):
        return None

    """Добавляем карту в кучу "защиты" """ 
    kycha_defence[message.chat.id]+=message.text

    """Удаляем карту из  "рук" игрока ,т.к в Python строки неизменяемы, для этого нужна отдельная функция."""
    player_cards[message.from_user.id]=delete(player_cards[message.from_user.id],message.text,message.chat.id)   

    """Показываем игроку его карты """ 
    show(message.from_user.id,message.chat.id)
    
    """Функция Create_table создаёт игровой стол,она будет рассмотена позже."""
    bot.send_message(message.chat.id,Create_table(message))
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")    



@bot.message_handler(func=lambda message:(message.chat.id in Is_game) and  (Is_game[message.chat.id]==True))
def Add_card(message):
 try:   
    """10 хранится в программе в виде 1 , но игрок вводит обычную 10 ,поэтому мы отрезаем конечный ноль.""" 
    if (len(message.text)==3):
        message.text=message.text[:-1] 
    """Если игрок решил закончить ход переходим к соотвецтвующей функции"""    
    if (message.text=="Бито"):
        Finish_turn(message)
        return

    """Проверяем ,что игрок не мухлюет (кинул карту ,которая есть в его колоде и которую он может подкинуть.)"""    
    if (Is_everything_alright(message)==False):
        return

    """Пытаемся остановить таймер, тем самым предотвращая завершение хода."""
    try:
        Timer[message.chat.id].cancel() 
    except Exception as e:
        None   
    
    """Добавляем карту в кучу "атаки" """
    kycha[message.chat.id]+=message.text
    
    """Удаляем карту из  "рук" игрока ,т.к в Python строки неизменяемы, для этого нужна отдельная функция."""
    player_cards[message.from_user.id]=delete(player_cards[message.from_user.id],message.text,message.chat.id)   
    
    """Переходим к следующему шагу,это означает что была кинута первая карта"""
    step[message.chat.id]=2 
    
    """Показываем игроку его карты """ 
    show(message.from_user.id,message.chat.id)
   
    """Функция Create_table создаёт игровой стол,она будет рассмотена позже."""
    bot.send_message(message.chat.id,Create_table(message))
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")      




def Can_we_finish_turn(message):
 try:   
     """Проверяем ,что все карты побиты и что существует хотябы одна "активная карта". """
     if (len(kycha[message.chat.id])==len(kycha_defence[message.chat.id])) and (len(kycha[message.chat.id])!=0):
         """Проверяем ,что клавишу нажал именно "обороняюшийся" , а не кто-то другой."""
         if (message.from_user.id!=player_defender[message.chat.id].id):
             return True
     return False         
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")  


def Create_table(message):
 try:
    s=""
    s+="Игровой стол:"
    s+="\n\nАктивные игроки:"
    for i in range(1,players_in_game[message.chat.id]+1):
              s+="\n"+str(players_of_the_game[i][message.chat.id].first_name)+"-"+str(len(player_cards[players_of_the_game[i][message.chat.id].id])//2) +"карт"
    s+="\n\nКарт в колоде -"+str(len(Coloda[message.chat.id])//2)+"\n"
    s+="\nКозырь -" +str(Cozur[message.chat.id])+"\n\n"
    for i in range(0,len(kycha[message.chat.id])-1,2) :
        s+=kycha[message.chat.id][i]+kycha[message.chat.id][i+1]
        
        """10 хранится в программе в виде 1 , поэтому надо добавить ноль, чтобы пользователь увидел 10, а не 1."""
        s+=Is_ten(kycha[message.chat.id][i+1])

        if (i<len(kycha_defence[message.chat.id])-1):
            s+=" vs "+kycha_defence[message.chat.id][i]+kycha_defence[message.chat.id][i+1]
            
            """10 хранится в программе в виде 1 , поэтому надо добавить ноль, чтобы пользователь увидел 10, а не 1."""
            s+=Is_ten(kycha_defence[message.chat.id][i+1])

        s+=" || "
    return s
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")   



def Is_ten(a):
 if a=="1":
     return "0"
 else:
     return ""    

def the_game(message):
 try:   
    """Если step=1 ,то это начало хода- никто еще не походил, а если step=2 , то это конец хода и надо выдавать карты.""" 
    if (step[message.chat.id]==1):
        bot.send_message(message.chat.id,f"{players_of_the_game[turn[message.chat.id]][message.chat.id].first_name} - твой ход.")
        
        kycha[message.chat.id]=""
        kycha_defence[message.chat.id]=""

        """Переходим к следующему ходу""" 
        Next_turn(message)
        """Обозначем "обороняющегося" игрка."""
        player_defender[message.chat.id]=players_of_the_game[turn[message.chat.id]][message.chat.id]

        bot.send_message(message.chat.id,f"{player_defender[message.chat.id].first_name} на тебя ходят.Готовся откидываться")
    if (step[message.chat.id]==2):
        """После выдачи карт мы начнём новый ход"""
        step[message.chat.id]=1

        """ Если в колоде нет карт , то следует проверить не закончилась ли игра."""
        if (Coloda[message.chat.id]==""):         
            Is_game_over(message) 
        else:
          """Всем игрокам у которых меньше 6 карт выдаём карты и колоды.""" 
          for i in range(1,players_in_game[message.chat.id]+1):
              if (len(player_cards[players_of_the_game[i][message.chat.id].id])/2<6):
                   Give_cards(players_of_the_game[i][message.chat.id].id,message.chat.id)  
                   show(players_of_the_game[i][message.chat.id].id,message.chat.id) 

        """Начинаем следующий ход"""
        the_game(message)    
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")          


@bot.message_handler(commands=["host"])
def host_the_game(message):
 try: 
    """Вместо 200 можно использовать любое значение больше 10. """ 
    mini[message.chat.id]=200

    """Запустить уже запущенную игру нельзя,также нельзя запустить игру ,если ты один"""
    if players_in_game[message.chat.id]<2:
      bot.reply_to(message,"Должно быть не менее двух человек в игре.")
    elif Is_game[message.chat.id]==True:
      bot.reply_to(message,"Игра уже запущена!")
      return
    else:
     """ Начинаем новый ход """  
     step[message.chat.id]=1   
     
     """Ищем игрока с найменьшим козырем """
     for i in range(1,players_in_game[message.chat.id]+1):
          Who_first(players_of_the_game[i][message.chat.id].id,message.chat.id,i)
     
     """Показываем игрокам их карты"""     
     for i in range(1,players_in_game[message.chat.id]+1):
          show(players_of_the_game[i][message.chat.id].id,message.chat.id) 
     
     """Игра началась сообщаем об этом программе"""      
     Is_game[message.chat.id]=True

     """Переходим к игре"""
     the_game(message)
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")      


"""turn - содержит номер игрока, который  обороняется (в начале нового хода обороняющийся становится первым "атакующим"). """
def Next_turn(message):
 try:   
    turn[message.chat.id]%=players_in_game[message.chat.id]
    turn[message.chat.id]+=1
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")      


"""Рандомно сортирует колоду"""
def tosscards(message):
 try:    
    random.shuffle(Cards)
    Coloda[message.chat.id]=""
    for i in range(0,36):
        Coloda[message.chat.id]+=Cards[i] 
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")              


"""Функция запускается только если в колоде нет карт."""
def Is_game_over(message):
 try:   
    """Ищем игроков у которых закончились карты , поздравляем их с победой и удаляем из игры.""" 
    for i in range(1,players_in_game[message.chat.id]+1):
        if (len(player_cards[players_of_the_game[i][message.chat.id].id])==0):
            bot.send_message(message.chat.id,f"Поздравляю {players_of_the_game[i][message.chat.id].first_name} ты выиграл!")  
            delete_player(i,message)
    
    """
    Рассмотрим два варианта окончания игры:
    1)Остался один игрок -Дурак.
    2)У всех игроков карты заончились -Ничья.

    Если игра окончена запускаем функцию the_game_is_over.
    """        
    if (players_in_game[message.chat.id]==1):
      bot.send_message(message.chat.id,f"{players_of_the_game[1][message.chat.id].first_name} ты проиграл. Поприветствуйте нового дурака.")
      the_game_is_over(message)

    if (players_in_game[message.chat.id]==0):
       bot.send_message(message.chat.id,"Ничья. Ты посмотри какие все здесь умные.")
       the_game_is_over(message) 

    return False 
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")       
    


"""
Функция  удаляет игрока .
В начале мы меняем местами игрока ,которого надо "удалить", с следующим игроком и так пока он не тстанет последним.
Затем "удаляем" последнего игрока.   
"""

def delete_player(index,message):
 try:
     if (index!=players_in_game[message.chat.id]):
         for i in range(index,players_in_game[message.chat.id]+1):
             players_of_the_game[i][message.chat.id] ,players_of_the_game[i+1][message.chat.id]= players_of_the_game[i+1][message.chat.id] , players_of_the_game[i][message.chat.id]
     players_of_the_game[players_in_game[message.chat.id]][message.chat.id]=None
     players_in_game[message.chat.id]-=1
 
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.") 

"""
Функция выдаёт карты игроку.
Сначала определимся есть ли у игрока карты вообще.
Далее выдаём игроку карты , пока у него их не будет 6,паралельно удаляем карты из колоды.
"""

def Give_cards(user,chat):
 try:   
    if player_cards[user]=="":
        start=0
    else:
        start=len(player_cards[user])//2
    for i in range(start,6):
         if (Coloda[chat]==""):
            return None
         player_cards[user]+=Coloda[chat][-2]+Coloda[chat][-1]
         Coloda[chat]= Coloda[chat][:-2]   
 except Exception as e:
     bot.send_message(chat,"Случилась какая-то ошибка.")          


"""
Добавляет игрока в players_of_the_game на последнюю позицию-players_in_game[message.chat.id]
Сохраняет первое сообщение игрока в first_message
"""
def Add_player(message):
 try:  
    players_of_the_game[players_in_game[message.chat.id]][message.chat.id]=message.from_user
    first_message[message.from_user.id]=message
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")  


"""
Проверяет есть ли данный игрок в игре.
"""

def Is_in_game(message):
    try:
        if (player_cards[message.from_user.id]!=None):
            return True
        else:
            return False
    except Exception as e:
        return False



"""
"Обнуляет"  всех игроков в данном чате.
"""

def To_zero(message):
 try:   
    for i in range(1,7):
        player_cards[players_of_the_game[i][message.chat.id].id]=None
        players_of_the_game[i][message.chat.id]=None
 except Exception as e:
     None  



"""
Т.к в python строки неизменяемы , чтобы удалить элемент из строки создадим новую строку уже без этого элемента
"""

string_new={}

def delete(string, ellement,chat_id):
 try:  
    string_new[chat_id]=""
    for i in range(0,len(string)-1,2):
      if (string[i]+string[i+1]!=ellement) :
          string_new[chat_id]+=string[i]+string[i+1]
    return string_new[chat_id]  
 except Exception as e:
     bot.send_message(chat_id,"Случилась какая-то ошибка.")  


"""
Идём по картам каждого игрока , если встречаем козырь ,проверяем меньше ли он текущего минимального козыря mini.
Если меньше тогда , назначаем этого игрока на первый ход (index - номер игрока) и меняем mini на данный козырь.
"""

def Who_first(user,chat,index):
 try:   
    for i in range(0,len(player_cards[user]),2):
        if ((player_cards[user][i]==Cozur[chat]) and (Value[player_cards[user][i+1]]<mini[chat])):
            mini[chat]=Value[player_cards[user][i+1]]
            turn[chat]=index
 except Exception as e:
     bot.send_message(chat,"Случилась какая-то ошибка.")            
    


"""
Проверяем может ли игрок побиться данной картой.
"""

def Is_everything_alright_defence(message):
 try:   
    if len(kycha[message.chat.id])==len(kycha_defence[message.chat.id]):
        bot.reply_to(message,"Все карты уже побиты.")
        return False 
    if message.text not in Cards:
       return False
    if message.text not in player_cards[message.from_user.id]:
        bot.reply_to(message,"У вас нет такой карты.")  
        return False
    if ((kycha[message.chat.id][len(kycha_defence[message.chat.id])]!=Cozur[message.chat.id]) and (message.text[0]==Cozur[message.chat.id])):
        return True    
    if (kycha[message.chat.id][len(kycha_defence[message.chat.id])]!=message.text[0]):
        bot.reply_to(message,"Вы не можете бить картой другой масти если это не козырь.")  
        return False   
    if  (Value[kycha[message.chat.id][len(kycha_defence[message.chat.id])+1]]>=Value[message.text[1]]):
        bot.reply_to(message,"Эта карта слишком мала.")  
        return  False  
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")               


"""
Проверяем может ли игрок подкинуть данную карту.
В случае если это первый ход , проверяем что карту хочит добавить игрок ,который ходит.
Т.к turn указывает на "обороняющегося" ,то на игрок , который ходит, указывает -turn-1 или low(turn,chat.id)
"""

def Is_everything_alright(message):
 try:   
    if (step[message.chat.id]==1) and (message.from_user.id!=players_of_the_game[low(turn[message.chat.id],message.chat.id)][message.chat.id].id):
        return False
    if message.text not in Cards:
       return False
    if message.text not in player_cards[message.from_user.id]:
        bot.reply_to(message,"У вас нет такой карты.")  
        return False
    if (len(kycha[message.chat.id])!=0) and (message.text[1] not in kycha[message.chat.id]) and (message.text[1] not in kycha_defence[message.chat.id]):
        bot.reply_to(message,"Вы не можете добавлять карту которой нет на столе")
        return False
    if (0==player_cards[player_defender[message.chat.id].id]):
        bot.reply_to(message,"Больше карт добавлять нельзя!")
        return False
    return True
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")  



def low(a,chat_id):
 try:
    a=a-1
    if (a==0):
        return players_in_game[chat_id] 
    else: 
        return a
 except Exception as e:
     bot.send_message(chat_id,"Случилась какая-то ошибка.")          
        
"""Функция выбирает козырь"""
def Choze_cozur(message):
 try:  
    choice=["♦","♣","♥","♠"]
    Cozur[message.chat.id]=random.choice(choice)
    bot.send_message(message.chat.id,f"{Cozur[message.chat.id]} - козырь.")
 except Exception as e:
     bot.send_message(message.chat.id,"Случилась какая-то ошибка.")    

bot.polling()    

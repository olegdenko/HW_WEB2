from pathlib import Path
import os
import sys
import platform  # для clearscrean()
from RecordBook import AddressBook, Record, Name, Phone, Email, Birthday, Address, PhoneException, BirthdayException, EmailException
from RecordBook import AbstractUI, ConsoleUI
from clean import sort_main
from note_book import NoteBook, NoteRecord, Note, Tag
from datetime import datetime
import re
from logger import get_logger

from rich import print
from rich import box
from rich.table import Table
from rich.console import Console

# COMMANDS_WITH_PARAMETERS = ["add", "phone", "add phone",
#                             "show book", "birthday", "search",
#                             "close", "exit", "good bye",
#                             "show all", "remove", "change", "add email", "add address", "add birthday",
#                             "note add", "note change", "note del", "note sort",
#                             "note find", "note show", "sort"]
# COMMANDS_WITHOUT_PARAMETERS = [
#     "hello", "cls", "help", "help sort", "help note", "help contact"]

# Получаем абсолютный путь к запущенной программе
#absolute_path = os.path.abspath(sys.argv[0])
#path_book = Path(sys.path[0]).joinpath("data_12.bin")
#path_note = Path(sys.path[0]).joinpath("n_book.json")a
path_book = "data_12.bin"
path_note = "n_book.json"

book = AddressBook()
note_book = NoteBook()
ui = ConsoleUI(book)

# Головна функція роботи CLI(Command Line Interface - консольного скрипту) 


def main():
    note_book.load_data(path_note)
    clear_screen("")
    print("[bold white]CLI version 12.0[/bold white]")
    print("[white]Run >> [/white][bold red]help[/bold red] - list of the commands")
    load_phoneDB(path_book)

    while True:      
        cmd = ui.run()  # Запускаємо інтерфейс і отримуємо введену команду
        logger = get_logger(__name__)
        # 2. Виконуємо розбір командної строки
        cmd, prm = parcer_commands(cmd)

        # 3. Отримуємо handler_functions тобто ДІЮ
        if cmd:
            handler = get_handler(cmd)
        else:
            logger.error("Command was not recognized")
            # print("Command was not recognized")
            continue

        if cmd in ["add", "phone", "add phone",
                   "show book", "birthday", "search",
                   "close", "exit", "good bye",
                   "show all", "hello", "cls", "help", "help sort", "help note",
                    "help contact", "remove", "change", "add email", "add address", "add birthday",
                   "note add", "note change", "note del",
                   "note find", "note show", "note sort", "sort"]:
            result = handler(prm)
        elif cmd in ["save", "load"]:
            result = handler(path_book)

        save_phoneDB(path_book)

        # 4. Завершення роботи програми
        if result == "Good bye!":
            print("Good bye!")
            break

#------------------------------------------------------------------
            
# Декоратор для Обробки командної строки
def input_error(func):
    logger = get_logger(__name__)
    def inner(prm):
        try:
            result = func(prm) # handler()
            if not result == "Good bye!": 
                print(result)      # ПЕЧАТЬ всіх Message від всіх функцій обробників
            else: return result   
        
        # Обробка виключних ситуацій
        except BirthdayException as e:
            print(e)
        except PhoneException as e:
            print(e)
        except EmailException as e:
            print(e)
        except FileNotFoundError:    # Файл бази даних Відсутній
            print("The database isn't found")
        except ValueError:
            print("Incorect data or unsupported format while writing to the file")
        except KeyError:
            print("Record isn't in the database")
        except KeyboardInterrupt:
            func_exit(_)
        except TypeError:
            logger.error("Incorrect data")
    return inner


# Повертає адресу функції, що обробляє команду користувача
def get_handler(operator):
    return OPERATIONS[operator]    


#=========================================================
# Блок функцій для роботи з нотатками
#=========================================================
# >> note add <текст нотатки будь-якої довжини> <teg-ключове слово> 
# example >> note add My first note in this bot. #Note
#=========================================================
@input_error
def note_add(args):
    if args.rfind("#"):
        n = args.rfind("#")  
    key = str(datetime.now().replace(microsecond=0).timestamp())
    note = Note(args[:n].strip())
    tag = Tag(args[n:]) 
    record = NoteRecord(key, note, tag)
    return note_book.add_record(record)


#=========================================================

# >> note del <key-ідентифікатор запису>
# example >> note del 1691245959.0
#=========================================================
@input_error
def note_del(args):
    key = args.strip()
    rec : NoteRecord = note_book.get(key)
    try:
        return note_book.del_record(rec)
    except KeyError:
        return f"Record {key} does not exist."
            

#=========================================================
# >> note change <key-record> <New notes> <tag>
# example >> note change 1691245959.0 My new notes. #Tag 
#=========================================================
@input_error
def note_change(args):
    n = args.find(" ")
    key = args[:n]    
    m = args.rfind("#")
    if m == -1: 
        note = Note(args[n+1:])
        tag = None
    if len(args[n:m]) == 1: 
        note = None
        tag = Tag(args[m:])
    else:
        note = Note(args[n+1:m])
        tag = Tag(args[m:])
    rec : NoteRecord = note_book.get(key)
    if rec:
        return rec.change_note(rec.note.value, note if note else rec.note.value, tag if tag else rec.tag.value)
    else:
        return f"Record does not exist"
    

#=========================================================
# >> note find <fragment>
# Фрагмент має бути однією фразою без пробілів
# example >> note find word
#=========================================================
@input_error
def note_find(args):
    return note_book.find_note(args)


#=========================================================
# >> note show <int: необов'язковий аргумент кількості рядків>
# Передається необов'язковий аргумент кількості рядків 
# example >> note show /15
#=========================================================
@input_error
def note_show(args):
    if len(note_book.data) == 0: return f"The database is empty"
    if args.startswith("/") and args[1:].isdigit():
        args = int(args[1:])
    else:
        args = 5    
    for page, rec in enumerate(note_book.iterator(args), 1):
        print(f"Page {page}\n")
        for item in rec:
            print(f"{item}")
        input("\nPress enter for next page")
    return ""


#=========================================================
# >> note sort
# Сортування нотаток по тегу
# example >> note sort
#=========================================================
@input_error
def note_sort(args):    
    result = []
    for rec in note_book.values():
        line = f"{rec.tag}  {rec.note}  {rec.key}"
        result.append(line)
    result.sort()
    count = 0
    for item in result:
        print(item)
        count += 1
        if count == 5:
            input("\nFor next page press enter\n")
            count = 0
    return ""


#=========================================================
# >> add ...  DONE
# По этой команде бот сохраняет в памяти (в словаре например) новый контакт. 
# Вместо ... пользователь вводит ИМЯ и НОМЕР телефона, обязательно через пробел.
# example >> add Mike 02.10.1990 +380504995876
#=========================================================
@input_error
def func_add_rec(prm):
    args = prm.split(" ")
    if not prm.partition(" ")[0].capitalize() in book.keys():
        name = Name(args[0].capitalize())
        phone = Phone(args[1] if len(args) >= 2 else "None")
        email = Email(args[2] if len(args) >= 3 else "None")
        birthday = Birthday(args[3] if len(args) >= 4 else "None")
        address = Address(' '.join(args[4:]) if len(args) >= 5 else "None")
        rec = Record(name, phone, email, birthday, address) 
        return book.add_record(rec)
    else: return "The person is already in database"

#=========================================================
# >> add phone    Done
# функція розширює новим телефоном існуючий запис особи Mike   
# >> add phone Mike +380509998877
#=========================================================
@input_error
def add_phone(prm):
    args = prm.split(" ")
    count_prm = get_count_prm(prm)
    if prm and (count_prm >= 2):
        if args[0].capitalize() in book.keys():
            rec = book[args[0].capitalize()]
            if book[args[0].capitalize()].phones[0].value == "None": 
                book[args[0].capitalize()].phones.clear()
            return rec.add_phone(Phone(args[1]))
        else: return f"The person [bold red]{args[0].capitalize()}[/bold red] isn't in a database"
    else: return f"Expected 2 arguments, but {count_prm} was given.\nHer's an example >> add phone Mike +380509998877"

#=========================================================
# >> add ...  DONE
# По этой команде бот сохраняет в памяти контакта Email. 
# Вместо ... пользователь вводит ИМЯ и Email, обязательно через пробел.
# example >> add email Mike mike.djonsen@gmail.com
#=========================================================
@input_error 
def add_email(prm) -> str:
    args = prm.split(" ")
    rec = book[args[0].capitalize()]
    email = Email(args[1])
    rec.add_email(email)
    return f'The contact "{args[0].capitalize()}" was updated with new email: {rec.email}'

#=========================================================
# >> add ...  DONE
# По этой команде бот сохраняет в памяти контакта Address. 
# Вместо ... пользователь вводит ИМЯ и address, адресу можна вводити як завгодно.
# example >> add address Mike Stepan Banderi Avenue, 11A
#=========================================================
@input_error 
def add_address(prm) -> str:
    args = prm.split(" ")
    rec = book[args[0].capitalize()]
    rec.add_address(args[1:])
    return f'The contact "{args[0].capitalize()}" was updated with new address: {rec.address}'

#=========================================================
# >> add ...  DONE
# По этой команде бот сохраняет в памяти контакта birthday. 
# Вместо ... пользователь вводит ИМЯ и birthday, обязательно через пробел.
# example >> add birthday 31.12.2000
#=========================================================
@input_error
def add_birthday(prm) -> str:
    args = prm.split(" ")
    rec = book[args[0].capitalize()]
    rec.add_to_birthday(Birthday(args[1])) 
    return f"Date of birth {args[0].capitalize()}, recorded"

#=========================================================
# >> show all         Done
# По этой команде бот выводит все сохраненные контакты 
# с номерами телефонов в консоль. 
#=========================================================
@input_error
def func_all_phone(_)->str:
    if len(book.data) == 0: 
        return "The database is empty"
    else: 
        table = Table(box=box.DOUBLE)
        table.add_column("Name", justify="center", style="cyan", no_wrap=True)
        table.add_column("Phone number", justify="center", style="green", no_wrap=True)
        table.add_column("Email", justify="center", style="red", no_wrap=True)
        table.add_column("Birthday", justify="center", style="yellow", no_wrap=True)
        table.add_column("Address", justify="center", style="red", no_wrap=True)

        console = Console()
        _ = [table.add_row(str(record.name.value), str(', '.join(map(lambda phone: phone.value, record.phones))), str(record.email.value), str(record.birthday.value), str(record.address.value)) for record in book.data.values()]
        console.print(table)
        return ""   

#=========================================================
# >> show book /N
# Команда "show book" друкує книгу контактів по N записів
# де N - це кількість записів на одній сторінці
#=========================================================
@input_error
def func_book_pages(prm):
    # Итерируемся по адресной книге и выводим представление для каждой записи
    n = int(re.sub("\D", "", prm))
    n_page = 0
    for batch in book._record_generator(N=n):
        n_page += 1
        print(f"{'='*14} Page # [bold red]{n_page}[/bold red] {'='*16}")
        for record in batch:
            print("\n".join([f"{record.name.value}|{record.birthday.value}|{', '.join(map(lambda phone: phone.value, record.phones))}"]))
        print("="*40)    
        print("Press [bold red]Enter [/bold red]", end="")
        input("to continue next page...")
    return f"End of the book" 

#=========================================================
# >> "good bye", "close", "exit"
# По любой из этих команд бот завершает свою роботу 
# после того, как выведет в консоль "Good bye!".
#=========================================================
@input_error
def func_exit(_):
    note_book.save_data(path_note)
    return "Good bye!"


#=========================================================
# >> hello
# Отвечает в консоль "How can I help you?"
#=========================================================
@input_error
def func_greeting(_):
    return "How can I help you?"


#=========================================================
# >> phone ... Done
# По этой команде бот выводит в консоль номер телефона для указанного контакта.
# Вместо ... пользователь вводит Имя контакта, чей номер нужно показать.
# >> phone Ben
#=========================================================
@input_error
def func_phone(prm):
    prm = prm.split(" ")
    if prm[0] == "": return f'Missed "Name" of the person'
    name = prm[0].lower().capitalize()
    if name in book.keys():   
        if prm: return ", ".join([phone.value for phone in book[name].phones])
        else: return f"Expected 1 argument, but 0 was given.\nHer's an example >> phone Name"
    else:
        return f"The {name} isn't in the database"  

#=========================================================
# >> birthday    Done
# функція повертає кількість днів до Дня Народження особи    
# Example >> birthday Mike
# Example >> birthday /365
#=========================================================
@input_error
def func_get_day_birthday(prm):
    # порахуємо кількість параметрів
    count_prm = get_count_prm(prm)
    prm = prm.split(" ")
    if prm[0] == "": return f'Missed [bold red]Name[/bold red] of the person'
        
    if prm and (count_prm >= 1):
        if "/" in prm[0]:   # Example >> birthday /365
            count_day = int(re.sub("\/", "",prm[0]))
            if not count_day > 0: return f"Enter the number of days greater than zero"
            return book.get_list_birthday(count_day)
            
        else: # Example >> birthday Mike
            name = prm[0].lower().capitalize()
            if name in book.keys():
                if book[name].birthday.value == "None": return f"No [bold red]Birthday[/bold red] for {name}"
                return book[name].days_to_birthday() 
            else: return f"The [bold red]{name}[/bold red] isn't in a database"
    else: return f"Expected 1 arguments, but {count_prm} was given.\nHer's an example >> birthday Mike"

# ======================================================================================================
# =========================================[ remove ]===================================================
# ======================================================================================================

@input_error
def remove(prm:str):
    args = prm.split(" ")
    rec = book[args[1].capitalize()]
    if args[0].lower() == "name":
        if book[args[1].capitalize()].name.value == args[1].capitalize():
            del book[args[1].capitalize()]
            return f"{args[1].capitalize()} is deleted from the contact book"
        
    elif args[0].lower() == "phone":
        num = rec.remove_phone(Phone(args[2]))
        if num == "This contact has no phone numbers saved": return num
        return f"Phone number {args[1].capitalize()} : {num} - Deleted"

    elif args[0].lower() == "email":
        rec.remove_email()
        return f"{args[1].capitalize()}'s email has been removed from the contact list"

    elif args[0].lower() == "birthday":
        rec.remove_birthday()
        return f"{args[1].capitalize()}'s birthday has been removed from the contact list"

    elif args[0].lower() == "address":
        rec.remove_address()
        return f'address removed from {args[1].capitalize()}\'s profile'
    else:
        return "якийсь Error remove"
    
# ======================================================================================================
# =========================================[ change ]===================================================
# ======================================================================================================

@input_error
def change(prm:str):
    args = prm.split(" ")
    if args[1].capitalize() in book.keys():
        rec = book[args[1].capitalize()]
        if args[0].lower() == "name":
            if not args[2].capitalize() is book.data.keys():
                rec = book[args[1].capitalize()]
                rec.change_name(Name(args[1].capitalize()), Name(args[2].capitalize()))
                book.data.pop(args[1].capitalize())
                book[args[2].capitalize()] = rec
                return f"Contact name {args[1].capitalize()}`s changed to {args[2].capitalize()}'s"
            else: return f"Contact with the name {args[2].capitalize()}'s already exists"

        elif args[0].lower() == "phone":
            if rec: return rec.change_phone(Phone(args[2]), Phone(args[3]))
            return f"Contact wit name {args[1].capitalize()} doesn`t exist."

        elif args[0].lower() == "email":
            rec.change_email(Email(args[2]))
            return f"Email is profile {args[1].capitalize()}'s has been changed"

        elif args[0].lower() == "birthday":
            rec.change_birthday(Birthday(args[2]))
            return f"Birthday profile {args[1].capitalize()}'s has been changed"

        elif args[0].lower() == "address":
            rec.change_address(Address(args[2:]))
            return f'The contact "{args[1].capitalize()}" was updated with new address: {rec.address}'
        else:
            return "якийсь Error change"
    else: raise BirthdayException(f"Name {args[1].capitalize()} isn't in datebase")

#=========================================================
# >> search    Done
# функція виконує пошук інформації у довідковій книзі
#              example >> search Mike
#                      >> search 38073
#                      >> search none
#=========================================================
@input_error
def func_search(prm):
    count_prm = get_count_prm(prm)
    
    prm = prm.split(" ")
    if prm[0] == "": return f"[bold yellow]Enter search information[/bold yellow]"
    lst_result = []
    rec_str = ""
    if prm and (count_prm >= 1):
        for rec in book.values():
            rec_str = str(rec)
            if prm[0].lower() in rec_str.lower():
                lst_result.append(rec_str)
                
        s = "\n".join([rec for rec in lst_result])
        if lst_result: return f"[bold green]Search results:[/bold green]\n{s}"
        else: return f"No matches found for {prm[0]}"
    else: return f"Expected 1 arguments, but {count_prm} was given.\nHer's an example >> search Mike"
    
    
# =========================================================
# >> sort    Done
# функція викликає модул cleanfolder виконує сортування файлів у вказаній папці
#              example >> sort Testfolder
#                      >> sort C://Testfolder/testfolder
#                      >> sort .Testfolder/testfolder
# =========================================================
@input_error
def func_sort(prm):
    if prm[0] == "":
        return f"[bold yellow]Enter path[/bold yellow]"
    return sort_main(prm)
    # return f"[bold green]Sort {prm} finished:[/bold green]"
    
    
#=========================================================
# Функція читає базу даних з файлу - ОК
#========================================================= 
@input_error
def load_phoneDB(path):
    return book.load_database(path)
    #return book.load_database(book, path)


#=========================================================
# Функція виконує збереження бази даних у файл *.csv - OK
#========================================================= 
@input_error
def save_phoneDB(path):
    return book.save_database(path)
    
    
#=========================================================
# Функція виконує парсер команд та відповідних параметрів
#=========================================================
def parcer_commands(cmd_line):
    lst, tmp, cmd, prm  = [[], [], "", ""]
    
    if cmd_line:
        tmp = cmd_line.split()
        
        # перевіремо ПОДВІЙНУ команду
        if len(tmp) > 1 and f"{tmp[0]} {tmp[1]}".lower() in COMMANDS: #  add Mike 4589 94508
            cmd = f"{tmp[0]} {tmp[1]}".lower()
            prm = cmd_line.partition(cmd)[2].strip()
            
        # перевіремо ОДИНАРНУ команду
        elif tmp[0].lower() in COMMANDS:
            cmd = tmp[0].lower()
            prm = cmd_line.partition(" ")[2]
    return cmd, prm


@input_error
def func_help(arg):
    help_navigation = """[bold red]help all[/bold red] - виводить всю довідку на екран
[bold red]help contact[/bold red] - довідка по командам адресної книги
[bold red]help note[/bold red] - довідка по командам нотаток
[bold red]help sort[/bold red] - довідка по командам сортувальника
[bold red]hello[/bold red] - вітання
[bold red]good bye, close, exit[/bold red] - завершення програми
[bold red]load[/bold red] - завантаження інформації про користувачів із файлу
[bold red]save[/bold red] - збереження інформації про користувачів у файл
[bold red]cls[/bold red] - очищення екрану від інформації"""
    contact = """[bold red]show all[/bold red] - друкування всієї наявної інформації про користувачів
[bold red]show book /N[/bold red]  - друкування інформації посторінково, де [bold red]N[/bold red] - кількість записів на 1 сторінку
[bold red]add[/bold red] - додавання користувача до бази даних. 
      example >> [bold blue]add Mike[/bold blue]
              >> [bold blue]add Mike <phone> <email> <birthday> <address>[/bold blue]
              >> [bold blue]add Mike 380504995876 mike@mail.com 12.12.1970 Poltava,Soborna.str,1[/bold blue]              
[bold red]phone[/bold red] - повертає перелік телефонів для особи
      example >> [bold blue]phone Mike[/bold blue]
[bold red]add phone[/bold red] - додавання телефону для користувача
      example >> [bold blue]add phone Mike +380504995876[/bold blue]
[bold red]change phone[/bold red] - зміна номеру телефону для користувача
      Формат запису телефону: [bold green]+38ХХХ ХХХ ХХ ХХ[/bold green]
      example >> [bold blue]change phone Mike +380504995876 +380665554433[/bold blue]
[bold red]del phone[/bold red] - видаляє телефон для особи. 
      example >> [bold blue]del phone Mike +380509998877[/bold blue]
[bold red]birthday[/bold red] - повертає кількість днів до Дня народження, або список людей, чей день народження очікується.
      example >> [bold blue]birthday Mike[/bold blue]
      example >> [bold blue]birthday /<число днів>[/bold blue]
[bold red]change birthday[/bold red] - змінює/додає Дату народження для особи
      example >> [bold blue]change birthday Mike 02.03.1990[/bold blue]
[bold red]search[/bold red] - виконує пошук інформації по довідковій книзі
      example >> [bold blue]search Mike[/bold blue]"""
    note = """[bold red]note add[/bold red] - додає нотатку з тегом у записник нотаток
      example >> [bold blue]note add My first note #Tag[/bold blue]
[bold red]note del[/bold red] - видаляє нотатку за ключем із записника нотаток
      example >> [bold blue]note del 1691245959.0[/bold blue]
[bold red]note change[/bold red] - змінює нотатку з тегом за ключем у записнику нотаток
      example >> [bold blue]note change 1691245959.0 My first note #Tag[/bold blue]
[bold red]note find[/bold red] - здійснює пошук за фрагментом у записнику нотаток
      example >> [bold blue]note find <fragment>[/bold blue]
[bold red]note show[/bold red] - здійснює посторінковий вивід всіх нотаток
      example >> [bold blue]note show /10[/bold blue]
[bold red]note sort[/bold red] - здійснює сортування записів нотаток за тегами
      example >> [bold blue]note sort /10[/bold blue]"""
    sort = """[bold red]sort[/bold red] - виконує сортування файлів в указаній папці
      example >> [bold blue]sort folder_name <Path_to_folder>[/bold blue]"""
    
    if arg == "contact":
        return contact
    if arg == "note":
        return note
    if arg == "sort":
        return sort
    if arg == "all":
        return help_navigation + contact + note + sort

    return help_navigation
    
@input_error
def clear_screen(_):
    os_name = platform.system().lower()
    
    if os_name == 'windows':
        os.system('cls')
    elif os_name == 'linux' or os_name == 'darwin':
        os.system('clear')
    return ""


# Рахує та повертає кількість параметрів
def get_count_prm(prm: list):
    if len(prm) > 0: 
        count_prm = prm.count(" ", 0, -1) + 1
    else: count_prm = 0
    return count_prm


COMMANDS = ["good bye", "close", "exit",
            "hello", "add", "phone", "show all", "save", "load", 
            "cls", "add phone", "show book", # "change phone", "del phone"
            "birthday", "help", "search", # "change birthday"
            "note add", "note del", "note change", "note find", "note show", "note sort", "sort", "remove", "change", "add email", "add address", "add birthday"]

OPERATIONS = {"good bye": func_exit, "close": func_exit, "exit": func_exit,
              "hello": func_greeting, 
              "add": func_add_rec,
              "phone": func_phone, 
              "show all": func_all_phone,
              "save": save_phoneDB,
              "load": load_phoneDB,
              "cls": clear_screen,
              "show book": func_book_pages,
              "birthday": func_get_day_birthday,
              "help": func_help,
              "add phone": add_phone,
              "add email" : add_email,
              "add address" : add_address,
              "add birthday" : add_birthday,
              "remove" : remove,
              "change" : change,
              "search": func_search,
              "note add": note_add,
              "note del": note_del,
              "note change": note_change,
              "note find": note_find,
              "note show": note_show,
              "note sort": note_sort, 
              "sort": func_sort}

if __name__ == "__main__":
    main()
  

from cryptography.fernet import Fernet

try:
    from mariadb import connect
except ImportError:
    from mysql.connector import connect
    print('mariadb.connect is not available. \033[31mYou might run into issues\033[0m')

mydb = None
encryption_enabled = True
key_location = 'keyfile.txt'
name_len = 512  # length for each name, surname and patronic
phone_len = 11  # length for phone number in format +nnnnnnnnnn
login_len = 255  # length for matrix login in format @login:server.school.ru

key = ''
if encryption_enabled:
    # admins are responsible for key rotation and management
    with open(key_location, 'r') as file:
        key = file.readlines()[0].strip()

students_db = 'Students'
students_data = 'Students_Data'
students_rooms = 'Students_Rooms'

data_columns = [
    "ID",
    "First_Name",
    "Second_Name",
    "Third_Name",
    "Grade_Didgit",
    "Grade_Letter",
    "Phone_Number",
    "Matrix_Login",
    "Account_Type",
]

room_columns = [
    "ID",
    "Room_ID",
    "Grade_Didgits",
    "Grade_Letter",
    "Room_Type"
]


class RoomType:
    STUDENTS_TEACHER = 'students_teacher'
    STUDENTS = 'students'
    PARENTS_TEACHER = 'parents_teacher'
    PARENTS = 'parents'


# Creating table
def init_db(user, password, host='localhost'):
    global mydb, name_len, phone_len, login_len

    mydb = connect(
        host = host,
        user = user,
        password = password,
    )

    char = 'CHARACTER SET utf8'

    if encryption_enabled:
        # TODO: observe how length grows and calculate resulting length with 10% more space
        # Write logic behind the algorithm there
        # Do it in a function
        name_len = name_len * 6
        phone_len = max(phone_len * 3, 120)
        login_len = login_len * 3
    cursor = mydb.cursor()
    cursor.execute(f"create database if not exists {students_db};")
    cursor.execute(f"use {students_db};")
    cursor.execute(f"""create table if not exists {students_data} (ID INT PRIMARY key NOT NULL AUTO_INCREMENT,
                   First_Name   VARCHAR({name_len}) {char},
                   Second_Name  VARCHAR({name_len}) {char},
                   Third_Name   VARCHAR({name_len}) {char},
                   Grade_Didgit VARCHAR(100),
                   Grade_Letter VARCHAR(100) {char},
                   Phone_Number VARCHAR({phone_len}),
                   Matrix_Login VARCHAR({login_len}) {char},
                   Account_Type VARCHAR(100) {char});""")
    cursor.execute(f"create table if not exists {students_rooms} (ID INT PRIMARY key NOT NULL AUTO_INCREMENT, Room_ID VARCHAR(100) CHARACTER SET utf8, Grade_Didgits VARCHAR(23) CHARACTER SET utf8, Grade_Letter VARCHAR(100) CHARACTER SET utf8, Room_Type VARCHAR(100) CHARACTER SET utf8);")
    cursor.close()


def drop_all_databases(user, password, host='localhost'):
    global mydb

    mydb = connect(
        host = host,
        user = user,
        password = password,
    )
    cursor = mydb.cursor()
    cursor.execute(f"drop database {students_db};")
    cursor.close()


def add_room(Room_ID, Grade_didgits, Grade_letters, Room_type: RoomType):
    cursor = mydb.cursor()
    sql_val = (Room_ID, Grade_didgits, Grade_letters, Room_type)
    sql_code = f"insert into {students_rooms} (Room_ID, Grade_Didgits, Grade_Letter, Room_Type) values (%s, %s, %s, %s);"
    cursor.execute(f"use {students_db};")
    cursor.execute(sql_code, sql_val)
    mydb.commit()
    sql_code = f"select ID from {students_rooms} sd where Room_ID = %s;"
    sql_val = Room_ID,
    cursor.execute(sql_code, sql_val)
    result = cursor.fetchone()
    cursor.close()
    return result[0]


def get_column_info(column):
    cursor = mydb.cursor()
    sql_code = f"select {column} from {students_data};"
    cursor.execute(sql_code)
    result = cursor.fetchall()
    cursor.close()

    return [decrypt(i[0], key) for i in result]


def set_account_type(ID, account_type):
    cursor = mydb.cursor()
    sql_code = f"update {students_data} set Account_Type = %s where ID = %s;"
    sql_values = (account_type, ID)
    cursor.execute(f"use {students_data};")
    cursor.execute(sql_code, sql_values)
    mydb.commit()
    cursor.close()


def register(name, surname, patronic, Person_Grade_didgit, Person_Grade_letter, Person_Phone_Number, Matrix_Login, Person_Access):
    if '@' not in Matrix_Login:
        raise Exception('Matrix_Login is invalid! Use the following format: @user:matrix.example.com')

    cursor = mydb.cursor()
    sql_val = [encrypt(str(i), key) for i in (name, surname, patronic, Person_Grade_letter, Person_Grade_didgit, Person_Phone_Number, Matrix_Login, Person_Access)]
    sql_code = f"insert into {students_data} (First_Name, Second_Name, Third_Name, Grade_Letter, Grade_Didgit, Phone_Number, Matrix_Login, Account_Type) values (%s, %s, %s, %s, %s, %s, %s, %s)"

    cursor.execute(f"use {students_db};")
    cursor.execute(sql_code, sql_val)
    mydb.commit()
    cursor.close()


def get_info_rooms(room_id, columns=None):
    '''Returns all info from database with rooms by database ID'''
    if columns is None:
        columns = room_columns
    return _get_info_from_db(students_rooms, room_id, columns, decrypt=False)


def get_info(Person_ID, columns=None):
    '''Returns all info from database with users by database ID'''
    if columns is None:
        columns = data_columns
    return _get_info_from_db(students_data, Person_ID, columns)


def get_students():
    return _get_db(students_data, data_columns)


def get_rooms():
    return _get_db(students_rooms, room_columns)


# Column names is a list/tuple of prefered columns
def _get_info_from_db(db, ID, column_names=None, decrypt=True) -> dict:
    """This is an internal function to get specific columns from specific database by ID
    This function does not care about your errors/mistakes
    Use it carefully
    """

    cursor = mydb.cursor()
    cursor.execute(f"use {students_db};")

    # Get every value by default
    query = '*'
    if column_names is not None:
        query = ', '.join(column_names)
    sql_code = f"select {query} from {db} sd where ID = %s;"
    sql_val = (ID,)
    cursor.execute(sql_code, sql_val)
    rows = cursor.fetchone()
    res = {column_names[i]: v for i, v in enumerate(rows)}
    if db == f'{students_data}':
        return decrypt_table(res, key)
    return res


def _get_db(db, column_names) -> dict:
    """This is an internal function to get all columns from specific database
    This function does not care about your errors/mistakes
    Use it carefully
    """

    cursor = mydb.cursor()
    cursor.execute(f"use {students_db};")

    sql_code = f"select * from {db} sd;"
    cursor.execute(sql_code)
    rows = cursor.fetchall()
    res = [{column_names[i]: v for i, v in enumerate(row)} for row in rows]
    nres = []
    if db == f'{students_data}':
        for v in res:
            nres.append(decrypt_table(v, key))
        return nres
    return res


def _get_last_id(db_name) -> int:
    cursor = mydb.cursor()
    cursor.execute(f"use {students_db};")
    query = f"select count(ID) from {db_name} sd;"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0]


def _id_range(db_name) -> range:
    return range(1, _get_last_id(db_name) + 1)


# for students data
def get_id_by_value(Column, Column_value) -> int:
    Column_value = encrypt(Column_value, key)
    if Column not in data_columns:
        raise Exception(f"There is no such column: {Column}")
    cursor = mydb.cursor()
    cursor.execute(f"use {students_db};")
    sql_code = f"select ID from {students_data} sd where %s = %s;"
    sql_val = (Column, Column_value)
    cursor.execute(sql_code, sql_val)
    result = cursor.fetchone()
    return decrypt(result[0], key)


def get_last_id() -> int:
    return _get_last_id(students_data)


def get_last_id_room() -> int:
    return _get_last_id(students_rooms)


def id_range_students():
    return _id_range(students_data)


def id_range_rooms() -> range:
    return _id_range(students_rooms)


def encrypt(data: str, key) -> str:
    if encryption_enabled:
        return Fernet(key).encrypt(data.encode())
    return data


def decrypt(token, key) -> str:
    if encryption_enabled:
        return Fernet(key).decrypt(token).decode()
    return token


def decrypt_table(table: dict, key) -> dict:
    if not encryption_enabled:
        return table
    for k, v in table.items():
        if k == "ID":
            continue
        table[k] = decrypt(v, key)
    return table
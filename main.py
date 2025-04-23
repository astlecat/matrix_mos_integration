#!/usr/bin/env python

import requests
from argparse import ArgumentParser
from copy import deepcopy
from json import dumps, load, dump
from os.path import exists
from os import replace
from sys import stderr
from time import sleep
from getpass import getpass

import db


class ConfigManager:
    def __init__(self, file=None):

        self._url_components = ("protocol", "domain", "port")
        # default config
        self.config = {
            "protocol": "https",
            "db_user": "school",
            # "port": "443",
            "login": "schoolbot",
            "cache_location": "cache.json",
        }

        if file is not None:
            self.loadConfig(file)

        self.cache = {}
        if exists(self.get("cache_location")):
            self.loadCache(self.get("cache_location"))

    def set_cache(self, key, value):
        self.cache[key] = value
        verbose(self.get("cache_location"))

        with open(self.get("cache_location"), 'w') as file:
            dump(self.cache, file, ensure_ascii=False)

    def get_cache(self, key):
        return self.cache.get(key)

    def ask(question, default: bool | None = True) -> bool | KeyboardInterrupt:
        NORMAL = '\033[0m'
        BOLD = '\033[1m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        variants = 'Y/n'
        if default is False:
            variants = 'y/N'
        elif default is None:
            variants = 'y/n'
        ask_prompt = f'{question} [{variants}] '

        if needs_color():
            ask_prompt = f'{BOLD}{question} {OKCYAN}[{variants}]{NORMAL} '

        # if '--noconfirm' in sys.argv:
        #     print(ask_prompt)
        #     return bool(default)
        ans = input(ask_prompt).strip().lower()
        if ans == '' and default is not None:
            return default
        elif ans == 'y':
            return True
        elif ans == 'n':
            return False

    def get(self, key, _type: bool | int | str = str, interactive=True):
        res = self.config.get(key)

        if res is not None or not interactive:
            return res

        verbose(f'Key not found: {key}, using interactive configuration')
        if key == 'url':
            for component in self._url_components:
                self.get(component)
            verbose(f"Resulting url: {self.get('url')}")
            return self.get('url')

        if _type is bool:
            value = self.ask(f'Choose a value for "{key}"')
        elif key in ('password'):
            value = getpass('Enter a password: ')
        else:
            value = _type(input(f'Enter a value ({_type}) for "{key}": '))

        self.set(key, value)
        return value

    def set(self, key, value):
        self.config[key] = value

        if key in self._url_components:
            self.__set_url()

    def __set_url(self):
        protocol = self.get("protocol")
        domain = self.get("domain")
        port = self.get("port", interactive=False)
        self.config["url"] = f'{protocol}://{domain}'
        if port not in (None, ''):
            self.config["url"] += f':{port}'

    def setConfig(self, _config: dict):
        config = deepcopy(_config)
        for key, value in config.items():
            self.config[key] = value

        self.__set_url()

    def _filtered_config(self, _config: dict) -> dict:
        """Use this function to show the config to the user without exposing passwords"""
        res = {}
        for k, v in _config.items():
            if 'password' in k:
                v = '**********'
            res[k] = v
        return res

    def loadConfig(self, file: str):
        if not exists(file):
            raise FileNotFoundError('Where is yr config file?')

        with open(file, 'r') as json_file:
            config = load(json_file)
            verbose(f'Loaded config: {self._filtered_config(config)}')
            self.setConfig(config)

    def loadCache(self, file: str):
        if not exists(file):
            raise FileNotFoundError('Where is cache file?')

        with open(file, 'r') as json_file:
            self.cache = load(json_file)
            # verbose(f'Loaded cache: {self.cache}')

    def authorization(self):
        """Returns authorization headers"""
        return {"Authorization": f"Bearer {self.get('token')}"}


def needs_color():
    option = manager.get('color')
    if option == 'always':
        return True

    if option == 'never':
        return False

    if __import__('sys').stdout.isatty():
        return True
    return False


def key(text):
    if needs_color():
        return f'\033[3;1m{text}\033[0m'
    return text


def error(text):
    if needs_color():
        return f'\033[31;1m{text}\033[0m'
    return text


def bold(text: str):
    if needs_color():
        return f'\033[1m{text}\033[0m'
    return text


def italic(text: str):
    if needs_color():
        return f'\033[3m{text}\033[0m'
    return text


def log(*text, **kwargs):
    if not manager.get('quiet'):
        print(*text, **kwargs, file=stderr)


def verbose(*text, **kwargs):
    if manager.get('verbose'):
        print(*text, **kwargs, file=stderr)


def log_res(request_result: requests.Request):
    code = request_result.status_code
    json_response = jsonify(request_result.json())
    if code != 200:
        verbose(f'{key("Code:")} {code}')
    verbose(f'{key("Json:")} {json_response}')


def jsonify(data):
    return dumps(data, ensure_ascii=False, indent=4)


def fix_alias(alias: str):
    # This should be escaped
    return alias.replace('#', '%23')


def user(login: str):
    matrix_limit = 255
    postfix = f':{manager.get("domain")}'
    if len(postfix) + 1 >= matrix_limit:
        raise Exception(error('Your domain name is too long!\n'
                              f'Maximum length for login is {matrix_limit}'))

    end = matrix_limit - len(postfix) - 1
    truncated = login[:end]

    if end < len(login):
        verbose(error(f'Truncating username "{login}" ({len(login)} characters) '
                      f'to "{truncated}" ({len(truncated)} characters) '
                      f'in order to fit user id into {matrix_limit} characters'))
    return f'@{truncated}{postfix}'


def get_public_rooms():
    res = requests.get(f'{manager.get("url")}/_matrix/client/v3/publicRooms', headers=manager.authorization())
    log_res(res)

    res = res.json()
    return res["chunk"], res["total_room_count_estimate"]


def login(user: str, password: str, retry=True):
    parameters = {
        "type": "m.login.password",
        "user": user,
        "password": password,
        "device_id": "Python bot developed as a part of a school project",
    }
    while True:
        res = requests.post(f'{manager.get("url")}/_matrix/client/r0/login', json=parameters)

        log_res(res)
        response = res.json()
        if response.get("error") is None:
            return response
        if response.get("retry_after_ms") is not None:
            sleep(response.get("retry_after_ms") / 1000)
            continue
        raise Exception(error(f"Can't log in: {response}"))


def create_room(name: str, alias_name=None, topic='', preset="public_chat", retry=True):
    '''returns {"room_id": str, "alias": str, "short_alias": str}'''
    if alias_name is None:
        alias_name = name.title().replace(' ', '')

    if ":" in alias_name:

        raise Exception(error('":" is not permitted in the room alias name'))

    parameters = {
        "creation_content": {
            "m.federate": False,
            "creator": manager.get("user_id"),
        },
        "name": name,
        "preset": "public_chat",
        "room_alias_name": alias_name,
        "topic": topic,
    }
    proper_alias = f'#{alias_name}:{manager.get("domain")}'
    while True:
        res = requests.post(f'{manager.get("url")}/_matrix/client/v3/createRoom',
                            json=parameters, headers=manager.authorization())
        response = res.json()

        if res.status_code == 200:
            log(f'Created a room "{name}"')
            log_res(res)
            return {"id": response["room_id"], "alias": proper_alias, "short_alias": alias_name}
        if not retry:
            log_res(res)
            break

        if response["errcode"] == "M_LIMIT_EXCEEDED":
            seconds = response["retry_after_ms"] / 1000
            verbose(f'Waiting {seconds} seconds')
            sleep(seconds)
            continue
        elif response["errcode"] == "M_ROOM_IN_USE":
            return {"id": get_room_id(proper_alias), "alias": proper_alias, "short_alias": alias_name}

        log_res(res)
        print(error('^^^ Warning! We dont know what happened there!'))
    return {"id": None, "alias": proper_alias, "short_alias": alias_name}


def bot_create_room(name, grade_didgits, grade_letters, room_type: db.RoomType):
    room = create_room(name)
    db_id = db.add_room(room["id"], grade_didgits, grade_letters, room_type)
    room['db_id'] = db_id
    return room


def bot_get_all_members():
    members = []
    for room in db.get_rooms():
        room_id = room['Room_ID']
        room['Members'] = get_room_members(room_id)
        members.append(room)
    print(jsonify(members))
    return members


# https://spec.matrix.org/latest/client-server-api/#room-aliases
def get_room_id(alias: str):
    alias = fix_alias(alias)
    res = requests.get(f'{manager.get("url")}/_matrix/client/v3/directory/room/{alias}')

    if res.status_code != 200:
        log_res(res)
    return res.json()["room_id"]


# https://spec.matrix.org/latest/client-server-api/#room-aliases
def get_room_aliases(room_id: str):
    res = requests.get(f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/aliases',
                       headers=manager.authorization())
    response = res.json()

    if res.status_code != 200:
        log_res(res)
    return response["aliases"]


# https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3roomsroomidjoined_members
def get_room_members(room_id: str):
    if ':' not in room_id:
        print(error(f'Not a complete room_id: {room_id}'))
        return []
    res = requests.get(f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/joined_members',
                       headers=manager.authorization())
    response = res.json()

    if res.status_code != 200:
        log_res(res)
    return response["joined"]


# https://spec.matrix.org/latest/client-server-api/#joining-rooms
def join_room(room_id_or_alias: str):
    room_id_or_alias = fix_alias(room_id_or_alias)
    res = requests.post(
        f'{manager.get("url")}/_matrix/client/v3/join/{room_id_or_alias}',
        headers=manager.authorization()
    )
    if res.status_code != 200:
        log_res(res)
    else:
        verbose(f'Joined room {room_id_or_alias}')


# https://spec.matrix.org/latest/client-server-api/#leaving-rooms
def leave_room(room_id: str):
    res = requests.post(
        f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/leave',
        headers=manager.authorization()
    )
    if res.status_code != 200:
        log_res(res)
    verbose(f'Left room {room_id}')

# https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3roomsroomidstate
def get_room_state(room_id, state_key = None):
    res = requests.get(
        # f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/state/{state_key}/',
        f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/state',
        headers=manager.authorization()
    )

    response = res.json()
    if res.status_code != 200:
        log_res(res)

    if state_key is None:
        return response

    result = []
    for i in response:
        if i["type"] == state_key:
            result.append(i)
    return result


def get_user_power_levels(room_id):
    state = get_room_state(room_id, 'm.room.power_levels')[0]["content"]
    default = 0
    users = state["users"]
    if state.get("users_default") is None:
        verbose(f'users_default was not provided. Assuming {default}', state)
        default = state["users_default"]
    for user in get_room_members(room_id).keys():
        if users.get(user) is None:
            users[user] = default
    return users


# https://spec.matrix.org/latest/client-server-api/#mroompower_levels
def change_user_power_level(user_id, room_id, power_level: int = 50):
    parameters = get_room_state(room_id, 'm.room.power_levels')[0]["content"]
    # Setting the desired power level
    # If user_id isn't in the room, nothing bad happens
    parameters["users"][user_id] = power_level

    res = requests.put(
        f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels/',
        json=parameters, headers=manager.authorization()

    )
    if res.status_code != 200:
        verbose(error(f'An error occured while trying to change power level for {user_id} in {room_id} to {power_level}'))
        log_res(res)
    else:
        verbose(f'Changed {user_id} in {room_id} to {power_level}')
    return res



# https://spec.matrix.org/v1.12/client-server-api/#thirdparty_post_matrixclientv3roomsroomidinvite
def invite_user(user_id, room_id, reason=None):
    parameters = {
        "user_id": user_id
    }
    if reason is not None:
        parameters["reason"] = reason

    res = requests.post(
        f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/invite',
        json=parameters, headers=manager.authorization()
    )
    if res.status_code == 200:
        verbose(f'Invited {user_id} to {room_id}')
    elif res.status_code == 403 and 'already in the room' in res.json().get('error'):
        verbose(f'{user_id} is already in the room {room_id}')
    else:
        verbose(error(f'An error occured while trying to invite user {user_id} to room {room_id}'))
        log_res(res)
    return res


# https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3roomsroomidkick
def kick_user(user_id, room_id, reason=None):
    parameters = {
        "user_id": user_id
    }
    if reason is not None:
        parameters["reason"] = reason

    res = requests.post(
        f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/kick',
        json=parameters, headers=manager.authorization()
    )
    if res.status_code == 200:
        verbose(f'Kicked {user_id} from {room_id}')
    elif res.status_code == 403 and 'not in the room' in res.json().get('error'):
        verbose(f'{user_id} is not the room {room_id}')
    else:
        verbose(error(f'An error occured while trying to kick user {user_id} from room {room_id}'))
        log_res(res)
    return res


def generate_rooms(testing=False):
    db.manager = manager
    if testing:
        # character "𒀂" is four bytes
        test_name = '𒀂'*512
        db.register(test_name, test_name, test_name, 6, 'Ё', '+123456789101112121415', user('U'*512), "student")
        db.register('imya', 'familia', 'otchestvo', 10, 'М', '', user('test_pupl'), "student")
        db.register('Нестор', 'familia', 'otchestvo', 10, 'Г', '', user('kabachenkont'), "teacher")

        bot_create_room('10 Г - Лучшие!', '10', 'ГЛ', db.RoomType.STUDENTS)
        bot_create_room('10 АКМГ чат для делового общения', '10', 'АКМГ', db.RoomType.STUDENTS_TEACHER)
        bot_create_room('Солянка классов поболтать', '1,4,3', 'АКМГ', db.RoomType.PARENTS_TEACHER)
        bot_create_room('anyother', '1,2,5,10', 'АКМ', db.RoomType.PARENTS)

    for i in db.id_range_students():
        info = db.get_info(i)
        grade = info['Grade_Didgit']
        letter = info['Grade_Letter']
        user_id = info['Matrix_Login']
        account_type = info['Account_Type']
        for room_db_id in db.id_range_rooms():
            room = db.get_info_rooms(room_db_id)
            room_grades = room["Grade_Didgits"].split(',')
            room_letters = room["Grade_Letter"]
            room_id = room["Room_ID"]
            room_type = room["Room_Type"]
            if grade not in room_grades or letter not in room_letters:
                kick_user(user_id, room_id, f"Не стоит быть в этой комнате и учится в {grade} классе")
                continue
            if account_type in room_type:
                invite_user(user_id, room_id)
            if room_type in (db.RoomType.PARENTS_TEACHER, db.RoomType.STUDENTS_TEACHER) and account_type == 'teacher':
                verbose(f'making {user_id} an admin in {room_id} because their type is {account_type}')
                change_user_power_level(user_id, room_id, power_level=100)


# https://spec.matrix.org/v1.12/client-server-api/#mroomname
def rename_room(room_id: str, new_name: str):
    parameters = {
        "name": new_name,
    }

    res = requests.put(f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/state/m.room.name',
                       json=parameters, headers=manager.authorization())
    if res.status_code != 200:
        log_res(res)
    verbose(f'Renamed room {room_id} to "{new_name}"')


# https://spec.matrix.org/v1.12/client-server-api/#mroomtopic
def change_room_descripction(room_id: str, new_description: str):
    parameters = {
        "topic": new_description,
    }

    res = requests.put(f'{manager.get("url")}/_matrix/client/v3/rooms/{room_id}/state/m.room.topic',
                       json=parameters, headers=manager.authorization())
    if res.status_code != 200:
        log_res(res)
    verbose(f'Changed topic of room "{room_id}" to "{new_description}"')


def load_users_from_server():
    res = requests.get(
        f'{manager.get("url")}/_synapse/client/mos_integration/info',
        headers=manager.authorization()
    )
    if res.status_code != 200:
        verbose(error('An error occured while trying to load users from server'))
        log_res(res)
    return res.json()

# returns {"user_id": str, "access_token": str}
# login is just username, without server domain
def register_matrix_user(login, password, displayname) -> dict:
    parameters = {
        'login': login,
        'password': password,
        'displayname': displayname,
    }
    res = requests.post(
        f'{manager.get("url")}/_synapse/client/mos_integration/register',
        json=parameters, headers=manager.authorization()
    )
    if res.status_code != 200:
        verbose(error(f'An error occured while trying to register {login}'))
        log_res(res)
    return res.json()


# Function that should be used when adding users manually
def bot_add_user(
     name,
     surname,
     patronic,
     grade,
     letter,
     phone,
     login,
     status,
     password):
    db.register(
        name,
        surname,
        patronic,
        grade,
        letter,
        phone,
        user(login),
        int(status),
    )
    return register_matrix_user(login, password, f'{name} {surname}')


def add_new_users_to_db():
    users = load_users_from_server()
    for user in users:
        if user in db.get_column_info('Matrix_Login'):
            continue

        verbose(f'Adding {user["login"]} to db')
        res = [
            user["first"],
            user["last"],
            user["third"],
            user["parallel"],
            user["letter"],
        ]

        number = ''
        if len(user["phones"]) >= 1:
            number = user["phones"][0]
        res.append(number)
        res.append(user["login"])
        res.append(user["access"])

        db.register(*res)


def main():
    global manager

    parser = ArgumentParser()

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument('-v', '--verbose', action='store_true', help='Print more output')
    verbosity.add_argument('-q', '--quiet', action='store_true', help="Don't print anything")
    parser.add_argument('-c', '--config', type=str, metavar='FILE', help='Config file (json)')
    parser.add_argument('-C', '--color', type=str, help='Colorize the output',
                        choices=['always', 'auto', 'never'],
                        default='auto')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('-l', '--list-users', action='store_true', help='Get a list of all users from the database (json)')
    action.add_argument('-L', '--list-rooms', action='store_true', help='Show information about all rooms from the database (json)')
    action.add_argument('-g', '--generate', action='store_true', help='Create all necessary rooms and invite students there')
    action.add_argument('-k', '--generate-key', action='store_true', help=f'Generate a fernet key for encryption. Overwrites previous {db.key_location}. The previous file is backed up to {db.key_location}.bak just in case')
    action.add_argument('-p', '--permissions', type=str, metavar='ROOM_ID', help='Get current permissions in a room')
    action.add_argument('-P', '--set-permission', type=str, nargs=3, metavar=('USER_ID', 'ROOM_ID', 'POWER_LEVEL'), help='Set a power level for a user in a room')
    action.add_argument('-D', '--set-description', type=str, nargs=2, metavar=('ROOM_ID', 'DESCRIPTION'), help='Set a new description for a room')
    action.add_argument('-r', '--register', type=str, nargs=9, metavar=('NAME', 'SURNAME', 'PATRONIC', 'GRADE', 'LETTER', 'PHONE', 'LOGIN', 'STATUS', 'PASSWORD'), help='Register user manually. STATUS is one of the following strings: student, teacher')
    parser.add_argument('-t', '--testing', action='store_true', help='Run in a testing mode (create some students and rooms for testing purposes). Useful with --generate')
    action.add_argument('-m', '--members', type=str, metavar='ROOM_ID', help='Get a list of room members')
    action.add_argument('-M', '--get-all-members', action='store_true', help='Get a list of all rooms in the system with all of their members')
    action.add_argument('-i', '--get-id', type=str, metavar='ROOM_ALIAS', help='Get room id from ROOM_ALIAS')
    action.add_argument('-a', '--get-aliases', type=str, metavar='ROOM_ID', help='Get room aliases from ROOM_ID')
    action.add_argument('-U', '--gui', action='store_true', help='Launch PyQt-based GUI')
    action.add_argument('--drop-all-databases', action='store_true', default=False, help='Drop ALL databases with students data. Use CAREFULLY')
    parser.add_argument('-n', '--no-autofetch', action='store_true', default=False, help="Don't fetch new students from the server. Fetching is enabled by default")

    args = parser.parse_args()
    manager = ConfigManager()

    manager.set("verbose", args.verbose)
    manager.set("quiet", args.quiet)
    manager.set("color", args.color)

    if args.config is not None:
        manager.loadConfig(args.config)

    if not all((manager.get_cache("user_id"),
                manager.get_cache("token"))):
        login_response = login(manager.get("login"), manager.get("password"))
        manager.set_cache("user_id", login_response["user_id"])
        manager.set_cache("token", login_response["access_token"])

    manager.set("user_id", manager.get_cache("user_id"))
    manager.set("token", manager.get_cache("token"))

    db.init_db(manager.get("db_user"), manager.get("db_password"))

    if not args.no_autofetch:
        verbose('Fetching newly registered users...')
        add_new_users_to_db()

    if args.list_users:
        print(jsonify(db.get_students()))
    elif args.list_rooms:
        print(jsonify(db.get_rooms()))
    elif args.generate:
        generate_rooms(args.testing)
    elif args.generate_key:
        replace(db.key_location, f'{db.key_location}.bak')
        with open(db.key_location, 'w') as file:
            file.write(db.Fernet.generate_key().decode())
    elif args.permissions is not None:
        state = get_room_state(args.permissions, 'm.room.power_levels')[0]["content"]
        print(jsonify(state))
    elif args.set_permission is not None:
        permission = args.set_permission
        permission[-1] = int(permission[-1])
        # mabye?? this could be exploited
        change_user_power_level(*permission)
    elif args.members is not None:
        room_id = args.members
        print(jsonify(get_room_members(room_id)))
    elif args.get_all_members:
        print(jsonify(bot_get_all_members()))
    elif args.get_id is not None:
        print(get_room_id(args.get_id))
    elif args.get_aliases is not None:
        print(get_room_aliases(args.get_aliases))
    elif args.set_description is not None:
        change_room_descripction(*args.set_description)
    elif args.register is not None:
        print(jsonify(bot_add_user(*args.register)))
    elif args.gui:
        import gui
        gui.main(manager)
    elif args.drop_all_databases:
        db.drop_all_databases(manager.get("db_user"), manager.get("db_password"))



if __name__ == '__main__':
    main()

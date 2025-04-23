from typing import Awaitable, Callable, Optional, Tuple

import logging

import synapse
import json
from synapse import module_api
from synapse.module_api import DirectServeJsonResource, parse_json_object_from_request
from synapse.api.errors import AuthError, SynapseError
from twisted.web.resource import Resource

logger = logging.getLogger(__name__)

from octodiary.apis import AsyncMobileAPI, AsyncWebAPI
from octodiary.types.enter_sms_code import EnterSmsCode
from octodiary.urls import Systems
from octodiary.exceptions import APIError
import asyncio
from asyncio import run

# user: password
# when user already in tries, treat their new password as sms code
tries = {}
contents = []

class MosIntegration:
    def __init__(self, config: dict, api: module_api):
        logger.info('Starting MosIntegration...')

        self.api = api

        auth_checkers: Optional[Dict[Tuple[str, Tuple], CHECK_AUTH_CALLBACK]] = {}
        auth_checkers[("m.login.password", ("password",))] = self.check_m_login_password
        print('auth_checkers', auth_checkers)

        api.register_password_auth_provider_callbacks(
            auth_checkers=auth_checkers,
        )
        api.register_web_resource('/_synapse/client/mos_integration', UserServlet(self.api))

        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.mos_api = AsyncMobileAPI(system=Systems.MES)
        self.mos_web_api = AsyncWebAPI(system=Systems.MES)
        self.pass_handler = self.api._hs.get_set_password_handler()
        self.auth_handler = self.api._hs.get_auth_handler()


    async def check_m_login_password(
        self,
        username: str,
        login_type: str,
        login_dict: "synapse.module_api.JsonDict",
    ) -> Optional[
        Tuple[
            str,
            Optional[Callable[["synapse.module_api.LoginResponse"], Awaitable[None]]],
        ]
    ]:
        logger.warn("\n"*10+'check m login password')
        if login_type != "m.login.password":
            return None

        return await self._log_in_username_with_token("m.login.password", username, login_dict.get("password"))

    async def mos_ru_send_sms(self, login, password):
        logger.info('sending sms to %s', login)
        try:
            sms_code: EnterSmsCode = await self.mos_web_api.login(username=login, password=password)
        except APIError as e:
            logger.warn(e)
            return None

        return sms_code

    async def get_mos_ru_info(self, sms_code: EnterSmsCode, code: int, login: str):
        print('get_mos_ru_info')
        self.mos_api.token = await sms_code.async_enter_code(code)

        # получаем ID профиля
        info = await self.mos_api.get_users_profile_info()
        print(info)
        profile_id = (info)[0].id

        # Получаем инфо о профиле и сохраняем некоторые важные данные, которые будут нужны
        profile = await self.mos_api.get_family_profile(profile_id=profile_id)
        mes_role = profile.profile.type                      # тип пользователя
        person_id = profile.children[0].contingent_guid      # person-id ученика
        student_id = profile.children[0].id                  # <STUDENT-ID>
        contract_id = profile.children[0].contract_id        # <CONTRACT-ID>

        person_data = await self.mos_api.get_person_data(
            person_id=person_id,                            # person-id ученика (contingent_guid)
            profile_id=profile_id                           # <PROFILE-ID>
        )

        # print(person_data)

        emails = []
        numbers = []
        if person_data.contacts is not None:
            for contact in person_data.contacts:
                if contact["type"]["name"] == 'e-mail':
                    emails.append(contact["data"])
                # phone number
                elif contact["type"]["id"] == 1:
                    numbers.append(f'+7{contact["data"]}')
        parallel = '1'
        letter = 'А'  # Russian А
        for edu in person_data.education:
            edu = dict(edu)
            if dict(edu['class_']).get('parallel_id') is not None:
                parallel = edu["class_"].parallel.name
                letter = edu['class_'].letter
                break

        res = {
            'last': person_data.lastname,    # Ivanov
            'first': person_data.firstname,  # Ivan
            'third': person_data.patronymic, # Ivanovich
            'emails': tuple(emails),
            'phones': tuple(numbers),
            'parallel': parallel,
            'letter': letter,
            'login': f'@{login}:{self.api.server_name}',
            'access': mes_role,
        }
        # with open('mos.json', 'w', encoding='utf-8') as file:
            # contents = json.load(file)
            # contents.append(res)
            # print(contents)
            # json.dump(contents, file)
            # print('wrote contents')
        contents.append(res)

        return res


    async def _log_in_username_with_token(
        self,
        login_type: str,
        username: str,
        token: str,
    ) -> Optional[
        Tuple[
            str,
            Optional[Callable[["synapse.module_api.LoginResponse"], Awaitable[None]]],
        ]
    ]:
        logger.info('Authenticating user `%s` with login type `%s`', username, login_type)
        print(f'@{username}:{self.api.server_name}')
        # such user already exists
        # if user_info is not None:
            # print('already exists', user_info)
            # return None
        # print('failing why not')
        # print(await self.api._password_auth_provider.check_auth(username, login_type, {'password': token}))
        # return None
        # if self.credentials.get(username) == login_dict.get("password"):
            # print('authenticating user, cuz the password is right')
            # return (self.api.get_qualified_user_id(username), None)

        # logger.warn("\n"*10 + f'{username} ({token}) registerin in!!!!')

        if tries.get(username) is None:
            print(username, 'did not log in yet')
            sms_code: EnterSmsCode = self.loop.run_until_complete(self.mos_ru_send_sms(username, token))
            tries[username] = {}
            tries[username]['sms'] = sms_code
            tries[username]['password'] = token
            print('sent an sms_code')
            return None
        else:
            print(username, 'already tried to log in')
            print('treating it\'s password as sms code')
            try:
                code = int(token)
            except ValueError:
                logger.info('new password was not an sms code :(')
                sms_code: EnterSmsCode = self.loop.run_until_complete(self.mos_ru_send_sms(username, token))
                tries[username]['sms'] = sms_code
                tries[username]['password'] = token
                return None

            person_info = self.loop.run_until_complete(self.get_mos_ru_info(tries[username]['sms'], code, username))
            print(person_info)

        # mabye FIXME?
        user_id = f'@{username}:{self.api.server_name}'
        print('getting info')
        user_info = await self.api.get_userinfo_by_id(user_id)
        print('info', user_info)
        if user_info is None:
            user_id, access_token = await self.api.register(
                localpart=username,
                displayname=f"{user_info['first']} {user_info['last']}",
                emails=user_info['emails']
            )
        else:
            logger.warn('userinfo is not none')
        print('setting hash')


        new_password_hash = await self.auth_handler.hash(tries[username]['password'])
        print(new_password_hash)
        await self.pass_handler.set_password(user_id, new_password_hash, logout_devices=False)
        print('deling tries')

        del tries[username]
        print('returning success')

        return (user_id, None)
        # return  (self.api.get_qualified_user_id(username), None)


class UserServlet(Resource):
    def __init__(self, api: module_api):

        super().__init__()

        self.putChild(b'info', UserInfoServlet(api))
        self.putChild(b'register', UserRegisterServlet(api))

class UserInfoServlet(DirectServeJsonResource):
    """
    Telling info about a user
    """
    def __init__(self, api: module_api):
        self.api = api
        DirectServeJsonResource.__init__(self)

    async def _async_render_GET(self, request):
        """On GET requests on /info, send a json with new users if
        token belongs to a matrix admin user
        """
        logger.info('got info servlet')
        requester = await self.api.get_user_by_req(request)
        if not await self.api.is_user_admin(requester.user.to_string()):
            raise SynapseError(403, "You are not a server admin", "M_FORBIDDEN")

        # if not exists('mos.json'):
            # return 200, tuple()

        # with open('mos.json', 'r', encoding='utf-8') as file:
            # res = tuple(json.load(file))

        return 200, contents

class UserRegisterServlet(DirectServeJsonResource):
    """
    Register a user without synapse admin api
    """
    def __init__(self, api: module_api, ):
        self.api = api
        self.pass_handler = self.api._hs.get_set_password_handler()
        self.auth_handler = self.api._hs.get_auth_handler()
        DirectServeJsonResource.__init__(self)

    async def _async_render_POST(self, request):
        """On POST requests on /register create a user if
        token belongs to a matrix admin user
        """
        print('got register servlet')
        requester = await self.api.get_user_by_req(request)
        if not await self.api.is_user_admin(requester.user.to_string()):
            raise SynapseError(403, "You are not a server admin", "M_FORBIDDEN")

        req_json = parse_json_object_from_request(request)

        if req_json.get('displayname') is None:
            raise SynapseError(503, "No displayname", "M_FORBIDDEN")

        if req_json.get('login') is None:
            raise SynapseError(503, "No login", "M_FORBIDDEN")

        if req_json.get('password') is None:
            raise SynapseError(503, "No password", "M_FORBIDDEN")

        displayname = req_json['displayname']
        username = req_json['login']
        password = req_json['password']

        user_info = await self.api.get_userinfo_by_id(f'@{username}:{self.api.server_name}')
        if user_info is not None:
            raise SynapseError(503, "Already registered", "M_FORBIDDEN")

        user_id, access_token = await self.api.register(
            localpart=username,
            displayname=displayname,
            # emails=person_info['emails']
        )

        new_password_hash = await self.auth_handler.hash(password)
        await self.pass_handler.set_password(user_id, new_password_hash, logout_devices=False)

        return 200, {'user_id': user_id, 'access_token': access_token}


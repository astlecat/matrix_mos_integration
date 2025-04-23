from asyncio import run

from octodiary.apis import AsyncWebAPI, AsyncMobileAPI
from octodiary.types.enter_sms_code import EnterSmsCode
from octodiary.urls import Systems
from octodiary.exceptions import APIError
from getpass import getpass


async def get_personal_info():
    api = AsyncWebAPI(system=Systems.MES)

    # авторизовываемся, получаем токен и сохраняем его
    login = input("Логин: ")
    password = getpass("Пароль: ")
    try:
        sms_code: EnterSmsCode = await api.login(username=login, password=password)
    except APIError as e:
        print(e)
        return
    code = input("SMS-Code: ")
    api = AsyncMobileAPI(system=Systems.MES)
    api.token = await sms_code.async_enter_code(code)

    # получаем ID профиля
    info = await api.get_users_profile_info()
    profile_id = (info)[0].id

    # Получаем инфо о профиле и сохраняем некоторые важные данные, которые будут нужны
    profile = await api.get_family_profile(profile_id=profile_id)
    mes_role = profile.profile.type                   # тип пользователя
    person_id = profile.children[0].contingent_guid   # person-id ученика

    # Получить подробную информацию о профиле
    person_data = await api.get_person_data(
        person_id=person_id,        # person-id ученика (contingent_guid)
        profile_id=profile_id       # <PROFILE-ID>
    )
    print(person_data)
    print(mes_role)
    print(person_data.lastname)
    print(person_data.firstname)
    print(person_data.patronymic)
    if person_data.contacts is not None:
        for contact in person_data.contacts:
            print(contact["type"]["name"], contact["data"])

    for edu in person_data.education:
        edu = dict(edu)
        if dict(edu['class_']).get('parallel_id') is not None:
            print(edu["class_"].parallel.name, edu['class_'].letter)


async def main():
    await get_personal_info()

if __name__ == "__main__":
    run(main())

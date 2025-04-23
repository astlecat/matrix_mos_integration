### OAuth:

from cookie get aupd_token:
```kotlin
cookie_string.split("=")[1].split(";")[0]
```

then:

```kotlin
val tokenRequest = httpClient.get("https://school.mos.ru/v2/token/refresh?roleId=1&subsystem=2") {
    cookie("aupd_token", aupdToken)
    attributes.put(InsertAuthAttrs.DontInsert, true)
}
```

our token:

```kotlin
val token = tokenRequest.body<String>()
```

### Matrix

Документация серверного API matrix:

https://spec.matrix.org/latest/client-server-api/#creation

Вот что-то для homeserver.yaml, но оно не работает, т. к. "Invalid redirect uri" (на наш сайт):

```yaml
oidc_providers:
  - idp_id: mosru
    idp_name: "mos.ru"
    # skip_verification: true
    issuer: "https://sudir.mos.ru/"
    # client_id: "matrix.school.ru"
    client_id: "school.mos.ru"
    # authorisation_endpoint: "https://login.mos.ru/sps/oauth/ae?response_type=code&access_type=offline&client_id=dnevnik.mos.ru&scope=openid+profile+birthday+contacts+snils+bli
    # authorisation_endpoint: "https://login.mos.ru/sps/oauth/ae?response_type=code&access_type=offline"
    # authorisation_endpoint: "https://sudir.mos.ru/blitz/oauth/ae?response_type=code&redirect_uri=https://school.mos.ru/v3/auth/sudir/callback"
    authorisation_endpoint: "https://sudir.mos.ru/blitz/oauth/me"
    client_auth_method: "client_secret_basic"
    # authorisation_endpoint: "https://sudir.mos.ru/blitz/oauth/ae"
    client_secret: ""
    scopes: ["firstname", "lastname", "email"]
    user_mapping_provider:
      config:
        localpart_template: "{{ user.name }}"
        display_name_template: "{{ user.name|capitalize }}"
```

Password auth provider (это то, что нам нужно кажется (точно))

https://element-hq.github.io/synapse/latest/password_auth_providers.html

Конфигурация:

```yaml
modules:
 - module: "mos.MOSPasswordProvider"
   config:
     enabled: true
```

Notes:
```shell
sudo micro $(docker container inspect matrix_synapse | jq -r '.[0]["GraphDriver"]["Data"]["MergedDir"]')/usr/local/lib/python3.11/mos.py
```

Should be done with custom modules:

https://element-hq.github.io/synapse/latest/modules/index.html

module config:
```yaml
modules:
 - module: "mos.ssap"
 # - module: "mos.MOSPasswordProvider"
   config:
     enabled: true
     shared_secret: "kshf"
     uri: "ldap://ldap.example.com:389"
     start_tls: true
     base: "ou=users,dc=example,dc=com"
     attributes:
        uid: "cn"
        mail: "mail"
        name: "givenName"

```
Matrix поддерживает OpenIDConnect, надо тыкать доки mos.ru чтобы понять как их в сторонние сервисы интегрировать

https://habr.com/ru/companies/nixys/articles/566910/

Introduction to oauth

https://matrix.org/blog/2023/09/better-auth/

Synapse docs for oauth

https://element-hq.github.io/synapse/latest/openid.html

### mos.ru API

#### Official (doesn't include school)

- https://rpp.mos.ru/services/api/documentation/
- https://data.mos.ru/developers
- https://data.mos.ru/developers/documentation
- https://github.com/lesterrry/mosru - Ruby library
- https://github.com/grybakov/python-apidata-mos-ru - Python library (unmaintained)
- https://github.com/basiliocat/mos.ru - bash scripts to retrieve information about water (unmaintained for 6 years)

#### Reverse-engineered

Unofficial clients for school.mos.ru:
- https://github.com/OctoDiary/OctoDiary-kt
- https://github.com/x3lfyn/libremesh

Other:
- https://github.com/RedGuyRu/DnevnikApi - JavaScript library (under development)
- https://github.com/xD1rty/dnevniklib/blob/main/docs/api.md - Documentation for this undocumented api
- https://github.com/basiliocat/mos.ru - bash script for water something

Ссылки из api mos.ru, которые использует [libremesh](https://github.com/x3lfyn/libremesh/)
- https://login.mos.ru/sps/oauth/ae?response_type=code&access_type=offline&client_id=dnevnik.mos.ru&scope=openid+profile+birthday+contacts+snils+blitz_user_rights+blitz_change_password&redirect_uri=https://school.mos.ru/v3/auth/sudir/callback
- https://school.mos.ru/v3/auth/sudir/callback?code=

To switch termux package manager:
 - https://wiki.termux.com/wiki/Switching_package_manager
 - https://github.com/termux-pacman/termux-packages/releases/download/bootstrap-2024.09.15-r1%2Bpacman-android-7/bootstrap-aarch64.zip


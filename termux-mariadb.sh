#!/usr/bin/env bash

source config.sh

yes | pkg install mariadb

cd '/data/data/com.termux/files/usr' || exit 1
/data/data/com.termux/files/usr/bin/mariadbd-safe --datadir='/data/data/com.termux/files/usr/var/lib/mysql' & disown

echo "Waiting for socket... "
until [ -S '/data/data/com.termux/files/usr/var/run/mysqld.sock' ]; do
    sleep 1
done
echo "Changing root password... "
printf '%s\n' "use mysql;
set password for 'root'@'localhost' = password('$DB_PASSWORD');
flush privileges;" | mariadb -u root

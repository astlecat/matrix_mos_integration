#!/usr/bin/env bash

source config.sh

# Stop the script if anything fails
set -e

### INSTALL DOCKER ###
echo -e "\033[32mInstalling Docker...\033[0m "

# Add Docker's official GPG key:
sudo apt-get update --yes
sudo apt-get install ca-certificates curl --yes
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update --yes
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin --yes
######################

# https://hub.docker.com/r/matrixdotorg/synapse
### INSTALL SYNAPSE ###
echo -e "\033[32mInstalling Synapse...\033[0m "
sudo docker run -it --rm \
    --mount type=volume,src=synapse-data,dst=/data \
    -e SYNAPSE_SERVER_NAME="$SERVER" \
    -e SYNAPSE_REPORT_STATS=yes \
    matrixdotorg/synapse:latest generate

sudo docker run -d --name synapse \
    --mount type=volume,src=synapse-data,dst=/data \
    -p 8008:8008 \
    matrixdotorg/synapse:latest

# Adding user to group docker to run without sudo
# U might want to FIXME
sudo usermod -aG docker "$USER"
# Waiting until synapse is up
until curl --output /dev/null --silent --head --fail "http://$SERVER:8008"; do
    sleep 1
done

# Adding school_bot user
# Should be an admin to be able to register users
sudo docker exec -it synapse register_new_matrix_user \
    http://127.0.0.1:8008 \
    -c /data/homeserver.yaml \
    --exists-ok \
    --admin \
    --user "$BOT_NAME" \
    --password "$BOT_PASSWORD"

# Installing octodiary for auth provider
sudo docker exec -it synapse pip install octodiary
python_version="$(docker exec -it synapse /usr/local/bin/python --version | cut -d ' ' -f 2 | cut -d . -f -2)"
docker_dir="$(docker container inspect synapse | jq -r '.[0]["GraphDriver"]["Data"]["MergedDir"]')"
sudo cp auth/mos.py "${docker_dir}/usr/local/lib/python${python_version}/mos.py"
echo 'modules:
 - module: "mos.MosIntegration"
   config:
     enabled: true' | sudo docker exec -it synapse tee --append /data/homeserver.yaml
#######################


### Python setup ###
echo -e "\033[32mInstalling Python...\033[0m "
sudo apt install python3 python3-venv python3-pip --yes
####################

echo -e "\033[32mInstalling Mariadb...\033[0m "
sudo apt install mariadb-client{,-core} mariadb-server libmariadb-dev-compat -y
sudo mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
sudo systemctl start mariadb

echo -e "\033[32mAdding user \"${DB_USER}\" to mariadb...\033[0m "
echo "use mysql;
CREATE USER if not exists '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES on Students.* to '${DB_USER}'@'localhostt';
FLUSH PRIVILEGES;" | sudo mariadb
# echo -e "\033[32mInstalling other stuff...\033[0m "
# For generating passwords
# sudo apt install pwgen

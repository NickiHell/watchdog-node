#!/bin/bash

wait_db() {
  while ! /usr/bin/pg_isready -h $DB_HOST -p ${DB_PORT:-5432} >/dev/null 2>/dev/null; do
    echo "I'm waiting DB (Host: $DB_HOST, port: ${DB_PORT:-5432})"
    sleep 1
  done
}

wait_am() {
  while ! curl -s --max-time 5 --head --request GET $ACCOUNT_MANAGER_IP | grep "404" > /dev/null; do
    echo "I'm waiting AM (Host: $ACCOUNT_MANAGER_IP)"
    sleep 1
  done
}

wait_is() {
  while ! curl -s --max-time 5 --head --request GET $IMAGE_SERVICE_IP | grep "404" > /dev/null; do
    echo "I'm waiting IS (Host: $IMAGE_SERVICE_IP)"
    sleep 1
  done
}

sync() {
  STS=${STS_ENABLED:-'true'}
  STS_APP=metadata_manager.reloader:sts_reloader
  echo -e "\n### Migrate DB ###\n" && python manage.py migrate &&
  echo -e "\n### Sync permissions with AM ###\n" && python manage.py sync_perms_with_am &&
  echo -e "\n### Sync image fields with IS ###\n" && python manage.py sync_image_fields &&
  if [ "$STS" == "true" ];
    then echo -e "\n### Sync with STS ###\n" && stsreloader -a $STS_APP sync;
  fi
}

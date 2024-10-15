#!/bin/bash

if [ -z "$PASSWORD_BASIC_AUTH" ]; then
  echo "ERROR: La variable de entorno PASSWORD_BASIC_AUTH no está establecida."
  exit 1
fi

htpasswd -bc /etc/nginx/.htpasswd rafa "$PASSWORD_BASIC_AUTH"

/usr/sbin/nginx -g 'daemon off;'

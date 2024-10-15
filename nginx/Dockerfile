FROM nginx:latest

RUN apt-get update && apt-get install -y apache2-utils

COPY conf.d /etc/nginx/conf.d

ARG PASSWORD_BASIC_AUTH
RUN htpasswd -bc /etc/nginx/.htpasswd rafa ${PASSWORD_BASIC_AUTH}

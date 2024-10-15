FROM nginx:latest

RUN apt-get update && apt-get install -y apache2-utils

COPY conf.d /etc/nginx/conf.d
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

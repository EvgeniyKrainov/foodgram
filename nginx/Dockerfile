FROM nginx:1.22.1

COPY nginx.conf /etc/nginx/templates/default.conf.template

RUN mkdir -p /var/html/static && \
    mkdir -p /var/html/media && \
    chown -R nginx:nginx /var/html/ && \
    chmod -R 755 /var/html/

EXPOSE 80

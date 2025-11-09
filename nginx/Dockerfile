FROM nginx:1.22.1

COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN mkdir -p /var/html/static && \
    mkdir -p /var/html/media

EXPOSE 80

FROM nginx:1.29.4-alpine
COPY web/dist /usr/share/nginx/html
COPY deploy/web.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 8080

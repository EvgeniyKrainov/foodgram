FROM node:16-alpine as build

WORKDIR /app

# Копируем package файлы
COPY package.json package-lock.json ./

# Устанавливаем зависимости с ретраями и кэшем
RUN npm config set registry https://registry.npmjs.org/ && \
    npm install --no-optional --prefer-offline --fetch-retries 5 --fetch-timeout 600000

# Копируем исходный код и собираем
COPY . .
RUN npm run build

# Стадия для копирования файлов
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

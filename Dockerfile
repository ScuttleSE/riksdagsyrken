# Bygger den statiska sajten och serverar den med nginx.
# Datan (web/static/data.json) är redan framtagen av scrapern och följer med som den är.
FROM node:22-alpine AS build
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY web/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80

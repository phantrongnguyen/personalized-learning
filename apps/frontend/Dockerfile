FROM node:22-alpine AS build
WORKDIR /workspace/apps/frontend
COPY apps/frontend/package*.json ./
RUN npm ci
COPY apps/frontend ./
COPY packages /workspace/packages
RUN npm run build

FROM nginx:1.28-alpine
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/frontend/dist /usr/share/nginx/html
EXPOSE 80

FROM node:20-alpine

WORKDIR /app

COPY ./apps/supplier-portal/package*.json ./
RUN npm install

COPY ./apps/supplier-portal/ ./
EXPOSE 3004

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3004"]
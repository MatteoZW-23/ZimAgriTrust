FROM node:18-slim
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install --legacy-peer-deps --fetch-retry-maxtimeout=600000 --fetch-retry-mintimeout=20000 --fetch-retries=5
COPY . .
EXPOSE 19000 19001
CMD ["npm", "start"]

FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm config set fetch-retry-mintimeout 60000 && \
    npm config set fetch-retry-maxtimeout 1200000 && \
    npm config set fetch-retries 10 && \
    rm -f package-lock.json && \
    npm install --legacy-peer-deps
COPY . .
EXPOSE 19000 19001
CMD ["npm", "start"]

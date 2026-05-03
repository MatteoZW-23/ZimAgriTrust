FROM node:18-slim
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install --fetch-retry-maxtimeout=600000 --fetch-retry-mintimeout=20000 --fetch-retries=5
COPY . .
EXPOSE 3001
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]

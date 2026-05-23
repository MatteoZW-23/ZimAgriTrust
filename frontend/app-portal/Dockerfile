FROM node:20-slim

WORKDIR /app

# Copy the shared workspace package first so the file: dependency resolves
COPY packages/shared /packages/shared
RUN cd /packages/shared && npm install --legacy-peer-deps

COPY apps/app-portal/package*.json ./
RUN rm -f package-lock.json && npm install --legacy-peer-deps --fetch-retry-maxtimeout=600000 --fetch-retry-mintimeout=20000 --fetch-retries=5

COPY apps/app-portal/ .
EXPOSE 3003

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3003"]

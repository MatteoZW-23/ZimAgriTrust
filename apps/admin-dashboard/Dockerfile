FROM node:20-slim
WORKDIR /app

COPY packages/shared /packages/shared
RUN cd /packages/shared && npm install --legacy-peer-deps

COPY apps/admin-dashboard/package*.json ./
RUN rm -f package-lock.json && npm install --legacy-peer-deps --fetch-retry-maxtimeout=600000 --fetch-retry-mintimeout=20000 --fetch-retries=5

COPY apps/admin-dashboard/ .
EXPOSE 3001
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]

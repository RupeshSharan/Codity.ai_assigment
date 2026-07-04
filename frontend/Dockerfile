FROM node:22-alpine

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --ignore-scripts
COPY frontend /app

CMD ["npm", "run", "dev"]


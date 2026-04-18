FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Development - just expose the dev server
ENV FRONTEND_PORT=3000
EXPOSE ${FRONTEND_PORT}
CMD ["sh", "-c", "npm run dev -- --host 0.0.0.0 --port ${FRONTEND_PORT}"]

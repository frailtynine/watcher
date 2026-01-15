FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Development - just expose the dev server
EXPOSE 3000
CMD ["npm", "run", "dev"]

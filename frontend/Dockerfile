FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install --prefer-offline
COPY . .
EXPOSE 3000
ENV HOST=0.0.0.0
ENV WATCHPACK_POLLING=true
CMD ["npm", "start"]
FROM node:20-alpine

WORKDIR /app

COPY phase4/frontend/package*.json ./
RUN npm install

COPY phase4/frontend/ ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM node:20-alpine

WORKDIR /app

# Les dépendances sont installées au démarrage du conteneur (cf.
# docker-compose.yml : volume anonyme sur /app/node_modules) afin de
# fonctionner correctement avec le bind-mount du code source en
# développement, quelle que soit la plateforme hôte.
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

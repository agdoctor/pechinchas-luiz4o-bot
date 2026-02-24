FROM atendai/evolution-api:latest

# Define as variáveis de ambiente base
ENV AUTHENTICATION_TYPE=apikey
ENV AUTHENTICATION_API_KEY=pechinchas_key_928374
ENV DATABASE_ENABLED=true
ENV DATABASE_CONNECTION_URI=./database.db
ENV DATABASE_TYPE=sqlite

EXPOSE 80
CMD ["node", "dist/src/main.js"]

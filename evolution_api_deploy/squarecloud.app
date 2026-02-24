DISPLAY_NAME=Evolution API
MEMORY=1024
TYPE=node
MAIN=index.js
SUBDOMAIN=evolution-pechinchas
AUTO_RESTART=true
START=npx prisma generate --schema ./prisma/postgresql-schema.prisma && npm run build && npm run start:prod

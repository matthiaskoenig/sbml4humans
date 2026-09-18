git pull
# the commit the footer of the deployed application links, the build context has no repository
export VITE_COMMIT=$(git rev-parse HEAD)
./docker-purge.sh
docker compose -f docker-compose-production.yml up --force-recreate --always-recreate-deps --build --detach

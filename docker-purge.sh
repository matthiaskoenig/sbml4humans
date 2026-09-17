# shut down all containers (remove images and volumes)
docker compose -f docker-compose-production.yml down --volumes --rmi local
# docker-compose -f docker-compose-develop.yml down --volumes --rmi local

# make sure containers are removed (if not running)
docker container rm -f sbml4humans-nginx-1
docker container rm -f sbml4humans-backend-1
docker container rm -f sbml4humans-frontend-1

# make sure images are removed
docker image rm -f sbml4humans-nginx:latest
docker image rm -f sbml4humans-backend:latest
docker image rm -f sbml4humans-frontend:latest

# make sure volumes are removed
docker volume rm -f sbml4humans_node_modules
docker volume rm -f sbml4humans_vue_dist

# cleanup all dangling images, containers, volumes and networks
docker system prune --force

# Deployment

SBML4Humans is deployed as docker containers behind a proxy server: the proxy terminates https for sbml4humans.de and forwards the requests to the server which runs the containers. Setting up the deployment therefore means setting up the proxy with its certificates and then the containers on the machine behind it.

## The proxy

Log in to the proxy server `denbi-head`.

The configuration of the site is `nginx/sbml4humans.de` of the repository, which proxies to the server the containers run on. Update the IP of that server in the configuration before you copy it, then activate the site:

```bash
cp <repo>/nginx/sbml4humans.de /etc/nginx/sites-available/sbml4humans.de
sudo ln -s /etc/nginx/sites-available/sbml4humans.de /etc/nginx/sites-enabled/
```

### Certificates

The certificates come from Let's Encrypt with [certbot](https://certbot.eff.org/). The first certificate is issued with nginx stopped; `certbot certonly` asks which domains to issue it for, which are `sbml4humans.de` and `www.sbml4humans.de`:

```bash
sudo mkdir -p /usr/share/nginx/letsencrypt
sudo service nginx stop
sudo certbot certonly
sudo service nginx start
sudo service nginx status
```

A renewal is issued from the webroot the site configuration serves the ACME challenge from, so nginx keeps running. `--dry-run` runs the renewal without issuing a certificate:

```bash
sudo certbot certonly --webroot -w /usr/share/nginx/letsencrypt -d sbml4humans.de -d www.sbml4humans.de --dry-run
```

## The server

Log in to the server `denbi-node-2`, which runs the containers with docker compose. Clone the repository once:

```bash
cd /var/git
git clone https://github.com/matthiaskoenig/sbml4humans.git
```

### The containers

`deploy.sh` is the deployment: it pulls the latest changes, removes the containers, images and volumes of the previous deployment with `docker-purge.sh`, and rebuilds and starts the backend, the frontend and the nginx container of `docker-compose-production.yml` in the background.

```bash
./deploy.sh
```

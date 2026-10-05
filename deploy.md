# Deployment

SBML4Humans is deployed as docker containers behind a proxy server: the proxy terminates https for sbml4humans.de and forwards the requests to the server which runs the containers. Setting up the deployment therefore means setting up the proxy with its certificates and then the containers on the machine behind it.

## The proxy

Log in to the proxy server `denbi-head`.

The configuration of the site is `nginx/sbml4humans.de` of the repository, which proxies to the server the containers run on. It includes two snippets of the repository: `nginx/ssl.conf`, the TLS settings (TLS 1.2 and 1.3 only), and `nginx/security-headers.conf`, the security headers and the Content-Security-Policy of the frontend. Update the IP of the server the containers run on in the configuration before you copy it, then copy the snippets, activate the site, test the configuration and reload nginx:

```bash
sudo cp <repo>/nginx/sbml4humans.de /etc/nginx/sites-available/sbml4humans.de
sudo cp <repo>/nginx/ssl.conf /etc/nginx/snippets/ssl.conf
sudo cp <repo>/nginx/security-headers.conf /etc/nginx/snippets/sbml4humans-security-headers.conf
sudo ln -s /etc/nginx/sites-available/sbml4humans.de /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

`/etc/nginx/snippets/ssl.conf` may be included by other sites of the proxy; it no longer sets `Strict-Transport-Security`, a site which relied on it has to set the header itself.

The Content-Security-Policy allows exactly what the built frontend loads: its own scripts, styles and fonts, the api on the same origin, images of the notes of a model from any https url and Google Analytics. When the frontend starts to load anything from another origin, extend the policy in `nginx/security-headers.conf`, otherwise the browser blocks it and logs the violation in the console.

### Certificates

The certificates come from Let's Encrypt with [certbot](https://certbot.eff.org/) for `sbml4humans.de` and `www.sbml4humans.de`. nginx cannot start with a site whose certificate does not exist yet, so the first certificate is issued with nginx stopped, by the standalone authenticator:

```bash
sudo mkdir -p /usr/share/nginx/letsencrypt
sudo systemctl stop nginx
sudo certbot certonly --standalone --cert-name sbml4humans.de -d sbml4humans.de -d www.sbml4humans.de
sudo systemctl start nginx
```

certbot renews with the authenticator the certificate was issued with. A certificate issued by the standalone authenticator cannot renew while nginx holds port 80, so switch it to the webroot authenticator right away, from which the site configuration serves the ACME challenge (`/.well-known/acme-challenge/` is the one path of http which does not redirect to https), and let every renewal reload nginx, which otherwise keeps serving the old certificate until it restarts. This issues a new certificate and stores both in `/etc/letsencrypt/renewal/sbml4humans.de.conf`; it also renews an expired certificate, with nginx running:

```bash
sudo certbot certonly --webroot -w /usr/share/nginx/letsencrypt --cert-name sbml4humans.de -d sbml4humans.de -d www.sbml4humans.de --deploy-hook "systemctl reload nginx"
```

The renewal itself is the `certbot.timer` of systemd (or `/etc/cron.d/certbot`), which the certbot package installs and which runs `certbot renew` twice a day. Check the renewal after every change of the proxy and whenever the expiry date comes close:

```bash
sudo certbot certificates                        # expiry date of the certificate
grep -E "authenticator|webroot|deploy_hook" /etc/letsencrypt/renewal/sbml4humans.de.conf  # webroot and the reload hook
systemctl list-timers certbot.timer             # the next run of the renewal
sudo certbot renew --cert-name sbml4humans.de --dry-run   # a renewal against the staging server
echo | openssl s_client -connect sbml4humans.de:443 -servername sbml4humans.de 2>/dev/null | openssl x509 -noout -enddate  # the certificate nginx serves
```

A failing renewal is logged in `/var/log/letsencrypt/letsencrypt.log`; the usual causes are a redirect or a 404 for `http://sbml4humans.de/.well-known/acme-challenge/...` and port 80 not reaching the proxy.

## The server

Log in to the server `denbi-node-2`, which runs the containers with docker compose. Clone the repository once:

```bash
cd /var/git
git clone https://github.com/matthiaskoenig/sbml4humans.git
```

### The containers

`deploy.sh` is the deployment: it pulls the latest changes, removes the containers, images and volumes of the previous deployment with `docker-purge.sh`, and rebuilds and starts the backend, the frontend and the nginx container of `docker-compose-production.yml` in the background. The nginx container is published on port 8084, which the proxy forwards to; it serves the frontend with gzip and caching headers (`nginx/config/conf.d/local.conf`) and proxies `/api` to the backend, which runs as an unprivileged user from the code in its image and publishes no port, so it is reachable through the docker network alone. It also exports `VITE_COMMIT`, the commit it deploys, which the frontend build takes as an argument and the footer of the application links; the build context is `./frontend` and holds no repository to read it from, so a build without that variable shows the version alone.

The backend keeps the cache of the web services (OLS, ChEBI, UniProt, the registry) on the named volume `cache` (`/cache`, `SBML4HUMANS_CACHE`) next to the volume `uploads` (`/uploads`, `SBML4HUMANS_UPLOADS`), so that it survives a restart of the container; a deploy removes the volumes (`docker-purge.sh`) and starts with an empty cache. The validations run in child processes of the backend, each limited to 60 seconds and 2 GiB of address space. `SBML4HUMANS_VALIDATIONS` of `docker-compose-production.yml` sets how many run at a time, 2; without it the backend would run half the cpus it may run on, which in a container are all cpus of the host unless `--cpuset-cpus` restricts them (a cpu quota such as `--cpus` does not change the number). The validations may take their number times 2 GiB of memory, 4 GiB with 2, on top of the memory of the backend itself (its forkserver included), which grows with the largest report it builds: size `SBML4HUMANS_VALIDATIONS` so that `SBML4HUMANS_VALIDATIONS` x 2 GiB plus the backend stays within the memory the host has for it. Twice as many validations wait for a child, a further one is answered at once as busy. These numbers hold per server process: the backend runs one uvicorn process, and `--workers N` would multiply both the validations it admits and the children by N.

```bash
./deploy.sh
```

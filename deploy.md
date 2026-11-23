# Deployment

SBML4Humans is deployed as docker containers behind a proxy server: the proxy terminates https for sbml4humans.de and forwards the requests to the server which runs the containers. Setting up the deployment therefore means setting up the proxy with its certificates and then the containers on the machine behind it.

## The proxy

Log in to the proxy server `denbi-head`.

The configuration of the site is `nginx/sbml4humans.de` of the repository, which proxies to the server the containers run on. It includes two snippets of the repository: `nginx/ssl.conf`, the TLS settings (TLS 1.2 and 1.3 only), and `nginx/security-headers.conf`, the security headers and the Content-Security-Policy of the frontend. Update the IP of the server the containers run on in the configuration before you copy it (both `proxy_pass` directives), then copy the snippets, activate the site, test the configuration and reload nginx:

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

The limits of this section live in `nginx/` of the repository and are copied to the proxy by hand, with the steps above: a deploy of the containers (`deploy.sh`, below) does not carry them, so a change of them reaches the site only once the configuration is copied and nginx is reloaded. Do that with the deploy it belongs to.

The validations are limited per client by the proxy, keyed by the address of the client: the backend admits a few validations at a time for everyone (each may run 60 seconds, see the containers below), so that one client cannot keep that admission busy for all others, `location /api/validation/` allows a client 2 open validation requests at a time (`limit_conn`, with http/2 every request counts) and 12 a minute with a burst of 12 (`limit_req`). A request beyond is answered `429 Too Many Requests` by nginx, which the frontend shows as busy, like the busy answer of the backend. A request a client aborts frees its place in the proxy at once, and so it does in the backend: the backend cancels a validation whose client disconnected, it stops waiting for a child or kills its child and frees its admission, so a client cannot fill the admission by firing requests and aborting them. The one exception is the download of `GET /api/validation/url`, which is not cancelled and holds its admission until it ends, at most the 60 seconds of the download deadline. The numbers are per address: several readers behind one NAT (a university network) or one reader with several tabs share the 2 open validations and may see "busy"; raise `limit_conn` if that happens often. The zones (`limit_req_zone`, `limit_conn_zone`) are at the top of the configuration, in the `http` context the site is included in, and carry the prefix `sbml4humans_` so that they do not clash with the zones of other sites of the proxy. The limits belong to this proxy: the nginx container behind it sees the address of the proxy alone, so `nginx/config/conf.d/local.conf` limits nothing and a limit keyed by the address there would count every reader of the site as one client. The local server of `sbml4humans.show` (`/api/local/`) is not behind a proxy and not limited. To see the limits work, `grep -c '" 429 ' /var/www/logs/sbml4humans.de_access.log` counts the refused requests.

The reports of a request are limited per client in the same way and for the same reason: the backend admits three reports at a time for everyone with the `SBML4HUMANS_REPORTS: "1"` of the containers below (one child and twice as many requests waiting for it, a running report may take 180 seconds), and a report is what a reader of the site comes for, so one client must not be able to hold that admission alone. `location ~ ^/api/(file|url|content|upload|ode)(/|$)` allows a client 2 open report requests at a time (`limit_conn`) and 20 a minute with a burst of 20 (`limit_req`), which leaves a place of the admission for every other reader while a reader never meets the limit: one page view is one report, the page then asks for the validation of the same document, which is counted in the zones of the validation and not in these, the equations of a model are one download per format, six of them, and a reader who opens several models in several tabs stays below both numbers. The paths are those which build the report of a document a request brings, the four report endpoints with the downloads of `/api/ode/`; the report of an example (`/api/examples/`) is built once in the server process and kept and is not limited, while the ODE download of an example is, since it flattens and analyses that model on every request, in the server process and behind the one lock of sbmlode. A location of a regular expression wins over a location of a prefix, and this one matches no path of the locations above it, which keep the requests they had. A request beyond either number is answered `429 Too Many Requests` by nginx, which the frontend shows as too many requests from this address. Raise the two numbers together with `SBML4HUMANS_REPORTS`, never the open requests above the admission of the backend, which is three times that variable: a client which may hold all of it is what the limit prevents. `GET /api/url` is the request the limit matters most for: it is admitted before its download and the download is not cancelled, so one which points at a slow host holds its place for up to the 60 seconds of the download deadline, also when its client is already gone.

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

The backend keeps the cache of the web services (OLS, ChEBI, UniProt, the registry) on the named volume `cache` (`/cache`, `SBML4HUMANS_CACHE`) next to the volume `uploads` (`/uploads`, `SBML4HUMANS_UPLOADS`), so that it survives a restart of the container; a deploy removes the volumes (`docker-purge.sh`) and starts with an empty cache.

Every touch of libsbml with the content of a request runs in a child process of the backend: the validations, each limited to 60 seconds and 2 GiB of address space, and the reports of a request with the ODE downloads of `/api/ode/`, each limited to 180 seconds and 4 GiB of address space, which is about ten times the time and twice the memory the report of Recon3D, the largest model of the examples, takes on a development machine (17 seconds, 1.9 GB of resident memory). `SBML4HUMANS_VALIDATIONS` and `SBML4HUMANS_REPORTS` of `docker-compose-production.yml` set how many of each run at a time, 2 and 1; without them the backend would run half the cpus it may run on for each of the two, which in a container are all cpus of the host unless `--cpuset-cpus` restricts them (a cpu quota such as `--cpus` does not change the number). The two are counted apart, so that reports which fill their pool refuse no validation and validations none of the reports, and the host pays for both: `SBML4HUMANS_REPORTS` x 4 GiB for the reports, 4 GiB with 1, and `SBML4HUMANS_VALIDATIONS` x 2 GiB for the validations, 4 GiB with 2, on top of the memory of the backend itself (its forkserver included), which grows with the largest report of an example it builds and keeps, no longer with the report of a request, which its child builds and compresses, so that the backend holds it gzipped, a few megabytes even for Recon3D, unless a client which does not accept gzip asks it to expand it. Size both variables so that their memory plus the backend stays within the memory the host has for it. The memory of `denbi-node-2` is not recorded anywhere, which is the open question of these numbers: production builds one report at a time because 1 x 4 GiB and 2 x 2 GiB and the backend are about 8 GiB, which a host of this kind has, and not because the host was measured. Read the figure (`free -g` on the server, `docker stats` for what the containers use) before you raise `SBML4HUMANS_REPORTS`; without it the bound is found by the OOM killer of the kernel, which ends whichever process it picks and not the report which asked for too much. Twice as many validations and twice as many reports wait for a child, a further one is answered at once as busy, a busy report with the message to try again in a moment. These numbers hold per server process: the backend runs one uvicorn process, and `--workers N` would multiply both the work it admits and the children by N. The reports of a request are limited per client by the proxy as the validations are (`location ~ ^/api/(file|url|content|upload|ode)(/|$)` of `nginx/sbml4humans.de`, above), so that no address holds the admission of the whole server alone; a report whose client disconnects is cancelled like a validation, which frees its child and its admission at once, and the 900 seconds the proxy allows a request (`proxy_read_timeout`) leave the 180 seconds of a report room below them.

```bash
./deploy.sh
```

# Scrapy & Docker Postgres — Command Cheatsheet

## Scrapy Cache

### Clear the HTTP cache and force a fresh crawl

```bash
rm -rf .scrapy/httpcache/
```

### Disable cache for a single run

```bash
scrapy crawl bayt -s HTTPCACHE_ENABLED=False
```

---

## Docker Compose — Deployment

> When deploying this setup, the **pgAdmin** web interface will be available at port `5050`
> (e.g. `http://localhost:5050`).

### Start the containers

```bash
docker compose up
```

### Stop the containers

```bash
docker compose down
```

### Stop and delete all persistent data (volumes)

```bash
docker compose down -v
```

---

## Docker Compose — Cleanup & Reset

### Stop, remove containers, and clean up orphaned networks

```bash
docker compose down --remove-orphans
```

### Verify nothing is left running

```bash
docker ps -a | grep -E "postgres|pgadmin"
```

### Bring everything back up fresh

```bash
docker compose up -d
```

---

## Connectivity Test

### Ping Postgres from inside the pgAdmin container

```bash
docker exec -it pgadmin ping postgres
```

---

### Fix File Permission Issues in a Project Directory

If a tool (like a formatter or linter) reports **`Permission denied (os error 13)`**, some files in the project may be owned by another user (often `root`). You can reset ownership of all files in the current directory to your current user with:

```bash
sudo chown -R $USER:$USER .
```
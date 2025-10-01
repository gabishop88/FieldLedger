# FieldLedger Setup Guide

This document explains how to set up FieldLedger for development.

Thank you tiangolo for the [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template). This is the primary foundation for this project. Most of the documentation and workflow was inspired by or taken directly from that project.

## 1. Manually Installed Tools

These are the prerequisite tools that will need to be installed manually on your machine.

* [uv](https://docs.astral.sh/uv/): Python Dependency and Environment Manager
* Docker: Platform-agnostic application building and deployment.
  * You can install [Docker Desktop](https://www.docker.com/)
  * Or [Docker Engine](https://docs.docker.com/engine/install/) + [Docker Compose Plugin](https://docs.docker.com/compose/install/)(Linux) if you just want the tools without the desktop program.
* Node.js manager. Choose either:
  * Node Version Manager (nvm) [installation guide](https://github.com/nvm-sh/nvm#installing-and-updating).
  * Fast Node Manager (fnm) [installation guide](https://github.com/Schniz/fnm#installation).

> All other dependencies will be handled inside docker or via `uv`/`npm`

## 2. Clone Project

Clone the repo and `cd` into the project folder:

```bash
git clone #TODO
cd FieldLedger
```

Copy or replace `.env.example` to `.env` and fill in the indicated env variables.

Copy

```bash
cp .env.example .env
```

or Replace

```bash
mv .env.example .env
```

## 3. Running Docker

Start the full stack (backend, fronend, database, adminer, and traefik):

```bash
docker compose up --build -d
```

Check logs:

```bash
docker compose logs -f backend
```

> Replace `backend` with any container, such as `db`, `frontend`, etc.

Stop Everything

```bash
docker compose down -v
```

> While running, services will be available at:
>
> `backend` (API Base): http://localhost:8000
>
> `backend` (API Docs): http://localhost:8000/docs or http://localhost:8000/redoc
>
> `frontend` (User Interface): http://localhost:5173
>
> `adminer` (Database Manager): http://localhost:8080
>
> `traefik` (Network Dashboard): http://localhost:8090

## 4. Backend Development

### 4.1 Install Python Dependencies

```bash
cd ./backend
uv sync
source .venv/bin/activate
```

> Once you are in the `./backend` directory, you can install the required python packages with `uv sync`, which creates a virtual environment at `.venv`. To run the python backend, you will need to activate that virtual environment with the `source` command.

:warning: Make sure your editor is using `./backend/.venv/bin/python` as the python interpreter.

> #NOTE: Everything below here is copied from the full stack reference, and has not yet been implemented or verified.

### 4.2 Live reload with Docker

`docker-compose.override.yaml` mounts your code into the backend container and runs `fastapi run --reload`. This means you can edit your code locally and see changes immediately without rebuilding.

Restart container after syntax errors:

```bash
docker compose watch
```

### 4.3 VSCode Debugging

There is already a configuration in `./.vscode/launch.json` that will run the backend through the vscode debugger (`Run and debug` menu). This lets you use break points, pause and explore variables, etc. This also has live reload, similar to the docker live reload.

The setup is configured so that you can run backend tests through the VS Code Python tests lab.

### 4.4 Alembic Migrations

If you update the `models.py` or need to make changes to the database, you can do so through an Alembic migration. Once you make the changes in the Sqlalchemy models, or have the SQL script prepared for the change, you can perform an Alembic migration to apply those changes to the database, in a persistent and versioned way. 

If you are inside the `backend` Docker container:

```bash
docker compose exec backend bash
```

To get a terminal for the following commands. If you are running the backend outside of a container, you can do so with your editor's terminal. #TODO: fact check this

1. Create a new migration

```bash
alembic revision --autogenerate -m "Describe what you changed"
```

2. Apply Migration

```bash
alembic upgrade head
```

### 4.5 Backend Tests

> In VS Code or other editors, you can run tests through the python testing lab.

Run tests from command line:

```bash
bash ./backend/scripts/test.sh
```

If your stack is already up and running, and you just want to run the tests, you can use:

```bash
docker compose exec backend bash scripts/tests-start.sh
```

You can forward additional arguments to PyTest just by adding them at the end.

Once the tests are run, `htmlcov/index.html` is generated. you can open this in your browser to see test coverage.

### 4.? Future Proofing

Here are a few things that may need updated, and how to do so.

1. If `uv` needs to be updated:
   1. `uv self update` to update the local install
   2. in `./backend/Dockerfile`, change the pinned version of uv under the `#Install uv` comment to update the uv version used in the Docker image.
2. To update to a newer python version
   1. `uv python install 3.13` (or new version)
   2. `uv python pin 3.13`
   3. `uv lock --upgrade`
   4. update any references to the old version to use the newer version in `./backend/pyproject.toml`.
   5. #TODO: Figure out what else needs changed to update python version.

### 4.?? My Setup

I just wanted to put here a list of the commands I ran for my initial setup, in case they are helpful later.

(after installing general dependencies from Section 1)

1. `mkdir frontend backend`
2. `cd backend`
3. `mkdir app`
4. `uv init --python 3.12 --name app`
5. `uv add fastapi[standard] uvicorn[standard] sqlmodel alembic psycopg[binary] geoalchemy2`
6. `uv add --dev pytest mypy ruff pre-commit coverage`
7. `uv sync`
8. `uv run alembic init app/alembic`
9. Create `./backend/Dockerfile` and fill it out based on reference project
10. Edit `./backend/alembic.ini` to basically match reference project (comment the path stuff out)
11. Delete `./backend/main.py` that was created somewhere along the way (probably `uv init`)
12. Set up basic backend project structure by creating:
    1. folders `./backend/app/api`, `./backend/app/core`, `./backend/app/db`
    2. `./backend/app/__init__.py`
    3. `./backend/app/api/__init__.py`
    4. `./backend/app/core/__init__.py`
    5. `./backend/app/db/__init__.py`
    6. Create `./backend/app/api/routes` and add `./backend/app/api/routes/__init__.py`
    7. Create `./backend/app/db/crud` and add `./backend/app/db/crud/__init__.py`
13. In order to edit `./backend/app/alembic/env.py` (which is the next step) I need to implement some other project files so that I can match the `env.py` from the reference project:
    1. Create `./backend/app/core/config.py`
    2. Create `./backend/app/db/models.py`
    3. `uv add pydantic pydantic_settings; uv sync`
    4. Fill out config.py with the Settings class from the reference project
    5. Fill out FieldLedger/.env with the env variables from the reference project.
    6. I removed the DOCKER_IMAGE_FRONTEND/_BACKEND for now, and hardcoded them in `./docker-compose.yaml`
    7. I added `./.vscode/settings.json` to set the default interpreter path to the .venv created by uv. I also had to put the path to it into the `Select Interpreter` box, but it helped me get vscode to recognize and use the correct interpreter.
    8. Next, I need to start filling in `./backend/app/db/models.py`. For now, I just added a basic User mode, which will probably change soon. I will come back to this file later.
    9. Finally, edit `./backend/app/alembic/env.py`. Pretty much just used the reference project again, with minor modifications.
14. The next main stage will be setting up the database through alembic. For this, I will need to test to make sure I can create the database and connect to it, then start adding basic setup through alembic migrations, then tables, etc.
     1. For now, I commented out any models in app.db.models to keep things as simple as possible.
     2. `docker compose up -d --build`
     3. ran into an issue: `unable to get image './backend': Cannot connect to the Docker daemon at unix:///home/gbishop3/.docker/desktop/docker.sock. Is the docker daemon running?`
     4. `sudo systemctl status docker` (says active?!)
     5. `export DOCKER_HOST=unix:///var/run/docker.sock` (thanks ChatGPT). This worked for now, but I will either need to find another way or add this to a .bashrc or something?
     6. After fixing a few errors in `docker-compose.yaml` and `./backend/Dockerfile`, the containers started.
     7. 
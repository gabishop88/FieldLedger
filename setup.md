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
> `backend` (API Base): <http://localhost:8000>
>
> `backend` (API Docs): <http://localhost:8000/docs> or <http://localhost:8000/redoc>
>
> `frontend` (User Interface): <http://localhost:5173>
>
> `adminer` (Database Manager): <http://localhost:8080>
>
> `traefik` (Network Dashboard): <http://localhost:8090>

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

1. Create a new migration: `alembic revision --autogenerate -m "Describe what you changed"`
2. Apply Migration: `alembic upgrade head`

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

### 4.6 Future Proofing

#### 4.6.1 Updating tools

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

## 5. Workflows

These are short guides on how to properly edit different things.

:warning: All of these things should be done in a development environment. Please don't stop containers in a production or staging environment to make experimental changes. To apply properly tested changes, see the section on deployment (#TODO: insert link to this section?)

### 5.1 Editing the database structure

If you want to update the database structure, i.e. make changes to tables, functions, schemas, extensions, or really anything that is not just updating the data stored by the database, then you can follow these steps to make database changes in a way that they will be safe and properly versioned.

> #TODO: test this to make sure the `alembic current` part works and only returns one result, etc. Do I need something more like: `$(uv run alembic current --head-only | tr -d '[:space:]')

1. Always back up your data before making changes. Here is the command I recommend: `pg_dump -h localhost -p 5432 -U postgres -d fieldledger_db -Fc -f app/alembic/backups/$(date +%m%d%Y)_rev_$(uv run alembic current)`. Since the database in the db docker container is also accessible from localhost, this will get the data from that container. You may want to replace `localhost`, `5432`, `postgres` or `fieldldger_db` with their own values if those values were changed in `.env`. Alternately, you can modify that command to use env variables directly.
2. With your data backed up, you can make your edits:
3. Now, you should make the database changes.
   1. To edit tables, simply edit their sqlmodel representations in `./backend/app/db/models.py`.
   2. Now, begin an alembic revision with `uv run alembic revision --autogenerate -m "summary of your edits"`. Use `--autogenerate` if you edited `models.py`, or leave it out if you want to make manual changes that don't involve the tables directly.
   3. If you are making changes to schemas, functions, or other database components that are not tables (which should always be edited using `models.py`), you can open the alembic migration script for this migration (the filename is given when it was generated in the previous line) and execute SQL commands with `op.execute("SQL COMMAND")`. Even if you are just editing tables check this file to make sure the edits that were generated by alembic make sense for what you intended to change.
   4. Once you have everything in the migration checked over and ready to go, you can apply the alembic changes with `docker compose exec backend uv run alembic upgrade head`. This will apply the changes and update the database with your changes.
   5. Now, make sure that your data is still in tact, if there is an issue, some options include downgrading, restoring the data, and trying again, or in a worst-case scenario, stopping docker, deleting the volume, using alembic to recreate the database back into any revision necessary, and restoring the data from that revision using the associated file in `backups/`.
   6. Once your database modification is working, make sure to update any project code that may need to be updated to reflect the change, update or create tests to make sure the modifications are covered, and test everything to make sure something unexpected has not broken.

## ?. My Setup Process

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
      7. (after `docker compose up -d --build` for the last time) I ran `docker compose exec backend uv run alembic revision --autogenerate -m "init"`
      8. Of course there were errors, which I fixed through the `docker-compose.yaml` environment setup to generate my first alembic revision. I realized it was trying to remove a bunch of stuff provided by PostGIS, so I am going to have to do something about that before I commit any changes.
      9. I also changed `docker-compose.yaml` to bind the backend container to my project directory. It is a little risky and should probably be changed later, but allows the changes, particularly the alembic revisions to be saved in my actual project directory, meaning they will be properly saved and applied even if I destroy the docker containers and rebuild them or the volumes.
      10. `docker compose down -v` and removed all volumes as well. I am clearing everything to prepare for my next attempt.
      11. I saw that I could remove a file (`alembic.ini`) so I added the configs that are supported into `pyproject.toml` and removed the logging setup in `alembic/env.py` and it seems to work the same, but now with `alembic.ini` gone. If I need those logging config options later, I can always undo this step.
      12. Now, everything seems to (finally) be in order for my first alembic revision. I created one with `docker compose exec backend uv run alembic revision -m "extension setup"`.
      13. I realized that creating this inside the docker container made it so that I can only edit the revision file in my local editor if I use sudo to save it. To fix this, I deleted it and tried again with `uv run alembic revision -m "extension setup"` since it shouldn't matter whether I create it from inside the container or not since they share my local project directory. This had to be done inside of `cd backend`. I edited my revision (see `app/alembic/versions/467c05fa4c34_extension_setup.py`)
      14. I used `docker compose exec backend uv run alembic upgrade head` to apply the changes to the database. Afterwards, I used pgAdmin4 (doesn't matter what tool) to look at the database and make sure the updates were applied.
  15. I accidentally lost a bunch of progress working towards getting roles properly setup (including my steps here), so here are the steps I took to get back to (hopefully) where I left off:
      1. First, I had noticed that I accidentally included my .env in my commits. I purged them from my commit history (but accidentally lost my uncommited changes in the process). So, the first thing I am doing is adding .env to .gitignore.
      2. Next, I am changing my .env to change my default admin user `POSTGRES_USER` and `POSTGRES_PASSWORD` to an admin user, and in the process adding new env variables for two new users, `POSTGRES_API_USER` and `POSTGRES_READONLY_USER` (plus their passwords). These are to separate permissions into an admin role which can modify database structure and will be used by alembic, an api role that can only read/modify data, and a readonly role that I don't have a specific use for but makes sense to have.
      3. Now, I am adding a .env.example file to the git repo so that I can show what is required to have in the .env file, but not show all my secrets.
      4. With this, I am modifying my `backend/app/core/config.py` to replace `SQLALCHEMY_DATABASE_URI` with my three connections, `ADMIN_DATABASE_URI`, `API_DATABASE_URI`, and `READONLY_DATABASE_URI`.
      5. Who knows what broke in the docker container, so I am removing everything, `docker compose down -v`
      6. `alembic revision -m "role setup"` -> fill in ..._role_setup.py with role stuff.
      7. Now, test that everything is working correctly. `docker compose up -d --build`, log in on pgAdmin4 with new admin role (works)
      8. `docker compose exec backend alembic upgrade head`, check roles and schemas on pgAdmin4 (looks good!)
      9. Commit on github properly this time.
  16. I was experimenting with the copilot to help me create my first table models. I still had to do most of the work, so I am not really sure it is worth using. However, I created my first three tables: `identity.app_user`, `asset.farm`, and `ref.field_type`. This is just a sample of three different types of tables that don't rely on any other tables to get me started. Now, I used `alembic revision --autogenerate -m "first tables"`. I realized that the autogenerated revision wanted to drop the `public.spatial_ref_sys` table, so I had to add that to an `include_object` function in `backend/app/alembic/env.py` so that it would get ignored. Then, to be safe I deleted and regenerated the alembic revision. Satisfied, I ran `docker compose exec backend alembic upgrade head`. Then, commit changes!
  17. Now that I have the basic stuff in place and feel like I understand it well enough to continue building, I think it is a good time to step back and work on tests. This way, I can proceed with a test-first design strategy. This is something I am still working on learning how to do.
      1. First I created the `backend/tests` folder. I then created `backend/tests/conftest.py`. This is where my test fixtures will go. I need a decent amount of my FastAPI structure in place to get this working.
      2. The first thing I had to figure out is whether to use the same engine as FastAPI to get the session, which will mean my test results use the actual database container, and should mean that the tests are as applicable as possible. On the other hand, I could make a temporary test database that I quickly spin up using the same alembic revisions and a copy of the backup data from the actual database, which means I keep things separate and my tests can't mess up the actual database, but if there is something messed up with the database that isn't represented by the alembic revisions + recent backup, then it won't get caught by tests. Hypothetically, there is nothing wrong with using the same database to make the session, and then just delete/roll back the changes at the end.
      3. Since it is straightforward, I also created the `client` fixture that can test the API.
      4. I created the database `engine` and a connection check in `app/db/__init__.py`. I think that maybe this should be moved to its own .py file, but this at least ensures the database engine's validity automatically any time you import from the `app.db`. My reasoning for this was to avoid setting up scripts to do prechecks and initializations every time you run the app through scripts, since they will be run one whenever the project is built anyway. Since docker makes the backend container wait on the health of the db container anyway, this should always be fine.
      5. I committed these basic changes without adding any actual tests or scripts, since I still don't have much of the basic setup that I need to run the tests. I also want to figure out which of the scripts for testing, or performing alembic migrations I will need and how to integrate them.
  18. Now, since it doesn't rely on anything else, but later stuff does rely on it, I filled out `app/core/security.py`
  19. I wanted to get some basic stuff working, so I added the most fundamental routing stuff for the docs pages, openapi.json, etc. and a health check. This sets up the routing structure, but doesn't add any actually useful routes yet.
  20. Okay, now I have a little bit of stuff in place, and I have to decide on a workflow to get everything else in place in a controlled manner. Here is what I will start with, and make any needed adjustments as I go:
      1. Add a few tables to `/backend/app/db/models.py`
      2. `alembic revision --autogenerate -m "What I added"`, manually go over the revision file in `backend/app/alembic/versions`
      3. `docker compose exec backend alembic upgrade head`, manually check that my changes were properly applied to the database
      4. Make sure all of the necessary functions are in place in order to CRUD records for the new tables.
      5. Add tests to make sure I can properly modify the new tables in the database and get those records out.
      6. Add the basic endpoints to edit records through the API
      7. Add tests to fairly rigourously test those basic endpoints.
      8. [Optional] Find and add actual data to the tables
      9. [Optional] Save a data backup with the name of the revision before repeating.
  21. Before I could continue with the workflow, I had to change my models.py to have all of the models needed for the API recieve and return updates to the user table model. Then, I added a CRUD class to handle table operations (except for reading) and special functions to handle users.
  22. In the process, I changed how the database initialization and connection checks work, and added a precheck to the docker-compose to make sure everything is working properly. Afterwards, I recreated my docker containers and volumes to test that this worked as intended.
  23. For some reason, alembic completely broke. I have spent days trying to fix it, but it is just showing behaviors like dropping some tables, etc. that I can't find anywhere when looking up help.
      1. The first thing I am changing is the `identity` schema -> `iam` (Identity and Access Management). This is more descriptive (if a little jargon-y), and doesn't use the word identity, which may be a reserved word (not sure but playing it safe).
      2. I also changed the search_path for the fieldledger_admin role. I think that adding the `include_schemas=True` in the alembic `env.py` script interacted strangely with my search_path from the 4th revision including all of the relevant schemas, and caused it to keep trying to remove tables, or move them to different schemas. In the end, I just have `public` in the search_path for fieldledger_admin. I left the other schemas in the path for the other roles for now, I will see how the api interacts with the database and see if I need to change them later. For now, if you are using the admin role, you will need to fully qualify tables (schema.tablename) every time you do anything, but should be okay, since the admin role should be used by someone to make important changes, and that is probably for the best anyway to avoid confusion.
  24. I added tests for the basic endpoints. (step 5 of the workflow in section 20)
  25. I added a UserSession which is a write session, but with app.current_user session var set to the authenticated `user.id`.
  26. I added a 'RESET "app.current_user"' in each of the non-user session dependencies so that trying to SHOW it will return "" instead of error.
  27. Added the an extensions for fuzzymatching strings to the extensions migration (recreated db) and used it in the user search endpoint.
  28. Now, I was able to fill out the endpoints that I think are important for users, and write all of the tests I can think of right now for them. This also involved getting pytest set up properly, so hopefully it will take a lot less time to write tests in the future.
  29. The next major step is to start working on the asset tables/endpoints. I already have the farm table, so I will also need to add more. However, I am worried about security. I think that this is a good place to figure that out before I have too much built on top that would have to be changed.
      1. First of all, as far as I can tell, the only place that this security is necessary is when requesting information (GET Requests), since this is the only place returning multiple records.
      2. The first option is to do this at the API level. This would mean that most of my project logic stays in the python in backend/, which means less things to maintain and debug about the database itself. An implementation here would likely look like overriding get requsts using the CRUD classes and inserting filters in all requests that narrow down results to just what you have access to.
      3. The second option I can think of is an RLS policy in the database. This is definitely the safest, as it will mean the database only returns the rows a user has access to. However, this would mean that I have to write (and maintain) an RLS policy for every table that is added to the database, and those policies would have to be maintained as SQL code in the migrations scripts that add those tables. This isn't the end of the world, but probably not ideal. In practice, this will probably look like a policy that checks the "app.current_user" session variable, then uses an access table like iam.user_access to give access to rows connected to the farms that have access.
      4. The third option is to create secure views. This is similar to the previous option, but a slightly different approach. Here, when I create a table, I would also create a view that uses "app.current_user" to filter the rows. Then, instead of querying from the table, the API would query from the view. This has nearly all of the same drawbacks and advantages as the previous method.
      5. The fourth option is a mix between the second and third. Here, I would create an RLS policy on the asset.farm table, and then use views for the other tables that have to be filtered that will join with the farm table. This should essentially make a single RLS policy, and then use that to filter access to anything that is connected to the farm table. This option could be done with views like option 3, but it could also possibly be done with sqlalchemy filters on every request, like in option 1? I am genuinely not sure what the best policy or combination of policies is for RLS in this app.
      6. Is it acutally better to just skip this for now, let every user access every record, and then come back and implement whichever makes sense once it becomes important? Right now, we literally are just storing data for the South Farms. RLS probably isn't important unless we actually need to separate access, e.g. if we had data from lots of farms and users that should only have access to some. It doesn't seem like any of these methods would actually be that hard to implement later. I am already setting the session variable, so I don't think I even need to worry about that, which means all I would need to do is: add logic to get funcs in CRUD (and use those funcs if I wasn't) OR add RLS policies to all tables OR add RLS to asset.farm and either views to the other tables that rely on asset.farm, or just add the same filters that I would be using to make those views to the get functions mentioned previously.
  30. I noticed that the `asset.farm` table didn't have a Unique constraint on `asset.farm.name`. I feel like this is important, so I went to go back and edit the first_tables revision, since it is not too late to make changes like that. In the process, I noticed that none of the constraints come with names by default in alembic. It is recommended to set these names manually in the alembic revision scripts. However, the way I have built this project, this is something that can be done later if it becomes important and the db can be rebuilt without affecting anything. For now, I am going to leave a note that this should be done, and that I should come back and do this if I ever do something where I need to refer to any constraint by name. I did add the unique constraint to farm here, but left the default naming.
  31. I have already noticed that it is a pain to edit Exception messages. Should I collect them in one place so they are easy to edit? Maybe a StrEnum?
  32. I added endpoints to CRUD the farm table, and tests as well.
>
> * identity.get_current_user()
> * audit.change_trigger() (+ add as trigger on all tables)
> * asset.match_fields(farm, queries, olap)

Things I am putting off for now that may need to be revisited:

* Implementing RLS. This should be done if the db is expanded to hold data outside of the organization where access control is needed.
* Naming convention for table constraints. This should be implemented if I need to do anything that refers to a constraint by name, otherwise it is fine to put off.
* Centralize(ish) exception messages by hardcoding the strings, maybe in a StrEnum?

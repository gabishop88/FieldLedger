# FieldLedger Setup Guide

This document explains how to set up FieldLedger for development.

Thank you tiangolo for the [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template). This is the primary foundation for this project. Most of the documentation and workflow was directly inspired by that project.

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

New Updates:

0. For each of the commands shown below, the shortest version that can work is shown. These can all be run through uv and/or docker using the following modifications:
    * If you are having issues with a command or library not existing, try `uv run <command>` to run using everything that has been installed through uv.
    * E.g. `uv run python -m app.db.backup`
    * If you want (or need) to run any command in the docker container that is running the API or PostGIS, use `docker compose exec <service name> <command>`. The service name for the API is `backend` and for postgis is `db`.
    * E.g. `docker compose exec backend uv run alembic upgrade head` (this also uses the `uv run` part).
1. To backup the current data prior to modifying the database, run `python -m app.db.backup`.
2. Applying Edits
    0. I recommend running `alembic revision --autogenerate -m "Checking Autogenerate"` and looking at the generated revision to make sure both `upgrade()` and `downgrade()` functions are empty, which means there are no pending changes before you make your modifications that could create unintended behavior later. **Make sure to delete this "checking_autogenerate" revision from `backend/app/alembic/versions` before moving on to the next step**
    1. Then, Edit SQLModel representations in `backend/app/db/models.py`.
    2. Create your actual revision with `alembic revision --autogenerate -m "99 Short summary of changes"` where 99 is the next number that hasn't been used yet in `backend/app/alembic/versions`. This is purely to help a person understand the revision order and will not change the functionality.
    3. Go into the newly generated revision file, `backend/app/alembic/versions/abcd12349876_99_short_summary_of_changes.py`, and make sure the changes are exactly what you want. **Always do this, even if you think the changes are simple**. The `upgrade()` function should include tables you create or remove, changes to table rows, etc. Every change you made in `models.py` should be reflected here with a line of sqlalchemy. The `downgrade()` function should always perfectly undo what is done in `upgrade()`. If there are missing or additional changes you do not expect, I recommend trying to fix it by carefully checking `models.py` and regenerating the revision rather than just making the changes, as it is easy to make mistakes that will lead to later revisions experiencing unintended behavior or the database getting out of sync with the API. There are a few changes that often have to be made to the revision file that will not be handled by autogenerate. These include:
        * sa.Uuid() -> sa.UUID()
        * Add changelog trigger for new tables: `op.execute("""--sql
            CREATE TRIGGER table_audit
            AFTER INSERT OR UPDATE OR DELETE ON schema.table
            FOR EACH ROW EXECUTE FUNCTION audit.change_trigger();
            """)`
        * `import sqlmodel.sql.sqltypes as sm` and replace `sqlmodel.sql.sqltypes` with `sm` everywhere.
        > Keep this list updated.
    4. Once the alembic revision has been thouroughly checked, you can use `alembic upgrade head` to apply the newest update.
    5. This upgrade should keep the data from previous revisions, but I highly recommend looking at most of the tables to make sure the data is still in tact and then making a new backup that is compatible with the new revision using `python -m app.db.backup`. If there is something wrong with the data, you can downgrade to the previous revision code, clear/reload the data from the dump, and try again with the new revision, or you can delete the container and/or volume and edit `backend/app/db/prestart.py` to (temporarily) upgrade to a specific version instead of the latest revision by replacing `"head"` in `["alembic", "upgrade", "head"]` with the revision code (the number at the beginning of the revision filename).
    6. Now that the changes have been applied to the database, make sure to update any CRUD functions, endpoint functions, and tests based on those changes.

## 6. The Process

(after installing general dependencies from Section 1)

  1. `mkdir frontend backend`
  2. `cd backend`
  3. `mkdir app`
  4. `uv init --python 3.12 --name app`
  5. `uv add fastapi[standard] uvicorn[standard] sqlmodel alembic psycopg[binary] geoalchemy2[shapely]`
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
      2. `alembic revision --autogenerate -m "What I changed"`, manually go over the revision file in `backend/app/alembic/versions`
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
  33. I was really tired of looking for exception detail messages while writing tests, and making sure they were formatted the same between using similar detail messages, so I added app/api/messages.py with a StrEnum called `ExeMsg` that will store consistent exception messages to reuse across the app and in tests.
  34. The next thing I want to work on before I go throuugh another round of adding tables is to add some data to the database and set up the data migration stuff (so that after I run alembic revisions, it should also bring in any data I have associated with that version). I have to make sure to be careful with my revision workflow. I also have to decide whether I should overwrite previous backups, or save them like: `revision_timestamp.dump` and get the newest The steps should look like:
      1. Develop db changes
      2. `alembic revision --autogeneratae -m ""`
      3. save backup of previous data just before upgrading db (overwrite previous?)
      4. `alembic upgrade head`
      5. save backup of current data with updated revision
      6. Now it is safe to regenerate the database and everything, just make sure to occasionally make new backups.
  35. Okay, I added `app/db/backup.py`. Now, a backup can be manually created with any of the following methods:
      1. `docker compose exec backend uv run python -m app.db.backup`
      2. `docker compose exec backend uv run python app/db/backup.py`
      3. `uv run python -m app.db.backup` (If this says the pg_dump version is incompatible, you may need to install `postgresql-client-18`, and maybe set `PATH=/usr/lib/postgresql/18/bin:$PATH` to make sure you are using the version 18 pg_dump to match the db.)
  36. I don't really like the change I had to make to `backend/Dockerfile` to install the pg_dump tool. See about changing this in the future.
  37. The last thing I can think of that should be added before I move on is the `audit.changelog` table. This will just sit in the background and hopefully not be thought about unless something goes wrong and we need to see what happened. I created the table manually with a revision and added it to be ignored in autogeneration. This is because I didn't want to add it to `models.py` since it should not be used by the API. If for some reason it ever is used by the API, just add it to `models.py` in the same way it was originally defined, and then remove from the ignore in `env.py` (then autogenerate a revision to make sure it is empty).
  38. I feel like I am ready to add new tables. For this round, I want to add `ref.boundary_type`, `ref.product_type`, `ref.equipment_type`, `ref.unit`, `ref.crop`, `asset.field`, `asset.field_boundary`, `asset.product`, `asset.equipment`. That's quite a few tables, but they are generally related. Part of adding all of these is including the important API endpoints and tests.
  39. Here, I went back and fixed a series of issues that were caught by both tests and manual testing. This was a long process, but at the end I am prepared to start adding the above tables and data.
  40. After adding the tables via app/db/models.py, using alembic and manually validating the alembic revision script, I added some initial values for `ref.boundary_type`, `ref.field_type`, `ref.product_type`, and `ref.unit`. I added crud methods for ref tables and the field table, as well as basic tests for everything so far. I also added data into `asset.field` and `asset.field_boundary`, but I still need crud, endpoints, and tests for field_boundary.
  41. Finished basic crud, endpoints and tests for `asset.field_boundary` added inital values from MDJ data and added a note that they are from MJD.
  42. Before moving on, I took a look at the tables I have to see which have data, which still need it, and whether I could address them at this time. The existing tables that were still empty are `ref.crop`, `ref.equipment_type`, `asset.equipment`, `asset.product`. I need access to the Operations Center - Equipment API in MyJD before I can fill out `ref.equipment_type` and `asset.equipment`, so I added 53 reasonable crops for now, with more to come later if necessary.
  43. Afterwards, I noticed that I had also missed `asset.product`, so I wanted to focus on filling in these tables now that I had access to equipment in the Operations Center. I used the /equipmentTypes and /equipmentISGTypes endpoints to fill out `ref.equipment_type`.
  44. While I was working on `asset.equipment`, I realized that the table has a `farm_id` FK column. I am not sure this makes much sense for the University data, since all of the `asset.equipment` and `asset.product` equipment should probably have ownership at the organization level, and I also have to choose whether my solution becomes too specific to the university or if I try to still allow for data from a farm that is individually owned rather than by an organization. This also realates to the issue of row-level access control for AppUsers. I think the best option for now is to make an Org table that owns the assets and for individually owned farms in the future, it may just have to create a dummy org internally to handle all of that. Then, users will get access to the org? may need to add other options down the line, but this seems like a reasonably futureproof solution, and it follows MyJD's conventions.
  45. I didn't like how the API endpoints were shaping up, they were getting really long unncessarily, and it would only get worse if I added the org level to the hierarchy as it was. So, I decided to refactor the endpoints (and therefore supporting functions and tests) to be more condensed.
  46. I first removed all of the `*_type` tables in the `ref` schema. I moved those values into enums in `app.core.enums` and fixed everything else to use them properly. They have the same values, and these values can be easily modified in enums.py and the new values will be used immediately. The only downside currently is that existing table values will not be updated automatically like they would be with an FK.
  47. I added all of the operation tables, `field_op`, `op_input`, `op_output`, and `op_equipment`. I also added columns to the latter three to store measurements relating to those resource uses. I have spent a lot of time working to properly collect, format, and sync data from Operations Center APIs to fill out these tables.
  48. I added a miscellaneous endpoint to allow me to get a current ERD of the database as a mermaid diagram. I served this as a webpage to render the markdown, so you need to request it through a browser (localhost:8000/api/v1/erd) rather than the docs page if you want the rendered version and not just the HTML.
  49. I spent a few months learning and experimenting with MyJohnDeere Operations Center APIs. Part of this process was also using that data to make the kinds of example outputs and visualizations that I want my API to be capable of. I wrote a script to get data from those APIs, format it into something usable, find obvious garbage data, etc. This script uses eTags to request only updated information in preparation for creating my official sync pipeline. Near the end of working on this, I learned through a support ticket that John Deere is planning on deprecating eTags in the next year, even though their documentation does not mention it.
  50. I have started using a tool called redis through docker along with a python library called arq to make an asynchronous worker that can execute tasks put into the redis queue. I am working to adapt the previous sync script for this workflow, with the plan to use webhooks instead of eTags, which is the direction John Deere is moving in.
  51. I added the integration schema with jd_connection and jd_record_link to allow for a sync protocol, but these are subject to significant change as I discover the best way to integrate a sync into the API.
  52. I added the redis and sync_worker services to docker-compose.yaml. I seem to have caused an issue though where when I ran `docker compose` the sync_worker generated a bunch of `__pycache__`, `.venv`, and `.uv` files that are owned by root and it messed up my local interpreter. I moved around the docker bind to only mount backend/app and backend/tests instead of all of backend in `docker-compose.yaml`, which seems to have resolved the issue by allowing me to keep the `.venv` that is local and the one generated by the docker image separate.

Loose Notes and TODOs:

* Implementing RLS. This should be done if the db is expanded to hold data outside of the organization where access control is needed.
* Naming convention for table constraints. This should be implemented if I need to do anything that refers to a constraint by name, otherwise it is fine to put off.
* I should tweak the String similarity thresholds for searching, but that will have to happen once I have data in there to do a bunch of testing with. If there are a couple of really good values, then I can maybe centralize them in settings or something.
* It is also worth noting that the trigger function runs per row in a transaction. This means for sessions with bulk transactions, the function will call a select on iam.app_user and alembic_revision tables for every row in the transaction. This can cause some slowdown on bulk operations. I don't expect large bulk insertions that need to be fast as a common use-case for the API, so I am not worrying about this. If this becomes an issue later, the app_user and revision values that are compused in change_trigger() can be cached at the beginning of the transaction to be reused. For example, by wrapping the trigger in a trigger function that triggers once per transaction that gets those values and calls the current trigger function for each row and passing the values (change_trigger modified to take them as parameters).
* I could add a check constraint to ref.unit like "(si_unit_name <> name) OR (si_conv = 1.0)" to ensure SI base units refer to themself with a multiplier of 1.0.
* For now, I am cascading deletes over FKs. If I want to reduce the risk of accidental deletion, I may want to change that behavior or handle it manually?
* I need to figure out where I should have a fk be a string vs the Relationship() object? Especially for reference column like `field.type`.
* Should I make `asset.product.farm_id` nullable so that I can create cross-farm products, like 'default' options that everyone has access to?
* Should I add a `ref.equipment_type.category` column like `ref.product_type.category`?
* Everywhere I have a FK in models.py, should I add the `max_length` or is it fine since that constraint is on the col it references? like `ColInfo(sa_column=Column(ForeignKey(...), nullable=False), max_length=32)` or something.
* Is it okay to use the AutoString for everything in models.py (by just using str annotation)? Should I remove the max_length=255 constraints?
* Should I add a superuser endpoint that executes a data backup?
* I am thinking about allowing uuid searching in places where it is less important (like you can give a partial uuid and it will match it if it is the only uuid that starts with that sequence? kind of like the alembic revision searching).
* I could generate enum types that have the reference table values and then use those as the type annotation (instead of str) in the models with FKs to those reference tables. This would tell the fastapi schema what values are allowed.
* Should I change the 'farm' uri prefix to 'farms'?
* Should I add tests for `app/api/deps.py`, `app/api/router.py`, `app/core/settings.py`, `app/core/security.py`, `app/db/crud/*.py`, `app/main.py`?
* Should I add `standard_payable_moisture` to `ref.crop`?
* Should I add `bale` and `lb1bale-1` to `ref.unit` (and fill in relevant `ref.crop.density` values)?
* Should I modify `backend/app/alembic/env.py` to run a `python -m app.db.backup` (or the functions inside it) before and after upgrades?
* Should I provide a command line argument or env var for docker when I compose to pass `prestart` a different alembic revision? Only seems useful to try to fix broken db and apply a previous data backup from and old revision. There is probably an easier way to go about that and I could probably just provide instructions to fix things should that situation occur.
* Should I put `Energy Farm` under a different org (and maybe some of the others) and then I can also work later with sharing resources between orgs?
* Should I make endpoints that return either paginated json or csv with embed options to allow building up any amount of the structure in each row/object? E.g. list all farms with orgs. List all fields with farms, list all fields with farms and orgs. List all fields with boundaries, list all operations with fields, boundaries, farms, and orgs, etc.
* Should I make an endpoint that a frontend could use to basically get a tree of objects to make it easier/faster/fewer requests to get the info about everything a user has access to to fill the UI (probably wait until I know more about what this would require).
* Should I add a `resource.equipment.fuel_use` (+`unit`) column?
* What kinds of geometrically conscious features should I provide?
  * Try to search for field records based on a point or polygon
  * Generate a crop/management history for a point/polygon
  * Tools for changing/splitting/merging boundaries?
* What kinds of features could be useful to help with data curation? Like tools to easily find and fix missing/unusual data
  * Checks for probable duplicate entries
  * Checks for important missing information
  * Some way to send in information that may be overlapping and only incorporate new information (maybe ask when uncertain)
  * Maybe even some kind of method to generate a list of cleaning tasks so you can just go through them, answer questions, put some off, etc.
  * Data scanning, but also data curation at time of input
  * Reasonable ranges for values+units and confirmation for values outside of those bounds.
* I want to go back and clean up the equipment table, It kind of looks terrible.
* Replace all of the x + x_unit columns with a single string column and use postgresql-unit extension
  * Also define an enum of the units I allow people to use so it can be a dropdown instead of typing.
  * Maybe instead of one enum have a few for different quantities or columns so that I can give the available options per table.column
* `from sqlmodel import Field as ColConfig` instead of `ColInfo` in `app.db.models`?
* Divide `app.db.models` into multiple files by schema or just break apart to separate the actual table models?
* Create a `CropCreate` and `CropPublic` model in `app.db.models`?
* Remove `density_unit` from `Crop` models?
* Make alternate `xPublic` models that include Relationships instead of the PK to return nested jsons and provide a query param or header to request them?
* I need to encrypt tokens like access_token and refresh_token in `JDConnection`, but I will need to get a stable SECRET_KEY or the refresh token in particular will be invalidated every time the API starts (see settings.SECRET_KEY in app.core.config).
* Should I try to make the jd/oauth-capture function more secure by ensuring that the user_id passed through state came from the same person that initiated the authorization process? Would this even help in terms of security?
* write test cases to exhaustively test all sync state transitions for `change_state` since it is very complicated. Ideally, just see which function was called and what the resulting state is.
* Should I move the backups from `backend/app/alembic/backups` to another folder outside of `backend/app` so that it cannot be generated by the docker containers, which means I won't end with root owned backups? I think it means that backups generated locally can be applied locally or by container, but those generated by the container can only be applied by the container or using root permissions? I think this is *ok*, since the backups are almost exlusively applied by the prestart service, meaning it can probably use them? I should at least test this.
* I should probably move where the `.coverage` directory is generated, or add `app/.coverage` to the relevant `docker-compose.yaml` volumes with `.venv` and `.uv` in order to seperate them from the locally generated version.
* I need to eventually protect the redis container since it is unprotected will theoretically accept connections and maybe? queue sync jobs from unauthorized sources if someone spent the time or effort to make that happen. The ideal solution is probably to restrict it to only accept jobs from the API directly.
* I removed FLAG as a sync state because I want to have some kind of flagging system available later. Basically, I don't want to call them flags (even though they are) because John Deere has literal flags as points in the field you can attach a label to, but I am refering to warning flags for garbage data. For now, I may put in some basic warning logs for bad data, but evenually, I want an IntEnum of quality-flags on different tables so that I can automatically and users can manually mark things with flags to indicate different things. This will probably be complicated, though, which is why I am putting it off.
* In the `change_status` function, I should prevent an update from DIRTY to anything until I have checked that there are no other jobs working on the update currently. Do do this, I will have to use job names or ids in the redis pool and key them on the resource link.
* Maybe add a state transition table to the status change function in sync.py, it is a bit confusing.
* I will need to test the John Deere sync stuff. In order to do so, I should make a test version of the JDClient that will give me example data for testing.
* To deal with the bad data, I could incorporate an LLM (ideally locally run, as docker container?) to identify and maintain flags for potential bad data. To go with bad data detection, I could have a tool designed to allow the frontent to generate a link that the user could click to send the changes to John Deere. Basically, instead of just giving them a link to go find the thing on Op Center and fix it, I could package the change as an API request that could be sent off (ideally with a cool animation) to make that change, and then the change would get propogated back to the FieldLedger UI through sync so you know it was successful.
* Is there any way that I could use simulations like SCE to help with decision on crop rotations? Could I use a farm's historical data to train a simulation to be much more accurate for their farm so that they can simulate new scenarios, and maybe even export APSIM files that would allow them to use other simulation tools with that higher accuracy?
* Before this tool is published, I should add a table to the `audit` schema for bug reports and user feedback and put into place a feedback system?
* Should I have op_inputs and op_outputs? If I only ever have inputs OR outputs for a given operation, it would kind of make sense to just have op_product and op_equipment?

Could I take a dataset from Dryad, ideally from UIUC, that has a location component and use it to illustrate the tool's capabilities?

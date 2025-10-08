from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.models import SQLModel
from app.core.config import settings

# Access to the config options in the .ini file
# `opt = config.get_main_option("opt")` to get options from .ini to use in env.py.
config = context.config

# NOTE: I commented this section so I could delete alembic.ini.
# If I need to work with logging, I can either add back alembic.ini or do it manually.
# Set up loggers, interpret config file for python logging
# from logging.config import fileConfig
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = SQLModel.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Return True if Alembic should include this object in autogenerate.

    We skip the PostGIS `spatial_ref_sys` table because it is a system table
    managed by the PostGIS extension and should not be dropped or recreated
    by migrations.
    """
    # object may be None for some autogenerate hooks; just include in that case
    if type_ == "table" and name == "spatial_ref_sys":
        return False
    return True


def get_url() -> str:
    return str(settings.ADMIN_DATABASE_URI)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as conn:
        context.configure(
            connection=conn,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

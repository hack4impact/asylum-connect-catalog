#!/usr/bin/env python
import os
import subprocess
# from config import Config

from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Shell
from redis import Redis
from rq import Connection, Queue, Worker

from app import create_app, db
from app.models import (CsvBodyCell, CsvBodyRow, CsvContainer, CsvHeaderCell,
                        CsvHeaderRow, Descriptor, OptionAssociation,
                        RequiredOptionDescriptor, Resource, ResourceBase,
                        ResourceSuggestion, Role, TextAssociation, User)

# Import settings from .env file. Must define FLASK_CONFIG
if os.path.exists('.env'):
    print('Importing environment from .env file')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(
        app=app,
        db=db,
        User=User,
        Role=Role,
        CsvBodyCell=CsvBodyCell,
        CsvBodyRow=CsvBodyRow,
        CsvContainer=CsvContainer,
        CsvHeaderCell=CsvHeaderCell,
        CsvHeaderRow=CsvHeaderRow,
        ResourceBase=ResourceBase,
        ResourceSuggestion=ResourceSuggestion,
        Descriptor=Descriptor,
        TextAssociation=TextAssociation,
        OptionAssociation=OptionAssociation)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.drop_all()
    db.create_all()
    db.session.commit()


@manager.option(
    '-n',
    '--number-users',
    default=10,
    type=int,
    help='Number of each model type to create',
    dest='number_users')
def add_fake_data(number_users):
    """
    Adds fake data to the database.
    """
    User.generate_fake(count=number_users)
    ResourceSuggestion.generate_fake_edits()
    ResourceSuggestion.generate_fake_inserts()


@manager.command
def add_seattle_data():
    Resource.add_seattle_data()


@manager.command
def setup_dev():
    """Runs the set-up needed for local development."""
    setup_general()

    admin_email = os.environ.get('ADMIN_EMAIL') or 'maps4all.team@gmail.com'
    if User.query.filter_by(email=admin_email).first() is None:
        User.create_confirmed_admin('Default', 'Admin', admin_email,
                                    'password')


@manager.command
def setup_prod():
    """Runs the set-up needed for production."""
    setup_general()


def setup_general():
    """Runs the set-up needed for both local development and production."""
    Role.insert_roles()
    RequiredOptionDescriptor.init_required_option_descriptor()


@manager.command
def run_worker():
    """Initializes a slim rq task queue."""
    listen = ['default']
    conn = Redis(
        host=app.config['RQ_DEFAULT_HOST'],
        port=app.config['RQ_DEFAULT_PORT'],
        db=0,
        password=app.config['RQ_DEFAULT_PASSWORD'])

    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()


@manager.command
def format():
    """Runs the yapf and isort formatters over the project."""
    isort = 'isort -rc *.py app/'
    yapf = 'yapf -r -i *.py app/'

    print 'Running {}'.format(isort)
    subprocess.call(isort, shell=True)

    print 'Running {}'.format(yapf)
    subprocess.call(yapf, shell=True)


if __name__ == '__main__':
    manager.run()

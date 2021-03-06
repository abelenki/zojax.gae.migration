# -*- coding: utf-8 -*-

import os
import webapp2, ndb
import logging

from jinja2 import Template
from webapp2_extras import jinja2

from google.appengine.ext import db
from google.appengine.api import taskqueue

from .migrate import default_config, MigrationEntry
from .migrate import read_migrations, MigrationList, call_next, get_migration_dirs



class BaseHandler(webapp2.RequestHandler):
    """
         BaseHandler for all requests

         Holds the auth and session properties so they are reachable for all requests
     """
    config_key = __name__

    def __init__(self, request=None, response=None):
        super(BaseHandler, self).__init__(request=request, response=response)

        self.config = request.app.config.load_config(self.config_key,
                        default_values=default_config,
                        #user_values=config
                        )
        self.migration_model = self.config.get("migration_model", MigrationEntry)

        self.migrations = read_migrations(get_migration_dirs())


    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.

        context["request"] = self.request
        context["uri_for"] = self.uri_for

        rv = self.jinja2.render_template(_template, **context)

        self.response.write(rv)



class MigrationHandler(BaseHandler):
    """
    Handler for running the migrations.
    """
    template = Template(open(os.path.join(os.path.dirname(__file__),
                                            "templates",
                                            "migrate.html")).read())

    def get(self):
        self.render_response(self.template, **{
                                                "entities": self.migrations,
                                                })
        return


class QueueHandler(BaseHandler):
    """
    Puts migrations into task queue.
    """

    def get(self):

        action = self.request.GET.get("action")
        target_index = self.request.GET.get("index", None)
        application = self.request.GET.get("app")

        call_next(self.migrations, application, target_index, action, self.uri_for("migration_worker"))

        self.redirect_to("migration")

        return


class MigrationWorker(BaseHandler):

    def post(self):
        application = self.request.get('application')
        action = self.request.get('action')
        index = self.request.get('index')
        target_index = self.request.get('target_index')

        if not action or not index or not target_index or not application:
            return

        try:
            migrations = self.migrations[application]
            migration = migrations[int(index)]
        except (ValueError, IndexError, KeyError):
            migration = None
            migrations = []

        if migration is not None:
            migration.target_index = target_index
            getattr(migration, action)()


class MigrationStatus(BaseHandler):

    def post(self):

        status = self.request.get('status')
        try:
            id = int(self.request.get('id'))
        except (ValueError, TypeError):
            id = None

        migration_object = self.migration_model.get_by_id(id)

        if migration_object:
            if status == "rollback success": # we can entirely remove the migration entry
                #logging.info("MigrationStatus: removing migration_object %s " % str(migration_object))
                migration_object.key.delete()
                return

            migration_object.status = status
            migration_object.put()
            #logging.info("MigrationStatus: put migration_object %s " % str(migration_object))
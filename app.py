from tornado import web, gen, template
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import parse_command_line
from tornado.escape import json_decode
from db import dsn
import logging
import psycopg2
import momoko
import arrow
import json
import os

# logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
root = os.path.dirname(os.path.abspath(__file__))
loader = template.Loader(os.path.join(root))

class BaseHandler(web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    @property
    def select(self):
        return """SELECT raw
                    FROM metrics
                    WHERE name = ALL(%(name)s)
                    AND ts <@ tsrange(%(sts)s, %(ets)s, '[]');
                """

    @property
    def insert(self):
        return """INSERT INTO metrics (name, value, ts, raw)
                   VALUES (%(name)s, %(value)s, %(ts)s, %(raw)s);
                """


class MetricsAPI(BaseHandler):

    @gen.coroutine
    def get(self):
        try:
            name = self.get_arguments('name')
            sts = self.get_arguments('sts')
            ets = self.get_arguments('ets')
            sts = sts[0] if len(sts) == 1 else None
            ets = ets[0] if len(ets) == 1 else None
            params = dict(name=name,sts=sts,ets=ets)
            cursor = yield self.db.execute(self.select, params)
        except (psycopg2.Warning, psycopg2.Error) as error:
            self.write(str(error))
        else:
            self.write(json.dumps([m[0] for m in cursor.fetchall()]))
        self.finish()

    @gen.coroutine
    def post(self):
        try:
            metric = json_decode(self.request.body)
            metric['raw'] = json.dumps(metric)
            metric['ts'] = arrow.get(metric.get('ts')).datetime
            yield self.db.execute(self.insert, metric)
        except (psycopg2.Warning, psycopg2.Error) as error:
            self.write(str(error))
        else:
            self.write(json.dumps({'resp': 'success'}))
        self.finish()


if __name__ == '__main__':
    parse_command_line()

    app = web.Application(
        handlers=[
            web.url('/v1/metrics', MetricsAPI),
        ],
        debug=False
    )

    ioloop = IOLoop.instance()

    app.db = momoko.Pool(
        dsn=dsn,
        size=19,
        ioloop=ioloop,
    )

    future = app.db.connect()
    ioloop.add_future(future, lambda f: ioloop.stop())
    ioloop.start()
    future.result()  # raises exception on connection error
    server = HTTPServer(app)
    server.listen(5000, "127.0.0.1")
    ioloop.start()

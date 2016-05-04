from tornado import web, gen, websocket
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.escape import json_decode
import psycopg2
import momoko
import arrow
import json
import logging
from urllib.parse import urlparse
import os


WSS = []  # websockets


class SocketHandler(websocket.WebSocketHandler):
    """
    The websocket handler defines the basic functionality of the
    websockets. Javascript snippet to try in browser:
    socket = new WebSocket('ws://127.0.0.1:5000/v1/ws');
    """

    def check_origin(self, origin):
        return True

    def open(self):
        if self not in WSS:
            WSS.append(self)

    def on_message(self, message):
        print(message)

    def on_close(self):
        if self in WSS:
            WSS.remove(self)


class BaseHandler(web.RequestHandler):
    """
    Helper class to store frequently accessed properties like
    database connection and queries.
    """

    @property
    def db(self):
        return self.application.db

    @property
    def select(self):
        return """SELECT raw
                    FROM metrics
                    WHERE name = ALL(%(name)s)
                    AND ts <@ tstzrange(%(sts)s, %(ets)s, '[]')
                    ORDER BY ts;
                """

    @property
    def insert(self):
        return """INSERT INTO metrics (name, value, ts, raw)
                   VALUES (%(name)s, %(value)s, %(ts)s, %(raw)s);
                """


class MetricsAPI(BaseHandler):
    """
    This is the main meat of the API.  Here we define the GET and POST handling.
    Note that 'name' must either be an empyt list or a list of one element to be
    to the the db.execute.
    """

    @gen.coroutine
    def get(self):
        try:
            name = self.get_arguments('name')
            sts = self.get_arguments('sts')
            ets = self.get_arguments('ets')
            sts = sts[0] if len(sts) == 1 else None
            ets = ets[0] if len(ets) == 1 else None
            params = dict(name=name, sts=sts, ets=ets)
            cursor = yield self.db.execute(self.select, params)
        except (psycopg2.Warning, psycopg2.Error) as error:
            self.set_status(400)
            self.write(str(error))
        else:
            self.write(json.dumps([m[0] for m in cursor.fetchall()]))
        self.finish()  # ends the http part of the request

    @gen.coroutine
    def post(self):
        try:
            metric = json_decode(self.request.body)
            metric['raw'] = json.dumps(metric)
            metric['ts'] = arrow.get(metric.get('ts')).datetime
            yield self.db.execute(self.insert, metric)
        except (psycopg2.Warning, psycopg2.Error) as error:
            self.set_status(400)
            self.write(str(error))
        else:
            self.write(json.dumps({'resp': 'success'}))
        self.finish()  # ends the http part of the request
        for ws in WSS:
            ws.write_message(metric['raw'])


class IndexHandler(web.RequestHandler):
    """Serves the index.html page"""

    def get(self):
        self.render("index.html")


if __name__ == '__main__':

    hobby_url = 'postgres://yydnwotpybvjqe:zWt1CPlryiEmQbxL4HRXNpGPs-@ec2-50-16-230-234.compute-1.amazonaws.com:5432/ddnifpbdv12vc6'
    host = os.environ.get("DOMAIN", "127.0.0.1")
    port = os.environ.get("PORT", "5000")
    db_url = urlparse(os.environ.get("DATABASE_URL", hobby_url))
    dsn = (
        'dbname={} '
        'user={} '
        'password={} '
        'host={} '
        'port={}'.format(db_url.path[1:], db_url.username, db_url.password, db_url.hostname, db_url.port)
    )

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

    app = web.Application(
        handlers=[
            (r'/', IndexHandler),
            (r"/static/(.*)", web.StaticFileHandler, {"path": "static/"}),
            (r'/v1/metrics', MetricsAPI),
            (r'/v1/ws', SocketHandler)
        ],
        debug=True
    )

    ioloop = IOLoop.instance()

    app.db = momoko.Pool(
        dsn=dsn,
        size=15,
        ioloop=ioloop,
    )

    future = app.db.connect()
    ioloop.add_future(future, lambda f: ioloop.stop())
    ioloop.start()
    future.result()  # raises exception on database connection error
    server = HTTPServer(app)
    server.listen(port, host)
    ioloop.start()

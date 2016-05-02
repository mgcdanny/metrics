import signal
import logging
from tornado import web, gen, httpclient, httpserver, ioloop, template
from db import Metric, Session
import os
import json
from tornado.escape import json_decode
from datetime import datetime
import arrow


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
root = os.path.dirname(os.path.abspath(__file__))
loader = template.Loader(os.path.join(root))

QUERY = """SELECT raw
           FROM metrics
           WHERE name = ALL(:name)
           AND ts <@ tsrange(:sts, :ets, '[]');"""


class MetricsAPI(web.RequestHandler):

    @gen.coroutine
    def get(self):
        name = self.get_arguments('name')
        sts = self.get_arguments('sts')
        ets = self.get_arguments('ets')
        sts = sts[0] if len(sts) == 1 else None
        ets = ets[0] if len(ets) == 1 else None
        params = dict(name=name,sts=sts,ets=ets)
        session = Session()
        metrics = session.execute(QUERY, params).fetchall()
        session.commit()
        session.close()
        self.write(json.dumps([m[0] for m in metrics]))
        # self.write(json.dumps({'a':1}))

    @gen.coroutine
    def post(self):
        metric = json_decode(self.request.body)
        metric['raw'] = metric.copy()
        metric['ts'] = arrow.get(metric.get('ts')).datetime
        session = Session()
        session.add(Metric(**metric))
        session.commit()
        session.close()
        self.write(json.dumps({'resp': 'success'}))


app = web.Application(
    handlers=[
        web.url('/v1/metrics', MetricsAPI),
    ],
    debug=True
)


if __name__ == '__main__':
    logging.info('Starting http server')
    server = httpserver.HTTPServer(app)
    server.bind(5000, "127.0.0.1")
    server.start()
    loop = ioloop.IOLoop.instance()
    loop.start()

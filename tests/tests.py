# Running this script from the command line will DROP and CREATE the metrics table
# It will also run a simple test to check that POST and GET queries are running as expected
# The Metrics API server needs to be running inorder for the tests to work

from sqlalchemy import create_engine, schema, Column
from sqlalchemy.types import Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from itertools import cycle
import requests as rq
import os

hobby_url = 'postgres://yydnwotpybvjqe:zWt1CPlryiEmQbxL4HRXNpGPs-@ec2-50-16-230-234.compute-1.amazonaws.com:5432/ddnifpbdv12vc6'
db_url = os.environ.get("DATABASE_URL", hobby_url)
host = os.environ.get("DOMAIN", "127.0.0.1")
port = os.environ.get("PORT", 5000)
url = 'http://' + host + ':' + str(port)


def load_db(N=100):
    """
    Helper function to populate the db with test data
    """
    n = cycle(['foo', 'bar', 'baz'])
    v = cycle([1, 2, 3, 4])
    t = cycle(['2016-01-01', '2016-01-02', '2016-01-03', '2016-01-04'])
    for i in range(N):
        data = {'name': next(n), 'value': next(v), 'ts': next(t)}
        rq.post('{}/v1/metrics'.format(url), json=data)


def test_get():
    """
    Helper function to test various combinations of queries
    Shoud be used after load_db function with N=100
    """
    assert 100 == len(rq.get('{}/v1/metrics'.format(url)).json())
    assert 34 == len(rq.get('{}/v1/metrics'.format(url), params=dict(name='foo')).json())
    assert 34 == len(rq.get('{}/v1/metrics'.format(url), params=dict(name='foo', sts='2016-01-01')).json())
    assert 34 == len(rq.get('{}/v1/metrics'.format(url), params=dict(name='foo', ets='2016-01-04')).json())
    assert 9 == len(rq.get('{}/v1/metrics'.format(url), params=dict(name='foo', sts='2016-01-01', ets='2016-01-01')).json())
    assert 25 == len(rq.get('{}/v1/metrics'.format(url), params=dict(sts='2016-01-01', ets='2016-01-01')).json())
    assert 100 == len(rq.get('{}/v1/metrics'.format(url), params=dict(sts='2016-01-01')).json())
    assert 25 == len(rq.get('{}/v1/metrics'.format(url), params=dict(ets='2016-01-01')).json())


if __name__ == '__main__':

    engine = create_engine(db_url, echo=True)
    metadata = schema.MetaData(engine)
    Base = declarative_base(metadata=metadata)

    class Metric(Base):
        """
        This is an ORM constructor for the metrics table.
        Using the ORM makes it easier to create and destroy the table, as well as
        change to different backends.  For example, to use sqlite for local development.
        The table has the following columns:
            uid = a unique auto increment row id
            ts = timestamp supplied by the user via POST request
            name = metric name
            value = metric value
            raw = copy of the original json POST request
        """

        __tablename__ = 'metrics'

        uid = Column(Integer, primary_key=True)
        ts = Column(TIMESTAMP(timezone=True), index=True)
        name = Column(String(length=512), index=True)
        value = Column(String(length=512))
        raw = Column(JSONB)

        def asdict(self):
            return dict(id=self.uid, ts=str(self.ts), name=self.name, value=self.value, raw=self.raw)

    print('dropping metrics table')
    Base.metadata.drop_all()
    print('creating metrics table')
    Base.metadata.create_all()
    print('loading db')
    load_db()
    print('testing queries')
    test_get()
    print('testing complete')

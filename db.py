from sqlalchemy import create_engine, schema, Column
from sqlalchemy.types import Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import psycopg2
from itertools import cycle
import requests as rq


host = 'postgres://hmxbsqopfcqsjk:wGXeq1B1_Ya-5HgadWYZ7YPEju@ec2-54-225-165-132.compute-1.amazonaws.com:5432/danhgdplbg6q6f'

dsn = ('dbname=danhgdplbg6q6f '
      'user=hmxbsqopfcqsjk '
      'password=wGXeq1B1_Ya-5HgadWYZ7YPEju '
      'host=ec2-54-225-165-132.compute-1.amazonaws.com '
      'port=5432')

conn = psycopg2.connect(dsn)


"""
note: name is a list
cur.execute("SELECT * FROM metrics WHERE name = ALL(%s) AND ts <@ tsrange(%s, %s, '[]') limit 10;", (name,sts,ets))
"SELECT * FROM metrics WHERE name = ALL(:name) AND ts <@ tsrange(:sts, :ets, '[]') limit 10;", dict(name=name,sts=sts,ets=ets)
"""

# engine = create_engine('sqlite:///db', echo=True)
engine = create_engine(host, echo=True)
metadata = schema.MetaData(engine)
Base = declarative_base(metadata=metadata)
Session = sessionmaker(bind=engine)


class Metric(Base):
    __tablename__ = 'metrics'

    uid = Column(Integer, primary_key=True)
    ts = Column(TIMESTAMP)
    name = Column(String(length=512))
    value = Column(String(length=512))
    raw = Column(JSONB)

    def asdict(self):
        return dict(id=self.uid, ts=str(self.ts), name=self.name, value=self.value, raw=self.raw)


def load_db(N=100):
    """Helper function to populate the db with test data"""
    n = cycle(['foo', 'bar', 'baz'])
    v = cycle([1,2,3,4])
    t = cycle(['2016-01-01', '2016-01-02', '2016-01-03', '2016-01-04'])
    for i in range(N):
        data = {'name': next(n), 'value': next(v), 'ts': next(t)}
        rq.post('http://127.0.0.1:5000/v1/metrics', json=data)

def test_get():
    """
    Helper function to test various combinations of queries
    Shoud be used after load_db function with N=100
    """
    assert 100 == len(rq.get('http://127.0.0.1:5000/v1/metrics').json())
    assert 34 == len(rq.get('http://127.0.0.1:5000/v1/metrics', params=dict(name='foo')).json())
    assert 34 == len(rq.get('http://127.0.0.1:5000/v1/metrics', params=dict(name='foo', sts='2016-01-01')).json())
    assert 34 == len(rq.get('http://127.0.0.1:5000/v1/metrics', params=dict(name='foo', ets='2016-01-04')).json())
    assert 9 == len(rq.get('http://127.0.0.1:5000/v1/metrics', params=dict(name='foo', sts='2016-01-01', ets='2016-01-01')).json())
    assert 25 == len(rq.get('http://127.0.0.1:5000/v1/metrics', params=dict(sts='2016-01-01', ets='2016-01-01')).json())
    assert 100 == len(rq.get('http://127.0.0.1:5000/v1/metrics', params=dict(sts='2016-01-01')).json())
    assert 25 == len(rq.get('http://127.0.0.1:5000/v1/metrics', params=dict(ets='2016-01-01')).json())



if __name__ == '__main__':
    Base.metadata.drop_all()
    Base.metadata.create_all()
    print('loading db')
    load_db()
    print('testing queries')
    test_get()



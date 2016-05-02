# Metrics
## Know Thyself with Metrics API

### Intro

The Metrics API is a REST web server that has three general functionalities:
- Insert new metrics via POST
- Query metrics via GET
- Stream updates via web sockets

This server is hard coded to a free version of Postgresql hosted on Heroku (max 10,000 rows and 20 concurrent connections)

Install requirements with pip:

```python
pip install -r requirements.txt
```

Linux dependencies for psycopg2
  
```
sudo apt-get install libpq-dev python-dev
```

To start the server on 127.0.0.1:5000 use:

```python
python app.py
```

Run the tests, which insert 100 sample metrics into the db:

```python
python db.py
```

### Inserting New Metrics

To insert a metric, make a JSON encoded post request containing at least the following three fields:
  - name
  - value
  - ts (timestamp)

#### Examples:

```
curl -H "Content-Type: application/json" -X POST -d '{"name":"asdf", "ts": "2016-01-01", "value": "qwerty"}' "http://127.0.0.1:5000/v1/metrics"
```

### Querying for metrics:

Metrics can be queried by name and / or time range. The three query parameters are:
  - name
  - sts (start timestamp)
  - ets (end timestamp)

The start and end timestamps are both **inclusive**.
Timestamps should follow ISO-8601 conventions but are without time zone.

Omitting all parameters will return everything (SELECT * FROM metrics)
Omitting 'name' from the request will return all names.
Omitting timestamps will return the entire range.
To get an exact timestamp set the sts and ets equal to each other.


The return value is a list of 'metric' objects, which are exactly the same as what was originally sent in the POST requests.


#### Examples:

Return all instances where:
  
  name is 'foo':
  
```
curl -X GET "http://127.0.0.1:5000/v1/metrics?name=foo"
```
  
  name is 'foo' and timestamp is greater than or equal to 2016-01-01:
  
```
curl -X GET "http://127.0.0.1:5000/v1/metrics?name=foo&sts=2016-01-01"
```
  
  name is 'foo' and timestamp is less than or equal to 2016-01-02:
  
```
curl -X GET "http://127.0.0.1:5000/v1/metrics?ets=2016-01-02"
```
  
  name is 'foo' and timestamp greater than or equal to 2016-01-01 and less than or equal to 2016-01-02:
  
```
curl -X GET "http://127.0.0.1:5000/v1/metrics?name=foo&sts=2016-01-01&ets=2016-01-02"
```
  
  name is 'foo' and timestamp is exactly 2016-02-02:
  
```
curl -X GET "http://127.0.0.1:5000/v1/metrics?name=foo&sts=2016-01-02&ets=2016-01-02"
```

  timestamp is greater than or equal to 2016-01-02
      
```
curl -X GET "http://127.0.0.1:5000/v1/metrics?sts=2016-01-02"
```
  
  timestamp is less than or equal to 2016-01-02

```
curl -X GET "http://127.0.0.1:5000/v1/metrics?ets=2016-01-02"
```

### Web sockets:
  Every post request updates a web socket, for example, go to http://127.0.0.1:5000/ as python db.py is running


### Performance:
Metrics API is built with the python frameworks Tornado Momoko and Postgresql.  Benchmarks are created using ApacheBench.

POST:

  ```
  ab -n 1000 -c 10 -p sample.json -T application/json http://127.0.0.1:5000/v1/metrics

  Server Software:        TornadoServer/4.3
  Server Hostname:        127.0.0.1
  Server Port:            5000

  Document Path:          /v1/metrics
  Document Length:        19 bytes

  Concurrency Level:      10
  Time taken for tests:   2.688 seconds
  Complete requests:      1000
  Failed requests:        0
  Total transferred:      162000 bytes
  Total body sent:        195000
  HTML transferred:       19000 bytes
  Requests per second:    371.96 [#/sec] (mean)
  Time per request:       26.885 [ms] (mean)
  Time per request:       2.688 [ms] (mean, across all concurrent requests)
  Transfer rate:          58.84 [Kbytes/sec] received
                          70.83 kb/s sent
                          129.68 kb/s total

  Connection Times (ms)
                min  mean[+/-sd] median   max
  Connect:        0    0   0.0      0       0
  Processing:    15   27  11.1     26     257
  Waiting:       15   27  11.1     26     257
  Total:         15   27  11.1     26     257
  ```

### Data Model:
- Postgresql allows for both a json field and standard sql columns.  The standard columns help greatly with the timestamp range querying.  In fact, all the combinations of GET requests are handled with only one query.  Additionally, the json field allows flexibility for clients to create new keys.  For example, a 'host' key might be helpful to identify which server the metrics are coming from.  The clients can start adding the 'host' key right away and at some later point in time the metrics table could be updated and backfilled with the host column if desired to do so.


### Other:
- I attempted to use asynchronous programming to optimize for database inserts.  Since most of the API is blocked by I/O, the async paradigm seemed fitting; however, async is still emerging in python and thus there is a bit of a learning curve. In the ApacheBench tests results improved as concurrency increased (from 1 to 10 concurrent requests) therefore the async functionality seems to work as expected.
- I added web sockets for fun because I was going to try to build a 'real-time' plotting library using http://smoothiecharts.org/ but I didn't have time.  Right now index.html just dumps the results to screen as text.  Getting the chart working should be somewhat trivial.  To get the same effect without using web sockets, some databases, like rethinkDB, provide streaming support.
- I wrote a basic test suite, but there could be more.
- I didn't do anything with logging.
- Error handling could be improved by passing around a standardized error response across HTTP verbs.

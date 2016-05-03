# Metrics
## Know Thyself with Metrics API

### Intro

The Metrics API is a REST web server that has three general functionalities:
- Insert new metrics via POST
- Query metrics via GET
- Stream updates via web sockets

This server is hard coded to a free version of Postgresql hosted on Heroku (max 10,000 rows and 20 concurrent connections)


This project uses python 3.5


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

Run the tests, which drobs, creates, and insert 100 sample metrics into the metrics table:

```python
python tests.py
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
Timestamps should follow ISO-8601 conventions and the "default time zone is specified as a constant numeric offset from UTC" according to http://www.postgresql.org/docs/current/static/datatype-datetime.html

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
  Every post request updates a web socket, for example, go to http://127.0.0.1:5000/ as python test.py is running


### Performance:
Metrics API is built with the python frameworks Tornado Momoko and Postgresql.  Benchmarks are created using ApacheBench. The sample.json file is in the tests/ directory.


POST:

  ```
  ab -n 1000 -c 10 -p sample.json -T application/json http://127.0.0.1:5000/v1/metrics

  Server Software:        TornadoServer/4.3
  Server Hostname:        127.0.0.1
  Server Port:            5000

  Document Path:          /v1/metrics
  Document Length:        19 bytes

  Concurrency Level:      10
  Time taken for tests:   3.145 seconds
  Complete requests:      1000
  Failed requests:        0
  Total transferred:      162000 bytes
  Total body sent:        203000
  HTML transferred:       19000 bytes
  Requests per second:    317.93 [#/sec] (mean)
  Time per request:       31.454 [ms] (mean)
  Time per request:       3.145 [ms] (mean, across all concurrent requests)
  Transfer rate:          50.30 [Kbytes/sec] received
                          63.03 kb/s sent
                          113.32 kb/s total

  Connection Times (ms)
                min  mean[+/-sd] median   max
  Connect:        0    0   0.2      0       5
  Processing:    16   31   6.9     30      62
  Waiting:       16   31   6.9     30      62
  Total:         16   31   6.9     30      62

  Percentage of the requests served within a certain time (ms)
    50%     30
    66%     33
    75%     35
    80%     36
    90%     40
    95%     44
    98%     49
    99%     54
   100%     62 (longest request)
  ```


GET:

  ```
  ab -n 1000 -c 10  http://127.0.0.1:5000/v1/metrics

  Server Software:        TornadoServer/4.3
  Server Hostname:        127.0.0.1
  Server Port:            5000

  Document Path:          /v1/metrics
  Document Length:        66900 bytes

  Concurrency Level:      10
  Time taken for tests:   20.545 seconds
  Complete requests:      1000
  Failed requests:        0
  Total transferred:      67096000 bytes
  HTML transferred:       66900000 bytes
  Requests per second:    48.67 [#/sec] (mean)
  Time per request:       205.453 [ms] (mean)
  Time per request:       20.545 [ms] (mean, across all concurrent requests)
  Transfer rate:          3189.21 [Kbytes/sec] received

  Connection Times (ms)
                min  mean[+/-sd] median   max
  Connect:        0    0   0.0      0       0
  Processing:    82  205  63.6    192     842
  Waiting:       82  204  63.6    192     841
  Total:         82  205  63.6    192     842

  Percentage of the requests served within a certain time (ms)
    50%    192
    66%    204
    75%    215
    80%    229
    90%    265
    95%    284
    98%    309
    99%    550
   100%    842 (longest request)
  ```

### Data Model:
- Postgresql allows for both a json field and standard sql columns.  The standard columns help greatly with the timestamp range querying.  In fact, all the combinations of GET requests are handled with only one query.  Additionally, the json field allows flexibility for clients to create new keys.  For example, a 'host' key might be helpful to identify which server the metrics are coming from.  The clients can start adding the 'host' key to the json right away and at some later point in time the metrics table could be updated and backfilled with a 'host' column if desired to do so.  I added indexing to the name and ts columns to help with GET requests.  The indexes slowed the POST requests by about 100 requests per second.


### Other:

- I attempted to use asynchronous programming to optimize for database inserts.  Since most of the API is blocked by I/O, the async paradigm seemed fitting; however, async is still emerging in python and thus there is a bit of a learning curve. In the ApacheBench tests results improved as concurrency increased (from 1 to 10 concurrent requests) therefore the async functionality seems to work as expected.

- I added web sockets for fun because I wanted to try the plotting library http://smoothiecharts.org.  The index.html has a basic plot and dumps the results to screen as text.


### TODO
- The test suite is very basic and it is also the script to initilize the database
- Write logs to files
- Error handling could be improved by passing around a standardized error response across HTTP verbs.

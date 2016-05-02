# Metrics
## Know Thyself with Metrics API


### Intro

The Metrics API is a REST webserver that has three general functionalities:
- Insert new metrics via POST
- Query metrics via GET
- Stream updates via websockets


### Inserting New Metrics

To insert a a new metric, make a JSON encoded post request containing at least the following three fields:
  - name
  - value
  - ts (timestamp)

#### Examples:

    ```sh
    curl -H "Content-Type: application/json" -X POST -d '{"name":"asdf", "ts": "2016-01-01", "value": "qwerty"}' "http://127.0.0.1:5000/v1/metrics"
    ```

### Querying for metrics:

Metrics can be queryied by name and / or time range. The three query parameters are:
  - name
  - sts (start timestamp)
  - ets (end timestamp)

The start and end timestamps are both **inclusive**.
Timestamps should follow ISO-8601 conventions.

Omitting all parameters will return everything (SELECT * FROM metrics)
Omitting 'name' from the request will return all names.
Omitting timestamps will return the entire range.
To get an exact timestamp set the sts and ets equal to each other.


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

  timestamp is greater than or eqaul to 2016-01-02
      
      ```
      curl -X GET "http://127.0.0.1:5000/v1/metrics?sts=2016-01-02"
      ```
  
  timestamp is less than or eqaul to 2016-01-02
      
      ```
      curl -X GET "http://127.0.0.1:5000/v1/metrics?ets=2016-01-02"
      ```

### Websockets:
  TODO: websockets


### Performance:
Metrics API is built with python using Tornado and Momoko.  Bechmarks are created using Apache ApacheBench.

POST:

  ```sh  
  ab -n 1000 -c 10 -p sample.json -T application/json http://127.0.0.1:5000/v1/metrics
  ```

  Server Software:        TornadoServer/4.3
  Server Hostname:        127.0.0.1
  Server Port:            5000

  Document Path:          /v1/metrics
  Document Length:        19 bytes

  Concurrency Level:      10
  Time taken for tests:   2.427 seconds
  Complete requests:      1000
  Failed requests:        0
  Total transferred:      162000 bytes
  Total body sent:        195000
  HTML transferred:       19000 bytes
  Requests per second:    412.06 [#/sec] (mean)
  Time per request:       24.268 [ms] (mean)
  Time per request:       2.427 [ms] (mean, across all concurrent requests)
  Transfer rate:          65.19 [Kbytes/sec] received
                          78.47 kb/s sent
                          143.66 kb/s total

  Connection Times (ms)
                min  mean[+/-sd] median   max
  Connect:        0    0   0.0      0       0
  Processing:    14   24   5.6     23      64
  Waiting:       14   24   5.6     22      64
  Total:         14   24   5.6     23      64



### Data Model:
- combining json with columns
- suggest adding a 'host' field


### Other:
- Linux dependencies for psycopg2
  - sudo apt-get install libpq-dev python-dev
- logging


https://github.com/klen/py-frameworks-bench/blob/develop/frameworks/tornado/app.py
https://github.com/wg/wrk

swagger: '2.0'
info:
  title: Metrics API
  description: Know Thyself with Metrics API
  version: "1.0.0"
# the domain of the service
host: localhost:5555
# array of all schemes that your API supports
schemes:
  - http
# will be prefixed to all paths
basePath: /v1
produces:
  - application/json
paths:
  /metrics:
    post:
      summary: insert a new metric into the metric database
      responses:
        200:
          description: Successful insertion of data
          schema:
            type: string
        default:
          description: Unexpected error
          schema:
            $ref: '#/definitions/Error'
          
    get:
      summary: Product Types
      description: |
        The Metrics endpoint returns information about the metrics at a given time or a time range. The response is an array containing zero or more Metric objects.
      parameters:
        - name: name
          in: query
          description: name of metric
          required: false
          type: string
        - name: sts
          in: query
          description: Starting Timestamp (inclusive)
          required: false
          type: string
          format: date-time
        - name: ets
          in: query
          description: Ending Timestamp (inclusive)
          required: false
          type: string
          format: date-time
      tags:
        - Metrics
      responses:
        200:
          description: An array of Metric objects
          schema:
            type: array
            items:
              $ref: '#/definitions/Metric'
        default:
          description: Unexpected error
          schema:
            $ref: '#/definitions/Error'
definitions:
  Metric:
    type: object
    properties:
      timesatmp:
        type: string
        description: Timestamp of metric.
      name:
        type: string
        description: Name of metric
      value:
        type: string
        description: Value of metric
  Error:
    type: object
    properties:
      code:
        type: integer
        format: int32
      message:
        type: string
      fields:
        type: string

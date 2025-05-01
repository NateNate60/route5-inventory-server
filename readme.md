# `route5-inventory-server`

A backend server written in Flask which implements a RESTful API for Route 5's inventory management software.

## How to use

1. Make a Mongo DB cluster, with a database called `route5` and collections called `tokens`, `buys`, `consignments`, `inventory`, and `sales`.
2. Make a file called `src/config.py` which contains the following constants:
    - `MONGODB_PASSWORD`, which is the password to connect to your Mongo DB cluster
    - `MONGODB_USERNAME`, which is the username to connect to your Mongo DB cluster
    - `MONGODB_APPNAME`, which is the app name on Mongo DB
    - `MONGODB_CLUSTER`, which is where your cluster is, i.e. something like `route5.abcdefg1.mongodb.net`.
3. Use your favourite WSGI server and point it to `src/main.py`.
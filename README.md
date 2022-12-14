## Ray + Feast + Redis: Loan Request Prediction Demo

This repo shows an end to end Machine Learning pipeline that uses
 - Feast to orchestrate data movement and feature registry
 - Redis to serve features
 - Ray to perform distributed training with XGBoost
 - Ray Serve + FastAPI to serve the trained XGBoost model
 
 
![RayRedis_Feast](https://user-images.githubusercontent.com/13009163/186022617-577f212f-1ee9-466a-9cd9-039dcc241a2b.png)

### Citations

This demo pulls heavily from the following examples
 - [This Feast/Ray demo by Jules Damji](https://github.com/dmatrix/feast_workshops/tree/master/module_3)
 - [AWS Feast credit-scoring demo](https://github.com/feast-dev/feast-aws-credit-scoring-tutorial)

### Getting Started

The following will run through what you need to get started with this
workflow

Prerequisites:
 - A running Redis instance
      - (mac) ``brew install redis`` or ``brew install redis-stack`` if you want a UI for Redis
      - (linux) ``sudo apt install redis`` on linux
      - (cloud) Free instance on [Redis.com](https://redis.com/try-free/)
 - A python virtual environment
 - A running ray cluster (optional as the script can also spin one up)

A makefile is provided that is meant to assist with setting up the
workflow. Below is the help output obtained by running ``make``.
Note: ``Make`` must be installed to use the makefile.

```text
Ray/Redis/Feast Demo Makefile help

help                      - display this makefile's help information

Feature Store
-------------
init-fs                   - intialize the Feast feature store with Redis
test-fs                   - Test feature retrieval

Train
----
train                     - Train on a single node w/o Ray
train-ray                 - Train distributed with Ray

Infer
-----
serve                     - Serve trained XGBoost model with Ray Serve
test-infer                - Test the inference pipeline for a sample loan request

```

### Step 1: Install Python requirements

Install the needed Python dependencies (make sure virtual environment is active)

```bash
pip install -r requirements.txt
```

### Step 2: Setup Feature Store

Once you've installed Redis, ensure you're redis instance/cluster is running:

```bash
redis-cli -h <host> -p <port> -a <password> ping
```

if it's not running and you installed it locally, start it with

```bash
redis-server --port <port> --protected-mode no --requirepass <password> --bind 0.0.0.0
```
Note: this is usually not how you should run Redis in production.

### Step 3: Register and upload features to Redis

Edit the feature_store.yaml in the ``feature_repo`` directory
```bash
project: feature_repo
registry: data/registry.db
provider: local
online_store:
  type: redis
  redis_type: redis
  connection_string: "<your redis host from above>,password=<your password>"
entity_key_serialization_version: 2
```

Then, to initialize the feature store you can run

```bash
make init-fs
```
Assuming everything in the yaml is correct, this should look like:

![feature-loading](https://user-images.githubusercontent.com/13009163/186022733-b9b018b8-1fcb-4729-aefb-a6a6fc96547a.png)

### Step 4: Test Feature Retrieval

To test that the feature store is setup correctly, run the script
located in ``utils/data_fetcher.py`` which can be run with

```bash
make test-fs
```

This should output 3 groups of data which should be *non-null*

### Step 5: Train

There are two scripts available
 - ``train.py`` - single node XGBoost without Ray
 - ``train_w_ray_distributed.py`` - distributed XGBoost training with Ray

To run single node training:
```bash
make train
```

This should spin up a ray cluster (single worker) on whatever system you
launched the workflow on if there is no pre-existing cluster setup.

### Step 5b: Train with Ray

To run with Ray without previously setting up a ray cluster
you can run

```bash
make train-ray
```

This should output a ``credit_model_xgb.pkl`` object in the ``data`` directory.

### Step 5c: Train with Remote Ray Cluster

Before training with Ray ensure you're Ray cluster is setup
and that the environment variables for Ray are set in the
same terminal where you will be training with Ray.

```bash
EXPORT RAY_ADDRESS=<address of Ray head node>:<ray head port>
```
Ensure the values for ``RAY_ACTORS``, and ``RAY_CPU_PER_ACTOR``
are set appropriately in the top of the ``train_w_ray_distribtuted.py``
file in ``feature_repo/actions``

and then run
```bash
make train-ray
```

Like 5b, this should output a ``credit_model_xgb.pkl`` object in the ``data`` directory.

### Step 6a: (optional) View Ray Dashboard

The dashboard has informative views on ray workers as well as logs which
can be very helpful.

<img width="1602" alt="new-dash" src="https://user-images.githubusercontent.com/13009163/186023058-ad9e98f1-a637-4bd3-bd10-7017ac8a7c7d.png">


The ray dashboard is located at localhost:8265 which can be port
forwarded back to your laptop through SSH if your ray cluster is running
on a remote system like mine was. Note, this will not be visible unless
you have a Ray cluster running.

ex. of port forwarding

```bash
# from laptop
ssh -L 8265:localhost:8265 <username>@<hostname of ray head node>
```

### Step 6b: (optional) View Feast Dashboard

The feast dashboard shows feature views, services, and data sources which help
orchcestrate the data movement of features. 

<img width="1239" alt="feature-service" src="https://user-images.githubusercontent.com/13009163/186023287-8aff1e6c-10a0-4be6-8dbb-ec9cf4aa9da1.png">

Similar to Ray, the Feast dashboard is located at localhost:8888 which can be port
forwarded back to your laptop through SSH if your ray cluster is running
on a remote system like mine was.


```bash
# with python environment active
feast ui
```

ex. of port forwarding
```bash
# from laptop
ssh -L 8888:localhost:8888 <username>@<hostname of where feast server is running>
```

### Step 7: Serve the trained XGBoost model

To serve the trained XGBoost model with Ray Serve, there is a
script within the ``actions`` directory named ``serve.py``. This
model pulls features from the online feature store, Redis, which
is coordinated by Redis.

The ``LoanModel`` class is a FastAPI application served by Ray.
Similar to training, make sure ``RAY_ADDRESS`` is set if you
are using a pre-existing cluster.

To serve the model you can run:

```bash
make serve
```

To test the inference serving pipeline with a sample loan request,
run the following command:

```bash
make test-infer
```

If this works, ``Approved!`` should be printed to the terminal.



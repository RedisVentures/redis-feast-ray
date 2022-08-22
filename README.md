## Ray + Feast + Redis: Credit Scoring Demo

This repo shows an end to end Machine Learning Pipeline that uses
 - Feast to orchestrate data movement and feature registry
 - Redis to serve features
 - Ray to perform distributed training with XGBoost
 - Ray Serve to serve the trained XGBoost model

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
Note: this is not how you should run Redis in production.

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

### Step 5b: Train with Ray

To run with Ray without previously setting up a ray cluster
you can run

```bash
make train-ray
```

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

### Step 6a: (optional) View Ray Dashboard

The ray dashboard is located at localhost:8265 which can be port
forwarded back to your laptop through SSH if your ray cluster is running
on a remote system like mine was.

ex. of port forwarding

```bash
# from laptop
ssh -L 8265:localhost:8265 <username>@<hostname of ray head node>
```

### Step 6b: (optional) View Feast Dashboard

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
import logging
import redis
import os
import socket
import time

import os.path as ospath

OVERLORD_REDIS_HOST = "ec2-18-194-116-218.eu-central-1.compute.amazonaws.com"

PROMETHEUS_REDIS_PATH = "/net/archive/groups/plggluna/blazej/redis/redis-3.2.7/src/"

EAGLE_REDIS_PATH = "/home/plgrid/plgtgrel/blazej/redis-3.2.11/src/"

logger = logging.getLogger(__name__)

def start_local_redis_plgrid(connection_id, port=None, unixsocket=None):
    if not port:
        # getting a free port
        s = socket.socket()
        s.bind(("", 0))
        port = int(s.getsockname()[1])
        s.close()

    location = os.environ.get("SLURM_CLUSTER_NAME", "local")
    if location == "prometheus":
        redis_path = PROMETHEUS_REDIS_PATH
    elif location == "eagle":
        redis_path = EAGLE_REDIS_PATH
    else:
        from pathlib import Path
        redis_path = str(Path.home().joinpath("redis/redis-3.2.11/src"))
        assert ospath.exists(redis_path), "redis server not installed on this machine in {}".format(redis_path)
    pid = os.fork()
    if pid == 0:
        args = ["redis-server", ospath.join(redis_path, "../redis.conf"), "--port", str(port)]
        if unixsocket:
            args += ["--unixsocket", unixsocket]
        os.execvp(ospath.join(redis_path, "redis-server"), args)

    host = socket.gethostname()
    overlord_redis = redis.StrictRedis(host=OVERLORD_REDIS_HOST, port=6379)
    overlord_redis.set(connection_id, "{}:{}".format(host, port))
    return pid, host, port

def get_redis_config(connection_id, tries=300, base_delay=4.):
    overlord_redis = redis.StrictRedis(host=OVERLORD_REDIS_HOST, port=6379)
    for i in range(tries):
        host_port_b = overlord_redis.get(connection_id)
        if host_port_b is not None:
            host, port = host_port_b.decode("UTF-8").split(":", 1)
            return {"host": host, "port": port}

        # Sleep and retry if any key wasn't available
        if i != tries - 1:
            delay = base_delay * (1 + (os.getpid() % 10) / 9)
            logger.warning('Connection for id {} not found. Retrying after {:.2f} sec (attempt: {}/{})'.format(connection_id, delay, i + 2, tries))
            time.sleep(delay)
    raise RuntimeError('Connection for id {} not found'.format(connection_id))

def get_redis_connection(connection_id, tries=300, base_delay=4.):
    return redis.StrictRedis(**get_redis_config(connection_id, tries, base_delay))
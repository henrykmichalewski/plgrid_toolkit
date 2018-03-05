from PIL import Image
from deepsense import neptune
import argparse
from munch import Munch as Bunch
import os
import sqlite3
import json
import time

NEPTUNE_CTX = None

def get_neptune_context():
    global NEPTUNE_CTX
    return NEPTUNE_CTX

def set_neptune_context(ctx):
    global NEPTUNE_CTX
    NEPTUNE_CTX = ctx

def handler(str):
    return_str = "Success"
    try:
        # Version working with python 2
        # exec str in globals()
        exec(str, globals())
    except:
        return_str = "Failed"
    return return_str

def get_neptune_value(val_str):
    try:
        val = float(val_str)
        if val.is_integer():
            val = int(val_str)
    except:
        val = str(val_str)

    return val

def get_neptune_parameters():
    global NEPTUNE_CTX, IMAGE_CHANNEL, is_in_neptune
    args = {}

    for param in NEPTUNE_CTX.params.__dict__:
        if "__" not in param:

            s = getattr(NEPTUNE_CTX.params, param)[1:-1]

            val = get_neptune_value(s)

            print("Setting {} to {} with type {}.".
                  format(param, val, type(val)))
            args[param] = val

    return args


import numpy as np


def mean_aggregate_fun(l):
    return np.mean(l)


def max_aggregate_fun(l):
    return np.max(l)


def min_aggregate_fun(l):
    return np.min(l)


def last_aggregate_fun(l):
    return l[-1]



class NeptuneChannel(object):
    def add_value(self, value, x):
        raise NotImplementedError()


class NeptuneImageChannel(NeptuneChannel):
    def __init__(self, ch):
        self.ch = ch
        self.counter = 0

    def add_value(self, value, x):
        self.counter += 1
        if x is not None:
            x_to_send = x
        else:
            x_to_send = self.counter
        self.ch.send(x=x_to_send, y=value)


class NeptuneNumericChannel(NeptuneChannel):
    def __init__(self, ch, aggregate_n, aggregate_fun=mean_aggregate_fun):
        self.l = []
        self.ch = ch
        self.counter = 0
        self.aggregate_n = aggregate_n
        self.aggregate_fun = aggregate_fun

    def add_value(self, value, x=None):
        self.counter += 1
        self.l.append(value)
        if len(self.l) == self.aggregate_n:
            if x is not None:
                x_to_send = x
            else:
                x_to_send = self.counter

            self.ch.send(x=x_to_send, y=self.aggregate_fun(self.l))
            self.l = []


class FakeNeptuneHelper(object):
    # def __init__(self):
    #     self.exit_handler = None

    def setup_neptune(self, var_names):
        return

    def create_channels_and_series(self, l, aggregate_n=1, aggregate_fun=mean_aggregate_fun):
        return

    def create_image_channels(self, l):
        return

    def send_debug(self, text):
        print("Neptune debug:{}".format(text))

    def send_image(self, channel_name, image_name, description, value, x=None):
        print("Neptune image dropped.")


    def send_num_logs(self, channel_name_value_pairs_list, counter=None):
        for channel_name, value in channel_name_value_pairs_list:
            self.send_num_log(channel_name, value)

    def send_num_log(self, name, value, aggregate_n=1, x=None, aggregate_fun=mean_aggregate_fun):
        print("Neptune {}:{}".format(name, value))



class RedisNeptuneHelper(object):

    @staticmethod
    def get_redis_connection(create=False):
        import persistqueue

        storage_url = os.environ.get('STORAGE_URL')
        experiment_id = os.environ.get('EXPERIMENT_ID')
        queue_file = os.path.join(storage_url, experiment_id+"msg_queue")
        print("Queue file:{}".format(queue_file))

        q = persistqueue.FIFOSQLiteQueue(queue_file, auto_commit=True)
        return q
        # redis_metadata_file = os.path.join(storage_url,"{}_redis_metadata.txt".format(experiment_id))

        # # connection_id = os.environ.get('EXPERIMENT_ID')
        # if create:
        #     print("Creating queue")
        #     q = persistqueue.SQLiteQueue(queue_file, auto_commit=True)
        #     q.put("a")
        #     q.get()
        #     return q
        # else:
        #     timeout = 1200
        #     for x in range(timeout):
        #         if os.path.isfile(queue_file):
        #             while True:
        #                 try:
        #                     time.sleep(10)
        #                     q = persistqueue.SQLiteQueue(queue_file, auto_commit=True)
        #                     return q
        #                 except Exception as e:
        #                     print("Connection to queue failed. Retraying. Error code:{}".format(e))
        #         else:
        #             print("Waiting for queue to start.")
        #             time.sleep(5)


        raise Exception("Should not be here")


    DEBUG_CHANNEL_NAME = "debug"
    TOO_MANY_MESSAGES = 60
    NEPTUNE_KEY = "neptune"


    def __init__(self):
        # self.exit_handler = None
        self.r = None
        self.is_master = False
        try:
            from mpi4py import MPI
            self.is_master = (MPI.COMM_WORLD.Get_rank() == 0)
        except:
            self.is_master = True


    def setup_neptune(self, var_names):
        return

    def create_channels_and_series(self, l, aggregate_n=1, aggregate_fun=mean_aggregate_fun):
        return

    def create_image_channels(self, l):
        raise NotImplementedError()

    def send_debug(self, text):
        print("Debug:{}".format(text))
        key, val = self.DEBUG_CHANNEL_NAME, text
        neptune_message_str = json.dumps((key, val))
        self._put_safely(neptune_message_str)


    def send_image(self, channel_name, image_name, description, value, x=None):
        if self.r is not None:
            raise NotImplementedError()


    def send_num_logs(self, channel_name_value_pairs_list, counter=None):
        for channel_name, value in channel_name_value_pairs_list:
            self.send_num_log(channel_name, value)

    def send_num_log(self, name, value, aggregate_n=1, x=None, aggregate_fun=mean_aggregate_fun):
        neptune_message_str = json.dumps((name, value))
        self._put_safely(neptune_message_str)

    def _put_safely(self, str):
        if self.is_master:
            while True:
                try:
                    if self.r is None:
                        self.r = self.get_redis_connection()
                    self.r.put(str)
                    return
                except sqlite3.OperationalError as ex:
                    print("Failed to send log. Repeating in 5 secs: {}".format(ex))
                    self.r = None
                    time.sleep(5)

#
# class RedisNeptuneHelper(object):
#
#     @staticmethod
#     def get_redis_connection(create=False):
#         import redis
#         storage_url = os.environ.get('STORAGE_URL')
#         experiment_id = os.environ.get('EXPERIMENT_ID')
#         redis_metadata_file = os.path.join(storage_url,"{}_redis_metadata.txt".format(experiment_id))
#
#         connection_id = os.environ.get('EXPERIMENT_ID')
#         if create:
#             _, host, port = start_local_redis_plgrid(connection_id)
#             connection_data = {"host": host, "port": port}
#             with open(redis_metadata_file, "w") as f:
#                 json.dump(connection_data, f)
#             time.sleep(10)
#             r_conn = redis.StrictRedis(**connection_data)
#             # print("Bridge is connected to redis {}".format(r_conn))
#             return r_conn
#         else:
#             timeout = 1200
#             for x in range(timeout):
#                 if os.path.isfile(redis_metadata_file):
#                     while True:
#                         try:
#                             time.sleep(10)
#                             with open(redis_metadata_file, "r") as f:
#                                 connection_data = json.load(f)
#                             r_conn = redis.StrictRedis(**connection_data)
#
#                             return r_conn
#                         except Exception as e:
#                             print("Connection to redis failed. Retraying. Error code:{}".format(e))
#                 else:
#                     print("Waiting for redis to start.")
#                     time.sleep(5)
#
#         return get_redis_connection(connection_id)
#
#
#     DEBUG_CHANNEL_NAME = "debug"
#     TOO_MANY_MESSAGES = 60
#     NEPTUNE_KEY = "neptune"
#     @staticmethod
#     def get_redis_key(key):
#         return "{}:{}".format(key, os.environ.get('EXPERIMENT_ID'))
#
#     def __init__(self):
#         # self.exit_handler = None
#         self.r = None
#         try:
#             from mpi4py import MPI
#             is_master = (MPI.COMM_WORLD.Get_rank() == 0)
#         except:
#             is_master = True
#
#         if is_master:
#             # print("Master is connecting to redis.")
#             self.r = self.get_redis_connection()
#             print("Master is connected to redis at:{}".format(self.r))
#             # self._pipe = self.r.pipeline()
#             # self.counter = 0
#
#     def _send_to_redis(self, msg):
#         self.r.rpush(self.get_redis_key(self.NEPTUNE_KEY), msg)
#         print("Nepune:{}".format(msg))
#         # self.counter += 1
#         # if self.counter % 10 == 0:
#         #     self._pipe.execute()
#             #
#             # if self.r.llen(redis_key) >= self.TOO_MANY_MESSAGES:
#             #     if self.exit_handler != None:
#             #         self.exit_handler()
#
#         # self.r.rpush(self.get_redis_key(self.NEPTUNE_KEY), neptune_message_str)
#
#     def setup_neptune(self, var_names):
#         return
#
#     def create_channels_and_series(self, l, aggregate_n=1, aggregate_fun=mean_aggregate_fun):
#         return
#
#     def create_image_channels(self, l):
#         raise NotImplementedError()
#
#     def send_debug(self, text):
#         if self.r is not None:
#             print("Debug:{}".format(text))
#             key, val = self.DEBUG_CHANNEL_NAME, text
#             neptune_message_str = json.dumps((key, val))
#             self.r.rpush(self.get_redis_key(self.NEPTUNE_KEY), neptune_message_str)
#             l = text.split(":")
#             # print("Redis:{}xxx".format(l))
#             if len(l)==2:
#                 # print("Sending to redis:{}xxx".format(l))
#                 self.r.set(self.get_redis_key(l[0]), l[1])
#
#
#     def send_image(self, channel_name, image_name, description, value, x=None):
#         if self.r is not None:
#             raise NotImplementedError()
#
#
#     def send_num_logs(self, channel_name_value_pairs_list, counter=None):
#         if self.r is not None:
#             for channel_name, value in channel_name_value_pairs_list:
#                 self.send_num_log(channel_name, value)
#
#     def send_num_log(self, name, value, aggregate_n=1, x=None, aggregate_fun=mean_aggregate_fun):
#         if self.r is not None:
#             # print("Neptune send:{}={}".format(name, value))
#             neptune_message_str = json.dumps((name, value))
#             self._send_to_redis(neptune_message_str)
#

# class RedisNeptuneHelper(object):
#
#     @staticmethod
#     def create_redis_connection():
#         import redis
#         REDIS_HOST = "ec2-18-194-116-218.eu-central-1.compute.amazonaws.com"
#         REDIS_PORT = 6379
#         REDIS_DB = 1
#         return redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
#
#     DEBUG_CHANNEL_NAME = "debug"
#     TOO_MANY_MESSAGES = 60
#     NEPTUNE_KEY = "neptune"
#     @staticmethod
#     def get_redis_key(key):
#         return "{}:{}".format(key, os.environ.get('EXPERIMENT_ID'))
#
#     def __init__(self):
#         print("STARTING REDIS")
#         self.exit_handler = None
#         self.r = None
#         try:
#             from mpi4py import MPI
#             is_master = (MPI.COMM_WORLD.Get_rank() == 0)
#         except:
#             is_master = True
#
#         if is_master:
#             self.r = self.create_redis_connection()
#             self._pipe = self.r.pipeline()
#             self.counter = 0
#
#     def _send_to_redis(self, msg):
#         redis_key = self.get_redis_key(self.NEPTUNE_KEY)
#         self._pipe.rpush(self.get_redis_key(self.NEPTUNE_KEY), msg)
#         self.counter += 1
#         if self.counter % 10 == 0:
#             self._pipe.execute()
#
#             if self.r.llen(redis_key) >= self.TOO_MANY_MESSAGES:
#                 if self.exit_handler != None:
#                     self.exit_handler()
#
#         # self.r.rpush(self.get_redis_key(self.NEPTUNE_KEY), neptune_message_str)
#
#     def setup_neptune(self, var_names):
#         return
#
#     def create_channels_and_series(self, l, aggregate_n=1, aggregate_fun=mean_aggregate_fun):
#         return
#
#     def create_image_channels(self, l):
#         raise NotImplementedError()
#
#     def send_debug(self, text):
#         if self.r is not None:
#             key, val = self.DEBUG_CHANNEL_NAME, text
#             neptune_message_str = json.dumps((key, val))
#             self.r.rpush(self.get_redis_key(self.NEPTUNE_KEY), neptune_message_str)
#             l = text.split(":")
#             # print("Redis:{}xxx".format(l))
#             if len(l)==2:
#                 # print("Sending to redis:{}xxx".format(l))
#                 self.r.set(self.get_redis_key(l[0]), l[1])
#
#
#     def send_image(self, channel_name, image_name, description, value, x=None):
#         if self.r is not None:
#             raise NotImplementedError()
#
#
#     def send_num_logs(self, channel_name_value_pairs_list, counter=None):
#         if self.r is not None:
#             for channel_name, value in channel_name_value_pairs_list:
#                 self.send_num_log(channel_name, value)
#
#     def send_num_log(self, name, value, aggregate_n=1, x=None, aggregate_fun=mean_aggregate_fun):
#         if self.r is not None:
#             # print("Neptune send:{}={}".format(name, value))
#             neptune_message_str = json.dumps((name, value))
#             self._send_to_redis(neptune_message_str)


class SQLLiteNeptuneHeper(object):

    @staticmethod
    def datbase_file_path():
        storage_url = os.environ.get('STORAGE_URL')
        experiment_id = os.environ.get('EXPERIMENT_ID')
        database_path = os.path.join(storage_url, "{}.db".format(experiment_id))
        print("Logs database:{}".format(database_path))
        return database_path


    def __init__(self):
        print("STARTING SQLLITE")
        # self.exit_handler = None
        from mpi4py import MPI
        if MPI.COMM_WORLD.Get_rank()==0:
            print("SQLLogger, create database")
            try:
                os.remove(SQLLiteNeptuneHeper.datbase_file_path())
            except:
                pass

            try:
                self.con = sqlite3.connect(SQLLiteNeptuneHeper.datbase_file_path())
                self.cur = self.con.cursor()
                self.cur.execute("CREATE TABLE LOGSnumerical (ChannelName varchar(32) NOT NULL, Val float)")
                self.cur.execute("CREATE TABLE LOGSdebug (ChannelName varchar(32) NOT NULL, Val varchar(256))")
                self.con.commit()
                # self.con.close()
            except Exception as e:
                print("database error:{}".format(e))
        else:
            print("SQLLogger, fake mode")


        self.send_debug("Log database:{}".format(SQLLiteNeptuneHeper.datbase_file_path()))

    def setup_neptune(self, var_names):
        return

    def create_channels_and_series(self, l, aggregate_n=1, aggregate_fun=mean_aggregate_fun):
        return

    def create_image_channels(self, l):
        raise NotImplementedError

    def send_debug(self, text):
        from mpi4py import MPI
        if MPI.COMM_WORLD.Get_rank()==0:
            try:
                self.cur.execute('INSERT INTO LOGSdebug VALUES ("debug", "{}")'.format(text))
                self.con.commit()
            except Exception as e:
                print("database error:{}".format(e))
        else:
            pass



    def send_image(self, channel_name, image_name, description, value, x=None):
        raise NotImplementedError

    def send_num_logs(self, channel_name_value_pairs_list, counter=None):
        for channel_name, value in channel_name_value_pairs_list:
            self.send_num_log(channel_name, value)
        self.con.commit()

    def send_num_log(self, name, value, aggregate_n=1, x=None, aggregate_fun=mean_aggregate_fun):
        from mpi4py import MPI
        if MPI.COMM_WORLD.Get_rank() == 0:
            try:
                self.cur.execute('INSERT INTO LOGSnumerical VALUES ("{}", "{}")'.format(name, value))
                self.con.commit()
            except Exception as e:
                print("database error:{}".format(e))


class NeptuneHelper(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.LIST_OF_CHANNELS = []
        self.IMAGE_CHANNEL = None
        self.DEBUG_CHANNEL = None
        self.DICT_OF_CHANNELS = {}
        # self.exit_handler = None

        self.send_debug_COUNTER = 0

    def setup_neptune(self, var_names):
        job = self.ctx.job
        for l in var_names:
            self.create_channels_and_series(l)

        self.DEBUG_CHANNEL = job.create_channel(name="Debugs", channel_type=neptune.ChannelType.TEXT)

        job.register_action("Setter", handler)

    def create_channels_and_series(self, l, aggregate_n=1, aggregate_fun=mean_aggregate_fun):
        job = self.ctx.job
        if type(l) is not list:
            l = [l]
        series = {}
        for name in l:
            ch = job.create_channel(name=name, channel_type=neptune.ChannelType.NUMERIC)
            self.DICT_OF_CHANNELS[name] = NeptuneNumericChannel(ch, aggregate_n, aggregate_fun=aggregate_fun)
            series[name] = ch
            self.LIST_OF_CHANNELS.append(ch)
        job.create_chart(name="{}".format(l), series=series)

    def create_image_channels(self, l):
        job = self.ctx.job
        if type(l) is not list:
            l = [l]
        series = {}
        for name in l:
            ch = job.create_channel(name=name, channel_type=neptune.ChannelType.IMAGE)
            self.DICT_OF_CHANNELS[name] = NeptuneImageChannel(ch)
            series[name] = ch
            self.LIST_OF_CHANNELS.append(ch)

    def send_debug(self, text):
        print("Send debug to neptune:{}".format(text))
        self.DEBUG_CHANNEL.send(self.send_debug_COUNTER, text)
        self.send_debug_COUNTER += 1

    def send_image(self, channel_name, image_name, description, value, x=None):
        print("PM:This code has not been tested.")
        if channel_name not in self.DICT_OF_CHANNELS:
            self.create_image_channels([channel_name])

        pil_image = Image.fromarray(value)
        neptune_image = neptune.Image(image_name, description, pil_image)

        self.DICT_OF_CHANNELS[channel_name].add_value(neptune_image, x)

    def send_num_logs(self, channel_name_value_pairs_list, counter=None):
        print('send_num_logs'), channel_name_value_pairs_list
        if counter is not None:
            self.send_num_logs.COUNTER = counter

        for channel_name, value in channel_name_value_pairs_list:
            self.send_num_log(channel_name, value)

    def send_num_log(self, name, value, aggregate_n=1, x=None, aggregate_fun=mean_aggregate_fun):
        if name not in self.DICT_OF_CHANNELS:
            self.create_channels_and_series([name], aggregate_n, aggregate_fun=aggregate_fun)

        print("neptune:{} {} {}".format(name, self.DICT_OF_CHANNELS[name], value))
        self.DICT_OF_CHANNELS[name].add_value(value, x)


NEPTUNE_HELPER = None

def get_neptune_helper():
    global NEPTUNE_HELPER
    if NEPTUNE_HELPER == None:
        if os.environ.get('MRUNNER_UNDER_NEPTUNE', '0') == '1':
            NEPTUNE_HELPER = NeptuneHelper(NEPTUNE_CTX)
        else:
            if os.environ.get('PMILOS_DEBUG', '0') == '1':
                NEPTUNE_HELPER = FakeNeptuneHelper()
            else:
                NEPTUNE_HELPER = RedisNeptuneHelper()


    return NEPTUNE_HELPER

def set_neptune_helper(helper):
    print('Setting neptune helper {}'.format(helper))
    global NEPTUNE_HELPER
    NEPTUNE_HELPER = helper

def get_configuration():
    global NEPTUNE_CTX
    if os.environ.get('MRUNNER_UNDER_NEPTUNE', '0') == '1':
        # running under neptune
        from deepsense import neptune
        ctx = neptune.Context()
        args = ctx.params
        exp_dir_path = ctx.storage_url
        NEPTUNE_CTX = ctx

        return ctx, args, exp_dir_path

    if os.environ.get('PMILOS_DEBUG', '0') == '1':
        parser = argparse.ArgumentParser(description='Debug run.')
        parser.add_argument('--ex', type=str)
        parser.add_argument("--spec", default='spec')
        parser.add_argument("--exp_dir_path", default='/tmp')
        commandline_args = parser.parse_args()
        vars = {}
        if commandline_args.ex != None:
            exec(open(commandline_args.ex).read(), vars)
            f = vars[commandline_args.spec]
            experiment = f()[0]
            args = Bunch(experiment.parameters)
        else:
            args = None
        exp_dir_path = commandline_args.exp_dir_path
        ctx = None

        return ctx, args, exp_dir_path

    parser = argparse.ArgumentParser(description='yaml paremters')
    parser.add_argument('--config', type=str)
    parser.add_argument("--exp_dir_path", default='spec')
    commandline_args = parser.parse_known_args()

    import yaml
    neptune_args = yaml.load(open(commandline_args[0].config))
    args = {}
    for param in neptune_args["parameters"]:
        args[param["name"]] = param["default"]

    exp_dir_path = os.environ['RESOURCE_DIR_PATH']
    ctx = None
    args = Bunch(args)

    return ctx, args, exp_dir_path


def standard_mrunner_main(job_main):
    ctx, args, exp_dir_path = get_configuration()
    job_main(ctx, args, exp_dir_path)




import re
# def get_file_name(file_specification):
#     import os, glob
#     if file_specification.startswith('file://'):
#         file_specification = file_specification[len('file://'):]
#
#         if file_specification.endswith("latest"):
#             dir_path = file_specification[:-6]
#             path = os.path.join(dir_path, "*.pkl")
#             return sorted(glob.glob(path))[-1]
#         else:
#             return file_specification
#
#     if file_specification.startswith("https://"):
#         storage_path = get_job(file_specification).storage_location
#         print storage_path
#         dump_dir = os.path.join(storage_path, 'dumpdir')
#         path = os.path.join(dump_dir, "*pkl")
#
#         # INFO(maciek): they have different lengths!
#         return sorted(glob.glob(path), key=lambda a: (len(a), a))[-1]
#
#     raise NotImplementedError("Could not read model: Protocol not supported {}".format(file_specification))
import unittest

from deeplib.neptune_connection.api import create_api


class ModelRestoreHandler(object):
    def handle(self, url):
        raise NotImplementedError


class MergedModelRestoreHandler(ModelRestoreHandler):
    def __init__(self, handlers):
        self.handlers = handlers

    def handle(self, url):
        if url is None:
            return None

        for handler in self.handlers:
            res = handler.handle(url)
            if res is not None:
                return res
        return None

import os

class FileModelRestoreHandler(ModelRestoreHandler):

    def __init__(self):
        '''assumes checkpoints in storage_path'''
        self.regex_str = 'file://(.*)'
        self.regex = re.compile(self.regex_str)

    def handle(self, url):
        # TODO(maciek): now we only handle purl url from neptune, add more options
        print(self.regex_str, url)
        res = self.regex.fullmatch(url)
        if res is None:
            return None
        path = res.group(1)
        return path


class TensorflowNeptuneUrlModelRestoreHandler(ModelRestoreHandler):

    def __init__(self, neptune_api, server_name='ml.neptune.deepsense.io'):
        '''assumes checkpoints in storage_path'''
        self.server_name = server_name
        self.neptune_api = neptune_api
        self.regex_str = 'https://{server_name}/#dashboard/job/(.*)'.format(server_name=self.server_name)
        self.regex = re.compile(self.regex_str)

    @classmethod
    def get_restore_checkpoint_path(cls, restore_checkpoint):
        import tensorflow as tf
        if restore_checkpoint is None:
            return None
        if os.path.isdir(restore_checkpoint):
            return tf.train.latest_checkpoint(restore_checkpoint)
        else:
            return restore_checkpoint


    def handle(self, url):
        # TODO(maciek): now we only handle purl url from neptune, add more options
        print(self.regex_str, url)
        #res = self.regex.fullmatch(url)

        res = self.regex.match(url)
        if res is None:
            return None
        job_id = res.group(1)
        print(job_id)
        job = self.neptune_api.jobs_job_id_get(job_id)
        storage_path = job.storage_location
        checkpoints_path = os.path.join(storage_path, 'checkpoints')
        return self.get_restore_checkpoint_path(checkpoints_path)



class TestModelRestore(unittest.TestCase):
    def get_maciek_ml_api(self):
        rest_api_url = 'https://ml.neptune.deepsense.io'
        api = create_api(
            username='maciej.klimek@codilime.com',
            password='gRsWXTDnifOA2RXHn',
            rest_api_url=rest_api_url)
        return api, rest_api_url

    def test_neptune_handler(self):
        # INFO(maciek): This test has external dependencies!!! We would have to mock them.
        neptune_api, neptune_api_url = self.get_maciek_ml_api()
        handler = TensorflowNeptuneUrlModelRestoreHandler(neptune_api, 'ml.neptune.deepsense.io')
        test_url = 'https://ml.neptune.deepsense.io/#dashboard/job/021f0628-8b13-4c67-92a0-6d308f02789f'
        res = handler.handle(test_url)
        print(res)

    def test_file_handler(self):
        test_url = 'file:///home/maciek/mhome/ml_robotics_pmilos/rl_robotics_rl/maciej.klimek@codilime.com/domainrandomization/201708101626/0/jobs/26d981d7-61f6-4937-9198-2235ba1bfa91/checkpoints/model-75815'
        handler = FileModelRestoreHandler()
        res = handler.handle(test_url)
        print(res)
        self.assertEqual(test_url[7:], res)

if __name__ == '__main__':
    unittest.main()

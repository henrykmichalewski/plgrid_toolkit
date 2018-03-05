import base64
from deepsense.generated.swagger_client.apis import DefaultApi
from deepsense.generated.swagger_client import ApiClient


def create_basic_auth_header(username, password):
    bytes = str.encode('%s:%s' % (username, password))
    credentials = base64.encodebytes(bytes)
    credentials = credentials.replace(str.encode('\n'), str.encode(''))
    credentials = credentials.decode()
    header_name = "Authorization"
    header_value = "Basic {}".format(credentials)
    return header_name, header_value


def create_api(username, password, rest_api_url):
    # print(username, password)
    header_name, header_value = create_basic_auth_header(username, password)
    return DefaultApi(
        ApiClient(
            host=rest_api_url, header_name=header_name, header_value=header_value))


def sh_escape(s):
    return s.replace("(","\\(").replace(")","\\)").replace(" ","\\ ").replace("@","\@")


def get_job(api, url):
    while True:
        try:
            def get_job_id_from_url(url):
                i = url.rfind("/")
                job_id = url[i + 1:]
                return job_id

            job_id = get_job_id_from_url(url)
            job = api.jobs_job_id_get(job_id)
            return job
        except Exception:
            print(100 * 'Neptune request timetout!')


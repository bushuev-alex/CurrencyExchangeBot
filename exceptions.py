from redis.exceptions import ResponseError


class APIException(Exception):
    pass


class DataFrameException(Exception):
    pass


class RedisResponseException(ResponseError):
    pass
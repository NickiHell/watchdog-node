from server.urls import api


@api.get('/ping')
def add(request, a: int, b: int):
    return {'result': a + b}

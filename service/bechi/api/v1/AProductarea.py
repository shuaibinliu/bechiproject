from bechi.common.base_resource import Resource
from bechi.control.CProductarea import CProductarea


class AProductarea(Resource):
    def __init__(self):
        self.cproductarea = CProductarea()

    def get(self, area):
        apis = {
            'get': self.cproductarea.get
        }
        return apis

    def post(self, area):
        apis = {
            'create': self.cproductarea.create,
            'update': self.cproductarea.update,
        }
        return apis

from bechi.common.base_resource import Resource
from bechi.control.CCategory import CCategory


class ACategory(Resource):
    def __init__(self):
        self.ccategory = CCategory()

    def get(self, category):
        apis = {
            'get': self.ccategory.get
        }
        return apis

    def post(self, category):
        apis = {
            'create': self.ccategory.create,
            'delete': self.ccategory.delete,
            'update': self.ccategory.update,
        }
        return apis

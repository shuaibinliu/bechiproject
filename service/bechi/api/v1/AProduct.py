from bechi.common.base_resource import Resource
from bechi.control.CProduct import CProduct


class AProduct(Resource):
    def __init__(self):
        self.cproduct = CProduct()

    def post(self, product):
        apis = {
            'create': self.cproduct.add_product,
            'update': self.cproduct.update_product,
            'confirm': self.cproduct.resubmit_product,
            'delete': self.cproduct.delete
        }
        return apis

    def get(self, product):
        apis = {
            'get': self.cproduct.get_product,
            'list': self.cproduct.get_produt_list
        }
        return apis

from bechi.common.base_resource import Resource
from bechi.control.CGroupBuying import CGroupBuying


class AGroupbuying(Resource):
    def __init__(self):
        self.cgroupbuying = CGroupBuying()

    def get(self, groupbuying):
        apis = {
            'list': self.cgroupbuying.list,
            'list_groupbuying': self.cgroupbuying.list_groupbuying,
            'list_groupbuyingitems': self.cgroupbuying.get_groupbuying_items,
        }
        return apis

    def post(self, groupbuying):
        apis = {
            'create': self.cgroupbuying.create,
            'update': self.cgroupbuying.update,
            'confirm': self.cgroupbuying.confirm,
            'start': self.cgroupbuying.start,
            'join': self.cgroupbuying.join,
        }
        return apis

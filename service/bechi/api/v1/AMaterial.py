# -*- coding: utf-8 -*-
from bechi.common.base_resource import Resource
from bechi.control.CMaterial import CMaterial


class AMaterial(Resource):
    def __init__(self):
        self.cmaterial = CMaterial()

    def get(self, material):
        apis = {
            'list': self.cmaterial.get_material_list,           # 素材列表
            'get': self.cmaterial.get_material,                 # 素材详情
            'get_comment': self.cmaterial.get_comment,          # 素材评论
            'dietitian': self.cmaterial.list_dietitian,         # 营养师
            'list_category': self.cmaterial.list_category,      # 所有分类
        }
        return apis

    def post(self, material):
        apis = {
            'create': self.cmaterial.post_material,             # 增删改素材
            'approve_comment': self.cmaterial.approve_comment,  # 审核评论
            'create_comment': self.cmaterial.create_comment,    # 发表评论
            'create_category': self.cmaterial.create_category,  # 创建分类
            'update_category': self.cmaterial.update_category,  # 修改分类
            'dietitian': self.cmaterial.post_dietitian,         # 增删改营养师
        }
        return apis
# -*- coding: utf-8 -*-
import json
from decimal import Decimal

from bechi import create_app
from bechi.config.enums import ItemAuthrity, ItemPostion, ItemType, ActivityType, CategoryType
from bechi.extensions.register_ext import db
# from bechi.models import Items, ProductBrand, Activity, PermissionType, Approval, ProductSku, Admin
from bechi.models import Admin

# 添加一些默认的数据
from bechi.models.material import MaterialCategory


def make_items():
    with db.auto_commit():
        s_list = []
        # index_hot_items = Items.create({  # 人气热卖标签
        #     'ITid': 'index_hot',  # id为'index'
        #     'ITname': '人气热卖',
        #     'ITdesc': '这是首页的人气热卖',
        #     'ITtype': ItemType.product.value,
        #     'ITauthority': ItemAuthrity.no_limit.value,
        #     'ITposition': ItemPostion.index.value
        # })
        # s_list.append(index_hot_items)
        #
        # index_brands_items = Items.create({
        #     'ITid': 'index_brand',
        #     'ITname': '品牌推荐',
        #     'ITdesc': '这是首页才会出现的品牌推荐',
        #     'ITtype': ItemType.brand.value,
        #     'ITposition': ItemPostion.index.value
        # })
        # s_list.append(index_brands_items)
        # index_brands_product_items = Items.create({
        #     'ITid': 'index_brand_product',
        #     'ITname': '品牌推荐商品',
        #     'ITdesc': '这是首页才会出现的品牌商品',
        #     'ITposition': ItemPostion.index.value
        # })
        # s_list.append(index_brands_product_items)
        #
        # index_recommend_product_for_you_items = Items.create({
        #     'ITid': 'index_recommend_product_for_you',
        #     'ITname': '首页为您推荐',
        #     'ITdesc': '首页的为您推荐的商品',
        #     'ITposition': ItemPostion.index.value
        # })
        # s_list.append(index_recommend_product_for_you_items)

        material_category = MaterialCategory.create({'MCid': 'case_community',
                                                     'MCname': '案例社区',
                                                     'MClevel': 1,
                                                     'MCsort': -3,
                                                     'MCtype': CategoryType.material.value,
                                                     })
        s_list.append(material_category)

        knowledge_classroom = MaterialCategory.create({'MCid': 'knowledge_classroom',
                                                       'MCname': '知识课堂',
                                                       'MClevel': 1,
                                                       'MCsort': -2,
                                                       'MCtype': CategoryType.material.value,
                                                       })
        s_list.append(knowledge_classroom)

        disease_treatment = MaterialCategory.create({'MCid': 'disease_treatment',
                                                     'MCname': '疾病治疗',
                                                     'MCparentid': 'knowledge_classroom',
                                                     'MClevel': 2,
                                                     'MCsort': -2,
                                                     'MCtype': CategoryType.material.value,
                                                     })
        s_list.append(disease_treatment)

        health_encyclopedia = MaterialCategory.create({'MCid': 'health_encyclopedia',
                                                       'MCname': '健康百科',
                                                       'MCparentid': 'knowledge_classroom',
                                                       'MClevel': 2,
                                                       'MCsort': -1,
                                                       'MCtype': CategoryType.material.value,
                                                       })
        s_list.append(health_encyclopedia)

        hot_topic = MaterialCategory.create({'MCid': 'hot_topic',
                                             'MCname': '热门话题',
                                             'MClevel': 1,
                                             'MCsort': -1,
                                             'MCtype': CategoryType.material.value,
                                             })
        s_list.append(hot_topic)
        db.session.add_all(s_list)

#
# def make_acvitity():
#     with db.auto_commit():
#         fresh = Activity.create({
#             'ACid': 0,
#             'ACbackGround': '/img/temp/2018/11/29/3hio8z3JgZWyGx8MP8Szanonymous.jpg_548x600.jpg',
#             'ACtopPic': '/img/temp/2018/11/29/4v815Zfzq3tXvVETkdt3anonymous.jpg_1076x500.jpg',
#             'ACbutton': '首单可免',
#             'ACtype': ActivityType.fresh_man.value,
#             'ACdesc': '分享给好友购买, 可返原价, 享受优惠',
#             'ACname': '新人首单',
#             'ACsort': 0
#         })
#
#
#         db.session.add(fresh)
#         guess = Activity.create({
#             'ACid': 1,
#             'ACbackGround': '/img/temp/2018/11/29/yxEMJIVoarojTCFZv5Qwanonymous.jpg_575x432.jpg',
#             'ACtopPic': '/img/temp/2018/11/29/4v815Zfzq3tXvVETkdt3anonymous.jpg_1076x500.jpg',
#             'ACbutton': '参与竞猜',
#             'ACtype': ActivityType.guess_num.value,
#             'ACdesc': '分享给好友购买, 可返原价, 享受优惠',
#             'ACname': '新人首单',
#             'ACsort': 1
#         })
#         db.session.add(guess)
#         magic = Activity.create({
#             'ACid': 2,
#             'ACbackGround': '/img/temp/2018/11/29/6qEKBbcPEd3yXyLq2r6hanonymous.jpg_1024x1024.jpg',
#             'ACtopPic': '/img/temp/2018/11/29/4v815Zfzq3tXvVETkdt3anonymous.jpg_1076x500.jpg',
#             'ACbutton': '邀请好友帮拆礼盒',
#             'ACtype': ActivityType.magic_box.value,
#             'ACname': '魔术礼盒',
#             'ACsort': 2
#         })
#         db.session.add(magic)
#
#         free = Activity.create({
#             'ACid': 3,
#             'ACbackGround': '/img/temp/2018/11/29/6qEKBbcPEd3yXyLq2r6hanonymous.jpg_1024x1024.jpg',
#             'ACtopPic': '/img/temp/2018/11/29/4v815Zfzq3tXvVETkdt3anonymous.jpg_1076x500.jpg',
#             'ACbutton': '我要试用',
#             'ACtype': ActivityType.free_use.value,
#             'ACname': '试用商品',
#             'ACsort': 3
#         })
#         db.session.add(free)

# def make_permissiontype():
#     with db.auto_commit():
#         toagent = PermissionType.create({
#             'PTid': 'toagent',
#             'PTname': '代理商申请',
#             'PTmodelName': 'User'
#         })
#         db.session.add(toagent)
#
#         tocash = PermissionType.create({
#             'PTid': 'tocash',
#             'PTname': '提现申请',
#             'PTmodelName': 'CashNotes'
#         })
#         db.session.add(tocash)
#         toshelves = PermissionType.create({
#             'PTid': 'toshelves',
#             'PTname': '商品上架申请',
#             'PTmodelName': 'Products'
#         })
#         db.session.add(toshelves)
#         topublish = PermissionType.create({
#             'PTid': 'topublish',
#             'PTname': '资讯发布申请',
#             'PTmodelName': 'News'
#         })
#         db.session.add(topublish)
#         toguessnum = PermissionType.create({
#             'PTid': 'toguessnum',
#             'PTname': '猜数字活动申请',
#             'PTmodelName': 'GuessNumAwardApply'
#         })
#         db.session.add(toguessnum)
#         tomagicbox = PermissionType.create({
#             'PTid': 'tomagicbox',
#             'PTname': '魔盒活动申请',
#             'PTmodelName': 'MagicBoxApply'
#         })
#         db.session.add(tomagicbox)
#         tofreshmanfirstproduct = PermissionType.create({
#             'PTid': 'tofreshmanfirstproduct',
#             'PTname': '新人首单商品活动申请',
#             'PTmodelName': 'FreshManFirstApply'
#         })
#         db.session.add(tofreshmanfirstproduct)
#         totrialcommodity = PermissionType.create({
#             'PTid': 'totrialcommodity',
#             'PTname': '试用商品上架申请',
#             'PTmodelName': 'TrialCommodity'
#         })
#         db.session.add(totrialcommodity)
#         toreturn = PermissionType.create({
#             'PTid': 'toreturn',
#             'PTname': '退货审请',
#             'PTmodelName': 'TrialCommodity'
#         })
#         db.session.add(toreturn)
#         toactivationcode = PermissionType.create({
#             'PTid': 'toactivationcode',
#             'PTname': '激活码购买申请',
#             'PTmodelName': 'ActivationCodeApply'
#         })
#         db.session.add(toactivationcode)
#         tosettlenment = PermissionType.create({
#             'PTid': 'tosettlenment',
#             'PTname': '供应商结算异常申请',
#             'PTmodelName': 'SettlenmentApply'
#         })
#         db.session.add(tosettlenment)


def make_admin():
    with db.auto_commit():
        from werkzeug.security import generate_password_hash
        db.session.add(Admin.create({
            'ADid': 'adid1',
            'ADnum': 100001,
            'ADname': '管理员',
            'ADtelphone': '13588046135',
            'ADpassword': generate_password_hash('12345'),
            'ADfirstname': '管理员',
            'ADheader': '/img/defaulthead/2018/11/28/db7067a8-f2d0-11e8-80bc-00163e08d30f.png',
            'ADlevel': 1,
        }))


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # admin = PermissionType.query.first_()
        # admin_str = json.dumps(admin, cls=JSONEncoder)
        # print(admin.__dict__)
        # print(admin_str)
        # make_acvitity()
        make_items()
        # make_permissiontype()
        # make_admin()

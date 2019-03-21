# -*- coding: utf-8 -*-
import json
from datetime import datetime

from flask import request

from bechi.common.params_validates import parameter_required
from bechi.common.success_response import Success
from bechi.common.token_handler import get_current_user, is_admin, common_user, is_supplizer
from bechi.config.enums import GroupBuyingStatus, ProductStatus
from bechi.models.activity import GroupBuying, GroupbuyingProduct, GroupbuyingSku
from bechi.models.product import ProductSku, Products, ProductSkuValue, ProductItems


class CGroupBuying():

    def list(self):
        now = datetime.now()
        filter_set = {
            GroupBuying.isdelete == False,
        }
        if common_user():
            filter_set.add(GroupBuying.GBstatus == GroupBuyingStatus.agree.value)
            filter_set.add(GroupBuying.GBstarttime < now)
            filter_set.add(GroupBuying.GBendtime > now)
        if is_supplizer():
            filter_set.add(GroupBuying.GBstart == request.user.USid)
        gblist = GroupBuying.query.filter(*filter_set).order_by(GroupBuying.GBstarttime).all()
        product_list = []
        for gb in gblist:

            gp = GroupbuyingProduct.query.filter(
                GroupbuyingProduct.GBid == gb.GBid,
                GroupbuyingProduct.isdelete == False).first_('活动已结束')

            product = Products.query.filter(
                Products.PRid == gp.PRid,
                Products.isdelete == False,
                Products.PRstatus == ProductStatus.usual.value,
            ).first_('活动已结束')

            product.fill('GPprice', gp.GPprice)
            product.fill('GPfreight', gp.GPfreight)
            product.fill('GPstocks', gp.GPstocks)

            gs_list = GroupbuyingSku.query.filter(
                GroupbuyingSku.isdelete == False,
                GroupbuyingSku.GPid == gp.GPid
            ).all()
            # skus = self.sproduct.get_sku({'PRid': prid})
            sku_value_item = []
            sku_price = []
            skus = []
            # preview_get = []
            for gs in gs_list:
                sku = ProductSku.query.filter(ProductSku.SKUid == gs.SKUid, ProductSku.isdelete == False).first()
                if not sku:
                    continue
                sku.SKUattriteDetail = json.loads(sku.SKUattriteDetail)
                sku_value_item.append(sku.SKUattriteDetail)
                sku_price.append(sku.SKUprice)
                skus.append(sku)

            product.fill('skus', skus)
            min_price = min(sku_price)
            max_price = max(sku_price)
            if min_price != max_price:
                product.fill('price_range', '{}-{}'.format('%.2f' % min_price, '%.2f' % max_price))
            else:
                product.fill('price_range', "%.2f" % min_price)
            sku_value_instance = ProductSkuValue.query.filter_by_({
                'PRid': product.PRid
            }).first()
            if not sku_value_instance:
                sku_value_item_reverse = []
                for index, name in enumerate(product.PRattribute):
                    value = list(set([attribute[index] for attribute in sku_value_item]))
                    value = sorted(value)
                    temp = {
                        'name': name,
                        'value': value
                    }
                    sku_value_item_reverse.append(temp)
            else:
                sku_value_item_reverse = []
                pskuvalue = json.loads(sku_value_instance.PSKUvalue)
                for index, value in enumerate(pskuvalue):
                    sku_value_item_reverse.append({
                        'name': product.PRattribute[index],
                        'value': value
                    })
            product.fill('SkuValue', sku_value_item_reverse)
            # todo 增加商品列表需要参数
            # product_sku_value = self.sproduct.get_sku_value({'PRid': prid})
            # product_sku_value.PSKUvalue = json.loads(getattr(product_sku_value, 'PSKUvalue', '[]'))
            # product.fill('ProductSkuValue', product_sku_value)
            # 场景
            # items = self.sproduct.get_item_list([
            #     ProductItems.PRid == product.PRid,
            #     ProductItems.isdelete == False
            # ])
            # # 月销量
            # month_sale_instance = self.sproduct.get_monthsale_value_one({'PRid': prid})
            # month_sale_value = getattr(month_sale_instance, 'PMSVnum', 0)
            # product.fill('month_sale_value', month_sale_value)
            # product.fill('items', items)
            #
            # if is_admin() or is_supplizer():
            #     if product.PCid and product.PCid != 'null':
            #         product.fill('pcids', self._up_category_id(product.PCid))
        return Success(data=product_list)

    def get(self):

        # todo  在普通商品详情里修改

        now = datetime.now()
        data = parameter_required(('prid', ))
        prid = data.get('prid')
        filter_set = {
            GroupBuying.GBstarttime < now,
            GroupBuying.GBendtime > now,
            GroupBuying.isdelete == False,
            GroupbuyingProduct.PRid == prid,
        }
        if common_user():
            filter_set.add(GroupBuying.GBstatus == GroupBuyingStatus.agree.value)
        if is_supplizer():
            filter_set.add(GroupBuying.GBstart == request.user.USid)

        gblist = GroupBuying.join(
            GroupbuyingProduct, GroupbuyingProduct.GBid == GroupBuying.GBid
        ).query.filter(*filter_set).order_by(GroupBuying.GBstarttime).first()
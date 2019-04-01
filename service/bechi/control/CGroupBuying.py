# -*- coding: utf-8 -*-
import json
import datetime
import re
import uuid

from flask import request, current_app
from sqlalchemy import or_

from bechi.common.error_response import ParamsError, SystemError
from bechi.common.params_validates import parameter_required
from bechi.common.success_response import Success
from bechi.common.token_handler import get_current_user, is_admin, common_user, is_supplizer, admin_required, \
    token_required
from bechi.config.enums import GroupBuyingStatus, ProductStatus, GroupbuyingItemStatus, GroupbuyingUserStatus
from bechi.control.CProduct import CProduct
from bechi.extensions.register_ext import db
from bechi.models.activity import GroupBuying, GroupbuyingProduct, GroupbuyingSku, GroupbuyingItem, GroupbuyingUser
from bechi.models.product import ProductSku, Products, ProductSkuValue


class CGroupBuying(CProduct):

    def list(self):
        """前台获取商品列表"""
        now = datetime.datetime.now()
        data = parameter_required()
        try:
            order, desc_asc = data.get('order_type', 'time|desc').split('|')  # 排序方式
            order_enum = {
                'time': GroupBuying.GBstarttime,
                'sale_value': Products.PRsalesValue,
                'price': GroupbuyingProduct.GPprice,
            }
            assert order in order_enum and desc_asc in ['desc', 'asc'], 'order_type 参数错误'
        except Exception as e:
            raise e
        filter_set = {
            GroupBuying.isdelete == False,
        }
        if common_user():
            filter_set.add(GroupBuying.GBstatus == GroupBuyingStatus.agree.value)
            filter_set.add(GroupBuying.GBstarttime < now)
            filter_set.add(GroupBuying.GBendtime > now)

        product_order = order_enum.get(order)
        if desc_asc == 'desc':
            by_order = product_order.desc()
        else:
            by_order = product_order.asc()
        gblist = GroupBuying.query.join(
            GroupbuyingProduct, GroupbuyingProduct.GBid == GroupBuying.GBid).join(
            Products, Products.PRid == GroupbuyingProduct.PRid).filter(*filter_set).order_by(by_order).all_with_page()
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

            self._fill_product(product, gp, gb)
            product_list.append(product)

        return Success(data=product_list)

    @admin_required
    def list_groupbuying(self):
        # 后台获取拼团商品
        data = parameter_required()
        gb_list = GroupBuying.query.filter(GroupBuying.isdelete == False).all_with_page()
        try:
            order, desc_asc = data.get('order_type', 'time|desc').split('|')  # 排序方式
            order_enum = {
                'time': GroupBuying.GBstarttime,
                'sale_value': Products.PRsalesValue,
                'price': GroupbuyingProduct.GPprice,
            }
            assert order in order_enum and desc_asc in ['desc', 'asc'], 'order_type 参数错误'
        except Exception as e:
            raise e

        for gb in gb_list:
            gp = GroupbuyingProduct.query.filter(
                GroupbuyingProduct.GBid == gb.GBid, GroupbuyingProduct.isdelete == False).first()
            if not gp:
                current_app.logger.info('后台数据异常')
                raise SystemError
            product = Products.query.filter(
                Products.PRid ==GroupbuyingProduct.PRid, Products.isdelete == False).first()
            self._fill_product(product, gp, gb)
            gb.fill('product', product)
            gb.fill('gbstatus_zh', GroupBuyingStatus(gb.GBstatus).zh_value)
            gb.fill('gbstatus_en', GroupBuyingStatus(gb.GBstatus).name)

        return Success(data=gb_list)

    @admin_required
    def create(self):
        data = parameter_required((
            'starttime', 'endtime', 'gbnum', 'prid', 'gpprice', 'skus', 'gbtimes'))
        starttime, endtime = self._check_time(data.get('starttime'), data.get('endtime'))
        if not self._check_pint(data.get('gbnum')):
            raise ParamsError('gbnum 格式错误')
        if not self._check_pint(data.get('gbtimes')):
            raise ParamsError('gbtimes 格式错误')
        product = Products.query.filter(
            Products.isdelete == False,
            Products.PRid == data.get('prid'),
            Products.PRstatus == ProductStatus.usual.value
        ).first_('商品未上架')
        # todo 校验商品不在同一时间的其他活动里
        self._check_product(data.get('prid'), starttime, endtime)
        with db.auto_commit():
            instance_list = []
            gb_instance = GroupBuying.create({
                'GBid': str(uuid.uuid1()),
                'GBstarttime': starttime,
                'GBendtime': endtime,
                'GBnum': data.get('gbnum'),
                'GBtimes': data.get('gbtimes'),
                'GBstatus': GroupBuyingStatus.wait_check.value
            })
            instance_list.append(gb_instance)
            instance_list.extend(self._add_groupbuying_product(data, product, gb_instance.GBid))

            db.session.add_all(instance_list)
        return Success('申请成功')

    @admin_required
    def update(self):
        data = parameter_required(('gbid',))
        gb = GroupBuying.query.filter(
            GroupBuying.isdelete == False, GroupBuying.GBid == data.get('gbid')).first_('该活动已删除')
        with db.auto_commit():
            starttime, endtime = self._check_time(
                data.get('starttime') or str(gb.GBstarttime), data.get('endtime') or str(gb.GBendtime))
            gb.GBendtime = endtime
            gb.GBstarttime = starttime
            gb.GBstatus = GroupBuyingStatus.wait_check.value
            if data.get('delete'):
                self._delete_gb(gb)

            if data.get('gbnum'):
                if not self._check_pint(data.get('gbnum')):
                    raise ParamsError('gbnum 格式错误')
                gb.GBnum = data.get('gbnum')
            if data.get('gbtimes'):
                if not self._check_pint(data.get('gbtimes')):
                    raise ParamsError('gbtimes 格式错误')
                gb.GBtimes = data.get('gbtimes')
            if data.get('prid') or data.get('gpfreight') or data.get('gpstocks') or data.get('skus'):
                self._update_groupbuying_product(data, gb)
        return Success('更新成功')

    @admin_required
    def confirm(self):
        """活动确认"""
        data = parameter_required(('gbid',))
        gb = GroupBuying.query.filter(
            GroupBuying.GBid == data.get('gbid'),
            GroupBuying.isdelete == False,
            GroupBuying.GBstatus != GroupBuyingStatus.agree.value).first_('已经确认')
        with db.auto_commit():
            gb.GBstatus = GroupBuyingStatus.agree.value
        return Success('确认活动成功')

    @token_required
    def join(self):
        """用户加入拼团"""
        user = get_current_user()
        data = parameter_required(('giid',))
        gu = GroupbuyingUser.query.join(GroupbuyingItem, GroupbuyingItem.GIid == GroupbuyingUser.GIid).filter(
            GroupbuyingItem.isdelete == False,
            GroupbuyingUser.isdelete == False,
            GroupbuyingItem.GIstatus == GroupbuyingItemStatus.underway.value,
            GroupbuyingUser.USid == user.USid,
            GroupbuyingUser.GIid == data.get('giid')
        ).first()
        if gu:
            raise ParamsError('账号已经在队伍里了')
        gi = GroupbuyingItem.query.filter(
            GroupbuyingItem.isdelete == False, GroupbuyingItem.GIid == data.get('giid')).first_('该拼团已结束')
        now = datetime.datetime.now()
        gb = GroupBuying.query.filter(
            GroupBuying.GBstarttime <= now,
            GroupBuying.GBendtime >= now,
            GroupBuying.GBid == gi.GBid,
            GroupBuying.isdelete == False).first_('活动已结束')
        gus = GroupbuyingUser.query.filter(
            GroupbuyingUser.GIid == gi.GIid, GroupbuyingUser.isdelete == False).all()

        if len(gus) >= int(gb.GBnum):
            raise ParamsError('队伍已经满了，选择另外一个队伍吧')
        # gu_times = GroupbuyingUser.query.join(GroupbuyingItem, GroupbuyingItem.GIid == GroupbuyingUser.GIid).join(
        #     GroupBuying, GroupBuying.GBid == GroupbuyingItem.GBid).filter(
        #     GroupbuyingUser.USid == user.USid, GroupBuying.GBid == data.get('gbid')).count()
        # if gu_times >= gb.GBtimes:
        #     raise ParamsError('超过限购次数')
        self._check_bgtimes(gb.GBid, user.USid, gb.GBtimes)
        with db.auto_commit():
            gu = GroupbuyingUser.create({
                'GUid': str(uuid.uuid1()),
                'GIid': data.get('giid'),
                'USid': user.USid,
                'UShead': user.USheader,
                'USname': user.USname
            })
            db.session.add(gu)
            if int(gb.GBnum) - len(gus) == 1:
                gi.GIstatus = GroupbuyingItemStatus.success.value

        return Success('加入成功')

    @token_required
    def start(self):
        """用户发起拼团"""
        # data = parameter_required(('prid', ))
        user = get_current_user()
        now = datetime.datetime.now()
        # now = datetime.datetime.now()
        data = parameter_required(('gbid',))

        gb = GroupBuying.query.filter(
            GroupBuying.GBstarttime <= now,
            GroupBuying.GBendtime >= now,
            GroupBuying.GBid == data.get('gbid'),
            GroupBuying.isdelete == False).first_('活动已结束')
        self._check_bgtimes(data.get('gbid'), user.USid, gb.GBtimes)

        with db.auto_commit():
            gi = GroupbuyingItem.create({
                'GIid': str(uuid.uuid1()),
                'GBid': gb.GBid,
                'GIstatus': GroupbuyingItemStatus.underway.value
            })
            gu = GroupbuyingUser.create({
                'GUid': str(uuid.uuid1()),
                'GIid': gi.GIid,
                'USid': user.USid,
                'UShead': user.USheader,
                'USname': user.USname,
                'GUstatus': GroupbuyingUserStatus.waitpay.value
            })
            # TODO 异步任务，24h 修改超时状态
            db.session.add(gi)
            db.session.add(gu)

        return Success('发起拼团成功')

    @token_required
    def pay(self):
        """下单"""
        return Success('购买成功')

    def get_groupbuying_items(self):
        # now = datetime.datetime.now()
        data = parameter_required(('gbid', ))
        gb = GroupBuying.query.filter(
            GroupBuying.GBid == data.get('gbid'),
            GroupBuying.GBstatus == GroupBuyingStatus.agree.value
        ).first_('活动已结束')
        filter_args = {
            GroupbuyingItem.isdelete == False,
            GroupbuyingItem.GBid == gb.GBid
        }
        if not is_admin():
            filter_args.add(GroupbuyingItem.GIstatus == GroupbuyingItemStatus.underway.value)

        gi_list = GroupbuyingItem.query.filter(*filter_args).all()
        for gi in gi_list:
            gu_list = GroupbuyingUser.query.filter(
                GroupbuyingUser.isdelete == False, GroupbuyingUser.GIid == gi.GIid).all()
            gi.fill('gus', gu_list)
            gi.fill('gistatus_en', GroupbuyingItemStatus(gi.GIstatus).name)
            gi.fill('gistatus_zh', GroupbuyingItemStatus(gi.GIstatus).zh_value)
            end_time = gi.createtime + datetime.timedelta(days=1)
            gi.fill('countdown', self._get_timedelta(end_time))
            gi.fill('gbnum', gb.GBnum)
        return Success(data=gi_list)

    def _update_groupbuying_product(self, data, gb):
        gp = GroupbuyingProduct.query.filter(
            GroupbuyingProduct.isdelete == False, GroupbuyingProduct.GBid == data.get('gbid')
        ).first_('数据异常')
        if data.get('prid') and gp.PRid != data.get('prid'):
            # 更换商品
            gp.isdelete = True
            product = Products.query.filter(
                Products.isdelete == False,
                Products.PRid == data.get('prid'),
                Products.PRstatus == ProductStatus.usual.value
            ).first_('商品未上架')
            self._check_product(product.PRid, gb.GBstarttime, gb.GBendtime)
            instance_list = self._add_groupbuying_product(data, product, data.get('gbid'))
            # db.session.add_all(instance_list)
        else:
            # 修改商品及其sku
            product = Products.query.filter(
                Products.PRid == gp.PRid,
                Products.isdelete == False,
                Products.PRstatus == ProductStatus.usual.value).first_('商品未上架')
            self._check_product(product.PRid, gb.GBstarttime, gb.GBendtime, gp.GPid)
            # 先把库存还回去
            product.PRstocks += gp.GPstocks
            # 显示价格和运费修改
            if data.get('gpprice'):
                self._check_price(data.get('gpprice'))
                gp.GPprice = data.get('gpprice')
            if data.get('gpfreight'):
                gp.GPfreight = data.get('gpfreight')

            new_sku = []
            sku_ids = []
            gp_stock = 0
            instance_list = []
            skus = data.get('skus', [])
            for sku in skus:
                # sku 修改。如果不修改，需要返回原来的参数，要不然无法记录库存
                gsid = sku.get('gsid')
                if gsid:
                    # gs修改
                    gs_model = GroupbuyingSku.query.filter(
                        GroupbuyingSku.GSid == sku.get('gsid'), GroupbuyingSku.isdelete == False).first_('参数异常')

                    sku_model = ProductSku.query.filter(
                        ProductSku.SKUid == gs_model.SKUid, ProductSku.isdelete == False).first_('sku 已失效')
                    if sku.get('skugpprice'):
                        # 价格修改
                        self._check_price(sku.get('skugpprice'))
                        gs_model.SKUgpPrice = sku.get('skugpprice')
                    if sku.get('skugpstock') and self._check_pint(sku.get('skugpstock')):
                        # 涉及库存修改
                        current_app.logger.info('SKU修改库存前 skuid {} 活动库存 {} 原商品库存 {}'.format(
                            sku_model.SKUid, gs_model.SKUgpStock, sku_model.SKUstock))
                        sku_model.SKUstock += (gs_model.SKUgpStock - int(sku.get('skugpstock')))
                        gs_model.SKUgpStock = int(sku.get('skugpstock'))
                        gp_stock += int(sku.get('skugpstock'))
                        current_app.logger.info('SKU修改库存后 skuid {} 活动库存 {} 原商品库存 {}'.format(
                            sku_model.SKUid, gs_model.SKUgpStock, sku_model.SKUstock))
                    else:
                        # 不对库存修改 直接累计
                        gp_stock += gs_model.SKUgpStock
                elif sku.get('skuid'):
                    # 新增活动sku
                    sku_model = ProductSku.query.filter(
                        ProductSku.SKUid == sku.get('skuid'), ProductSku.isdelete == False).first_('参数缺失')
                    if not self._check_pint(sku.get('skugpstock')):
                        raise ParamsError('库存数目异常')
                    assert int(sku.get('skugpstock')) <= sku_model.SKUstock, \
                        '{}库存不足 需要 {} 原有 {}'.format(sku.get('skuid'), sku.get('skugpstock'), sku_model.SKUstock)

                    self._check_price(sku.get('skugpprice'))

                    gs_model = GroupbuyingSku.create({
                        'GSid': str(uuid.uuid1()),
                        'GPid': gp.GPid,
                        'SKUid': sku.get('skuid'),
                        'PRid': gp.PRid,
                        'SKUgpPrice': sku.get('skugpprice'),
                        'SKUgpStock': sku.get('skugpstock')
                    })
                    gsid = gs_model.GSid

                    sku_model.SKUstock -= gs_model.SKUgpStock
                    gp_stock += gs_model.SKUgpStock
                    new_sku.append(gsid)
                    instance_list.append(gs_model)
                else:
                    # 没有gsid 和skuid  则视为无效修改
                    continue
                # 记录有效gsid
                sku_ids.append(gsid)
            # 记录废弃sku并返回库存
            old_skus = GroupbuyingSku.query.filter(
                GroupbuyingSku.GSid.notin_(sku_ids),
                GroupbuyingSku.isdelete == False,
                GroupbuyingSku.GPid == gp.GPid).all()
            for old_sku in old_skus:
                old_sku.isdelete = True
                sku_model = ProductSku.query.filter(
                    ProductSku.SKUid == old_sku.SKUid, ProductSku.isdelete == False).first()
                if not sku_model:
                    continue
                current_app.logger.info('SKU 退出该活动 skuid {} 活动剩余库存 {} 原商品库存 {}'.format(
                    old_sku.SKUid, old_sku.SKUgpStock, sku_model.SKUstock))
                sku_model.SKUstock += old_sku.SKUgpStock
            # 校验整个商品库存是否满足
            self._check_stocks(gp_stock, product)
            gp.GPstocks = gp_stock

            product.PRstocks -= gp_stock
            current_app.logger.info('本次修改之后 商品 prid {} 参与活动库存总计 {} 原商品库存总计 {} '.format(
                product.PRid, gp_stock, product.PRstocks))
            current_app.logger.info(
                '删除了{}个不需要的sku, 更新了{}个sku, 添加了{}个新sku '.format(len(old_skus), len(sku_ids), len(new_sku)))
            if gp_stock == 0:
                self._delete_gb(gb, not_update=False)
        db.session.add_all(instance_list)

    def _add_groupbuying_product(self, data, product, gbid):
        instance_list = []
        self._check_price(data.get('gpprice'))

        gpid = str(uuid.uuid1())

        gp_stock = 0

        # error_list = []
        for sku in data.get('skus'):
            sku_model = ProductSku.query.filter(
                ProductSku.isdelete == False, ProductSku.SKUid == sku.get('skuid')).first()
            if not sku_model or sku.get('skugpstock') > sku_model.SKUstock:
                current_app.logger.info('{} 已删除或库存不足'.format(sku))
                raise ParamsError('该sku 库存不足')

            gs_instance = GroupbuyingSku.create({
                'GSid': str(uuid.uuid1()),
                'GPid': gpid,
                'SKUid': sku.get('skuid'),
                'PRid': product.PRid,
                'SKUgpPrice': sku.get('skugpprice'),
                'SKUgpStock': sku.get('skugpstock')
            })
            sku_model.SKUstock -= sku.get('skugpstock')
            gp_stock += gs_instance.SKUgpStock
            instance_list.append(gs_instance)

        # 校验库存
        self._check_stocks(gp_stock, product)
        product.PRstocks -= gp_stock
        gp_instance = GroupbuyingProduct.create({
            'GPid': gpid,
            'GBid': gbid,
            'PRid': product.PRid,
            'PRtitle': product.PRtitle,
            'GPprice': data.get('gpprice'),
            'GPfreight': data.get('gpfreight'),
            'GPstocks': gp_stock,
        })

        instance_list.append(gp_instance)
        return instance_list

    def _check_time(self, starttimestr, endtimestr):
        # todo  截止时间校验
        now = datetime.datetime.now()
        try:
            starttime = datetime.datetime.strptime(starttimestr, '%Y-%m-%d %H:%M:%S')
            endtime = datetime.datetime.strptime(endtimestr, '%Y-%m-%d %H:%M:%S')
            if starttime < endtime and now < endtime:
                return starttime, endtime
        except Exception as e:
            current_app.logger.info('转置时间错误 starttime is {} endtime is {} error msg is {}'.format(
                starttimestr, endtimestr, e.args))
            raise ParamsError('起止时间非法')

        raise ParamsError('起止时间非法')

    def _check_product(self, prid, starttime, endtime, gpid=None):
        """校验该商品是否重复提交活动"""
        # 拼团
        filter_args = {
            GroupBuying.isdelete == False,
            or_(GroupBuying.GBstarttime < endtime, GroupBuying.GBendtime > starttime),
            GroupbuyingProduct.isdelete == False,
            GroupbuyingProduct.PRid == prid
        }
        if gpid:
            filter_args.add(GroupbuyingProduct.GPid != gpid)
        gb = GroupBuying.query.join(
            GroupbuyingProduct, GroupbuyingProduct.GBid == GroupBuying.GBid).filter(*filter_args).first()
        if gb:
            raise ParamsError('该商品已经参与拼团')
        return True

    def _check_price(self, price):
        assert re.match(r'^\d+\.?\d*$', str(price)) and float(price) > 0, '活动价不合理'

    def _check_stocks(self, stock, product):
        assert str(stock).isdigit() and stock <= product.PRstocks, '商品库存不足'

    def _fill_product(self, product, gp, gb):
        product.fill('GPprice', gp.GPprice)
        product.fill('GBid', gb.GBid)
        product.fill('GPfreight', gp.GPfreight)
        product.fill('GPstocks', gp.GPstocks)
        product.fill('countdown', self._get_timedelta(gb.GBendtime))

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
            sku.fill('skugpprice', gs.SKUgpPrice)
            sku.fill('skugpstocks', gs.SKUgpStock)
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
        attribute_product = json.loads(product.PRattribute) \
            if isinstance(product.PRattribute, str) else product.PRattribute
        if not sku_value_instance:
            sku_value_item_reverse = []
            for index, name in enumerate(attribute_product):
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
                    'name': attribute_product[index],
                    'value': value
                })

        product.fill('prattribute', json.loads(product.PRattribute or "[]"))
        product.fill('SkuValue', sku_value_item_reverse)
        product.fill('prsalesvalue', max(product.PRsalesValueFake, product.PRsalesValue))

    def _delete_gb(self, gb, not_update=True):
        gb.isdelete = True
        # todo  清除库存
        if not_update:
            gp = GroupbuyingProduct.query.filter(
                GroupbuyingProduct.GBid == gb.GBid, GroupbuyingProduct.isdelete == False).first()
            gs_list = GroupbuyingSku.query.filter(
                GroupbuyingSku.isdelete == False, GroupbuyingSku.GPid == gp.GPid
            ).all()
            # 开始退还库存
            product = Products.query.filter(Products.isdelete == False, Products.PRid == gp.PRid).first()
            if not product:
                return
            product.PRstocks += gp.GPstocks
            gp.isdelete = True
            for gs in gs_list:
                sku = ProductSku.query.filter(ProductSku.isdelete == False, ProductSku.SKUid == gs.SKUid).first()
                if not sku:
                    continue
                sku.SKUstock += gs.SKUgpStock

    def _check_bgtimes(self, gbid, usid, times):
        gu_times = GroupbuyingUser.query.join(GroupbuyingItem, GroupbuyingItem.GIid == GroupbuyingUser.GIid).join(
            GroupBuying, GroupBuying.GBid == GroupbuyingItem.GBid).filter(
            GroupbuyingUser.GUstatus >= GroupbuyingUserStatus.waitpay.value,
            GroupbuyingItem.GIstatus <= GroupbuyingItemStatus.cancel.value,
            GroupbuyingUser.USid == usid, GroupBuying.GBid == gbid).count()

        if gu_times >= times:
            raise ParamsError('已超出限购次数')

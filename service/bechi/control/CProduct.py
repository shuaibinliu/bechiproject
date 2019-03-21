import datetime
import json
import re
import uuid

from flask import current_app, request
from sqlalchemy import or_, and_

from bechi.common.error_response import NotFound, DumpliError, AuthorityError, ParamsError
from bechi.common.params_validates import parameter_required
from bechi.common.success_response import Success
from bechi.common.token_handler import is_admin, is_tourist, token_required
from bechi.config.enums import ProductStatus, ProductFrom, UserSearchHistoryType
# from bechi.control.BaseControl import BASEAPPROVAL
from bechi.extensions.register_ext import db
from bechi.models import UserSearchHistory
from bechi.models.activity import GroupBuying, GroupbuyingProduct, GroupbuyingSku
from bechi.models.product import Products, ProductBrand, ProductSkuValue, ProductItems, ProductCategory, ProductImage, \
    ProductSku


class CProduct():

    def get_product(self):
        data = parameter_required(('prid',))
        prid = data.get('prid')
        product = Products.query.filter(Products.PRid == prid, Products.isdelete == False).first_('商品已下架')
        if not product:
            return NotFound()
        # 获取商品评价平均分（五颗星：0-10）
        praveragescore = product.PRaverageScore
        if float(praveragescore) > 10:
            praveragescore = 10
        elif float(praveragescore) < 0:
            praveragescore = 0
        else:
            praveragescore = round(praveragescore)
        product.PRaverageScore = praveragescore
        product.fill('fiveaveragescore', praveragescore / 2)
        product.fill('prstatus_en', ProductStatus(product.PRstatus).name)
        # product.PRdesc = json.loads(getattr(product, 'PRdesc') or '[]')
        product.PRattribute = json.loads(product.PRattribute)
        product.PRremarks = json.loads(getattr(product, 'PRremarks') or '{}')
        # 顶部图
        images = ProductImage.query.filter(
            ProductImage.PRid == prid, ProductImage.isdelete == False).order_by(ProductImage.PIsort).all()
        product.fill('images', images)

        # sku
        skus = ProductSku.query.filter(ProductSku.PRid == prid, ProductSku.isdelete == False).all()
        sku_value_item = []
        sku_price = []

        for sku in skus:
            sku.SKUattriteDetail = json.loads(sku.SKUattriteDetail)
            sku_value_item.append(sku.SKUattriteDetail)
            sku_price.append(sku.SKUprice)

        product.fill('skus', skus)
        min_price = min(sku_price)
        max_price = max(sku_price)
        if min_price != max_price:
            product.fill('price_range', '{}-{}'.format('%.2f' % min_price, '%.2f' % max_price))
        else:
            product.fill('price_range', "%.2f" % min_price)

        # sku value
        # 是否有skuvalue, 如果没有则自行组装
        sku_value_instance = ProductSkuValue.query.filter_by_({
            'PRid': prid
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
        # todo X人购买没有自增地方

        if is_admin():
            if product.PCid and product.PCid != 'null':
                product.fill('pcids', self._up_category_id(product.PCid))

        # 活动内容填充

        self.fill_activity(product)
        return Success(data=product)

    def get_produt_list(self):
        data = parameter_required()
        try:
            order, desc_asc = data.get('order_type', 'time|desc').split('|')  # 排序方式
            order_enum = {
                'time': Products.updatetime,
                'sale_value': Products.PRsalesValue,
                'price': Products.PRprice,
            }
            assert order in order_enum and desc_asc in ['desc', 'asc'], 'order_type 参数错误'
        except Exception as e:
            raise e
        kw = data.get('kw', '').split() or ['']  # 关键词
        # pbid = data.get('pbid')  # 品牌
        # 分类参数
        pcid = data.get('pcid')  # 分类id
        pcid = pcid.split('|') if pcid else []
        pcids = self._sub_category_id(pcid)
        pcids = list(set(pcids))

        prstatus = data.get('prstatus')
        if not is_admin():
            prstatus = prstatus or 'usual'  # 商品状态
        if prstatus:
            prstatus = getattr(ProductStatus, prstatus).value
        product_order = order_enum.get(order)
        if desc_asc == 'desc':
            by_order = product_order.desc()
        else:
            by_order = product_order.asc()
        #
        filter_args = [
            and_(*[Products.PRtitle.contains(x) for x in kw]),
            Products.PCid.in_(pcids),
            Products.PRstatus == prstatus,
        ]

        query = Products.query.filter(Products.isdelete == False)
        products = query.filter_(*filter_args).order_by(by_order).all_with_page()
        # 填充
        for product in products:
            product.fill('prstatus_en', ProductStatus(product.PRstatus).name)
            product.fill('prstatus_zh', ProductStatus(product.PRstatus).zh_value)
            # 品牌
            # brand = self.sproduct.get_product_brand_one({'PBid': product.PBid})
            # brand = ProductBrand.query.filter(ProductBrand.PBid == product.PBid).first() or {}
            # product.fill('brand', brand)
            product.PRattribute = json.loads(product.PRattribute)
            product.PRremarks = json.loads(getattr(product, 'PRremarks') or '{}')
            if is_admin():
                # 分类
                category = self._up_category(product.PCid)
                product.fill('category', category)
                # sku
                skus = ProductSku.query.filter(
                    ProductSku.isdelete == False,
                    ProductSku.PRid == product.PRid
                ).all()
                for sku in skus:
                    sku.SKUattriteDetail = json.loads(sku.SKUattriteDetail)
                product.fill('skus', skus)
            # product.PRdesc = json.loads(getattr(product, 'PRdesc') or '[]')
        # 搜索记录表
        if kw != [''] and not is_tourist():
            with db.auto_commit():
                db.session.expunge_all()
                instance = UserSearchHistory.create({
                    'USHid': str(uuid.uuid1()),
                    'USid': request.user.id,
                    'USHname': ' '.join(kw)
                })
                current_app.logger.info(dict(instance))
                db.session.add(instance)
        return Success(data=products)

    # @token_required
    def add_product(self):
        # TOdo  增加虚拟销量
        # if is_admin():
        product_from = ProductFrom.platform.value
        # else:
        #     raise AuthorityError()
        data = parameter_required((
            'pcid', 'prtitle', 'prprice', 'prattribute',
            'prmainpic', 'prdesc', 'images', 'skus'
        ))
        pbid = data.get('pbid')  # 品牌id
        pcid = data.get('pcid')  # 3级分类id
        images = data.get('images')
        skus = data.get('skus')
        prfeatured = data.get('prfeatured', False)
        prdescription = data.get('prdescription')  # 简要描述
        # PCtype 是表示分类等级， 该系统只有两级
        product_category = ProductCategory.query.filter(
            ProductCategory.PCid == pcid, ProductCategory.isdelete == False
        ).first_('指定目录不存在')
        if not re.match(r'^\d+$', str(data.get('prsalesvaluefake'))):
            raise ParamsError('虚拟销量数据异常')

        prstocks = 0
        with db.auto_commit() as s:
            session_list = []
            # 商品
            prattribute = data.get('prattribute')
            prid = str(uuid.uuid1())
            prmarks = data.get('prmarks')  # 备注
            if prmarks:
                try:
                    prmarks = json.dumps(prmarks)
                    if not isinstance(prmarks, dict):
                        raise TypeError
                except Exception:
                    pass
            prdesc = data.get('prdesc')
            if prdesc:
                if not isinstance(prdesc, list):
                    raise ParamsError('prdesc 格式不正确')
            # sku
            sku_detail_list = []  # 一个临时的列表, 使用记录的sku_detail来检测sku_value是否符合规范
            for index, sku in enumerate(skus):
                sn = sku.get('skusn')
                # self._check_sn(sn=sn)
                skuattritedetail = sku.get('skuattritedetail')
                if not isinstance(skuattritedetail, list) or len(skuattritedetail) != len(prattribute):
                    raise ParamsError('skuattritedetail与prattribute不符')
                sku_detail_list.append(skuattritedetail)
                skuprice = float(sku.get('skuprice'))
                skustock = int(sku.get('skustock'))
                skudeviderate = sku.get('skudeviderate')

                assert skuprice > 0 and skustock >= 0, 'sku价格或库存错误'
                prstocks += int(skustock)
                sku_dict = {
                    'SKUid': str(uuid.uuid1()),
                    'PRid': prid,
                    'SKUpic': sku.get('skupic'),
                    'SKUprice': round(skuprice, 2),
                    'SKUstock': int(skustock),
                    'SKUattriteDetail': json.dumps(skuattritedetail),
                    'SKUsn': sn,
                    'SkudevideRate': skudeviderate
                }
                sku_instance = ProductSku.create(sku_dict)
                session_list.append(sku_instance)
            # 商品
            product_dict = {
                'PRid': prid,
                'PRtitle': data.get('prtitle'),
                'PRprice': data.get('prprice'),
                'PRlinePrice': data.get('prlineprice'),
                'PRfreight': data.get('prfreight'),
                'PRstocks': prstocks,
                'PRmainpic': data.get('prmainpic'),
                'PCid': pcid,
                'PBid': pbid,
                'PRdesc': prdesc,
                'PRattribute': json.dumps(prattribute),
                'PRremarks': prmarks,
                'PRfrom': product_from,
                'CreaterId': "bechiadmin",
                'PRsalesValueFake': int(data.get('prsalesvaluefake')),
                'PRdescription': prdescription,  # 描述
                # 'PRfeatured': prfeatured,  # 是否为精选
            }
            # 库存为0 的话直接售罄
            if prstocks == 0:
                product_dict['PRstatus'] = ProductStatus.sell_out.value
            product_instance = Products.create(product_dict)
            session_list.append(product_instance)
            # sku value
            pskuvalue = data.get('pskuvalue')
            if pskuvalue:
                if not isinstance(pskuvalue, list) or len(pskuvalue) != len(prattribute):
                    raise ParamsError('pskuvalue与prattribute不符')
                sku_reverce = []
                for index in range(len(prattribute)):
                    value = list(set([attribute[index] for attribute in sku_detail_list]))
                    sku_reverce.append(value)
                    # 对应位置的列表元素应该相同
                    if set(value) != set(pskuvalue[index]):
                        raise ParamsError('请核对pskuvalue')
                # sku_value表
                sku_value_instance = ProductSkuValue.create({
                    'PSKUid': str(uuid.uuid1()),
                    'PRid': prid,
                    'PSKUvalue': json.dumps(pskuvalue)
                })
                session_list.append(sku_value_instance)
            # images
            for image in images:
                image_dict = {
                    'PIid': str(uuid.uuid1()),
                    'PRid': prid,
                    'PIpic': image.get('pipic'),
                    'PIsort': image.get('pisort'),
                }
                image_instance = ProductImage.create(image_dict)
                session_list.append(image_instance)

            s.add_all(session_list)

        return Success('添加成功', {'prid': prid})

    # @token_required
    def update_product(self):
        """更新商品"""
        data = parameter_required(('prid',))
        # product_from = ProductFrom.platform.value

        prid = data.get('prid')
        pbid = data.get('pbid')  # 品牌id
        pcid = data.get('pcid')  # 分类id
        images = data.get('images')
        skus = data.get('skus')
        prdescription = data.get('prdescription')
        if data.get('prsalesvaluefake'):
            if not re.match(r'^\d+$', str(data.get('prsalesvaluefake'))):
                raise ParamsError('虚拟销量数据异常')
        else:
            data['prsalesvaluefake'] = 0
        with db.auto_commit():
            session_list = []
            # 商品
            prattribute = data.get('prattribute')
            product = Products.query.filter_by_({'PRid': prid}).first_('商品不存在')
            prmarks = data.get('prmarks')  # 备注
            if prmarks:
                try:
                    prmarks = json.dumps(prmarks)
                    if not isinstance(prmarks, dict):
                        raise TypeError
                except Exception as e:
                    pass
            if pcid:
                product_category = ProductCategory.query.filter(
                    ProductCategory.PCid == pcid, ProductCategory.isdelete == False).first_('指定目录不存在')

            # sku, 有skuid为修改, 无skuid为新增
            if skus:
                new_sku = []
                sku_ids = []  # 此时传入的skuid
                prstock = 0
                for index, sku in enumerate(skus):
                    skuattritedetail = sku.get('skuattritedetail')
                    if not isinstance(skuattritedetail, list) or len(skuattritedetail) != len(prattribute):
                        raise ParamsError('skuattritedetail与prattribute不符')
                    skuprice = int(sku.get('skuprice', 0))
                    skustock = int(sku.get('skustock', 0))
                    assert skuprice > 0 and skustock >= 0, 'sku价格或库存错误'
                    # 更新或添加删除
                    if 'skuid' in sku:
                        skuid = sku.get('skuid')
                        sn = sku.get('skusn')
                        # self._check_sn(sn=sn, skuid=skuid)
                        sku_ids.append(skuid)
                        sku_instance = ProductSku.query.filter_by({'SKUid': skuid}).first_('sku不存在')
                        sku_instance.update({
                            'SKUpic': sku.get('skupic'),
                            'SKUattriteDetail': json.dumps(skuattritedetail),
                            'SKUstock': int(skustock),
                            'SKUprice': sku.get('skuprice'),
                            'SKUsn': sn
                        })
                    else:
                        sku_instance = ProductSku.create({
                            'SKUid': str(uuid.uuid1()),
                            'PRid': prid,
                            'SKUpic': sku.get('skupic'),
                            'SKUprice': round(skuprice, 2),
                            'SKUstock': int(skustock),
                            'SKUattriteDetail': json.dumps(skuattritedetail),
                            'SKUsn': sku.get('skusn'),

                        })
                        new_sku.append(sku_instance)

                    session_list.append(sku_instance)

                    prstock += sku_instance.SKUstock
                # 剩下的就是删除
                old_sku = ProductSku.query.filter(
                    ProductSku.isdelete == False,
                    ProductSku.PRid == prid,
                    ProductSku.SKUid.notin_(sku_ids)
                ).delete_(synchronize_session=False)
                current_app.logger.info(
                    '删除了{}个不需要的sku, 更新了{}个sku, 添加了{}个新sku '.format(old_sku, len(sku_ids), len(new_sku)))

            prdesc = data.get('prdesc')
            product_dict = {
                'PRtitle': data.get('prtitle'),
                'PRprice': data.get('prprice'),
                'PRlinePrice': data.get('prlineprice'),
                'PRfreight': data.get('prfreight'),
                'PRstocks': prstock,
                'PRmainpic': data.get('prmainpic'),
                'PCid': pcid,
                'PBid': pbid,
                'PRdesc': prdesc,
                'PRattribute': json.dumps(prattribute),
                'PRremarks': prmarks,
                'PRdescription': prdescription,
                'PRsalesValueFake': int(data.get('prsalesvaluefake')),
                'PRstatus': ProductStatus.auditing.value,
                # 'PRfeatured': prfeatured,
            }
            product.update(product_dict)
            if product.PRstocks == 0:
                product.PRstatus = ProductStatus.sell_out.value
            session_list.append(product)
            # sku value
            pskuvalue = data.get('pskuvalue')
            if pskuvalue:
                if not isinstance(pskuvalue, list) or len(pskuvalue) != len(json.loads(product.PRattribute)):
                    raise ParamsError('pskuvalue与prattribute不符')
                # todo  skudetail校验
                # sku_value表
                exists_sku_value = ProductSkuValue.query.filter_by_({
                    'PRid': prid
                }).first()
                if exists_sku_value:
                    exists_sku_value.update({
                        'PSKUvalue': json.dumps(pskuvalue)
                    })
                    session_list.append(exists_sku_value)
                else:
                    sku_value_instance = ProductSkuValue.create({
                        'PSKUid': str(uuid.uuid1()),
                        'PRid': prid,
                        'PSKUvalue': json.dumps(pskuvalue)
                    })
                    session_list.append(sku_value_instance)
            else:
                sku_value_instance = ProductSkuValue.query.filter_by_({
                    'PRid': prid,
                }).first()
                if sku_value_instance:
                    # 默认如果不传就删除原来的, 防止value混乱, todo
                    sku_value_instance.isdelete = True
                    session_list.append(sku_value_instance)

            # images, 有piid为修改, 无piid为新增
            if images:
                piids = []
                new_piids = []
                for image in images:
                    if 'piid' in image:  # 修改
                        piid = image.get('piid')
                        piids.append(piid)
                        image_instance = ProductImage.query.filter_by({'PIid': piid}).first_('商品图片信息不存在')
                    else:  # 新增
                        piid = str(uuid.uuid1())
                        image_instance = ProductImage()
                        new_piids.append(piid)
                        image_dict = {
                            'PIid': piid,
                            'PRid': prid,
                            'PIpic': image.get('pipic'),
                            'PIsort': image.get('pisort'),
                            'isdelete': image.get('isdelete')
                        }
                        image_instance.update(image_dict)

                    session_list.append(image_instance)
                # 删除其他
                delete_images = ProductImage.query.filter(
                    ProductImage.isdelete == False,
                    ProductImage.PIid.notin_(piids),
                    ProductImage.PRid == prid,
                ).delete_(synchronize_session=False)
                current_app.logger.info('删除了{}个图片, 修改了{}个, 新增了{}个 '.format(delete_images, len(piids),
                                                                           len(new_piids)))

            db.session.add_all(session_list)

        return Success('更新成功')

    # @token_required
    def resubmit_product(self):
        data = parameter_required(('prid',))
        product = Products.query.filter(Products.isdelete == False,
                                        Products.PRid == data.get('prid')).first_('商品不存在')
        with db.auto_commit():
            product.PRstatus = ProductStatus.usual.value
            db.session.add(product)

        return Success('申请成功')

    # @token_required
    def delete(self):
        data = parameter_required(('prids',))
        prids = data.get('prids')
        if not isinstance(prids, list):
            raise ParamsError('prids 参数异常')

        with db.auto_commit():
            Products.query.filter(
                Products.isdelete == False,
                Products.PRid.in_(prids)
            ).delete_(synchronize_session=False)
        return Success('删除成功')

    @token_required
    def off_shelves(self):
        """下架"""
        data = parameter_required(('prids',))
        if not isinstance(data.get('prids'), list):
            raise ParamsError('数据异常')

        with db.auto_commit():
            product = Products.query.filter(
                Products.PRid.in_(data.get('prid')),
                Products.isdelete == False
            ).first_('商品不存在')
            product.PRstatus = ProductStatus.off_shelves.value
        return Success('下架成功')

    def search_history(self):
        """"搜索历史"""
        if not is_tourist():
            args = parameter_required(('shtype',))
            shtype = args.get('shtype')
            if shtype not in ['product', 'news']:
                raise ParamsError('shtype, 参数错误')
            shtype = getattr(UserSearchHistoryType, shtype, 'product').value
            usid = request.user.id
            search_history = UserSearchHistory.query.filter(
                UserSearchHistory.USid == usid,
                UserSearchHistory.USHtype == shtype,
                UserSearchHistory.isdelete == False,
            ).order_by(UserSearchHistory.createtime.desc()).all_with_page()
        else:
            search_history = []
        return Success(data=search_history)

    def del_search_history(self):
        """清空当前搜索历史"""
        if not is_tourist():
            data = parameter_required(('shtype',))
            shtype = data.get('shtype')
            if shtype not in ['product', 'news']:
                raise ParamsError('shtype, 参数错误')
            shtype = getattr(UserSearchHistoryType, shtype, 'product').value
            usid = request.user.id
            with db.auto_commit() as s:
                s.query(UserSearchHistory).filter_by({'USid': usid, 'USHtype': shtype}).delete_()
        return Success('删除成功')

    def guess_search(self):
        """推荐搜索"""
        data = parameter_required(('kw', 'shtype'))
        shtype = data.get('shtype')
        if shtype not in ['product', 'news']:
            raise ParamsError('shtype, 参数错误')
        shtype = getattr(UserSearchHistoryType, shtype, 'product').value
        kw = data.get('kw').strip()
        if not kw:
            raise ParamsError()
        search_words = UserSearchHistory.query.filter(
            UserSearchHistory.USHtype == shtype,
            UserSearchHistory.USHname.like(kw + '%'),
        ).order_by(UserSearchHistory.createtime.desc()).all_with_page()
        [sw.hide('USid', 'USHid') for sw in search_words]
        return Success(data=search_words)

    # def _can_add_product(self):
    #     if is_admin():
    #         current_app.logger.info('管理员添加商品')
    #         self.product_from = ProductFrom.platform.value
    #         self.prstatus = None
    #     elif is_supplizer():  # 供应商添加的商品需要审核
    #         current_app.logger.info('供应商添加商品')
    #         self.product_from = ProductFrom.supplizer.value
    #         # self.prstatus = ProductStatus.auditing.value
    #         self.prstatus = None
    #     else:
    #         raise AuthorityError()

    def _sub_category_id(self, pcid):
        """遍历子分类, 返回id列表"""
        queue = pcid if isinstance(pcid, list) else [pcid]
        pcids = []
        while True:
            if not queue:
                return pcids
            pcid = queue.pop()
            if pcid not in pcids:
                pcids.append(pcid)
                # subs = ({'ParentPCid': pcid})
                subs = ProductCategory.query.filter(ProductCategory.ParentPCid == pcid).order_by(
                    ProductCategory.PCsort, ProductCategory.createtime).all()
                if subs:
                    for sub in subs:
                        pcid = sub.PCid
                        queue.append(pcid)

    def _up_category_id(self, pcid, pc_list=()):
        """遍历上级分类至一级"""
        pc_list = list(pc_list)
        pc_list.insert(0, pcid)
        category = ProductCategory.query.filter_by({
            'PCid': pcid,
            'isdelete': False,
        }).first()
        if not category.ParentPCid or category.ParentPCid in pc_list:
            return pc_list
        return self._up_category_id(category.ParentPCid, pc_list)

    def _up_category(self, pcid, pc_list=()):
        pc_list = list(pc_list)
        p_category = ProductCategory.query.filter_by({
            'PCid': pcid,
            'isdelete': False,
        }).first()

        if not p_category or p_category in pc_list:
            return pc_list
        pc_list.insert(0, p_category)
        if not p_category.ParentPCid:
            return pc_list
        return self._up_category(p_category.ParentPCid, pc_list)

    def _update_stock(self, old_new, product=None, sku=None, **kwargs):
        from .COrder import COrder
        corder = COrder()
        corder._update_stock(old_new, product, sku, **kwargs)

    def _check_sn(self, **kwargs):
        current_app.logger.info(kwargs)
        sn = kwargs.get('sn')
        if not sn:
            return
        skuid = kwargs.get('skuid')
        exists_sn_query = ProductSku.query.filter(
            # ProductSku.isdelete == False,
            ProductSku.SKUsn == sn,
        )
        if skuid:
            exists_sn_query = exists_sn_query.filter(ProductSku.SKUid != skuid)
        exists_sn = exists_sn_query.first()
        if exists_sn:
            raise DumpliError('重复sn编码: {}'.format(sn))

    def fill_activity(self, product):
        now = datetime.datetime.now()
        # todo  填充其他活动商品数据
        self.fill_group_buying(product, now)

    def fill_group_buying(self, product, now):
        # 同一时间段 同一商品只能参加一次拼团
        gp = GroupbuyingProduct.query.join(
            GroupBuying, GroupbuyingProduct.GBid == GroupBuying.GBid).filter(
            GroupbuyingProduct.isdelete == False,
            GroupBuying.isdelete == False,
            GroupbuyingProduct.PRid == product.PRid,
            GroupBuying.GBstarttime <= now,
            GroupBuying.GBendtime >= now
        ).first()

        if gp:
            product.fill('isgroupbuying', True)
            product.fill('GPprice', gp.GPprice)
            product.fill('GPstocks', gp.GPstpcks)
            product.fill('GPfreight', gp.GPfreight)
            for sku in product.skus:
                gs = GroupbuyingSku.query.filter(
                    GroupbuyingSku.GPid == gp.GPid,
                    GroupbuyingSku.isdelete == False,
                    GroupbuyingSku.SKUid == sku.SKUid
                ).first()
                if not gs:
                    continue
                sku.fill('SKUgpPrice', gs.SKUgpPrice)
                sku.fill('SKUgpStock', gs.SKUgpStock)
        else:
            product.fill('isgroupbuying', False)

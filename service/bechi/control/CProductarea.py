import re
import uuid

from flask import current_app

from bechi.common.error_response import ParamsError
from bechi.common.params_validates import parameter_required
from bechi.common.success_response import Success
from bechi.config.enums import ProductAreaStatus
from bechi.control.CProduct import CProduct
from bechi.extensions.register_ext import db
from bechi.models.product import ProductArea, Products, ProductCategory


class CProductarea(CProduct):

    def get(self):
        filter_args = {
            ProductArea.isdelete == False,
        }
        # todo 增加是否是管理员判断
        # filter_args.add(ProductArea.PAstatus == ProductAreaStatus.normal.value)
        productareas = ProductArea.query.filter(*filter_args).order_by(ProductArea.PAsort).all()
        for pa in productareas:
            pa.fill('pastatus_zh', ProductAreaStatus(pa.PAstatus).zh_value)
            pcid_list = super(CProductarea, self)._sub_category_id(pa.PCid)
            # 默认根据X 人购买字段排序
            products = Products.query.filter(
                Products.PCid.in_(pcid_list), Products.isdelete == False).order_by(Products.PRpurchaseNum.desc()).all()

            # 筛选前4个
            pa.fill('products', products[:4])

        return Success(data=productareas)

    def create(self):
        data = parameter_required(('pcid', 'pasort', 'paimg'))
        self._check_pcid(data.get('pcid'))
        pasort = data.get('pasort')
        # assert isinstance(pasort, int), 'pasort 类型错误'
        if not isinstance(pasort, int):
            raise ParamsError('类型错误')
        pasort = self._check_pasort(pasort)
        productarea_instance = ProductArea.create({
            'PAid': str(uuid.uuid1()),
            'PCid': data.get('pcid'),
            'PAstatus': ProductAreaStatus.wait.value,
            'PAdesc': data.get('padesc'),
            'PAsort': pasort,
            'PAimg': data.get('paimg'),
        })
        with db.auto_commit():
            db.session.add(productarea_instance)
        return Success(data=productarea_instance.PAid)

    def update(self):
        data = parameter_required(('paid', ))

        with db.auto_commit():
            productarea = ProductArea.query.filter(ProductArea.PAid == data.get('paid')).first_('专题已取消')
            if data.get('delete'):
                productarea.isdelete = True
                return Success('删除成功')
            if data.get('pastatus'):
                # if re.match(r'^-?\d+$', str(data.get('pastatus'))):
                if self._check_int(data.get('pastatus')):
                    # ProductAreaStatus.
                    try:
                        productarea.PAstatus = ProductAreaStatus(int(data.get('pastatus'))).value
                    except Exception as e:
                        current_app.logger.info('pastatus {} 违法 error msg {}'.format(data.get('pastatus'), e.args) )
                        raise ParamsError('pastatus 参数违法')

            if data.get('pcid'):
                self._check_pcid(data.get('pcid'))
                productarea.PCid = data.get('pcid')
            if data.get('pasort'):
                productarea.PAsort = self._check_pasort(data.get('pasort'))
            if data.get('paimg'):
                productarea.PAimg = data.get('paimg')

        return Success('更新成功')

    def _check_pasort(self, pasort):
        # if not re.match(r'^-?\d+$', str(pasort)):
        if not self._check_int(pasort):
            raise ParamsError('pasort 类型异常')
        pasort = int(str(pasort))
        if pasort < 1:
            return 1

        pacount = ProductArea.query.filter(
            ProductArea.isdelete == False, ProductArea.PAstatus == ProductAreaStatus.normal.value).count()

        if pasort > pacount:
            return pacount
        return pasort

    def _check_pcid(self, pcid):
        return ProductCategory.query.filter(
            ProductCategory.PCid == pcid, ProductCategory.isdelete == False).first_('分类已失效，重新选择')

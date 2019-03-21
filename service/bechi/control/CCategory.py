import uuid

from bechi.common.error_response import ParamsError
from bechi.common.params_validates import parameter_required
from bechi.common.success_response import Success
from bechi.common.token_handler import admin_required
from bechi.config.enums import ProductStatus
from bechi.extensions.register_ext import db
from bechi.models.product import ProductCategory, Products


class CCategory():
    # @admin_required
    def create(self):
        data = parameter_required(('pcdesc', 'pcname', 'pcpic'))
        pcdesc = data.get('pcdesc')
        pcname = data.get('pcname')
        pcpic = data.get('pcpic')
        parentpcid = data.get('parentpcid')
        pcsort = data.get('pcsort', 1)
        if not isinstance(pcsort, int):
            raise ParamsError('pcsort 类型错误')

        if not parentpcid:
            pctype = 1
        else:
            # parent_catory = self._get_category_one(parentpcid, '指定父级目录不存在')
            parent_catory = ProductCategory.query.filter(
            ProductCategory.PCid == parentpcid, ProductCategory.isdelete == False).first_('指定父级目录不存在')
            pctype = parent_catory.PCtype + 1

        pcsort = self._check_sort(pctype, pcsort, parentpcid)

        with db.auto_commit() as s:

            category_instance = ProductCategory.create({
                'PCid': str(uuid.uuid4()),
                'PCtype': pctype,
                'PCname': pcname,
                'PCdesc': pcdesc,
                'ParentPCid': parentpcid,
                'PCpic': pcpic,
                'PCsort': pcsort,
                'PCtopPic': data.get('pctoppic')
            })
            s.add(category_instance)
        return Success('创建成功', {'pcid': category_instance.PCid})

    def get(self):
        data = parameter_required()
        up = data.get('up') or None
        deep = data.get('deep', 0)  # 深度
        # pctype = 1 if not up else None
        # categorys = self.sproduct.get_categorys({'ParentPCid': up, 'PCtype': pctype})
        filter_args = {
            ProductCategory.isdelete == False
        }
        if up:
            filter_args.add(ProductCategory.ParentPCid == up)
        else:
            filter_args.add(ProductCategory.PCtype == 1)

        categorys = ProductCategory.query.filter(*filter_args).all()
        for category in categorys:
            self._sub_category(category, deep)
        return Success(data=categorys)

    # @admin_required
    def delete(self):
        data = parameter_required(('pcid', ))
        pcid = data.get('pcid')
        with db.auto_commit() as s:
            product_category_instance = s.query(ProductCategory).filter_by_({'PCid': pcid}).first_('该分类不存在')
            product_category_instance.isdelete = True
            s.add(product_category_instance)
            s.query(Products).filter_(Products.PCid == product_category_instance.PCid).update({
                'PRstatus': ProductStatus.off_shelves.value,
                'PCid': None
            }, synchronize_session=False)

        return Success('删除成功')

    # @admin_required
    def update(self):
        """更新分类"""
        data = parameter_required(('pcid', 'pcdesc', 'pcname', 'pcpic'))
        pcdesc = data.get('pcdesc')
        pcname = data.get('pcname')
        pcpic = data.get('pcpic')
        parentpcid = data.get('parentpcid')
        pcsort = int(data.get('pcsort', 1))
        pctoppic = data.get('pctoppic')
        with db.auto_commit():
            current_category = ProductCategory.query.filter(
                ProductCategory.isdelete == False,
                ProductCategory.PCid == data.get('pcid')
            ).first_('分类不存在')
            pcsort = self._check_sort(current_category.PCtype, pcsort, parentpcid)
            if parentpcid:
                parent_cat = ProductCategory.query.filter(
                    ProductCategory.isdelete == False,
                    ProductCategory.PCid == parentpcid
                ).first_('指定上级目录不存在')
                current_category.PCtype = parent_cat.PCtype + 1
            else:
                current_category.PCtype = 1
            current_category.update({
                'PCname': pcname,
                'PCdesc': pcdesc,
                'ParentPCid': parentpcid,
                'PCsort': pcsort,
                'PCpic': pcpic,
                'PCtopPic': pctoppic
            }, null='not ignore')
            db.session.add(current_category)
        return Success('更新成功')

    def _sub_category(self, category, deep, parent_ids=()):
        """遍历子分类"""
        parent_ids = list(parent_ids)
        try:
            deep = int(deep)
        except TypeError as e:
            raise ParamsError()
        if deep <= 0:
            del parent_ids
            return
        deep -= 1
        pcid = category.PCid
        if pcid not in parent_ids:
            # subs = self.sproduct.get_categorys({'ParentPCid': pcid})
            subs = ProductCategory.query.filter(
                ProductCategory.ParentPCid == pcid, ProductCategory.isdelete == False).all()
            if subs:
                parent_ids.append(pcid)
                category.fill('subs', subs)
                for sub in subs:
                    self._sub_category(sub, deep, parent_ids)

    def _check_sort(self, pctype, pcsort, parentpcid=None):
        count_pc = ProductCategory.query.filter_by_(PCtype=pctype, ParentPCid=parentpcid).count()
        if pcsort < 1:
            return 1
        if pcsort > count_pc:
            return count_pc
        return pcsort

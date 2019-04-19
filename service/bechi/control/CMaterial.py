# -*- coding: utf-8 -*-
import json
import re
import uuid

from flask import request, current_app

from bechi.common.error_response import ParamsError
from bechi.common.params_validates import parameter_required
from bechi.common.success_response import Success
from bechi.common.token_handler import admin_required, common_user, is_admin, token_required
from bechi.config.enums import UserStatus, CollectionType, MaterialCommentStatus, CategoryType
from bechi.extensions.register_ext import db
from bechi.models import Admin, User, UserCollections
from bechi.models.material import MaterialCategory, Material, MaterialCategoryRelated, MaterialComment, \
    MaterialFavorite, Dietitian, DietitianCategoryRelated


class CMaterial(object):
    def list_category(self):
        """素材库分类"""
        args = request.args.to_dict()
        mctype = args.get('mctype', 0) or 0
        categorys = MaterialCategory.query.filter(MaterialCategory.isdelete == False,
                                                  MaterialCategory.MCtype == mctype,
                                                  MaterialCategory.MCparentid.is_(None)
                                                  ).order_by(MaterialCategory.MCsort.asc(),
                                                             MaterialCategory.createtime.desc()).all()
        for category in categorys:
            subs = self._sub_category(category.MCid, mctype)
            if subs:
                category.fill('sub', subs)
                for sub in subs:
                    sb = self._sub_category(sub.MCid, mctype)
                    if sb:
                        sub.fill('sub', sb)
        return Success('获取成功', data=categorys)

    @staticmethod
    def _sub_category(mcid, mctype):
        sub = MaterialCategory.query.filter(MaterialCategory.isdelete == False,
                                            MaterialCategory.MCtype == mctype,
                                            MaterialCategory.MCparentid == mcid
                                            ).order_by(MaterialCategory.MCsort.asc(),
                                                       MaterialCategory.createtime.desc()).all()
        if mcid == 'hot_topic':
            for sb in sub:
                # 帖子总数
                posts = Material.query.outerjoin(MaterialCategoryRelated,
                                                 MaterialCategoryRelated.MTid == Material.MTid
                                                 ).filter(MaterialCategoryRelated.isdelete == False,
                                                          MaterialCategoryRelated.MCid == sb.MCid,
                                                          Material.isdelete == False).count()
                # 参与总数
                participation = MaterialComment.query.outerjoin(MaterialCategoryRelated,
                                                                MaterialCategoryRelated.MTid == MaterialComment.MTid
                                                                ).filter(MaterialCategoryRelated.isdelete == False,
                                                                         MaterialCategoryRelated.MCid == sb.MCid,
                                                                         MaterialComment.isdelete == False).count()
                sb.fill('total_posts', posts)
                sb.fill('total_participation', participation)
        return sub

    @admin_required
    def create_category(self):
        """创建分类"""
        self._check_admin(request.user.id)
        data = parameter_required(('mcname', 'mctype', ))
        mcsort = data.get('mcsort')
        mcparentid = data.get('mcparentid')
        mctype = data.get('mctype')
        try:
            mctype = CategoryType(mctype)
        except Exception as e:
            raise e
            mctype = 0
        mctype = data.get('mctype')
        with db.auto_commit():
            if mctype == CategoryType.material.value:
                if not mcparentid:
                    raise ParamsError('创建素材分类时 mcparentid 不能为空')
                parent_category = MaterialCategory.query.filter_by_(MCid=mcparentid).first_('上级分类不存在')
                if parent_category.MCid == 'knowledge_classroom':
                    raise ParamsError('不允许在该层下创建分类')  # 知识课堂下不允许创建二级分类
                mcsort = self._check_sort(mctype, mcsort, mcparentid)
                category_dict = {'MCid': str(uuid.uuid1()),
                                 'MCname': data.get('mcname'),
                                 'MCparentid': mcparentid,
                                 'MClevel': parent_category.MClevel + 1,
                                 'MCsort': mcsort,
                                 'MCtype': mctype
                                 }
                if category_dict['MClevel'] > 3:
                    raise ParamsError('超出分类最高层级')
                if mcparentid == 'hot_topic':  # 热门话题有简介 和 图片
                    category_dict['MCpicture'] = data.get('mcpicture')
                    category_dict['MCdesc'] = data.get('mcdesc')
            else:
                if mcparentid:
                    raise ParamsError('创建营养师分类时 不允许有 mcparentid')
                category_dict = {'MCid': str(uuid.uuid1()),
                                 'MCname': data.get('mcname'),
                                 'MClevel': 1,
                                 'MCsort': mcsort,
                                 'MCtype': mctype
                                 }
            category_instance = MaterialCategory.create(category_dict)
            db.session.add(category_instance)
        return Success('创建成功', data=dict(MCid=category_dict['MCid']))

    @admin_required
    def update_category(self):
        """更新/删除分类"""
        self._check_admin(request.user.id)
        data = parameter_required(('mcid', 'mcname', 'mctype'))
        mcid, mctype, mcsort = data.get('mcid'), data.get('mctype', 0), data.get('mcsort', 0)
        mcisdelete = data.get('mcisdelete')
        category = MaterialCategory.query.filter_by_(MCid=mcid, MCtype=mctype).first_('要修改的分类不存在')
        if mctype == CategoryType.material.value:
            if mcid in ['case_community', 'knowledge_classroom', 'disease_treatment', 'health_encyclopedia', 'hot_topic']:
                raise ParamsError('系统内置分类不允许更改')
            mcsort = self._check_sort(mctype, mcsort, category.MCparentid)
            if category.MClevel == 1:
                raise ParamsError('该层分类不允许修改')
        update_dict = {'MCname': data.get('mcname'),
                       'MCsort': mcsort,
                       }
        if category.MCparentid == 'hot_topic':
            update_dict['MCpicture'] = data.get('mcpicture')
            update_dict['MCdesc'] = data.get('mcdesc')
        with db.auto_commit():
            if mcisdelete:
                category.update({'isdelete': True})
            else:
                category.update(update_dict)
            db.session.add(category)
        return Success('修改成功', data=dict(MCid=mcid))

    @staticmethod
    def _check_sort(mctype, mcsort, mcparentid=None):
        count_pc = MaterialCategory.query.filter_by_(MCtype=mctype, MCparentid=mcparentid).count()
        if not count_pc:
            count_pc = 1
        if mcsort < 1:
            return 1
        if mcsort > count_pc:
            return count_pc
        return mcsort

    @admin_required
    def post_material(self):
        """创建/更新素材"""
        admin = self._check_admin(request.user.id)
        data = parameter_required(('mttitle', 'mtcontent', 'mcids'))
        mttitle, mtcontent, mtpicture, mtvideo = (data.get('mttitle'), data.get('mtcontent'),
                                                  data.get('mtpicture'), data.get('mtvideo'))
        mtfakeviews, mtfakefavorite= data.get('mtfakeviews', 0), data.get('mtfakefavorite', 0)
        mtfakeforward = data.get('mtfakeforward', 0)
        mtid = data.get('mtid')
        mcids = data.get('mcids') or []

        for rex_str in [mtfakeviews, mtfakefavorite, mtfakeforward]:
            if not re.match(r'^[0-9]+$', str(rex_str)):
                raise ParamsError('虚拟量只能输入数字')

        if mtpicture and isinstance(mtpicture, list):
            mtpicture = json.dumps(mtpicture)
        if mtvideo and isinstance(mtvideo, list):
            mtvideo = json.dumps(mtvideo)
        with db.auto_commit():
            material_dict = {'MTauthor': admin.ADid,
                             'MTauthorname': admin.ADname,
                             'MTauthoravatar': admin.ADheader,
                             'MTtitle': mttitle,
                             'MTcontent': mtcontent,
                             'MTtext': data.get('mttext'),
                             'MTpicture': mtpicture,
                             'MTvideo': mtvideo,
                             'MTfakeviews': mtfakeviews,
                             'MTfakefavorite': mtfakefavorite,
                             'MTfakeforward': mtfakeforward,
                             'MTisrecommend': data.get('mtisrecommend'),
                             'MTsort': data.get('mtsort')
                             }
            if mtid:
                material_instance = Material.query.filter_by_(MTid=mtid).first_('要修改的文章不存在')
                if data.get('isdelete'):
                    material_instance.update({'isdelete': True})
                    MaterialCategoryRelated.query.filter_by(MTid=mtid, isdelete=False).delete_()  # 删除分类关联
                    MaterialFavorite.query.filter_by(MTid=mtid, isdelete=False).delete_()  # 删除点赞
                    MaterialComment.query.filter_by(MTid=mtid, isdelete=False).delete_()  # 删除评论
                else:
                    material_instance.update(material_dict)
                    ids = list()
                    for mcid in mcids:
                        if mcid in ['case_community', 'knowledge_classroom', 'disease_treatment',
                                    'health_encyclopedia', 'hot_topic']:
                            continue
                        ids.append(mcid)
                        mcr = MaterialCategoryRelated.query.filter_by(MCid=mcid, MTid=mtid, isdelete=False).first()
                        if not mcr:
                            db.session.add(MaterialCategoryRelated.create({'MCRid': str(uuid.uuid1()),
                                                                           'MTid': mtid,
                                                                           'MCid': mcid}
                                                                          )
                                           )
                    MaterialCategoryRelated.query.filter(MaterialCategoryRelated.MCid.notin_(ids),
                                                         MaterialCategoryRelated.isdelete == False
                                                         ).delete_(synchronize_session=False)

            else:
                mtid = str(uuid.uuid1())
                material_dict['MTid'] = mtid
                material_instance = Material.create(material_dict)
                for mcid in mcids:
                    db.session.add(MaterialCategoryRelated.create({'MCRid': str(uuid.uuid1()),
                                                                   'MTid': mtid,
                                                                   'MCid': mcid}
                                                                  )
                                   )
            db.session.add(material_instance)
        return Success('修改成功', data=dict(mtid=mtid))

    def get_material_list(self):
        """素材列表"""
        args = parameter_required(('mcid', 'page_size', 'page_num'))
        mcid = args.get('mcid')
        mc = MaterialCategory.query.filter_by_(MCid=mcid).first_('分类不存在')

        order = args.get('by_order')  # hot | new

        if mc.MCparentid == 'hot_topic' and str(order) == 'hot':
            by_order = [Material.MTfakeviews.desc(), Material.MTviews.desc(),
                        Material.MTsort.asc(), Material.createtime.desc()]
        elif mc.MCparentid == 'hot_topic' and str(order) == 'new':
            by_order = [Material.createtime.desc(), ]
        else:
            by_order = [Material.MTsort.asc(), Material.createtime.desc()]

        query = Material.query.filter(Material.isdelete == False)
        if mcid in ['case_community', 'disease_treatment', 'health_encyclopedia']:
            query = query.outerjoin(MaterialCategoryRelated, MaterialCategoryRelated.MTid == Material.MTid
                                    ).outerjoin(MaterialCategory,
                                                MaterialCategory.MCid == MaterialCategoryRelated.MCid
                                                ).filter(MaterialCategoryRelated.isdelete == False,
                                                         MaterialCategory.isdelete == False,
                                                         MaterialCategory.MCparentid == mcid,
                                                         Material.MTisrecommend == True
                                                         )  # “案例社区”、“疾病治疗”、“健康百科” mcid 默认获取其下所有的推荐
        else:
            query = query.outerjoin(MaterialCategoryRelated, MaterialCategoryRelated.MTid == Material.MTid
                                    ).filter(MaterialCategoryRelated.isdelete == False,
                                             MaterialCategoryRelated.MCid == mcid,
                                             Material.isdelete == False,
                                             )
        materials = query.order_by(*by_order).all_with_page()

        for material in materials:
            self.update_pageviews(material.MTid)  # 增加浏览量
            category = MaterialCategory.query.outerjoin(MaterialCategoryRelated,
                                                        MaterialCategoryRelated.MCid == MaterialCategory.MCid
                                                        ).filter(MaterialCategoryRelated.isdelete == False,
                                                                 MaterialCategory.isdelete == False,
                                                                 MaterialCategoryRelated.MTid == material.MTid).all()
            material.fill('category', category)
            if material.MTvideo:
                material.MTvideo = json.loads(material.MTvideo)
                mainpic = material.MTvideo[0].get('thumbnail')
                showtype = 'video'
                material.fill('mainpic', mainpic)
                material.fill('showtype', showtype)
            elif material.MTpicture:
                material.MTpicture = json.loads(material.MTpicture)
                mainpic = material.MTpicture[0]
                showtype = 'picture'
                material.fill('mainpic', mainpic)
                material.fill('showtype', showtype)

            if material.MTtext:
                material.MTtext = material.MTtext[:100] + ' ... '

            material.hide('MTcontent')

            comment_count = MaterialComment.query.filter_by_(MTid=material.MTid).count()  # todo 仅话题下有评论数 （参与）
            favorite_count = material.MTfakefavorite or MaterialFavorite.query.filter_by_(MTid=material.MTid).count()
            views_cout = material.MTfakeviews or material.MTviews

            material.fill('comment_count', comment_count)
            material.fill('favorite_count', favorite_count)
            material.fill('views_cout', views_cout)
        if mc.MCparentid == 'hot_topic':
            total_posts = Material.query.outerjoin(MaterialCategoryRelated,
                                                   MaterialCategoryRelated.MTid == Material.MTid
                                                   ).filter(MaterialCategoryRelated.isdelete == False,
                                                            MaterialCategoryRelated.MCid == mcid,
                                                            Material.isdelete == False).count()

            total_participation = MaterialComment.query.outerjoin(MaterialCategoryRelated,
                                                                  MaterialCategoryRelated.MTid == MaterialComment.MTid
                                                                  ).filter(MaterialCategoryRelated.isdelete == False,
                                                                           MaterialCategoryRelated.MCid == mcid,
                                                                           MaterialComment.isdelete == False).count()

            return Success('获取成功', data=dict(data=materials)
                           ).get_body({'total_posts': total_posts,
                                       'total_participation': total_participation}
                                      )
        return Success('获取成功', data=dict(data=materials))

    def get_material(self):
        """获取素材"""
        args = parameter_required(('mtid', ))
        mtid = args.get('mtid')
        material = Material.query.filter_by_(MTid=mtid).first_('文章不存在或已删除')

        pictures = getattr(material, 'MTpicture', '')
        pictures = json.loads(pictures) if pictures and isinstance(pictures, str) else None
        material.fill('mtpicture', pictures)

        videos = getattr(material, 'MTvideo', '')
        videos = json.loads(videos) if videos and isinstance(videos, str) else None
        material.fill('mtvideo', videos)

        comment_count = MaterialComment.query.filter_by_(MTid=mtid).count()  # todo 仅话题下有评论数 （参与）
        favorite_count = material.MTfakefavorite or MaterialFavorite.query.filter_by_(MTid=mtid).count()
        views_cout = material.MTfakeviews or material.MTviews

        material.fill('comment_count', comment_count)
        material.fill('favorite_count', favorite_count)
        material.fill('views_cout', views_cout)
        if common_user():
            user = self._check_user(request.user.id)
            is_favorite = bool(MaterialFavorite.query.filter_by_(MTid=mtid, USid=user.USid).first())
            is_collection = bool(UserCollections.query.filter_by_(UCScollectionid=mtid, USid=user.USid,
                                                                  UCStype=CollectionType.material.value).first())
        else:
            user = None
            is_favorite = False
            is_collection = False
        material.fill('is_favorite', is_favorite)
        material.fill('is_collection', is_collection)

        # 增加分类信息
        category = MaterialCategory.query.outerjoin(MaterialCategoryRelated,
                                                    MaterialCategoryRelated.MCid == MaterialCategory.MCid
                                                    ).filter(MaterialCategoryRelated.isdelete == False,
                                                             MaterialCategory.isdelete == False,
                                                             MaterialCategoryRelated.MTid == material.MTid).all()
        material.fill('category', category)
        self.update_pageviews(mtid)  # 增加浏览量
        return Success('获取成功', data=dict(data=material))

    @token_required
    def create_comment(self):
        user = self._check_user(request.user.id)
        data = parameter_required(('mtid', 'mcocontent', ))
        mtid = data.get('mtid')
        Material.query.filter_by_(MTid=mtid).first_('评论文章不存在或已删除')
        with db.auto_commit():
            mco_dict = {'MCOid': str(uuid.uuid1()),
                        'MTid': mtid,
                        'MCOcontent': data.get('mcocontent'),
                        'MCOstatus': MaterialCommentStatus.auditing.value,
                        'MCOauthor': user.USid,
                        'MCOauthorname': user.USname,
                        'MCOauthoravatar': user.USheader
                        }
            mco_instance = MaterialComment.create(mco_dict)
            db.session.add(mco_instance)
        return Success('评论成功，正在审核中', data=dict(mcoid=mco_dict['MCOid']))

    def get_comment(self):
        args = parameter_required(('mtid', 'mcostatus'))
        mtid = args.get('mtid')
        mcostatus = args.get('mcostatus', )
        ms = MaterialComment.query.filter_(MaterialComment.MTid == mtid,
                                           MaterialComment.MCOstatus == getattr(MaterialCommentStatus, mcostatus).value,
                                           MaterialComment.isdelete == False
                                           ).order_by(MaterialComment.MCOistop.desc(),
                                                      MaterialComment.createtime.desc()).all()
        for mc in ms:
            mc.fill('mcostatus_zh', getattr(MaterialCommentStatus, mc.MCOstatus).zh_value)
        return Success('获取成功', data=dict(data=ms))

    @admin_required
    def approve_comment(self):
        """处理评论 置顶/删除/通过/驳回"""
        self._check_admin(request.user.id)
        data = parameter_required(('mcoid', 'operation'))
        mcoid = data.get('mcoid')
        operation = data.get('operation')
        if operation not in ['top', 'del', 'pass', 'reject']:
            raise ParamsError('operation参数错误')
        with db.auto_commit():
            mco = MaterialComment.query.filter_by_(MCOid=mcoid).first_('该评论不存在')
            if str(operation) == 'top':
                opt_dict = {'MCOistop': True}
                MaterialComment.query.filter(MaterialComment.MTid == mco.MTid,
                                             MaterialComment.MCOid != mco.MCOid,
                                             MaterialComment.isdelete == False).update({'MCOistop': False})  # 只有一个置顶
            elif str(operation) == 'del':
                opt_dict = {'isdelete': True}
            elif str(operation) == 'pass':
                opt_dict = {'MCOstatus': MaterialCommentStatus.usual.value}
            else:
                opt_dict = {'MCOstatus': MaterialCommentStatus.reject.value}
            mco.update(opt_dict)
            db.session.add(mco)
        return Success('修改成功', data=dict(mcoid=mcoid))

    def post_dietitian(self):
        """创建营养师"""
        data = parameter_required(('mcids', 'dtname', 'dtphone', 'dtavatar', 'dtqrcode', 'dtintroduction'))
        dtphone = data.get('dtphone')
        dtid = data.get('dtid')
        mcids = data.get('mcids')
        if not re.match('^1[345789][0-9]{9}$', str(dtphone)):
            raise ParamsError('请输入正确的手机号码')
        with db.auto_commit():
            session_list = list()
            dietitian_dict = {'DTname': data.get('dtname'),
                              'DTphone': data.get('dtphone'),
                              'DTavatar': data.get('dtavatar'),
                              'DTqrcode': data.get('dtqrcode'),
                              'DTintroduction': data.get('dtintroduction'),
                              'DTisrecommend': data.get('dtisrecommend', False)
                              }
            if dtid:
                dietitian = Dietitian.query.filter_by_(DTid=dtid).first_('要修改的营养师资料不存在')
                if data.get('isdelete'):
                    dietitian.update({'isdelete': True})
                    DietitianCategoryRelated.query.filter(DietitianCategoryRelated.DTid == dietitian.DTid,
                                                          DietitianCategoryRelated.isdelete == False).delete_()
                    session_list.append(dietitian)
                else:
                    dietitian.update(dietitian_dict)
                    session_list.append(dietitian)
                    ids = list()
                    for mcid in mcids:
                        ids.append(mcid)
                        mc = MaterialCategory.query.filter_by_(MCid=mcid, MCtype=CategoryType.dietitian.value
                                                               ).first()
                        if not mc:
                            session_list.append(DietitianCategoryRelated.create({'DCRid': str(uuid.uuid1()),
                                                                                 'DTid': dietitian_dict['DTid'],
                                                                                 'MCid': mcid}))
                    DietitianCategoryRelated.query.filter(DietitianCategoryRelated.DTid == dietitian.DTid,
                                                          DietitianCategoryRelated.isdelete == False,
                                                          DietitianCategoryRelated.MCid.notin_(ids)).delete_()

            else:
                dietitian_dict['DTid'] = str(uuid.uuid1())
                dietitian = Dietitian.create(dietitian_dict)
                session_list.append(dietitian)
                for mcid in mcids:
                    MaterialCategory.query.filter_by_(MCid=mcid, MCtype=CategoryType.dietitian.value).first_('分类不存在')
                    session_list.append(DietitianCategoryRelated.create({'DCRid': str(uuid.uuid1()),
                                                                         'DTid': dietitian_dict['DTid'],
                                                                         'MCid': mcid}))
            db.session.add_all(session_list)
        return Success('修改成功')

    def list_dietitian(self):
        """营养师"""
        args = request.args.to_dict()
        mcid = args.get('mcid')
        if mcid:
            res = Dietitian.query.join(DietitianCategoryRelated,
                                       DietitianCategoryRelated.DTid == Dietitian.DTid
                                       ).filter(DietitianCategoryRelated.isdelete == False,
                                                Dietitian.isdelete == False,
                                                DietitianCategoryRelated.MCid == mcid).first()
        else:
            res = Dietitian.query.filter_by_(DTisrecommend=True).order_by(Dietitian.createtime.desc()).all()
        return Success('获取成功', dict(data=res))

    @staticmethod
    def update_pageviews(mtid):
        """增加浏览量"""
        with db.auto_commit():
            material = Material.query.filter_by_(MTid=mtid).first()
            if material:
                dict_views = {'MTviews': material.MTviews + 1}
                if material.MTfakeviews:
                    dict_views['MTfakeviews'] = material.MTfakeviews + 1
                db.session.add(material.update(dict_views))
        return

    @staticmethod
    def _check_admin(adid):
        return Admin.query.filter_by_(ADid=adid, ADstatus=UserStatus.usual.value).first_('账号信息错误')

    @staticmethod
    def _check_user(usid):
        return User.query.filter_by_(USid=usid).first_('账号信息错误')

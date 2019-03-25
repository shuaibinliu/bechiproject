# -*- coding: utf-8 -*-
from sqlalchemy import String, Text, Integer, Boolean, orm
from sqlalchemy.dialects.mysql import LONGTEXT

from bechi.common.base_model import Base, Column


class Material(Base):
    """素材"""
    __tablename__ = 'Material'
    MTid = Column(String(64), primary_key=True)
    MTauthor = Column(String(64), nullable=False, comment='作者id')
    MTauthorname = Column(String(128), comment='作者名')
    MTauthoravatar = Column(String(255), url=True, comment='作者头像')
    MTtitle = Column(String(128), nullable=False, comment='标题')
    MTcontent = Column(LONGTEXT, comment='文章富文本内容')
    MTtext = Column(Text, comment='文本内容')
    MTpicture = Column(LONGTEXT, comment='图片[url1, url2]')
    MTvideo = Column(LONGTEXT, comment='视频 [{},{}]')
    MTviews = Column(Integer, default=0, comment='浏览量')
    MTfakeviews = Column(Integer, default=0, comment='虚拟浏览量')
    MTfakefavorite = Column(Integer, default=0, comment='虚拟点赞数')
    MTforward = Column(Integer, default=0, comment='转发数')
    MTfakeforward = Column(Integer, default=0, comment='虚拟转发数')
    MTstatus = Column(Integer, default=0, comment='文章状态 {0: 已发布}')
    MTisrecommend = Column(Boolean, default=False, comment='是否推荐到首页')
    MTsort = Column(Integer, comment='顺序')

    @orm.reconstructor
    def __init__(self):
        super(Material, self).__init__()
        self.add('createtime')
        self.hide('MTfakeviews', 'MTfakefavorite', 'MTfakeforward')


class MaterialCategory(Base):
    """素材分类"""
    __tablename__ = 'MaterialCategory'
    MCid = Column(String(64), primary_key=True)
    MCname = Column(String(64), nullable=False, comment='分类名')
    MCparentid = Column(String(64), comment='父级id')
    MClevel = Column(Integer, default=1, comment='最高三级分类{1: 一级分类; 2: 二级分类; 3: 三级分类}')
    MCsort = Column(Integer, comment='顺序')
    MCtype = Column(Integer, default=0, comment='分类类别{0: 素材分类; 1: 营养师分类}')
    MCpicture = Column(Text, comment='图片，仅话题分类有')
    MCdesc = Column(String(255), comment='分类描述， 仅话题展示')


class MaterialCategoryRelated(Base):
    """素材分类关联表"""
    __tablename__ = 'MaterialCategoryRelated'
    MCRid = Column(String(64), primary_key=True)
    MTid = Column(String(64), nullable=False, comment='素材id')
    MCid = Column(String(64), nullable=False, comment='分类id')


class MaterialComment(Base):
    """素材评论"""
    ___tablename__ = 'MaterialComment'
    MCOid = Column(String(64), primary_key=True)
    MTid = Column(String(64), nullable=False, comment='素材id')
    MCOcontent = Column(String(255), comment='评论内容')
    MCOstatus = Column(Integer, default=0, comment='评论审核状态{0: 审核中 1：通过 2：拒绝}')
    MCOauthor = Column(String(64), nullable=False, comment='评论者id')
    MCOauthorname = Column(String(128), comment='评论者名')
    MCOauthoravatar = Column(String(255), url=True, comment='评论者头像')
    MCOistop = Column(Boolean, default=False, comment='是否置顶')

    @orm.reconstructor
    def __init__(self):
        super(MaterialComment, self).__init__()
        self.add('createtime')


class MaterialFavorite(Base):
    """素材点赞"""
    __tablename__ = 'MaterialFavorite'
    MFid = Column(String(64), primary_key=True)
    MTid = Column(String(64), nullable=False, comment='素材id')
    USid = Column(String(64), nullable=False, comment='用户id')


class Dietitian(Base):
    """营养师"""
    __tablename__ = 'Dietitian'
    DTid = Column(String(64), primary_key=True)
    DTname = Column(String(20), nullable=False, comment='营养师姓名')
    DTphone = Column(String(13), comment='手机号')
    DTavatar = Column(String(255), nullable=False, url=True, comment='头像')
    DTqrcode = Column(String(255), url=True, comment='营养师二维码')
    DTintroduction = Column(Text, comment='营养师简介')
    DTisrecommend = Column(Boolean, default=False, comment='是否推荐到首页')


class DietitianCategoryRelated(Base):
    """营养师分类关联表"""
    __tablename__ = 'DietitianCategoryRelated'
    DCRid = Column(String(64), primary_key=True)
    DTid = Column(String(64), nullable=False, comment='营养师id')
    MCid = Column(String(64), nullable=False, comment='分类id')

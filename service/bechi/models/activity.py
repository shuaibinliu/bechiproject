# -*- coding: utf-8 -*-
from sqlalchemy import String, Text, Integer, Boolean, Date, DateTime, DECIMAL, Float, BIGINT

from bechi.common.base_model import Base, Column


class GroupBuying(Base):
    """
    拼团配置
    """
    __tablename__ = 'GroupBuying'
    GBid = Column(String(64), primary_key=True)
    GBstarttime = Column(DateTime, nullable=False, comment='活动开始时间')
    GBendtime = Column(DateTime, nullable=False, comment='活动结束时间')
    GBnum = Column(Text, nullable=False, comment='拼团限制人数')
    GBstatus = Column(Integer, default=1, comment='拼团状态 1 审核中 10 上线 -10 撤销 -20 拒绝 -30 下架')
    GBreason = Column(Text, comment='拒绝理由')
    GBstart = Column(String(64), comment='发起人')


class GroupbuyingItem(Base):
    """
    子拼团主体
    """
    __tablename__ = 'GroupbuyingItem'
    GIid = Column(String(64), primary_key=True)
    GBid = Column(String(64), comment='主拼团id')
    GIstatus = Column(Integer, default=1, comment='子拼团状态 1 拼团中 2 拼团成功 3 撤销 4 超时结束')


class GroupbuyingUser(Base):
    """
    拼团用户
    """
    __tablename__ = 'GroupbuyingUser'
    GUid = Column(String(64), primary_key=True)
    GIid = Column(String(64), comment='参与的拼团团体')
    USid = Column(String(64), comment='参与的用户')
    UShead = Column(Text, comment='用户头像')
    USname = Column(Text, comment='用户昵称')


class GroupbuyingProduct(Base):
    """
    拼团商品
    """
    __tablename__ = 'GroupbuyingProduct'
    GPid = Column(String(64), primary_key=True)
    GBid = Column(String(64), comment='拼团主体')
    PRid = Column(String(64), comment='商品id')
    PRtitle = Column(String(255), nullable=False, comment='标题')
    GPprice = Column(DECIMAL(precision=28, scale=2), nullable=False, comment='拼团价格')
    # PRlinePrice = Column(DECIMAL(precision=28, scale=2), comment='划线价格')
    GPfreight = Column(DECIMAL(precision=10, scale=2), default=0, comment='运费')
    GPstocks = Column(BIGINT, comment='库存')
    # PRsalesValue = Column(Integer, default=0, comment='销量')
    # PRstatus = Column(Integer, default=10, comment='状态  0 正常, 10 审核中 60下架')
    # PRmainpic = Column(String(255), comment='主图', url=True)
    # PRattribute = Column(Text, comment='商品属性 ["网络","颜色","存储"]')
    # PCid = Column(String(64), comment='分类id')
    # PBid = Column(String(64), comment='品牌id')
    # PRdesc = Column(LONGTEXT, comment='商品详细介绍', url_list=True)
    # PRremarks = Column(String(255), comment='备注')
    # PRfrom = Column(Integer, default=0, comment='商品来源 0 平台发布 10 供应商发布')
    # PRdescription = Column(Text, comment='商品描述')
    # CreaterId = Column(String(64), nullable=False, comment='创建者')
    # PRaverageScore = Column(Float(precision=10, scale=2), default=10.00, comment='商品评价平均分')


class GroupbuyingSku(Base):
    """拼团商品sku"""
    __tablename__ = 'GroupbuyingSku'
    GSid = Column(String(64), primary_key=True)
    GPid = Column(String(64), comment='拼团商品id')
    SKUid = Column(String(64), comment='sku id')
    PRid = Column(String(64), nullable=False, comment='产品id')
    SKUgpPrice = Column(DECIMAL(precision=28, scale=2), nullable=False, comment='拼团价格')
    SKUgpStock = Column(BIGINT, comment='拼团库存')
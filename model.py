# -*- coding: utf-8 -*-
'''
# Created on 12月-29-20 20:46
# model.py
# @author: bamboo
'''

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, TIMESTAMP, text
from sqlalchemy.orm import relationship
import datetime

import setting
Base = declarative_base()


# 消费类别
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100))
    posttime = Column(DateTime, default=datetime.datetime.now)
    ts = Column(Integer)


# 消费人群
class People(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True, autoincrement=True)
    consumer = Column(String(100))
    posttime = Column(DateTime, default=datetime.datetime.now)
    ts = Column(Integer)


# 支付方式
class Payment(Base):
    __tablename__ = 'payment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    posttime = Column(DateTime, default=datetime.datetime.now)
    ts = Column(Integer)


# 消费信息
class Consumption(Base):
    __tablename__ = 'consumption'

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(String(100))
    category_id = Column(Integer, ForeignKey('category.id'))
    consumer_id = Column(Integer, ForeignKey('people.id'))
    payment_id = Column(Integer, ForeignKey('payment.id'))
    posttime = Column(Date, default=datetime.datetime.now)
    comments = Column(Text)
    ts = Column(Integer)


class Admins(Base):
    __tablename__ = 'admins'

    uid = Column(Integer, primary_key=True)
    username = Column(String(20))
    nickname = Column(String(50))
    userpass = Column(String(100))
    ts = Column(Integer)


# Base.metadata.create_all(setting.engine)

# -*- coding: utf-8 -*-
'''
# Created on 12月-29-20 21:55
# setting.py
# @author: bamboo
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os 
import web
from web.contrib.template import render_jinja




# jinjia2 模板
app_root = os.path.dirname(__file__)

templates_path = os.path.join(app_root,r'templates\global').replace('\\', '/')

global_render = render_jinja(
        templates_path,   	# 设置模板路径.
        encoding = 'utf-8', # 编码.
    )

# admin_render = render_jinja(
#         os.path.join(app_root, r'templates\manage').replace('\\', '/'),     # 设置模板路径.
#         encoding = 'utf-8', # 编码.
#     )

# sqlalchemy
# create_engine(数据库://用户名:密码(没有密码则为空)@主机名:端口/数据库名',echo =True)
# MYSQL_DB = "jizhang"
# MYSQL_USER = "root"
# MYSQL_PASS = "GgwhQpJBfV-N6qLtTDWV"
# MYSQL_HOST_M = "10.3.232.64"
# MYSQL_PORT = 3306

# engine = create_engine(
#     'mysql://%s:%s@%s:%s/%s?charset=utf8' %
#     (MYSQL_USER, MYSQL_PASS, MYSQL_HOST_M, MYSQL_PORT, MYSQL_DB),
#     encoding='utf8',
#     echo=False,
#     pool_recycle=5,
# )
#Unix/Mac - 4 initial slashes in total
# engine = create_engine('sqlite:////absolute/path/to/foo.db')
#Windows
engine = create_engine('sqlite:///jizhang.db')

def load_sqla(handler):
    web.ctx.orm = scoped_session(sessionmaker(bind=engine))
    try:
        return handler()
    except web.HTTPError:
       web.ctx.orm.commit()
       raise
    except:
        web.ctx.orm.rollback()
        raise
    finally:
        web.ctx.orm.commit()


# 禁用IP文件
denyipfile = os.path.join(app_root,r'ip.txt').replace('\\', '/')

#Session in mysql
db = web.database(dbn = "sqlite",db = "./jizhang.db")
# db = web.database(
#                     dbn  = 'mysql',
#                     user = MYSQL_USER,
#                     pw   = MYSQL_PASS, 
#                     host = MYSQL_HOST_M,
#                     port = MYSQL_PORT, 
#                     db   = MYSQL_DB
#                 )

# store = web.session.DBStore(db, 'sessions')
store = web.session.DiskStore('sessions')

month_eg = {
    "01": u"一月",
    "02": u"二月",
    "03": u"三月",
    "04": u"四月",
    "05": u"五月",
    "06": u"六月",
    "07": u"七月",
    "08": u"八月",
    "09": u"九月",
    "10": u"十月",
    "11": u"十一月",
    "12": u"十二月"
    }

length_pwd = 6
# -*- coding: utf-8 -*-
'''
# Created on 12月-29-20 20:47
# view.py
# @author: bamboo
'''
from urls import urls
import os
import web
import md5
import datetime,time 
from setting import global_render,length_pwd,denyipfile
from setting import load_sqla, store, month_eg
from web import form
from model import Category, People, Consumption, Admins, Payment
import json 
from sqlalchemy import distinct,func

web.config.debug = False
app = web.application(urls, globals())
# app.notfound = notfound
# app.internalerror = internalerror

app.add_processor(load_sqla)
if web.config.get('_session') is None:
    session = web.session.Session(app, store, {'count': 0})
    web.config._session = session
    web.config._session['timeout'] = 3600
else:
    session = web.config._session
    session['timeout'] = 3600


class Temp():
    pass 


def timetranfer(str_time):
    timeArray = datetime.datetime.strptime(str_time,"%Y-%m-%d")
    return timeArray


def getmonth(str_time):
    month = datetime.datetime.strptime(str_time,"%Y-%m-%d").month
    return "%02d"%month


class Index:
    def GET(self):
        try:
            session.logged_in == True
            cate_type_sum = []

            # 获取类型消费
            
            categoryinfo = web.ctx.orm.query(Category.title,func.sum(Consumption.amount).label('total')).filter(Category.id == Consumption.category_id ).group_by(Category.title)

            category_data = []
            for cad in categoryinfo:
                
                cate_type_sum.append(cad.title)
                category_data.append({"value": cad.total , "name": cad.title})

            # 获取年度消费
            # select sum(amount),strftime('%Y', posttime) as year  from consumption GROUP BY strftime('%Y', posttime);

            yearinfo = web.ctx.orm.query(func.strftime("%Y",Consumption.posttime).label('year'),func.sum(Consumption.amount).label('total')).group_by(func.strftime("%Y",Consumption.posttime))

            yeardata = []
            for yd in yearinfo:
                cate_type_sum.append(u"%s年度"%yd.year)
                yeardata.append({"value": yd.total,"name": u"%s年度"%yd.year})

            
            return global_render.index(
                cate_type_sum = json.dumps(cate_type_sum),
                yeardata = json.dumps(yeardata),
                category_data = json.dumps(category_data)
                )
        except Exception:
            raise web.seeother('/login')
            # return global_render.login()


def nianduinfo(year):
    
    # 公共数据源
    ts_start = '%s-01-01 00:00:00'%int(year)
    ts_end = '%s-01-01 00:00:00'%(int(year)+1)

    ts_start_timestamp = int(time.mktime(time.strptime(ts_start,"%Y-%m-%d %H:%M:%S")))
    ts_end_timestamp = int(time.mktime(time.strptime(ts_end,"%Y-%m-%d %H:%M:%S")))

    category = web.ctx.orm.query(Category).all()
    
    zhangdan = web.ctx.orm.query(Consumption).filter(Consumption.ts >= ts_start_timestamp).filter(Consumption.ts < ts_end_timestamp).all()
   
    # for cc in zhangdan:
    #     print cc.amount,cc.ts,cc.posttime

    # categoryinfo 分类id 对应 名字 title 
    categoryinfo = {}
    for ca in category:
        categoryinfo[str(ca.id)] = ca.title 

    # 获取账单里面的分类信息
    cate_list = []
    for gg in zhangdan:
        for cc in category:
            if gg.category_id == cc.id:
                cate_list.append((gg.category_id,cc.title))

    cate_name_all = ['product',]
    cate_id_all = []
    for x in cate_list:
        if x[1] not in cate_name_all:
            cate_name_all.append(x[1])
        if x[0] not in cate_id_all:
            cate_id_all.append(x[0])


    # 全年各分类的总数据
    cate_sum = {}
    metadata_sum = []
    
    for zd in zhangdan:
        cate_ids = 'cateid_%d'%zd.category_id
        if cate_ids not in cate_sum.keys():
            cate_sum[cate_ids] = []
            cate_sum[cate_ids].append(float(zd.amount))
        else:
            cate_sum[cate_ids].append(float(zd.amount))
    for k,v in cate_sum.items():
        for y in cate_list:
            id = k.split("_")[1]
            if y[0] == int(id):
                metadata_sum.append({y[1]: sum(v)})

    # 获得全年每个分类的总数
    # category id 对应的 名字 字典
    
    cate_type = []
    cate_data = []
    for cate in cate_list:
        sum_id = 'cateid_%s'%cate[0]
        if cate_sum.has_key(sum_id):
            cate_type.append(cate[1])
            cate_data.append(sum(cate_sum[sum_id]))
    

    # 显示图形样式及数量
    css = []    
    for _ in range(len(metadata_sum)):
        css.append({"type": 'bar'})


    # 获取每月各个分类的数据
    all_month = []
    for e in zhangdan:
        m1 = datetime.datetime.strftime(e.posttime,"%m")
        zh_mon = month_eg.get(m1).encode("utf-8")
        if (len(all_month) != 0 ) and (zh_mon not in  [x['product'] for x in all_month ]):
            every_month = {}
            every_month['product'] = zh_mon
            
            every_month[categoryinfo.get(str(e.category_id))] = int(e.amount)
            all_month.append(every_month)

        elif (len(all_month) != 0 ) and (zh_mon in  [x['product'] for x in all_month ]):
            for s in all_month:
                if s['product'] == zh_mon and s.has_key(categoryinfo.get(str(e.category_id))):
                    s[categoryinfo.get(str(e.category_id))] += int(e.amount)
                elif s['product'] == zh_mon and ( not s.has_key(categoryinfo.get(str(e.category_id)))):
                    s[categoryinfo.get(str(e.category_id))] = int(e.amount)

        elif len(all_month) == 0:
            every_month = {}
            every_month['product'] = zh_mon
            every_month[categoryinfo.get(str(e.category_id))] = int(e.amount)
            all_month.append(every_month)
    # print all_month

    # 获取全年所有分类的总数据
    cg_list = []
    cost_list = []
    for cs in zhangdan:
        for xc in cate_list:
            if cs.category_id == xc[0]:
                cg_list.append(xc[1])
                cost_list

    # 获取支付方式汇总信息 
    payinfo = web.ctx.orm.query(Payment.name,func.sum(Consumption.amount).label('total')).filter(Payment.id == Consumption.payment_id ).filter(Consumption.ts >= ts_start_timestamp ).filter(Consumption.ts < ts_end_timestamp ).group_by(Payment.id)
    payamount = []
    payname = []
    for py in payinfo:
        payamount.append(py.total)
        payname.append(py.name)

    return {
        "cate_name_all":json.dumps(cate_name_all),
        "series":json.dumps(css),
        "all_month": json.dumps(all_month),
        "cate_type": json.dumps(cate_type),
        "cate_data": json.dumps(cate_data),
        "payamount": json.dumps(payamount),
        "payname": json.dumps(payname)
        }


def yueduinfo(month):
    # 公共数据源
    res = datetime.datetime.now()
    year = res.year
    # month = res.month

    ts_start = '%s-%s-01 00:00:00'%(year,month)
    ts_end = '%s-%s-01 00:00:00'%(year,'%02d'%(int(month)+1))

    ts_start_timestamp = int(time.mktime(time.strptime(ts_start,"%Y-%m-%d %H:%M:%S")))
    ts_end_timestamp = int(time.mktime(time.strptime(ts_end,"%Y-%m-%d %H:%M:%S")))
    
    #SELECT sum(c.amount),p.name from consumption as c, payment as p where strftime('%m', c.posttime)='01' and p.id = c.payment_id GROUP BY payment_id;

    payinfo = web.ctx.orm.query(Payment.name,func.sum(Consumption.amount).label('total')).filter(Payment.id == Consumption.payment_id ).filter(Consumption.ts >= ts_start_timestamp ).filter(Consumption.ts < ts_end_timestamp ).group_by(Payment.id)
    payamount = []
    payname = []
    for py in payinfo:
        payamount.append(py.total)
        payname.append(py.name)


    # SELECT sum(amount),ca.title from consumption as c, category as ca where strftime('%m', c.posttime)='01' and ca.id = c.category_id GROUP BY c.category_id;

    payinfo2 = web.ctx.orm.query(Category.title,func.sum(Consumption.amount).label('total')).filter(Category.id == Consumption.category_id ).filter(Consumption.ts >= ts_start_timestamp ).filter(Consumption.ts < ts_end_timestamp ).group_by(Consumption.category_id)

    payamount1 = []
    paytitle = []
    for py in payinfo2:
        payamount1.append(py.total)
        paytitle.append(py.title)


    # 获取每个月，每天的信息

    # 类型list 
    # select ca.title from consumption c , category ca where c.category_id == ca.id and strftime('%m', c.posttime)='01' and strftime('%Y', c.posttime)='2021' GROUP BY c.category_id;
    categoryinfo = web.ctx.orm.query(Category.title).filter(Consumption.category_id == Category.id ).filter(func.strftime('%Y',Consumption.posttime) == str(year)).filter(func.strftime('%m',Consumption.posttime) == "%02d"%int(month)).group_by(Consumption.category_id)
    
    cate_type = ['product',]

    for cate in categoryinfo:
        # print cate.title
        cate_type.append(cate.title)


    # 获取每天每个类型的花费
    #
    # select c.amount,ca.title,c.posttime from consumption c,category ca  where strftime('%m', c.posttime)='01' and strftime('%Y', c.posttime)='2021' and c.category_id == ca.id;
    zhangdaninfo = web.ctx.orm.query(Category.title,Consumption.amount,Consumption.posttime).filter(Consumption.category_id == Category.id ).filter(func.strftime('%Y',Consumption.posttime) == str(year)).filter(func.strftime('%m',Consumption.posttime) == "%02d"%int(month)).order_by(Consumption.posttime)

    yuedudata = []

    for vv in zhangdaninfo:
        posttime = datetime.datetime.strftime(vv.posttime,"%Y-%m-%d")
        daynum = posttime.split('-')[-1]
        typedata = {'product': daynum}
        if daynum not in [ x.values()[0] for x in yuedudata]:
            yuedudata.append(typedata)

    for vc in zhangdaninfo:
        ptime = datetime.datetime.strftime(vc.posttime,"%Y-%m-%d")
        dnum = ptime.split('-')[-1]
        # print vv.amount,vv.title,vv.posttime

        for yd in yuedudata:
            if  yd['product'] == dnum:
                if not yd.has_key(vc.title):
                    yd[vc.title] = float(vc.amount)
                else:
                    yd[vc.title] += float(vc.amount)
    print yuedudata

    databar = []
    for _ in range(len(cate_type)):
        databar.append({'type':'bar'})

    
    # 获取每个从哪种方式支出的信息
    # select c.amount,ca.name,c.posttime from consumption c,payment ca  where strftime('%m', c.posttime)='01' and strftime('%Y', c.posttime)='2021' and c.payment_id == ca.id ORDER BY c.posttime;

    zhangdanpayinfo = web.ctx.orm.query(Payment.name,Consumption.amount,Consumption.posttime).filter(Consumption.payment_id == Payment.id ).filter(func.strftime('%Y',Consumption.posttime) == str(year)).filter(func.strftime('%m',Consumption.posttime) == "%02d"%int(month)).order_by(Consumption.posttime)

    payment_type = ['product',]

    for pi in zhangdanpayinfo:
        if pi.name not in payment_type:
            payment_type.append(pi.name)


    paydata = []

    for payd in zhangdanpayinfo:
        posttime = datetime.datetime.strftime(payd.posttime,"%Y-%m-%d")
        pdaynum = posttime.split('-')[-1]
        ptypedata = {'product': pdaynum}
        if pdaynum not in [ x.values()[0] for x in paydata]:
            paydata.append(ptypedata)

    for vp in zhangdanpayinfo:
        ptime = datetime.datetime.strftime(vp.posttime,"%Y-%m-%d")
        dnum = ptime.split('-')[-1]
        
        for pyd in paydata:
            if  pyd['product'] == dnum:
                if not pyd.has_key(vp.name):
                    pyd[vp.name] = float(vp.amount)
                else:
                    pyd[vp.name] += float(vp.amount)

    pdatabar = []
    for _ in range(len(paydata)):
        pdatabar.append({'type':'bar'})

    return {
        "payamount":json.dumps(payamount),
        "payname":json.dumps(payname),
        "payamount1":json.dumps(payamount1),
        "paytitle": json.dumps(paytitle),
        "cate_type": json.dumps(cate_type),
        "yuedudata": json.dumps(yuedudata),
        "databar": json.dumps(databar),
        "payment_type": json.dumps(payment_type),
        "paydata":json.dumps(paydata),
        "pdatabar":json.dumps(pdatabar)
    }


class Niandu:
    def GET(self):
        try:
            session.logged_in == True
            # 显示公告
            yearinfo = datetime.datetime.now()
            year = yearinfo.year
            ndinfo = nianduinfo(year)
            
            return global_render.niandu(year=year,
                                        curryear = year,
                                        cate_name_all=ndinfo["cate_name_all"],
                                        series=ndinfo["series"],
                                        all_month=ndinfo["all_month"],
                                        cate_type=ndinfo["cate_type"],
                                        cate_data = ndinfo["cate_data"],
                                        payamount = ndinfo["payamount"],
                                        payname = ndinfo["payname"]
                                        )
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')

    def POST(self):
        try:
            session.logged_in == True
            userselect = web.input()
            year = userselect.get('nianfen','')
            print year
            yearinfo = datetime.datetime.now()
            curryear = yearinfo.year
            if year.strip() == '':
                year = curryear
            
            ndinfo = nianduinfo(year)
            return global_render.niandu(year=year,
                                        curryear = curryear,
                                        cate_name_all=ndinfo["cate_name_all"],
                                        series=ndinfo["series"],
                                        all_month=ndinfo["all_month"],
                                        cate_type=ndinfo["cate_type"],
                                        cate_data = ndinfo["cate_data"]
                                        )
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')


class NianduBak:
    def GET(self):
        # 显示公告
        yearinfo = datetime.datetime.now()
        year = yearinfo.year

        # 公共数据源
        category = web.ctx.orm.query(Category).all()
        zhangdan = web.ctx.orm.query(Consumption).filter(Consumption.posttime >= '2021').all()

        # categoryinfo 分类id 对应 名字 title 
        categoryinfo = {}
        for ca in category:
            categoryinfo[str(ca.id)] = ca.title 

        # 获取账单里面的分类信息
        cate_list = []
        for gg in zhangdan:
            for cc in category:
                if gg.category_id == cc.id:
                    cate_list.append((gg.category_id,cc.title))

        cate_name_all = ['product',]
        cate_id_all = []
        for x in cate_list:
            if x[1] not in cate_name_all:
                cate_name_all.append(x[1])
            if x[0] not in cate_id_all:
                cate_id_all.append(x[0])


        # 全年各分类的总数据
        cate_sum = {}
        metadata_sum = []
        
        for zd in zhangdan:
            cate_ids = 'cateid_%d'%zd.category_id
            if cate_ids not in cate_sum.keys():
                cate_sum[cate_ids] = []
                cate_sum[cate_ids].append(float(zd.amount))
            else:
                cate_sum[cate_ids].append(float(zd.amount))
        for k,v in cate_sum.items():
            for y in cate_list:
                id = k.split("_")[1]
                if y[0] == int(id):
                    metadata_sum.append({y[1]: sum(v)})
         
        # print metadata_sum

        # 获得全年每个分类的总数
        # category id 对应的 名字 字典
        # print cate_list
        # print cate_sum
        cate_type = []
        cate_data = []
        for cate in cate_list:
            sum_id = 'cateid_%s'%cate[0]
            if cate_sum.has_key(sum_id):
                cate_type.append(cate[1])
                cate_data.append(sum(cate_sum[sum_id]))
        
        # print "#" * 20
        # print cate_type
        # print cate_data 


        # 显示图形样式及数量
        css = []    
        for _ in range(len(metadata_sum)):
            css.append({"type": 'bar'})


        # 获取每月各个分类的数据
        all_month = []
        for e in zhangdan:
            m1 = datetime.datetime.strftime(e.posttime,"%m")
            zh_mon = month_eg.get(m1).encode("utf-8")
            if (len(all_month) != 0 ) and (zh_mon not in  [x['product'] for x in all_month ]):
                every_month = {}
                every_month['product'] = zh_mon
                
                every_month[categoryinfo.get(str(e.category_id))] = int(e.amount)
                all_month.append(every_month)

            elif (len(all_month) != 0 ) and (zh_mon in  [x['product'] for x in all_month ]):
                for s in all_month:
                    if s['product'] == zh_mon and s.has_key(categoryinfo.get(str(e.category_id))):
                        s[categoryinfo.get(str(e.category_id))] += int(e.amount)
                    elif s['product'] == zh_mon and ( not s.has_key(categoryinfo.get(str(e.category_id)))):
                        s[categoryinfo.get(str(e.category_id))] = int(e.amount)

            elif len(all_month) == 0:
                every_month = {}
                every_month['product'] = zh_mon
                every_month[categoryinfo.get(str(e.category_id))] = int(e.amount)
                all_month.append(every_month)
        # print all_month

        # 获取全年所有分类的总数据
        cg_list = []
        cost_list = []
        for cs in zhangdan:
            for xc in cate_list:
                if cs.category_id == xc[0]:
                    cg_list.append(xc[1])
                    cost_list

                
        
        return global_render.niandu(year=year,
                                    cate_name_all=json.dumps(cate_name_all),
                                    series=json.dumps(css),
                                    all_month=json.dumps(all_month),
                                    cate_type=json.dumps(cate_type),
                                    cate_data = json.dumps(cate_data)
                                    )


class YueduBak:
    def GET(self):
        # 公共数据源
        res = datetime.datetime.now()
        year = res.year
        month = res.month

        ts_start = '%s-%s-01 00:00:00'%(year,month)
        ts_end = '%s-%s-01 00:00:00'%(year,'%02d'%(int(month)+1))

        ts_start_timestamp = int(time.mktime(time.strptime(ts_start,"%Y-%m-%d %H:%M:%S")))
        ts_end_timestamp = int(time.mktime(time.strptime(ts_end,"%Y-%m-%d %H:%M:%S")))
        

        #SELECT sum(c.amount),p.name from consumption as c, payment as p where strftime('%m', c.posttime)='01' and p.id = c.payment_id GROUP BY payment_id;

        payinfo = web.ctx.orm.query(Payment.name,func.sum(Consumption.amount).label('total')).filter(Payment.id == Consumption.payment_id ).filter(Consumption.ts >= ts_start_timestamp ).filter(Consumption.ts < ts_end_timestamp ).group_by(Payment.id)
        payamount = []
        payname = []
        for py in payinfo:
            payamount.append(py.total)
            payname.append(py.name)


        # SELECT sum(amount),ca.title from consumption as c, category as ca where strftime('%m', c.posttime)='01' and ca.id = c.category_id GROUP BY c.category_id;

        payinfo2 = web.ctx.orm.query(Category.title,func.sum(Consumption.amount).label('total')).filter(Category.id == Consumption.category_id ).filter(Consumption.ts >= ts_start_timestamp ).filter(Consumption.ts < ts_end_timestamp ).group_by(Consumption.category_id)

        payamount1 = []
        paytitle = []
        for py in payinfo2:
            payamount1.append(py.total)
            paytitle.append(py.title)


        # 获取每个月，每天的信息

        # 类型list 
        # select ca.title from consumption c , category ca where c.category_id == ca.id and strftime('%m', c.posttime)='01' and strftime('%Y', c.posttime)='2021' GROUP BY c.category_id;
        categoryinfo = web.ctx.orm.query(Category.title).filter(Consumption.category_id == Category.id ).filter(func.strftime('%Y',Consumption.posttime) == '2021').filter(func.strftime('%m',Consumption.posttime) == '01').group_by(Consumption.category_id)
        
        cate_type = ['product',]

        for cate in categoryinfo:
            # print cate.title
            cate_type.append(cate.title)


        # 获取每天每个类型的花费
        #
        # select c.amount,ca.title,c.posttime from consumption c,category ca  where strftime('%m', c.posttime)='01' and strftime('%Y', c.posttime)='2021' and c.category_id == ca.id;
        zhangdaninfo = web.ctx.orm.query(Category.title,Consumption.amount,Consumption.posttime).filter(Consumption.category_id == Category.id ).filter(func.strftime('%Y',Consumption.posttime) == '2021').filter(func.strftime('%m',Consumption.posttime) == '01').order_by(Consumption.posttime)

        yuedudata = []

        for vv in zhangdaninfo:
            posttime = datetime.datetime.strftime(vv.posttime,"%Y-%m-%d")
            daynum = posttime.split('-')[-1]
            typedata = {'product': daynum}
            if daynum not in [ x.values()[0] for x in yuedudata]:
                yuedudata.append(typedata)

        for vc in zhangdaninfo:
            ptime = datetime.datetime.strftime(vc.posttime,"%Y-%m-%d")
            dnum = ptime.split('-')[-1]
            # print vv.amount,vv.title,vv.posttime

            for yd in yuedudata:
                if  yd['product'] == dnum:
                    if not yd.has_key(vc.title):
                        yd[vc.title] = float(vc.amount)
                    else:
                        yd[vc.title] += float(vc.amount)


        databar = []
        for _ in range(len(yuedudata)):
            databar.append({'type':'bar'})

        # 获取每个从哪种方式支出的信息
        # select c.amount,ca.name,c.posttime from consumption c,payment ca  where strftime('%m', c.posttime)='01' and strftime('%Y', c.posttime)='2021' and c.payment_id == ca.id ORDER BY c.posttime;

        zhangdanpayinfo = web.ctx.orm.query(Payment.name,Consumption.amount,Consumption.posttime).filter(Consumption.payment_id == Payment.id ).filter(func.strftime('%Y',Consumption.posttime) == '2021').filter(func.strftime('%m',Consumption.posttime) == '01').order_by(Consumption.posttime)

        payment_type = ['product',]

        for pi in zhangdanpayinfo:
            if pi.name not in payment_type:
                payment_type.append(pi.name)


        paydata = []

        for payd in zhangdanpayinfo:
            posttime = datetime.datetime.strftime(payd.posttime,"%Y-%m-%d")
            pdaynum = posttime.split('-')[-1]
            ptypedata = {'product': pdaynum}
            if pdaynum not in [ x.values()[0] for x in paydata]:
                paydata.append(ptypedata)

        for vp in zhangdanpayinfo:
            ptime = datetime.datetime.strftime(vp.posttime,"%Y-%m-%d")
            dnum = ptime.split('-')[-1]
            
            for pyd in paydata:
                if  pyd['product'] == dnum:
                    if not pyd.has_key(vp.name):
                        pyd[vp.name] = float(vp.amount)
                    else:
                        pyd[vp.name] += float(vp.amount)

        pdatabar = []
        for _ in range(len(paydata)):
            pdatabar.append({'type':'bar'})

        return global_render.yuedu(
            month=month,
            year=year,
            payamount = json.dumps(payamount),
            payname = json.dumps(payname),
            payamount1 = json.dumps(payamount1),
            paytitle = json.dumps(paytitle),
            cate_type = json.dumps(cate_type),
            yuedudata = json.dumps(yuedudata),
            databar = json.dumps(databar),
            payment_type = json.dumps(payment_type),
            paydata = json.dumps(paydata),
            pdatabar = json.dumps(pdatabar)
            )

    def POST(self):
        userselect = web.input()
        month = userselect.get('yuefen','')
        return month


class Yuedu:
    def GET(self):
        try:
            session.logged_in == True
            # 公共数据源
            res = datetime.datetime.now()
            year = res.year
            month = res.month
            yuedus =  yueduinfo(month)

            return global_render.yuedu(
                month=month,
                year=year,
                payamount = yuedus.get("payamount"),
                payname = yuedus.get("payname"),
                payamount1 = yuedus.get("payamount1"),
                paytitle = yuedus.get("paytitle"),
                cate_type = yuedus.get("cate_type"),
                yuedudata = yuedus.get("yuedudata"),
                databar = yuedus.get("databar"),
                payment_type = yuedus.get("payment_type"),
                paydata = yuedus.get("paydata"),
                pdatabar = yuedus.get("pdatabar")
                )

        # return global_render.login()
        except Exception:
            raise web.seeother('/login')


    def POST(self):
        try:
            session.logged_in == True
            userselect = web.input()
            month = userselect.get('yuefen','')
            
            yuedus =  yueduinfo(month)

            return global_render.yuedu(
                month=month,
                year=year,
                payamount = yuedus.get("payamount"),
                payname = yuedus.get("payname"),
                payamount1 = yuedus.get("payamount1"),
                paytitle = yuedus.get("paytitle"),
                cate_type = yuedus.get("cate_type"),
                yuedudata = yuedus.get("yuedudata"),
                databar = yuedus.get("databar"),
                payment_type = yuedus.get("payment_type"),
                paydata = yuedus.get("paydata"),
                pdatabar = yuedus.get("pdatabar")
                )
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')


class Fenlei:
    def GET(self):
        try:
            session.logged_in == True
            # 获取类型数据
            #select sum(c.amount),ca.title from consumption c, category ca  where c.category_id = ca.id GROUP BY c.category_id;
            zhangdan_ca_type_info = web.ctx.orm.query(Category.title,func.sum(Consumption.amount).label('total')).filter(Consumption.category_id == Category.id ).group_by(Consumption.category_id)
            ca_type = []
            ca_cost = []
            for ca in zhangdan_ca_type_info:
                ca_type.append(ca.title)
                ca_cost.append(ca.total)
            
            # print ca_type
            # print ca_cost

            # 获取受益人
            # select sum(c.amount), p.consumer from consumption c, people p  where c.consumer_id = p.id GROUP BY p.id;
            zhangdan_peo_info = web.ctx.orm.query(People.consumer,func.sum(Consumption.amount).label('total')).filter(Consumption.consumer_id == People.id ).group_by(People.id)
            pe_type = []
            pe_cost = []

            for po in zhangdan_peo_info:
                pe_cost.append(po.total)
                pe_type.append(po.consumer)

        
            # 获取支付类型数据
            #SELECT sum(c.amount),p.name from consumption as c, payment as p where  p.id = c.payment_id GROUP BY c.payment_id;
            pay_type = []
            pay_cost = []
            zhangdan_pay_info = web.ctx.orm.query(Payment.name,func.sum(Consumption.amount).label('total')).filter(Consumption.payment_id == Payment.id ).group_by(Payment.id)

            for pp in zhangdan_pay_info:
                pay_type.append(pp.name)
                pay_cost.append(pp.total)


            return global_render.fenlei(
                ca_type = json.dumps(ca_type),
                ca_cost = json.dumps(ca_cost),
                pe_type = json.dumps(pe_type),
                pe_cost = json.dumps(pe_cost),
                pay_type = json.dumps(pay_type),
                pay_cost = json.dumps(pay_cost)
            )
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')


class ZhangDanList():
    def GET(self):
        try:
            session.logged_in == True
            consumption_list = web.ctx.orm.query(Consumption).order_by(Consumption.ts.desc()).all()
            allinfo = []
            for x in consumption_list:
                tmp = Temp()
                tmp.amount = x.amount
                category_id = x.category_id
                tmp.title = web.ctx.orm.query(Category).get(category_id).title
                consumer_id = x.consumer_id
                tmp.consumer = web.ctx.orm.query(People).get(consumer_id).consumer
                payment_id = x.payment_id
                tmp.payment = web.ctx.orm.query(Payment).get(payment_id).name
                tmp.posttime = x.posttime
                tmp.comments = x.comments
                allinfo.append(tmp)
            return global_render.zhangdanlist(consumption_list=allinfo)
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')


    def POST(self):
        try:
            session.logged_in == True
            queryinfo = web.input()
            nianfen = queryinfo.get('nianfen')
            yuefen = queryinfo.get("yuefen")
            if yuefen == '0':
                # select *  from consumption where strftime('%Y', posttime) == '2021' ORDER BY posttime desc;
                consumption_list = web.ctx.orm.query(Consumption).filter(func.strftime('%Y', Consumption.posttime) == nianfen).order_by(Consumption.ts.desc()).all()

            else:
                # select *  from consumption where strftime('%Y', posttime) == '2021' and strftime('%m', posttime) == '01' ORDER BY posttime desc;
                consumption_list = web.ctx.orm.query(Consumption).filter(func.strftime('%Y', Consumption.posttime) == nianfen).filter(func.strftime('%m', Consumption.posttime) == yuefen).order_by(Consumption.ts.desc()).all()            


            allinfo = []
            for x in consumption_list:
                tmp = Temp()
                tmp.amount = x.amount
                category_id = x.category_id
                tmp.title = web.ctx.orm.query(Category).get(category_id).title
                consumer_id = x.consumer_id
                tmp.consumer = web.ctx.orm.query(People).get(consumer_id).consumer
                payment_id = x.payment_id
                tmp.payment = web.ctx.orm.query(Payment).get(payment_id).name
                tmp.posttime = x.posttime
                tmp.comments = x.comments
                allinfo.append(tmp)
            return global_render.zhangdanlist(consumption_list=allinfo)

        # return global_render.login()
        except Exception:
            raise web.seeother('/login')


class Other:
    def GET(self):
        try:
            session.logged_in == True
            tmp = Temp()
            userinfo = []
            userlist = web.ctx.orm.query(Admins).order_by(Admins.ts).all()
            # time_format = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(timeStamp))

            for x in userlist:
                tmp = Temp()
                tmp.uid = x.uid
                tmp.username = x.username
                tmp.nickname = x.nickname
                tmp.ts = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(x.ts)))
                userinfo.append(tmp)
            return global_render.other(userlist = userinfo)

        except Exception:
            raise web.seeother('/login')


class Addzhangdan:
    def GET(self):
        try:
            session.logged_in == True
            category_list = web.ctx.orm.query(Category).all()
            people_list = web.ctx.orm.query(People).all()
            payment_list = web.ctx.orm.query(Payment).all()
            return global_render.addzhangdan(category_list=category_list,people_list=people_list,payment_list=payment_list)
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')

    def POST(self):
        try:
            session.logged_in == True
            zhangdanxinxi = web.input()
            xiaofeileixing_id = zhangdanxinxi.get("xiaofeileixing")
            beizhu = zhangdanxinxi.get("beizhu")
            shijian = zhangdanxinxi.get("shijian")
            p_time = timetranfer(shijian)
            jine = zhangdanxinxi.get("jine")
            shouyiren_id = zhangdanxinxi.get("shouyiren")
            zhifu_id = zhangdanxinxi.get('zhifu')
            
            consumption =  Consumption()
            consumption.amount = jine
            consumption.category_id = int(xiaofeileixing_id)
            consumption.consumer_id = int(shouyiren_id)
            consumption.payment_id = int(zhifu_id)
            consumption.posttime = p_time
            consumption.comments = beizhu
            consumption.ts = int(time.time())
            web.ctx.orm.add(consumption)
            web.ctx.orm.commit()
            return web.seeother('/zdlist')
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')


class Addshouyirenyuan:
    def GET(self):
        try:
            session.logged_in == True
            people_list = web.ctx.orm.query(People).order_by(People.ts.desc()).all()
            return global_render.addshouyirenyuan(people_list=people_list)
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')

    def POST(self):
        try:
            session.logged_in == True
            submitinfo = web.input()
            shouyiren = submitinfo.get("shouyiren")
            hasvalue = web.ctx.orm.query(People).filter_by(consumer=shouyiren).all()
            if len(hasvalue) == 0:
                people =  People()
                people.consumer = shouyiren
                people.posttime = datetime.datetime.now()
                people.ts = int(time.time())
                web.ctx.orm.add(people)
                web.ctx.orm.commit()
            print u"添加 shouyiren: %s  成功" % shouyiren
            return web.seeother('/addsyry')
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')


class Addfenlei():
    def GET(self):
        try:
            session.logged_in == True
            category_list = web.ctx.orm.query(Category).order_by(Category.ts.desc()).all()
            return global_render.addfenlei(category_list= category_list)
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')

    def POST(self):
        try:
            session.logged_in == True
            submitinfo = web.input()
            xiaofeileixing = submitinfo.get("xiaofeileixing")
            hasvalue = web.ctx.orm.query(Category).filter_by(title=xiaofeileixing).all()
            if len(hasvalue) == 0:
                category =  Category()
                category.title = xiaofeileixing
                category.posttime = datetime.datetime.now()
                category.ts = int(time.time())
                web.ctx.orm.add(category)
                web.ctx.orm.commit()
            print u"添加 xiaofeileixing: %s  成功" % xiaofeileixing
            return web.seeother('/addfl')
        # return global_render.login()
        except Exception:
            raise web.seeother('/login')


class Addpayment():
    def GET(self):
        try:
            session.logged_in == True
            payment_list = web.ctx.orm.query(Payment).order_by(Payment.ts.desc()).all()
            return global_render.addpayment(payment_list=payment_list)

        # return global_render.login() 
        except Exception:
            raise web.seeother('/login')

    def POST(self):
        try:
            session.logged_in == True
            paymentinfo = web.input()
            zhifufangshi = paymentinfo.get("zhifufangshi")
            hasvalue = web.ctx.orm.query(Payment).filter_by(name=zhifufangshi).all()
            if len(hasvalue) == 0:
                payment = Payment()
                payment.name = zhifufangshi
                payment.posttime = datetime.datetime.now()
                payment.ts = int(time.time())
                web.ctx.orm.add(payment)
                web.ctx.orm.commit()
            print u"添加 zhifufangshi: %s  成功" % zhifufangshi
            return web.seeother('/addpayment')

        # return global_render.login()
        except Exception:
            raise web.seeother('/login')

# /adduser
class AddUser:
    def POST(self):
        try:
            session.logged_in == True
            userinfo = web.input()
            admin =  Admins()
            admin.username = userinfo.get("username")
            admin.nickname = userinfo.get("nickname")
            admin.ts = int(time.time())
            password = userinfo.get("password").strip()
            confirm = userinfo.get("confirm").strip()
            if password == confirm:
                admin.userpass = str(md5.new(password).hexdigest())
                web.ctx.orm.add(admin)
                web.ctx.orm.commit()
                return web.seeother('/index')
        except Exception:
            raise web.seeother('/other')

#/deluser
class DelUser:
    def POST(self):
        try:
            session.logged_in == True
            data = web.data()
            userinfo = data.split("&")
            for user in userinfo:
                userid = int(user.split("=")[-1])
                web.ctx.orm.query(Admins).filter(Admins.uid==userid).delete()
            web.ctx.orm.commit()
            return web.seeother('/index')
        except Exception:
            raise web.seeother('/other')
    
# /modifypwd
class ModifyPwd:
    def POST(self):
        try:
            session.logged_in == True
            info = web.input()
            userid = int(info.get("mdyusername"))
            newuserpass = str(info.get("mdypassword"))
            curpasswd = str(info.get("mdypasswordold"))
            userinfo = web.ctx.orm.query(Admins).get(userid)
            pwdcheck = md5.new(curpasswd).hexdigest()

            if userinfo.userpass == pwdcheck:
                if newuserpass == str(info.get("mdyconfirm")) and len(newuserpass) >= length_pwd:
                    newpwd = md5.new(newuserpass).hexdigest()
                    web.ctx.orm.query(Admins).filter(Admins.uid==userid).update({Admins.userpass: newpwd})
                    return web.seeother('/index')
            raise web.seeother('/other')
        except Exception:
            raise web.seeother('/other')

def checktimes(ip):
    global flag
    flag = False
    if os.path.exists(denyipfile):
        with open(denyipfile,'r') as f:
            for xip in f:
                if xip.strip() == ip:
                    flag = True
                    break
    return flag

class PageDeny:
    def GET(self):
        return global_render.pagedeny()            



class Login(): 
    def GET(self):
        return global_render.login()
    
    def POST(self):
        # env = web.ctx.env
        # print env
        # print web.ctx.ip
        # print env.get("REMOTE_ADDR")
        if checktimes(web.ctx.ip):
            raise web.seeother('/denyany')
        logininfo = web.input()
        username = str(logininfo.get('username')).strip()
        password = str(logininfo.get('password')).strip()
        
        user = web.ctx.orm.query(Admins).filter_by(username=username).all()[0]
        if md5.new(password).hexdigest() == user.userpass:
            session.logged_in = True
            session.username = username
            return web.seeother('/index')
        else:
            return global_render.login(username=username,password=password)


class Logout():
    def GET(self):
        session.logged_in = False
        session.kill()
        # return global_render.login()
        raise web.seeother('/login')


def notfound():
    return  web.notfound(global_render.page404())


def internalerror():
    return web.internalerror(global_render.page500())


if __name__ == "__main__":
    app.notfound = notfound
    app.internalerror = internalerror
    app.run()
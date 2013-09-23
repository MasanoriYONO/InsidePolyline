#!/usr/bin/env python
# -*- coding: utf-8 -*-
#タブはパースエラーになるので不可。
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from django.utils import simplejson
import math
import os
import logging
import datetime

# pointクラス
class point:
  def __init__(self, lat, lng):
    self.lat = lat
    self.lng = lng

class PolyLine(db.Model):
    area = db.TextProperty()
    dest_point = db.StringProperty()
    remote_host = db.StringProperty()
    user_agent = db.StringProperty()
    updated_at = db.DateTimeProperty(auto_now_add=True)
    
def getRadian(vec0, vec1):
    dot = vec0.lat * vec1.lat + vec0.lng * vec1.lng
    d0 = math.sqrt( vec0.lat * vec0.lat + vec0.lng * vec0.lng )
    d1 = math.sqrt( vec1.lat * vec1.lat + vec1.lng * vec1.lng )
    cosine = dot / ( d0 * d1 )
    angle = math.acos( cosine )
    return angle
    
def getDirection(vec0, vec1):
    cross = vec0.lat * vec1.lng - vec1.lat * vec0.lng
    d0 = math.sqrt( vec0.lat * vec0.lat + vec0.lng * vec0.lng )
    d1 = math.sqrt( vec1.lat * vec1.lat + vec1.lng * vec1.lng )
    sine = cross / ( d0 * d1 )
    angle = math.asin( sine )
    if angle > 0:
        return 1
    else:
        return  -1

class MainHandler(webapp.RequestHandler):
    def get(self):
#こんなリクエストになる。
#http://localhost:8083/?args0=20&args1=%5B%7B%22lat%22%3A34.976489039860944%2C%22lng%22%3A138.38268417392737%7D%2C%7B%22lat%22%3A34.976137396208955%2C%22lng%22%3A138.38372487102515%7D%2C%7B%22lat%22%3A34.977108808121976%2C%22lng%22%3A138.38419157539374%7D%2C%7B%22lat%22%3A34.97702529352335%2C%22lng%22%3A138.38525909458167%7D%2C%7B%22lat%22%3A34.97975925351023%2C%22lng%22%3A138.38561314617164%7D%2C%7B%22lat%22%3A34.97957464815308%2C%22lng%22%3A138.38757652317054%7D%2C%7B%22lat%22%3A34.980620739674244%2C%22lng%22%3A138.38824171100623%7D%2C%7B%22lat%22%3A34.981561331564606%2C%22lng%22%3A138.3875872520066%7D%2C%7B%22lat%22%3A34.98222940896157%2C%22lng%22%3A138.3862032321549%7D%2C%7B%22lat%22%3A34.9825458647734%2C%22lng%22%3A138.3848299411393%7D%2C%7B%22lat%22%3A34.981192128559336%2C%22lng%22%3A138.38404673610694%7D%2C%7B%22lat%22%3A34.981455845161534%2C%22lng%22%3A138.38134306941993%7D%2C%7B%22lat%22%3A34.977904390291506%2C%22lng%22%3A138.38037747417457%7D%2C%7B%22lat%22%3A34.97746484308702%2C%22lng%22%3A138.38210481678016%7D%2C%7B%22lat%22%3A34.976805517856846%2C%22lng%22%3A138.38190096889502%7D%2C%7B%22lat%22%3A34.97663848795587%2C%22lng%22%3A138.38226574932105%7D%2C%7B%22lat%22%3A34.977385724339655%2C%22lng%22%3A138.38273781810767%7D%2C%7B%22lat%22%3A34.97720990462743%2C%22lng%22%3A138.38359612499244%7D%2C%7B%22lat%22%3A34.97655057734483%2C%22lng%22%3A138.38327425991065%7D%2C%7B%22lat%22%3A34.976612114782455%2C%22lng%22%3A138.3827807334519%7D%5D&args2=%7B%22lat%22%3A34.97551781745033%2C%22lng%22%3A138.3867389272308%7D&callback=dojo.io.script.jsonp_dojoIoScript6._jsonpCallback
        args0 = self.request.get("args0")
        if args0 == '':
            return
        v_count = int(args0)
        
        args1 = self.request.get("args1")
        args2 = self.request.get("args2")
        callback = self.request.get("callback")
        
        query1 = simplejson.loads(args1)
        query2 = simplejson.loads(args2)
        
        #dest_point = GeoPt(query2['lat'],query2['lng'])
        
        post_db = PolyLine()
        post_db.area = args1
        post_db.dest_point = args2
        post_db.remote_host = os.environ['REMOTE_ADDR']
        post_db.user_agent = os.environ['HTTP_USER_AGENT']
        post_db.put()
        
        vec = []
        for p in query1:
            #self.response.out.write("p in query1 : %s %s <br />" %(p['lat'],p['lng']))
            vec.append(point(p['lat'] - query2['lat'],p['lng'] - query2['lng']))

        #for p in vec:
            #self.response.out.write("p in vec : %s %s<br />" %(p.lat,p.lng))


        #self.response.out.write("query2 %s : %s %s<br />" %(len(query2),query2['lat'],query2['lng']))
        
        angle = 0
        for i in range(0, v_count):
            rad = 0
            sign = 0
            c = i
            #/終点の次は配列添字のiでは取れない。最後の処理は始点を使うため。2011/08/26 07:29
            n = i + 1
            n %= v_count
            # 2つのベクトルの角度を計算
            rad = getRadian( vec[c], vec[n] )
            # vec[ c ]から見てvec[ n ]が時計回り方向にいるのか反時計回り方向にいるのかチェック
            # 反時計回りが正方向。反時計周りだったらラジアンをプラス、時計回り方向だったらラジアンをマイナス
            # 内部の点なら総和が2πになるはず。ただし小数点の計算なので誤差が出る。
            sign = getDirection( vec[c], vec[n] )
            angle += sign * rad
            
        if math.fabs(angle) + 0.001 >= math.pi * 2:
            judge = True
        else:
            judge = False

        #
        value = simplejson.dumps({'judge':judge, 'radian':math.fabs(angle)})
        self.response.content_type = "text/javascript"
        #self.response.out.write("%s('{result:%s}');" %(callback, value))
        self.response.out.write("%s({result:%s});" %(callback, value))
        
        return

def main():
    application = webapp.WSGIApplication([('/', MainHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

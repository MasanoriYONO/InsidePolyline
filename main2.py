#!/usr/bin/env python
# -*- coding: utf-8 -*-
#タブはパースエラーになるので不可。
import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import login_required
#add 2011/10/08 17:56
from google.appengine.dist import use_library
use_library('django', '1.2')
#add end
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import mail
from django.utils import simplejson
import math
import logging
import datetime
import cgi
import random
import sgmllib

# pointクラス
class point:
  def __init__(self, lat, lng):
    self.lat = lat
    self.lng = lng

class PolyLine(db.Model):
    area = db.TextProperty()
    author = db.UserProperty()
    map_name = db.StringProperty()
    map_name_4view = db.StringProperty(default='')
    comment = db.StringProperty(multiline=True)
    category = db.StringProperty(default='')
    information = db.TextProperty(default='')
    remote_host = db.StringProperty()
    user_agent = db.StringProperty()
    updated_at = db.DateTimeProperty(auto_now_add=True)
    
    def remove(self, request, users):
        id = request.get("id")
        user = users.get_current_user()
        
        #logging.debug(request.get('delete')) 
        #if request.get('delete') == u'削除する':
        #if request.get('delete') != '':
        if str(self.key().id()) == id:
            #if users.is_current_user_admin() or self.user == user:
            if self.author == user:
                self.delete()
        #else:
        #    if users.is_current_user_admin():
        #        self.delete()
        
class MapRandom(db.Model):
    name = db.StringProperty()
    map_name_4view = db.StringProperty()
    center_lat_lng = db.StringProperty()
    zoom = db.IntegerProperty()
    author = db.UserProperty()
    remote_host = db.StringProperty()
    user_agent = db.StringProperty()
    updated_at = db.DateTimeProperty(auto_now_add=True)
    
    def remove(self, request, users):
        id = request.get("id")
        user = users.get_current_user()
        
        if str(self.key().id()) == id:
            if self.author == user:
                self.delete()

class PaidMembers(db.Model):
    account = db.StringProperty()
    valid = db.BooleanProperty()
    author = db.UserProperty()
    updated_at = db.DateTimeProperty(auto_now_add=True)
    
    def remove(self, request, users):
        id = request.get("id")
        user = users.get_current_user()
        
        if str(self.key().id()) == id:
            if users.is_current_user_admin():
                self.delete()

class MailHistory(db.Model):
    map_name = db.StringProperty()
    comment = db.StringProperty(multiline=True)
    category = db.StringProperty()
    information = db.TextProperty()
    user_location = db.StringProperty()
    inside_polygon = db.BooleanProperty()
    author = db.UserProperty()
    remote_host = db.StringProperty()
    user_agent = db.StringProperty()
    updated_at = db.DateTimeProperty(auto_now_add=True)
    
    def remove(self, request, users):
        id = request.get("id")
        user = users.get_current_user()
        
        if str(self.key().id()) == id:
            if users.is_current_user_admin():
                self.delete()
                
def getMapRandom():
    str = "0123456789bcdefghjkmnpqrstuvwxyz"
    strlist = list(str)
    x = random.randint(0,len(strlist)-1)
    res = ""
    for i in range(16):
         x = random.randint(0,len(strlist)-1)
         res += strlist[x]
    return res

#ユーザー地図の名前をセット
def setMapName(user):
    if not user:
        return
    #paid_member?
    post_db_query = PaidMembers.all()
    post_db_query.filter('account =', user.email()).filter('valid',True)
    res_ct = post_db_query.count(1)
    #paid member
    if res_ct == 1:
        return
    
    #free member
    else:
        #すでにマップが存在するかどうか。
        post_db_query = MapRandom.all()
        post_db_query.filter('author =', user)
        res_ct = post_db_query.count(1)
        #存在すれば戻る。
        if res_ct == 1:
            return
        #なければお試しマップを1つ作る。
        i = 0
        while True:
            name = getMapRandom()
            post_db_query = MapRandom.all()
            post_db_query.filter('name =', name)
            res_ct = post_db_query.count(1)
            if res_ct == 1:
                continue
            map_random = MapRandom()
            map_random.name = getMapRandom()
            #map_random.map_name_4view = u"サンプル" + str(i)
            map_random.map_name_4view = u"お試しマップ"
            map_random.author = user
            map_random.remote_host = os.environ['REMOTE_ADDR']
            map_random.user_agent = os.environ['HTTP_USER_AGENT']
            map_random.put()
            i = i + 1
            if i > 0:
                break

#ユーザー地図の名前一覧を取得
def getMapName(user):
    #paid_member?
    post_db_query = PaidMembers.all()
    post_db_query.filter('account =', user.email()).filter('valid',True)
    res_ct = post_db_query.count(1)
    #paid member
    if res_ct == 1:
        post_db_query = MapRandom.all()
        post_db_query.filter('author =', user)
        post_db_query.order('-updated_at')
        res_ct = post_db_query.count(100)
        if res_ct > 0:
            map_random = post_db_query.fetch(100)
            return map_random
        else:
            return
    else:
        post_db_query = MapRandom.all()
        post_db_query.filter('author =', user).filter
        res_ct = post_db_query.count(1)
        if res_ct > 0:
            map_random = post_db_query.fetch(1)
            return map_random
        else:
            return

#地図情報を取得。
def getMapInfo(map_name):
    post_db_query = MapRandom.all()
    post_db_query.filter('name =', map_name)
    res_ct = post_db_query.count(1)
    if res_ct > 0:
        map_random = post_db_query.fetch(1)
        return map_random
    else:
        return

#地図情報からユーザー情報を取得して有料ユーザーかどうかを判定。有料なら表示数制限は上限100エリアまで。
def getUserInfo(map_name):
    
    #マップ名からユーザーを引きあてる。
    post_db_query = MapRandom.all()
    post_db_query.filter('name =', map_name)
    res_ct = post_db_query.count(1)
    if res_ct == 1:
        map_random = post_db_query.fetch(1)
        for p in map_random:
            user = p.author
           
        #paid_member?
        post_db_query = PaidMembers.all()
        post_db_query.filter('account =', user.email()).filter('valid',True)
        res_ct = post_db_query.count(1)
        #paid member
        if res_ct == 1:
            return True
    
    return False

#有料ユーザーかどうかで表示するエリア情報を制限する。
def getAreas(paid_user,map_name):
    post_db_query = PolyLine.all()
    post_db_query.filter('map_name =', map_name)
    post_db_query.order('-updated_at')
    if paid_user:
        res_ct = post_db_query.count(1000)
        if res_ct > 0:
            areas = post_db_query.fetch(1000)
            map_names = getMapInfo(areas[0].map_name)
            template_values = {
                'areas': areas,
                'map_names':map_names,
                'selected_map':map_name,
                'host_path':os.environ['HTTP_HOST']
            }
        else:
            template_values = {
            }
    else:
        res_ct = post_db_query.count(5)
        if res_ct > 0:
            areas = post_db_query.fetch(5)
            map_names = getMapInfo(areas[0].map_name)
            template_values = {
                'areas': areas,
                'map_names':map_names,
                'selected_map':map_name,
                'host_path':os.environ['HTTP_HOST']
            }
        else:
            template_values = {
            }
    
    return template_values

def is_dev():
    return os.environ.get('SERVER_SOFTWARE', '').startswith('Development')

def UTC2JST(str):
    str = str + datetime.timedelta(hours=9)
    return str

class Stripper(sgmllib.SGMLParser):
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)

    def strip(self, some_html):
        self.theString = ""
        self.feed(some_html)
        self.close()
        return self.theString

    def handle_data(self, data):
        self.theString += data
        
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
###こんなリクエストになる。
###http:##localhost:8083/?args0=20&args1=%5B%7B%22lat%22%3A34.976489039860944%2C%22lng%22%3A138.38268417392737%7D%2C%7B%22lat%22%3A34.976137396208955%2C%22lng%22%3A138.38372487102515%7D%2C%7B%22lat%22%3A34.977108808121976%2C%22lng%22%3A138.38419157539374%7D%2C%7B%22lat%22%3A34.97702529352335%2C%22lng%22%3A138.38525909458167%7D%2C%7B%22lat%22%3A34.97975925351023%2C%22lng%22%3A138.38561314617164%7D%2C%7B%22lat%22%3A34.97957464815308%2C%22lng%22%3A138.38757652317054%7D%2C%7B%22lat%22%3A34.980620739674244%2C%22lng%22%3A138.38824171100623%7D%2C%7B%22lat%22%3A34.981561331564606%2C%22lng%22%3A138.3875872520066%7D%2C%7B%22lat%22%3A34.98222940896157%2C%22lng%22%3A138.3862032321549%7D%2C%7B%22lat%22%3A34.9825458647734%2C%22lng%22%3A138.3848299411393%7D%2C%7B%22lat%22%3A34.981192128559336%2C%22lng%22%3A138.38404673610694%7D%2C%7B%22lat%22%3A34.981455845161534%2C%22lng%22%3A138.38134306941993%7D%2C%7B%22lat%22%3A34.977904390291506%2C%22lng%22%3A138.38037747417457%7D%2C%7B%22lat%22%3A34.97746484308702%2C%22lng%22%3A138.38210481678016%7D%2C%7B%22lat%22%3A34.976805517856846%2C%22lng%22%3A138.38190096889502%7D%2C%7B%22lat%22%3A34.97663848795587%2C%22lng%22%3A138.38226574932105%7D%2C%7B%22lat%22%3A34.977385724339655%2C%22lng%22%3A138.38273781810767%7D%2C%7B%22lat%22%3A34.97720990462743%2C%22lng%22%3A138.38359612499244%7D%2C%7B%22lat%22%3A34.97655057734483%2C%22lng%22%3A138.38327425991065%7D%2C%7B%22lat%22%3A34.976612114782455%2C%22lng%22%3A138.3827807334519%7D%5D&args2=%7B%22lat%22%3A34.97551781745033%2C%22lng%22%3A138.3867389272308%7D&callback=dojo.io.script.jsonp_dojoIoScript6._jsonpCallback
##        args0 = self.request.get("args0")
##        if args0 == '':
##            return
##        v_count = int(args0)
##        
##        args1 = self.request.get("args1")
##        args2 = self.request.get("args2")
##        callback = self.request.get("callback")
##        
##        query1 = simplejson.loads(args1)
##        query2 = simplejson.loads(args2)
##        
##        #dest_point = GeoPt(query2['lat'],query2['lng'])
##        
##        post_db = PolyLine()
##        post_db.area = args1
##        post_db.dest_point = args2
##        post_db.remote_host = os.environ['REMOTE_ADDR']
##        post_db.user_agent = os.environ['HTTP_USER_AGENT']
##        post_db.put()
##        
##        vec = []
##        for p in query1:
##            #self.response.out.write("p in query1 : %s %s <br />" %(p['lat'],p['lng']))
##            vec.append(point(p['lat'] - query2['lat'],p['lng'] - query2['lng']))
##
##        #for p in vec:
##            #self.response.out.write("p in vec : %s %s<br />" %(p.lat,p.lng))
##
##
##        #self.response.out.write("query2 %s : %s %s<br />" %(len(query2),query2['lat'],query2['lng']))
##        
##        angle = 0
##        for i in range(0, v_count):
##            rad = 0
##            sign = 0
##            c = i
##            #/終点の次は配列添字のiでは取れない。最後の処理は始点を使うため。2011/08/26 07:29
##            n = i + 1
##            n %= v_count
##            # 2つのベクトルの角度を計算
##            rad = getRadian( vec[c], vec[n] )
##            # vec[ c ]から見てvec[ n ]が時計回り方向にいるのか反時計回り方向にいるのかチェック
##            # 反時計回りが正方向。反時計周りだったらラジアンをプラス、時計回り方向だったらラジアンをマイナス
##            # 内部の点なら総和が2πになるはず。ただし小数点の計算なので誤差が出る。
##            sign = getDirection( vec[c], vec[n] )
##            angle += sign * rad
##            
##        if math.fabs(angle) + 0.001 >= math.pi * 2:
##            judge = True
##        else:
##            judge = False
##
##        #
##        value = simplejson.dumps({'judge':judge, 'radian':math.fabs(angle)})
##        self.response.content_type = "text/javascript"
##        #self.response.out.write("%s('{result:%s}');" %(callback, value))
##        self.response.out.write("%s({result:%s});" %(callback, value))
        
        

        #user = users.get_current_user()
        #if not user:
        #    self.redirect(users.create_login_url(self.request.uri))
        
        map_names_query = MapRandom.all()
        map_names_query.order('-updated_at')
        map_names = map_names_query.fetch(20)
        
        post_db_query = PolyLine.all()
        #post_db_query.filter('author =', user)
        post_db_query.order('comment')
        res_ct = post_db_query.count(1000)
        #マップごとの登録エリア数を表示したい。
        each_maps = dict()
        for q in post_db_query:
        #distinctに変わるものがないので辞書を作成した。2011/09/23 14:30
            if each_maps.has_key(q.map_name):
                each_maps[q.map_name] = each_maps[q.map_name] + 1
            else:
                each_maps[q.map_name] = 1

        if res_ct > 0:
            areas = post_db_query.fetch(1000)
            template_values = {
                'areas': areas,
                'map_names':map_names,
                'each_maps': each_maps,
                'host_path':os.environ['HTTP_HOST']
            }
        else:
            template_values = {}
            
        path = os.path.join(os.path.dirname(__file__), 'polyline.html')
        self.response.out.write(template.render(path, template_values))
        
class EditAreaView(webapp.RequestHandler):
    def get(self):
        
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        map_names = getMapName(user)
        id = self.request.get('id')
        map_name = self.request.get('map_name')
        
        
        #areas = PolyLine(author = user)
        areas = PolyLine.get_by_id(long(id))
        
        template_values = {
            'area_points': areas,
            'map_names':map_names,
            'selected_map':map_name
        }
        path = os.path.join(os.path.dirname(__file__), 'polyline_edit.html')
        self.response.out.write(template.render(path, template_values))

class UpdateArea(webapp.RequestHandler):
    def post(self):
        
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        #ユーザー用の地図名の一括変更
        map_name = self.request.get('map_name')
        post_db = db.GqlQuery("SELECT * FROM MapRandom WHERE name = :1 AND author = :2",map_name,user)
        for post_db_query in post_db:
            map_name_4view = post_db_query.map_name_4view
            
        id = self.request.get('id')
        post_db = PolyLine(author = user)
        post_db = PolyLine.get_by_id(long(id))
        
        post_db.area = self.request.get('vertex')
        post_db.remote_host = os.environ['REMOTE_ADDR']
        post_db.user_agent = os.environ['HTTP_USER_AGENT']
        t_comment = self.request.get('comment')
        #t_comment = t_comment.replace('\r\n','<br />')
        post_db.comment = t_comment
        #2011/09/19 16:49 add
        t_information = self.request.get('information')
        post_db.information = t_information
        t_category = self.request.get('category')
        post_db.category = t_category
        
        post_db.map_name = map_name
        post_db.map_name_4view = map_name_4view
        
        db.put(post_db)
        
        self.redirect('/addview')
        
class AddAreaView(webapp.RequestHandler):
    @login_required
    def get(self):
        
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        user_address = users.get_current_user().email()
        setMapName(user)
        map_names = getMapName(user)
        post_db_query = PolyLine.all()
        post_db_query.filter('author =', user)
        
        map_name = self.request.get('map_name')
        if map_name != "":
            post_db_query.filter('map_name =', map_name)
        
        post_db_query.order('-updated_at')
        res_ct = post_db_query.count(1000)
        if res_ct > 0:
            areas = post_db_query.fetch(1000)
            template_values = {
                'areas': areas,
                'map_names':map_names,
                'selected_map':map_name,
                'host_path':os.environ['HTTP_HOST']
            }
        else:
            template_values = {
                'map_names':map_names,
                'host_path':os.environ['HTTP_HOST']
            }

        path = os.path.join(os.path.dirname(__file__), 'polyline_add.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        setMapName(user)
        map_names = getMapName(user)
        
        post_db_query = PolyLine.all()
        post_db_query.filter('author =', user)
        map_name = self.request.get('map_name')
        if map_name != "":
            post_db_query.filter('map_name =', map_name)
        
        post_db_query.order('-updated_at')
        res_ct = post_db_query.count(1000)
                
        if res_ct > 0:
            areas = post_db_query.fetch(1000)
            template_values = {
                'areas': areas,
                'map_names':map_names,
                'selected_map':map_name,
                'host_path':os.environ['HTTP_HOST']
            }
        else:
            template_values = {
                'map_names':map_names,
                'selected_map':map_name,
                'host_path':os.environ['HTTP_HOST']
            }

        path = os.path.join(os.path.dirname(__file__), 'polyline_add.html')
        self.response.out.write(template.render(path, template_values))

class UserMapView(webapp.RequestHandler):
    def get(self):
        map_name = self.request.get('map_name')
        paid_user = getUserInfo(map_name)
        template_values = getAreas(paid_user,map_name)
        if template_values:
            path = os.path.join(os.path.dirname(__file__), 'polyline_view.html')
            self.response.out.write(template.render(path, template_values))
        else:
            self.redirect('/')
class UserMapView4GPS(webapp.RequestHandler):
    def get(self):
        map_name = self.request.get('map_name')
        paid_user = getUserInfo(map_name)
        template_values = getAreas(paid_user,map_name)
        if template_values:
            path = os.path.join(os.path.dirname(__file__), 'polyline_view4gps.html')
            self.response.out.write(template.render(path, template_values))
        else:
            self.redirect('/')
class UserMapView4GPS1Time(webapp.RequestHandler):
    def get(self):
        map_name = self.request.get('map_name')
        paid_user = getUserInfo(map_name)
        template_values = getAreas(paid_user,map_name)
        if template_values:
            path = os.path.join(os.path.dirname(__file__), 'polyline_view4gps1time.html')
            self.response.out.write(template.render(path, template_values))
        else:
            self.redirect('/')
        
class SendInfo(webapp.RequestHandler):
    @login_required
    def get(self):
        user = users.get_current_user()
        #@login_requiredを使う場合はGET変数で受け取る必要があるみたい。
        #この書き方だとCookieの有効期限の影響か判定をTrueで抜けてしまい、ログイン画面に移動せず。
        #if not user:
        #    self.redirect(users.create_login_url(self.request.uri))
        
        #user_address = str(user) + "@gmail.com"
        #self.response.out.write("%s" %(user_address))
        message = mail.EmailMessage(subject = u"テストメール")
        #message.sender = str(user) + "@gmail.com"
        #message.to = str(user) + "@gmail.com"
        message.sender = users.get_current_user().email()
        message.to = users.get_current_user().email()
        
        key = self.request.get("key")
        map_name = self.request.get("map_name")
        lat = self.request.get("lat")
        lng = self.request.get("lng")
        
        #データストアから取得。
        post_db = PolyLine.get_by_id(long(key))
        #この書き方でいいみたい。
        comment = post_db.comment
        category = post_db.category
        information = post_db.information
        #内外の判定を行う。
        area = post_db.area
        t_list = area.replace('lat','"lat"')
        area = t_list.replace('lng','"lng"')
        t_area =  simplejson.loads( area )
        
        vec = []
        for p in t_area:
            vec.append(point(p['lat'] - float(lat),p['lng'] - float(lng)))
            
        angle = 0
        v_count = len(vec)
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
            inside_polygon_mes = u"エリア内にいます。"
        else:
            judge = False
            inside_polygon_mes = u"エリア外です。"

        
        message.body = u"""
あなたがクリックした情報ウィンドウの内容は以下の通りです。
--
コメント：%s
メール配信情報：%s
カテゴリ：%s
現在位置：%s,%s
エリア内／外：%s
--
%s
""" % (comment,information,category,lat,lng,inside_polygon_mes,os.environ['HTTP_USER_AGENT'])
        
        message.send()
        #メール送信履歴に書く。
        post_db = MailHistory()
        post_db.author = users.get_current_user()
        post_db.remote_host = os.environ['REMOTE_ADDR']
        post_db.user_agent = os.environ['HTTP_USER_AGENT']
        post_db.comment = comment
        post_db.information = information
        post_db.user_location = lat + "," +lng
        post_db.inside_polygon = judge
        post_db.category = category
        post_db.map_name = map_name
        post_db.put()
        
        referer = self.request.get("referer")
        if referer == "1":
            self.redirect('/user_map?map_name=' + map_name)
        elif referer == "2":
            self.redirect('/user_map4gps?map_name=' + map_name)
        elif referer == "3":
            self.redirect('/user_map4gps1time?map_name=' + map_name)
        elif referer == "4":
            self.redirect('/list/closed10gps')
        else:
            self.redirect('/user_map?map_name=' + map_name)
            
class getUserMapAreaJSONP(webapp.RequestHandler):
#http://localhost:8085/json?map_name=mc2w1zjuxngb8g3f&callback=aaa
    @login_required
    def get(self):
        user = users.get_current_user()
        callback = self.request.get("callback")
        if callback =="":
            return
        map_name = self.request.get('map_name')
        if map_name =="":
            return
        post_db_query = PolyLine.all()
        post_db_query.filter('map_name =', map_name).filter('author =', user)
        res_ct = post_db_query.count(1000)

        #self.response.out.write("res_ct:%s<br />" %(res_ct))

        if res_ct > 0:
            areas = post_db_query.fetch(1000)
        else:
            return
        #self.response.out.write("areas:%s<br />" %(len(areas)))
        
        vec = []
        for i in range(0, len(areas)):
            vec.append(areas[i].area)
            
        value = simplejson.dumps({'points':vec})
        self.response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        #self.response.out.write("%s('{result:%s}');" %(callback, value))
        self.response.out.write('%s({"result":%s});' %(callback, value))
        
        return
        
class getUserMapAreaJSON(webapp.RequestHandler):
#http://localhost:8085/json?map_name=mc2w1zjuxngb8g3f&callback=aaa
    @login_required
    def get(self):
        user = users.get_current_user()
        callback = self.request.get("callback")
        map_name = self.request.get('map_name')
        
        post_db_query = PolyLine.all()
        post_db_query.filter('map_name =', map_name).filter('author =', user)
        res_ct = post_db_query.count(1000)

        #self.response.out.write("res_ct:%s<br />" %(res_ct))

        if res_ct > 0:
            areas = post_db_query.fetch(1000)
        else:
            return
        #self.response.out.write("areas:%s<br />" %(len(areas)))
        
        vectors = []
        #for i in range(0, len(areas)):
        #    vec.append(areas[i].area)
        #value = simplejson.dumps({'points':vec})
        
        for i in range(0, len(areas)):
            vec =dict(id=areas[i].key().id(),area=areas[i].area,category=areas[i].category,comment=areas[i].comment,information=areas[i].information,map_name=areas[i].map_name,remote_host=areas[i].remote_host,user_agent=areas[i].user_agent)
            vectors.append(vec)
        value = simplejson.dumps({'PolyLine':vectors}, ensure_ascii=False)
        
        #self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
        self.response.content_type = "text/javascript"
        #self.response.out.write("%s('{result:%s}');" %(callback, value))
        self.response.out.write(value)
        
        #json decode
        self.response.out.write("<hr />")
        query1 = simplejson.loads(value)
        poly = query1.get('PolyLine')
        
        for p in poly:
            self.response.out.write("%s: %s %s %s %s %s %s %s<br />" %(p['id'],p['area'],p['category'],p['comment'],p['information'],p['map_name'],p['remote_host'],p['user_agent']))
            
        return
        
class getUserMapsJSON(webapp.RequestHandler):
#http://localhost:8085/user_map_json?map_name=mc2w1zjuxngb8g3f
    def get(self):
        #map_names_query = MapRandom.all()
        #map_names_query.order('-updated_at')
        key = u'お試しマップ'
        map_names_query = MapRandom.gql("WHERE map_name_4view != :1" ,key)
        res_ct = map_names_query.count(1000)
        
        if res_ct > 0:
            map_names = map_names_query.fetch(100)
        else:
            return

        map_name_vectors = []
        for i in range(0, len(map_names)):
            vec =dict(id=map_names[i].key().id(),name=map_names[i].name,name4view=map_names[i].map_name_4view)
            map_name_vectors.append(vec)

        value = simplejson.dumps({'map_names':map_name_vectors})
        self.response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        #self.response.out.write("%s('{result:%s}');" %(callback, value))
        self.response.out.write('{"user_maps":%s}' %(value))

        return
        
class getUserMapPointsJSON(webapp.RequestHandler):
#http://localhost:8085/user_map_json?map_name=mc2w1zjuxngb8g3f
    def get(self):
        map_name = self.request.get('map_name')
        
        post_db_query = PolyLine.all()
        post_db_query.filter('map_name =', map_name)
        post_db_query.order('-updated_at')
        res_ct = post_db_query.count(1000)
        if res_ct > 0:
            areas = post_db_query.fetch(1000)
        else:
            return

        res_str = '{"areas":['
        for p in areas:
            t_list = p.area
            t_list2 = t_list.replace('lat','"lat"')
            t_list = t_list2.replace('lng','"lng"')
            t_area =  simplejson.loads( t_list )
            
            #self.response.out.write('{"key":"%s",' %(p.key()))
            res_str = res_str + '{"id":"' +str(p.key().id()) + '",'
            res_str = res_str + '"key":"' +str(p.key()) + '",'

            #self.response.out.write("%s:%s<br />" %(type(t_area).__name__,t_area))
            #self.response.out.write('"area":[')
            stripper = Stripper()

            res_str = res_str + '"area":['
            for pp in t_area:
                #self.response.out.write("%s:%s,%s<br />" %(type(pp).__name__,pp['lat'],pp['lng']))
                #self.response.out.write('{"lat":%s,"lng":%s},' %(pp['lat'],pp['lng']))
                res_str = res_str  + '{"lat": ' + str(pp["lat"]) +',"lng":' + str(pp["lng"]) + '},'
                
            res_str = res_str.rstrip(',') + '],'
            #self.response.out.write('%s' %(res_str))
            #self.response.out.write('"author":"%s",' %(p.author))
            #res_str = res_str + '"author":"' + str(p.author) + '",'
            #self.response.out.write('"map_name":"%s",' %(p.map_name))
            res_str = res_str + '"map_name":"' + p.map_name + '",'
            #self.response.out.write('"map_name_4view":"%s",' %(p.map_name_4view))
            res_str = res_str + '"map_name_4view":"' + p.map_name_4view + '",'
            #self.response.out.write('"comment":"%s",' %(p.comment.replace('\r\n','')))
            res_str = res_str + '"comment":"' + stripper.strip(p.comment.replace('\r\n','')) + '",'
            #self.response.out.write('"category":"%s",' %(p.category))
            if p.category:
                res_str = res_str + '"category":"' + p.category + '",'
            #self.response.out.write('"information":"%s",' %(p.information))
            if p.information:
                res_str = res_str + '"information":"' + stripper.strip(p.information.replace('\r\n','')) + '",'
            #self.response.out.write('"remote_host":"%s",' %(p.remote_host))
            #res_str = res_str + '"remote_host":"' + p.remote_host + '",'
            #self.response.out.write('"user_agent":"%s",' %(p.user_agent))
            #res_str = res_str + '"user_agent":"' + p.user_agent + '",'
            #self.response.out.write('"updated_at":"%s"},' %(p.updated_at))
            res_str = res_str + '"updated_at":"' + str(p.updated_at) + '"},'
            
        res_str = res_str.rstrip(',') + ']}'
        
        self.response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        #self.response.out.write("%s('{result:%s}');" %(callback, value))
        self.response.out.write('%s' %(res_str))

        return
        
class EditMapView(webapp.RequestHandler):
    def post(self):
        
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        f_error = False
        map_name = self.request.get('map_name')
        if map_name == "":
            f_error = True
        
        map_name_4view = self.request.get('map_name_4view')
        if map_name_4view == "":
            f_error = True
            
        center_lat_lng = self.request.get('center_lat_lng')
        if center_lat_lng == "":
            f_error = True
            
        zoom = self.request.get('zoom')
        if zoom == "":
            f_error = True
        
        if f_error:
            self.redirect('/addview')
            return
            
        zoom = int(self.request.get('zoom'))
        
        post_db = db.GqlQuery("SELECT * FROM MapRandom WHERE name = :1 AND author = :2",map_name,user)
        #この書き方では更新できなかった。
        #post_db_query = MapRandom.all()
        #post_db = post_db_query.filter('author =', user).filter('name =', map_name)
        #rec_ct = post_db.count(1)
        #self.response.out.write('%s' %(post_db))
        
        for post_db_query in post_db:
            post_db_query.map_name_4view = map_name_4view
            post_db_query.center_lat_lng = center_lat_lng
            post_db_query.zoom = zoom
            #1行ごとの更新みたい。
            db.put(post_db_query)
        #ここでは更新してくれないみたい。
        #db.put(post_db)
        
        query = db.GqlQuery("SELECT * FROM PolyLine WHERE map_name = :1 AND author = :2",map_name,user)
        post_db = query.fetch(1000)
        for post_db_query in post_db:
            post_db_query.map_name_4view = map_name_4view
            #1行ごとの更新みたい。
            db.put(post_db_query)
        
        self.redirect('/addview')
        
class AddArea(webapp.RequestHandler):
    def post(self):
        
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        #ユーザー用の地図名の一括変更
        map_name = self.request.get('map_name')
        post_db = db.GqlQuery("SELECT * FROM MapRandom WHERE name = :1 AND author = :2",map_name,user)
        for post_db_query in post_db:
            map_name_4view = post_db_query.map_name_4view
            
        post_db = PolyLine()
        post_db.area = self.request.get('vertex')
        post_db.author = users.get_current_user()
        post_db.remote_host = os.environ['REMOTE_ADDR']
        post_db.user_agent = os.environ['HTTP_USER_AGENT']
        t_comment = self.request.get('comment')
        #t_comment = t_comment.replace('\r\n','<br />')
        post_db.comment = t_comment
        #2011/09/19 16:49 add
        t_information = self.request.get('information')
        post_db.information = t_information
        t_category = self.request.get('category')
        post_db.category = t_category
        
        post_db.map_name = map_name
        post_db.map_name_4view = map_name_4view
        
        post_db.put()
        
        self.redirect('/addview')

class Delete(webapp.RequestHandler):
    def get(self):
        
        user = users.get_current_user()
        
        post_db_query = PolyLine.all()
        post_db_query.filter('author =', user)
        areas = post_db_query.fetch(1000)
        for result in areas:
            result.remove(self.request, users)

        self.redirect('/addview')

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                         ('/addview', AddAreaView),
                                         ('/edit_view', EditMapView),
                                         ('/jsonp',getUserMapAreaJSONP),
                                         ('/json',getUserMapAreaJSON),
                                         ('/user_map_json',getUserMapsJSON),
                                         ('/user_map_points_json',getUserMapPointsJSON),
                                         ('/user_map',UserMapView),
                                         ('/user_map4gps',UserMapView4GPS),
                                         ('/user_map4gps1time',UserMapView4GPS1Time),
                                         ('/send',SendInfo),
                                         ('/add', AddArea),
                                         ('/edit', EditAreaView),
                                         ('/update', UpdateArea),
                                         ('/delete', Delete)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

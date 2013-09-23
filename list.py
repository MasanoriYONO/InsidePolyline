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
    category = db.StringProperty()
    information = db.TextProperty()
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
def getAreas(paid_user,map_name,user_lat_lng,user_location_date):
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
                'host_path':os.environ['HTTP_HOST'],
                'user_location_date': user_location_date,
                'user_lat_lng': '(' + user_lat_lng + ')'
            }
        else:
            template_values = {
            }
    else:
        res_ct = post_db_query.count(5)
        if res_ct > 0:
            areas = post_db_query.fetch(5)
            map_names = getMapInfo(areas[0].map_name)
            #無料ユーザーの場合はアクセスしてきたユーザーの情報ウィンドウに
            #日時が表示されない。テンプレート変数にセットしていないため。
            template_values = {
                'areas': areas,
                'map_names':map_names,
                'selected_map':map_name,
                'host_path':os.environ['HTTP_HOST'],
                'user_lat_lng': '(' + user_lat_lng + ')'
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

#ユーザーマップに登録されているエリアをリスト表示
class AreasListOnUserMap(webapp.RequestHandler):
    def post(self):
        map_name = self.request.get('map_name')
        post_db_query = PolyLine.all()
        post_db_query.filter('map_name =', map_name)
        post_db_query.order('-updated_at')
        res_ct = post_db_query.count(1000)
        if res_ct > 0:
            areas = post_db_query.fetch(1000)
            for p in areas:
                p.updated_at = UTC2JST(p.updated_at)
                template_values = {
                    'areas': areas,
                    }
            path = os.path.join(os.path.dirname(__file__), 'areas_list.html')
            self.response.out.write(template.render(path, template_values))

    def get(self):
        map_name = self.request.get('map_name')
        post_db_query = PolyLine.all()
        post_db_query.filter('map_name =', map_name)
        post_db_query.order('-updated_at')
        res_ct = post_db_query.count(1000)
        if res_ct > 0:
            areas = post_db_query.fetch(1000)
            for p in areas:
                p.updated_at = UTC2JST(p.updated_at)
                template_values = {
                    'areas': areas,
                    }
            path = os.path.join(os.path.dirname(__file__), 'areas_list.html')
            self.response.out.write(template.render(path, template_values))

                    
class UsersListView(webapp.RequestHandler):
    @login_required
    def get(self):
        user = users.get_current_user()
        if user:
            if users.is_current_user_admin():
                post_db_query = db.Query(MapRandom)
                post_db_query = MapRandom.all()
                post_db_query.order('author')
                all_author = dict()
                for q in post_db_query:
                    #distinctに変わるものがないので辞書を作成した。2011/09/17 14:53
                    if all_author.has_key(q.author.email()):
                        all_author[q.author.email()] = all_author[q.author.email()] + 1
                    else:
                        all_author[q.author.email()] = 1
                    #localhostでは
                    #'12004 ahNkZXZ-aW5zaWRlLXBvbHlsaW5lchALEglNYXBSYW5kb20Y5F0M [myono.c50@gmail.com]:避難所'というように出力される。
                    #実際の環境では
                    #'12004 ahFzfmluc2lkZS1wb2x5bGluZXIQCxIJTWFwUmFuZG9tGORdDA [myono.c50@gmail.com]:広域避難地および一次避難地'
                    #self.response.out.write("%s %s [%s]:%s<br />" %(q.key().id(),q.key(),q.author.email(),q.map_name_4view))
                
                #for k,v in all_author.iteritems():
                    #print k,'=',v
                    #self.response.out.write("after distinct :%s = %s<br />" %(k,v))
                
                map_details = post_db_query.fetch(1000)
                for p in map_details:
                    p.updated_at = UTC2JST(p.updated_at)
                #有料ユーザーの一覧
                post_db_query = db.Query(PaidMembers)
                post_db_query = PaidMembers.all()
                post_db_query.order('-updated_at')
                res_ct = post_db_query.count(1000)

                if res_ct > 0:
                    paid_members = post_db_query.fetch(1000)
                    for p in paid_members:
                        p.updated_at = UTC2JST(p.updated_at)

                    template_values = {
                        'map_owners': all_author,
                        'map_details': map_details,
                        'paid_members': paid_members
                    }
                else:
                    template_values = {
                        'map_owners': all_author,
                        'map_details': map_details
                    }

                path = os.path.join(os.path.dirname(__file__), 'paid_members.html')
                self.response.out.write(template.render(path, template_values))
                

#現在地から近い10箇所を表示。どのマップに登録されているかもあわせて表示。
#マップの種別ごとにフィルタをかけて表示したい。
class Closed10Areas(webapp.RequestHandler):
    def get(self):
    #latlng get from responce.
        t_lat = self.request.get('lat')
        t_lng = self.request.get('lng')
        
        if not(t_lat):
            lat = float("34.97285824647155")
        else:
            lat = float(t_lat)
        if not(t_lng):
            lng = float("138.3842183974839")
        else:
            lng = float(t_lng)
        
        #self.response.out.write("%s, %s<br />" %(lat,lng))
        #calculate closed vertex and distance from now location to registed vertex in areas.
        post_db_query = PolyLine.all()
        post_db_query.order('-updated_at')
        areas = post_db_query.fetch(1000)
        
        vertex = {}
        for p in areas:
            #JSON形式として扱えるように置換
            t_list = p.area
            t_list2 = t_list.replace('lat','"lat"')
            t_list = t_list2.replace('lng','"lng"')
            #self.response.out.write("%s:%s<br />" %(type(t_list).__name__,t_list))
            
            t_area =  simplejson.loads( t_list )
            #self.response.out.write("%s:%s<br />" %(type(t_area).__name__,t_area))
            
            vertex_id = []
            vertex_dist = []
            for pp in t_area:
                #self.response.out.write("%s:%s,%s<br />" %(type(pp).__name__,pp['lat'],pp['lng']))
                
                #push dictionary or list key of areas,distance,vertex
                dist = math.sqrt((pp['lat']-lat)*(pp['lat']-lat) + (pp['lng']-lng)*(pp['lng']-lng))
                
                vertex_dist.append(dist)
            
            min_dist = min(vertex_dist)
            vertex.update({p.key():min_dist})
        
        i = 0
        keys = []
        for k, v in sorted(vertex.items(), key=lambda x:x[1]):
            #self.response.out.write("area.key:%s => %s<br />" %(k, v))
            
            keys.append(k)
            i = i + 1
            if i >= 10:
                break;
        query = PolyLine.gql("WHERE __key__  IN :1 " ,keys)
        #self.response.out.write("record:%s<br />" %(query.count()))
        areas = query.fetch(10)
        
        #for result in sorted(areas.keys().id()):
            #self.response.out.write("key:%s<br />" %(result.key()))
        #sort dctionary ascendign.
        #top10 points query from GQL. IN(1,2,…,10)
        #render html
        
        
        template_values = {
           'areas': areas,
           'lat':lat,
           'lng':lng,
           'sort_keys':keys
           }
        
        path = os.path.join(os.path.dirname(__file__), 'closed10areas.html')
        self.response.out.write(template.render(path, template_values))

class Closed10Areas4gps(webapp.RequestHandler):
    def get(self):
    #latlng get from responce.
        t_lat = self.request.get('lat')
        t_lng = self.request.get('lng')
        
        if not(t_lat):
            lat = float("34.97285824647155")
        else:
            lat = float(t_lat)
        if not(t_lng):
            lng = float("138.3842183974839")
        else:
            lng = float(t_lng)
        
        #self.response.out.write("%s, %s<br />" %(lat,lng))
        #calculate closed vertex and distance from now location to registed vertex in areas.
        post_db_query = PolyLine.all()
        post_db_query.order('-updated_at')
        areas = post_db_query.fetch(1000)
        
        vertex = {}
        for p in areas:
            #JSON形式として扱えるように置換
            t_list = p.area
            t_list2 = t_list.replace('lat','"lat"')
            t_list = t_list2.replace('lng','"lng"')
            #self.response.out.write("%s:%s<br />" %(type(t_list).__name__,t_list))
            
            t_area =  simplejson.loads( t_list )
            #self.response.out.write("%s:%s<br />" %(type(t_area).__name__,t_area))
            
            vertex_id = []
            vertex_dist = []
            for pp in t_area:
                #self.response.out.write("%s:%s,%s<br />" %(type(pp).__name__,pp['lat'],pp['lng']))
                
                #push dictionary or list key of areas,distance,vertex
                dist = math.sqrt((pp['lat']-lat)*(pp['lat']-lat) + (pp['lng']-lng)*(pp['lng']-lng))
                
                vertex_dist.append(dist)
            
            min_dist = min(vertex_dist)
            vertex.update({p.key():min_dist})
        
        i = 0
        keys = []
        for k, v in sorted(vertex.items(), key=lambda x:x[1]):
            #self.response.out.write("area.key:%s => %s<br />" %(k, v))
            
            keys.append(k)
            i = i + 1
            if i >= 10:
                break;
        
        query = PolyLine.gql("WHERE __key__  IN :1 " ,keys)
        #self.response.out.write("record:%s<br />" %(query.count()))
        areas = query.fetch(10)
        #for result in results:
            #self.response.out.write("key:%s<br />" %(result.key()))
        #sort dctionary ascendign.
        #top10 points query from GQL. IN(1,2,…,10)
        #render html
        
        
        template_values = {
           'areas': areas,
           'lat':lat,
           'lng':lng
           }
        
        path = os.path.join(os.path.dirname(__file__), 'closed10areas4gps.html')
        self.response.out.write(template.render(path, template_values))
        
class Closed10AreasJSONP(webapp.RequestHandler):
    def get(self):
    #latlng get from responce.
        t_lat = self.request.get('lat')
        t_lng = self.request.get('lng')
        callback = self.request.get("callback")
        
        if not(t_lat):
            return
        else:
            lat = float(t_lat)
        if not(t_lng):
            return
        else:
            lng = float(t_lng)
        
        #self.response.out.write("%s, %s<br />" %(lat,lng))
        #calculate closed vertex and distance from now location to registed vertex in areas.
        post_db_query = PolyLine.all()
        post_db_query.order('-updated_at')
        areas = post_db_query.fetch(1000)
        
        vertex = {}
        for p in areas:
            #JSON形式として扱えるように置換
            t_list = p.area
            t_list2 = t_list.replace('lat','"lat"')
            t_list = t_list2.replace('lng','"lng"')
            #self.response.out.write("%s:%s<br />" %(type(t_list).__name__,t_list))
            
            t_area =  simplejson.loads( t_list )
            #self.response.out.write("%s:%s<br />" %(type(t_area).__name__,t_area))
            
            vertex_id = []
            vertex_dist = []
            for pp in t_area:
                #self.response.out.write("%s:%s,%s<br />" %(type(pp).__name__,pp['lat'],pp['lng']))
                
                #push dictionary or list key of areas,distance,vertex
                dist = math.sqrt((pp['lat']-lat)*(pp['lat']-lat) + (pp['lng']-lng)*(pp['lng']-lng))
                
                vertex_dist.append(dist)
            
            min_dist = min(vertex_dist)
            vertex.update({p.key():min_dist})
        
        i = 0
        keys = []
        for k, v in sorted(vertex.items(), key=lambda x:x[1]):
            #self.response.out.write("area.key:%s => %s<br />" %(k, v))
            
            keys.append(k)
            i = i + 1
            if i >= 10:
                break;
        
        query = PolyLine.gql("WHERE __key__  IN :1 " ,keys)
        areas = query.fetch(10)
        
        template_values = {
           'areas': areas,
           'lat':lat,
           'lng':lng
           }
        #self.response.out.write("%s" %(res_str))
        #value = simplejson.dumps(template_values)
        self.response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        
        #JSON
        #self.response.content_type = "application/json; charset=utf-8"
        #self.response.out.write("%s('{result:%s}');" %(callback, value))
        #self.response.out.write("%s({result:%s});" %(callback, template_values))
        #self.response.out.write('%s({"areas":[' %(callback))
        res_str = callback + '({"areas":['
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
            
        #res_str = res_str.rstrip(',') + ']});'
        #add keys
        res_str = res_str.rstrip(',') + '],'
        res_str = res_str + '"sort_keys":['
        for k in keys:
            res_str = res_str + '"' + str(k) + '",'
        res_str = res_str.rstrip(',') + ']});'
        
        self.response.out.write('%s' %(res_str))
        #self.response.out.write("]});")
        return
        
class MailHistoryList4Users(webapp.RequestHandler):
    @login_required
    def get(self):
        user = users.get_current_user()
        if user:
            #userのマップリストを取得。
            map_random = MapRandom.all()
            map_random.filter('author =', user)
            map_names = map_random.fetch(100)
            
            keys = []
            for p in map_names:
                keys.append(p.name)

            post_db_query = MailHistory.gql("WHERE map_name  IN :1 ORDER BY updated_at DESC" ,keys)
            #post_db_query = MailHistory.all()
            #post_db_query.order('-updated_at')
            res_ct = post_db_query.count(1000)
            if res_ct > 0:
                areas = post_db_query.fetch(1000)
                for p in areas:
                    p.updated_at = UTC2JST(p.updated_at)
                    template_values = {
                        'areas': areas,
                        }
                path = os.path.join(os.path.dirname(__file__), 'list_mail_history.html')
                self.response.out.write(template.render(path, template_values))
            else:
                self.response.out.write("メール履歴はありません。")

class UserLocationView(webapp.RequestHandler):
    @login_required
    def get(self):
        user = users.get_current_user()
        if user:
            #get areas from user's map_name,author,lat,lng,
            user_lat_lng = self.request.get('user_lat_lng')
            user_location_date = self.request.get('user_location_date')
            map_name = self.request.get('map_name')
            paid_user = getUserInfo(map_name)
            template_values = getAreas(paid_user,map_name,user_lat_lng,user_location_date)
            if template_values:
                path = os.path.join(os.path.dirname(__file__), 'user_location.html')
                self.response.out.write(template.render(path, template_values))
            else:
                self.redirect('/')

class MainHandler(webapp.RequestHandler):
    def get(self):
        post_db_query = MapRandom.all()
        post_db_query.order('-updated_at')
        map_names = post_db_query.fetch(10)
        for p in map_names:
            p.updated_at = UTC2JST(p.updated_at)
        
        #各マップのエリアを取得
        post_area_query = PolyLine.all()
        post_area_query.order('-updated_at')
        #マップごとの登録エリア数を表示したい。
        each_maps = dict()
        for q in post_area_query:
        #distinctに変わるものがないので辞書を作成した。2011/09/23 14:30
            if each_maps.has_key(q.map_name):
                each_maps[q.map_name] = each_maps[q.map_name] + 1
            else:
                each_maps[q.map_name] = 1
                        
        areas = post_area_query.fetch(1000)
                                
        template_values = {
            'map_names': map_names,
            'areas': areas,
            'each_maps': each_maps,
            'host_path':os.environ['HTTP_HOST']
            }

        path = os.path.join(os.path.dirname(__file__), 'map_list.html')
        self.response.out.write(template.render(path, template_values))
        
def main():
    application = webapp.WSGIApplication([('/list/', MainHandler),
                                         ('/list/mail_history',MailHistoryList4Users),
                                         ('/list/user_location',UserLocationView),
                                         ('/list/closed10', Closed10Areas),
                                         ('/list/closed10jsonp', Closed10AreasJSONP),
                                         ('/list/closed10gps', Closed10Areas4gps),
                                         ('/list/areas_on_user_map',AreasListOnUserMap)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

#!/usr/bin/python 
# -*- coding: utf-8 -*- 
#encoding=utf-8 
#Filename:states_code.py   

# 下载电影的

import sqlite3
import urllib2
import string
from lxml import etree
from lxml import html as HTML

class RedirctHandler(urllib2.HTTPRedirectHandler):   
	"""docstring for RedirctHandler"""  
	def http_error_301(self, req, fp, code, msg, headers):     
		pass  
	
	def http_error_302(self, req, fp, code, msg, headers):     
		pass   
		
def getUnRedirectUrl(url,timeout=10):   
	req = urllib2.Request(url)   
	debug_handler = urllib2.HTTPHandler(debuglevel = 1)   
	opener = urllib2.build_opener(debug_handler, RedirctHandler)      
	html = None  
	response = None  
	try:     
		response = opener.open(url,timeout=timeout)     
		html = response.read() 
	except urllib2.URLError as e:     
		if hasattr(e, 'code'):       
			error_info = e.code     
		elif hasattr(e, 'reason'):       
			error_info = e.reason
		print error_info
	finally:
		if response:
			response.close()
			
	if html:
		return html   
	else:     
		return error_info  
		
# 下载器
class MovieSpider:
	#数据库连接对象
	# 构造的时候直接打开数据库
	def __init__(self, db_path):
		self.db_conn = sqlite3.connect(db_path)

	# 构造url
	def build_page_url(self,page):
		return "http://www.bttiantang.com/?PageNo=%d"%page
	
	def get_last_page(self):
		cur = self.db_conn.cursor();
		cur.execute("SELECT COUNT(id) FROM page")
		row = cur.fetchone()[0]
		print "Resume Download From %d"%row
		return row
	
	# 正常化字符串
	def normal_str(self, str):
		if str is None:
			str = "N/A"
		return str.replace("'", "''").replace('%', "%%")		
	
	# 解析并保存到db中
	def parse_and_save(self, page, data):
		html = etree.HTML(data)
		all = html.xpath("////div[@class='item cl']/div[@class='title']")
		for itm in all:
			# 评分
			s_rate1 = itm.xpath("./p[@class='rt']/strong")[0].text
			s_rate2 = itm.xpath("./p[@class='rt']/em[@class='fm']")[0].text
			rate = string.atof(s_rate1 + '.' + s_rate2)
			# print "rate:%f" %rate
			
			# 别名
			s_alias = itm.xpath("./p/a[@target]")[1].text
			#print "alias:" + s_alias
			
			#描述，包括国家，出品年份
			s_des = itm.xpath("./p[@class='des']")[0].text.split("(")
			s_year = "0000"
			s_nation = "N/A"
			if len(s_des) == 2:
				s_year = s_des[0]
				s_nation = s_des[1].replace(')','')
			# print "des:" + s_year + "--" + s_nation
			
			# ------------------------
			lst_dom_title = itm.xpath("./p[@class='tt cl']")
			if len(lst_dom_title) == 0:
				continue
				
			# 名字
			dom_t = lst_dom_title[0].xpath("./a/b/font")	# 红色的
			if len(dom_t) == 0:
				s_title = lst_dom_title[0].xpath("./a/b")[0].text
			else:
				s_title = dom_t[0].text		# 灰色的
			# print "title:" + s_title
			
			# url 页面
			s_url = lst_dom_title[0].xpath("./a[@href]")[0].get("href","NA")
			# print "url:" + s_url
			
			# 更新日期
			dom_t = lst_dom_title[0].xpath("./span/font")	# 红色的
			if len(dom_t) == 0:
				s_date = lst_dom_title[0].xpath("./span")[0].text
			else:
				s_date = dom_t[0].text		# 灰色的
			# print "date:" + s_date
			
			print "Alrigh ----------------"
			print "Save to DB^^^^^^"
			
			# 保存到数据库中
			s_title = self.normal_str(s_title)
			s_alias = self.normal_str(s_alias)
			s_url = self.normal_str(s_url)
			s_nation = self.normal_str(s_nation)
			s_year = self.normal_str(s_year)
			s_date = self.normal_str(s_date)
			sqlsx = "insert into movie(name,alias,catelog,rate,url,nation,year,udate) values('%s','%s','',%f,'%s','%s','%s','%s')"%(s_title,s_alias,rate,s_url,s_nation,s_year,s_date)
			self.db_conn.execute(sqlsx)
			
		# 一个页面一次性提交
		self.db_conn.execute("insert into page(page) values(%d)"%(page))
		self.db_conn.commit();
	
	# 下载页面
	def download_page(self, page):   
		url = self.build_page_url(page)
		print "downloading..." + url
		
		req = urllib2.Request(url)
		debug_handler = urllib2.HTTPHandler(debuglevel = 1)
		opener = urllib2.build_opener(debug_handler, RedirctHandler)
		response = None  
		try:
			response = opener.open(url,timeout=10)     
			html = response.read();
			#print html.decode('utf-8','ignore').encode('gb2312','ignore')
			self.parse_and_save(page, html)
		except urllib2.URLError as e:     
			if hasattr(e, 'code'):       
				error_info = e.code     
			elif hasattr(e, 'reason'):       
				error_info = e.reason
			print error_info
		finally:
			if response:
				response.close()

if __name__=="__main__":
	# 下载前10页		
	inst = MovieSpider("movies.db")	
	for i in range(inst.get_last_page() + 1, 684):
		inst.download_page(i)

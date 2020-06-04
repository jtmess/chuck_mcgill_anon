#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chuck_mcgill shops for you
Modify keywords for search terms you're interested in
Modify run_freq to change the report interval
	Chuck will only search for new items since the last run
If url_base is within vehicles, Chuck will cross reference values against KBB and report percent difference
Chuck is trying to find a way to cross reference other item values against ebay
Chuck is learning to negotiate with sellers (think this needs to bypass recaptcha)
"""

"""
USER data
"""

ADDRESS = 'YOUR_ADDRESS'
EMAIL_ADDR = 'YOUR_EMAIL_ADDRESS'
EMAIL_PW = 'YOUR_EMAIL_PASSWORD' #put this here or obscure it in a separate file
gmaps = googlemaps.Client(key='YOUR_GOOGLE_MAPS_API')
run_freq = 12 # run frequency in hours
keywords = ['orion telescope', 'giant bicycle', 'surfboard', 'etc'] # things you want to search for

"""
end USER data
"""

import pandas as pd
from bs4 import BeautifulSoup as bs4
import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl
import numpy as np
import requests
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import googlemaps
import time
import sys
from django.utils.encoding import smart_str # , smart_unicode

# hard limit maximum gmaps API requests per day at something under 645

# %matplotlib inline


# first run time in 24h time
start_time = 8

# new URL
# https://sfbay.craigslist.org/d/for-sale/search/sss

def main():
	runs = 0
	while 1:
		before = datetime.now()
		scan(runs)
		after = datetime.now()
		delta = after-before
		print("time to run was "+str(delta))
		delta = int(delta.total_seconds())
		# check amount of time since
		runs = runs + 1
		time.sleep(43200-delta)
	
	
def scan(runs):
	api_queries = 0
	password = EMAIL_PW
	url_base = 'http://sfbay.craigslist.org/search/sss' #Change this if you're in a different city
	urls = []
	full_report = [] # list to store all the data from each keyword [[keyword 1[title, price, location, URL]][keyword 2[title, price, location, URL]]]
	all_new_posts = []
	for keyword in keywords:
		# create a dict of URL for each keyword
		# https://sfbay.craigslist.org/search/sss?query=scuba
		params = dict(sort='date', query=keyword)
		# filter out all the items that are in nearby markets
		rsp = requests.get(url_base, params=params)
		print(rsp.url)
		# print(rsp.text[:500])
		# print(rsp.text[:15000])
		full_report.append(['New Search:'+keyword])	#added to separate keywords in final output list

		# BS4 can quickly parse our text, make sure to tell it that you're giving html
		html = bs4(rsp.text, 'html.parser')
		# html = bs4(rsp.text, "html5lib")
		# print("BREAKING FROM HTML TO BS4 OUTPUT")
		# BS makes it easy to look through a document
		# print(html.prettify()[:1000])
		# print(html.prettify())

		items = html.find_all('li', attrs={'class': 'result-row'})
						### # ## # # # # NOTE: ITEMS MAX IS 120 PER PAGE. Issues should be avoided by date sorting
		# just throw away anything in items that's past 120
		print(len(items))
		current_time = datetime.now()
		key_new_posts = []

		for item in items:
			# print(item) # print all the html to debug
			date_str = item.find_all('time')
			# print(type(str(date_str[0]))) # type test for bs4 objects
			date = str(date_str[0]).split('"')[5][4:]
			day = date[:2]
			# print(day)
			month = date[3:][:3]
			hour = date[7:][:2]
			minute = date[10:][:2]
			if date[16:] == 'AM':
				if hour == '12':
					hour = '00'
			elif date[16:] == 'PM':
				if hour == '12':
					pass
				else:
					# print('Adding 12: hour is '+hour)
					hour = str(int(hour) + 12)
			# print(month)
			# print(hour)
			# print(minute)
			if date == 1: # if the date is posted since the last run, log it to new dict
				pass
			title = item.find_all('a', attrs={'class': 'result-title hdrlnk'})[0].text
			price = item.find_all('span', attrs={'class': 'result-price'})[0].text
			try:
				location = item.find_all('span', attrs={'class': 'result-hood'})[0].text
			except:
				location = 'NULL'
			directions = find_distance(location, api_queries)
			link_str = item.find_all('a', attrs={'class': 'result-title hdrlnk'})
			link = str(link_str[0]).split('"')[5]
			description = get_description(link)
			# print(month+'-'+day+'-2020-'+hour+'-'+minute)
			post_time = datetime.strptime(month+'-'+day+'-2020-'+hour+'-'+minute, '%b-%d-%Y-%H-%M')
			# print('Post time object is '+str(post_time))
			time_delta = current_time - post_time
			# print("time since posted is "+str(time_delta))
			hours_since = (time_delta.total_seconds())/3600
			# print(str(hours_since)+" hours since post")
			if hours_since < run_freq:
				# print("New Post!")
				# print(date)
				# print(title)
				# print(price)
				# print(link)
				# print(description)
				# print(location)
				distance = directions[0]+" away"
				time_no_traffic = directions[1]+" driving without traffic"
				time_with_traffic = directions[2]+" driving right now"
				key_new_posts.append([title, price, str(int(hours_since))+' Hour(s) Since Post', link, description, location, distance, time_no_traffic, time_with_traffic])
			else:
				# reached end of new posts, so stop searching
				# print("Reached the end of new posts for this catagory")
				break
			# print(breaker) # breakpoint to avoid sending emails
		print("appended "+str(len(key_new_posts))+" new posts from "+keyword)
		all_new_posts.append(key_new_posts)
	# print(all_new_posts)
	if runs%2 == 0:
		time = '8AM'
	else:
		time = '8PM'
	report(password, all_new_posts, time)

	# print(items[0])

def get_description(link):
	rsp = requests.get(link)
	# print(rsp.url)
	html = bs4(rsp.text, 'html.parser')
	description = html.find('meta')
	description = str(description).split('"')[1]
	return description
"""
sns.set_palette('colorblind')
sns.set_style('white')
"""

def find_distance(location, api_queries):
	if location == 'NULL':
		return['unknown', 'unknown', 'unknown', api_queries]
	else:
		# location = str(location)+', CA'
		# location = "دلم برات خیلی تنگ شده"+", CA"	# test an error location
		print("the location is currently: "+location)
		now = datetime.now()
		if api_queries < 645/(24/run_freq):
			try:
				directions_result = gmaps.directions(YOUR_ADDRESS, location, mode="driving", departure_time=now)
				api_queries = api_queries + 1
			except:
				print("Location had an error, not including it")
		else:
			print("GMaps API queries limited")
		try:
			mileage = directions_result[0]['legs'][0]['distance']['text']
			time_1am = directions_result[0]['legs'][0]['duration']['text']
			time_now = directions_result[0]['legs'][0]['duration_in_traffic']['text']
			return[mileage, time_1am, time_now, api_queries]
		except:
			return['error', 'error', 'error', api_queries]
		# return['10 mi', '28 mins', '45 mins']

def report(password, full_report, time):
	smtpObj=smtplib.SMTP('smtp.gmail.com',587)
	smtpObj.starttls()
		# log in to email account
	smtpObj.login(EMAIL_ADDR, EMAIL_PW)
	# print("logged in to email account")

	# amount_sold = 5.5
	
	# print(msg)
	#msg = MIMEText("In a long series of mailbot tests, this is iteration number %s" % count)
	
	message = ''
	message = message+'Semi-Daily Craigslist Report for the following keys:\n\n'
	keys_string= ''
	for key in keywords:
		keys_string = keys_string+', '+key
	message = message+keys_string+'\n\n'
	for result in full_report:
		for keyword_output in result:
			for data in keyword_output:
				message = message+str(data)+'\n'
			message = message+'\n'
	print(message)
	# message = smart_str(message)
	# message = message.decode('unicode-escape').encode('ascii', 'ignore')
	# message = message.replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u2013", "-").replace(u"\u2022", "*")
	print(type(message))
	#print("string index 6315 is "+message[6315])
	#print("string index 6316 is "+message[6316])
	#print("string index 6317 is "+message[6317])
	# msg = MIMEText("%s" % (message))
	# msg['Subject'] = "Semi-daily Craigslist report"
	msg = 'Subject: {}\n\n{}'.format("CRAIGSLIST REPORT, semi-daily", str(message))
	smtpObj.sendmail(EMAIL_ADDR, EMAIL_ADDR, msg)

	return 0;

if __name__ == "__main__":
	main()

"""
Complete database of queries and subqueries
Scuba
Bikes
Climbing
Guitars
Cross reference cars against KBB?
Cross reference everything against somewhere...ebay?
"""

"""
Email Format:

New Craigslist Posts:
QUERY TITLE:

item title
item price
item location
item description
seller email (recaptcha)
item link
"""

"""
Process: set global timing run variable
only new posts since last run analyzed (in time tag), but first run has to get all posts
neural net for interesting field

"""

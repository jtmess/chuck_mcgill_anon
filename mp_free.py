"""
Email and/or text whenever a new free post is made on MP free and for sale forum
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
import time
import sys
from django.utils.encoding import smart_str # , smart_unicode
from twilio.rest import Client

# Twilio credentials
account_sid = "AC4037da3816ae393b39c12d9b6f5bb909"
auth_token  = "69024deb5ee47685cb66ae5ab938f0fd"

# run frequency in SECONDS
run_freq = 30

def main():
	runs = 0
	last_page_num = 40
	last_post_num = 0
	last_post_num = scan(last_page_num, last_post_num, 1)
	while 1:
		before = datetime.now()
		last_post_num = scan(last_page_num, last_post_num, 0)
		if last_post_num == 20:  # 20 is max posts per page. If a page reaches 20, set posts to 0 and advance to the next page
			last_post_num = 0
			last_page_num = last_page_num + 1
		print("On page "+str(last_page_num)+" and post "+str(last_post_num))
		after = datetime.now()
		delta = after-before
		print("time to run was "+str(delta))
		delta = int(delta.total_seconds())
		# check amount of time since
		runs = runs + 1
		time.sleep(run_freq-delta)
	
	
def scan(last_page_num, last_post_num, test):
	url_base = 'https://www.mountainproject.com/forum/topic/114120919/free-geargiving-away' # example URL https://sfbay.craigslist.org/search/sss?sort=date&query=scuba
	params = dict(page=(last_page_num))
	rsp = requests.get(url_base, params=params)
	# print(rsp.url)
	# print(rsp.text[:500])
	# print(rsp.text[:15000])

	# BS4 can quickly parse our text, make sure to tell it that you're giving html
	html = bs4(rsp.text, 'html.parser')
	# print(html)

	# find all instances of "Joined" to see how many posts are on the page. If equal to 20, go on to the next page
	# log current number of posts
	items = html.find_all('body')
		#, attrs={'class': 'result-row'})
	# print(html.get_text())
	# print(items)
	posts_on_page = len(items) - 1

	message_url_list = []
	for link in html.find_all('a'):
		# print(link.get('href'))
		url = str(link.get('href'))
		if url.startswith('https://www.mountainproject.com/forum/message/'):
			message_url_list.append(url)
	if test == 1:
		print("Tested the number of starting posts and found "+str(posts_on_page))
		return posts_on_page
	# find out if there's a new post
	if posts_on_page > last_post_num:
		print("there's a new post!")
		# get the URL associated with the new post
		send_sms(message_url_list[-1])
	return posts_on_page

def send_sms(url):
	client = Client(account_sid, auth_token)
	message = client.messages.create(to="+14088198030", from_="+12405585899", body="New Post in MP Free! "+url)

if __name__ == "__main__":
	main()
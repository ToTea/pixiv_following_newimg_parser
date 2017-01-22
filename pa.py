import urllib
from urllib import request
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
import http.cookiejar
import os
from clint.textui import progress
import re
import getpass
import sys


invalid_characters = {
        '\\': '﹨',
        '/': '∕',
        '>': '＞',
        '<': '＜',
        '"': '”',
        '|': '｜',
        '?': '？',
        '*': '＊',
        ':': '：'
}

if not os.path.exists('download'):
	os.makedirs('download')

cookie = http.cookiejar.MozillaCookieJar()
if os.path.isfile('cookie.txt'):
	cookie.load('cookie.txt')

handler = urllib.request.HTTPCookieProcessor(cookie)
opener = urllib.request.build_opener(handler)

urls = []

if os.path.isfile('downloaded.txt'):
        with open('downloaded.txt', 'r') as f:
	            downloaded = f.readlines();
	            downloaded = [x.strip() for x in downloaded]
else:
        downloaded = []

if os.path.isfile('latest.txt'):
        with open('latest.txt', 'r') as f:
	            latest = f.readline().strip();
	            newlatest = latest
else:
        latest = '=-1'
        newlatest = latest

res = opener.open('http://www.pixiv.net')
soup = BeautifulSoup(res.read(), 'html.parser')
while len(soup.select('.signup-form__logo-box')) > 0:
	print("Not login or login fail. Please login.")
	pixiv_id = input('->Username: ')
	password = getpass.getpass('->Password: ')
	res = opener.open('https://accounts.pixiv.net/login')
	soup = BeautifulSoup(res.read(), 'html.parser')
	post_key = soup.select('#old-login input')[0]['value']
	postDict = {
		'pixiv_id': pixiv_id,
		'password': password,
		'post_key': post_key,
		'return_to': 'http://www.pixiv.net/',
		'lang': 'zh_tw',
		'source': 'pc'
	}
	postData = urllib.parse.urlencode(postDict).encode()
	res = opener.open('https://accounts.pixiv.net/login', postData)
	soup = BeautifulSoup(res.read(), 'html.parser')

	cookie.save('cookie.txt')

done = False
first = True
for page in range(1,50):
	new_image_url = 'http://www.pixiv.net/bookmark_new_illust.php?p=%d' % page

	res = opener.open(new_image_url)
	soup = BeautifulSoup(res.read(), 'html.parser')
	posts = soup.select('.image-item ._work')

	for post in posts:
		url = 'http://www.pixiv.net' + post['href']
		if first: newlatest = url
		first = False
		if int(url.split('=')[-1]) <= int(latest.split('=')[-1]):
			done = True
			break
		if url in downloaded: continue
		print(url)
		urls.append(url)
	if done: break

downloaded_file = open('downloaded.txt', 'a')

for i, url in enumerate(urls):
	print("\n->Download(%d/%d): %s" % ( i+1, len(urls), url))
	res = opener.open(url)
	soup = BeautifulSoup(res.read(), 'html.parser')

	author = soup.select('.profile-unit .user')[0].string
	title = soup.select('.work-info .title')[0].string
	for original, replacement in invalid_characters.items():
		author = author.replace(original, replacement)
		title = title.replace(original, replacement)
	
	# 動圖
	m = re.search(r'http:\\/\\/i\d.pixiv.net\\/img-zip-ugoira\\/img\\/\d+\\/\d+\\/\d+\\/\d+\\/\d+\\/\d+\\/[0-9a-z_]+1920x1080.zip', str(soup))
	more = soup.select('.works_display ._work')
	if m != None:
		img = m.group(0).replace('\\', '')
		file_name = "%s - %s.zip" % (author, title)
		print(file_name.encode(sys.stdin.encoding, "replace").decode(sys.stdin.encoding))
		download_link = img
		headers = {'Referer': url}
		opener.addheaders = list(headers.items())
		r = opener.open(download_link)

		if r.status != 200:
			print("  status wrong: %d" % (r.status))
			
		path = 'download/' + file_name
		if os.path.exists(path):
			path = "download/%s - %s (%s).zip" % (author, title, url.split('=')[-1])

		with open(path, 'wb') as f:
			total_length = int(r.getheader('content-length'))
			chunk_count = 0
			expected_size = int((total_length/1024) + 1)
			for i in progress.bar(range(expected_size)): 
				chunk = r.read(1024)
				if chunk:
					chunk_count += 1
					f.write(chunk)
					f.flush()
	# 多圖
	elif len(more) > 0:
		more = more[0]['href']
		more = 'http://www.pixiv.net/' + more

		folder_name = "%s - %s" % (author, title)

		if os.path.exists('download/' + folder_name):
			folder_name = "%s (%s)" %(folder_name, url.split('=')[-1])

		if not os.path.exists('download/' + folder_name):
			os.makedirs('download/' + folder_name)

		print(folder_name.encode(sys.stdin.encoding, "replace").decode(sys.stdin.encoding))
		print(more)

		res = opener.open(more)
		soup = BeautifulSoup(res.read(), 'html.parser')
		images = soup.select('.full-size-container')

		for i, img in enumerate(images):
			img = img['href'];
			res = opener.open("http://www.pixiv.net/" + img)
			soup = BeautifulSoup(res.read(), 'html.parser')
			img = soup.select('img')[0]['src']

			print(img)

			file_name = "%03d.%s" % (i+1, img.split('.')[-1])
			print(file_name.encode(sys.stdin.encoding, "replace").decode(sys.stdin.encoding))

			download_link = img
			headers = {'Referer': url}
			opener.addheaders = list(headers.items())
			r = opener.open(download_link)

			if r.status != 200:
				print("  status wrong: %d" % (r.status))
				
			path = "download/%s/%s" % (folder_name, file_name)
			with open(path, 'wb') as f:
				total_length = int(r.getheader('content-length'))
				chunk_count = 0
				expected_size = int((total_length/1024) + 1)
				for i in progress.bar(range(expected_size)): 
					chunk = r.read(1024)
					if chunk:
						chunk_count += 1
						f.write(chunk)
						f.flush()
	else:
		img = soup.select('._illust_modal img')[0]['data-src']
		file_name = "%s - %s.%s" % (author, title, img.split('.')[-1])
		
		print(file_name.encode(sys.stdin.encoding, "replace").decode(sys.stdin.encoding))
		print(img)

		download_link = img
		headers = {'Referer': url}
		opener.addheaders = list(headers.items())
		r = opener.open(download_link)

		if r.status != 200:
			print("  status wrong: %d" % (r.status))
			
		path = 'download/' + file_name
		if os.path.exists(path):
			path = "download/%s - %s (%s).%s" % (author, title, url.split('=')[-1], img.split('.')[-1])

		with open(path, 'wb') as f:
			total_length = int(r.getheader('content-length'))
			chunk_count = 0
			expected_size = int((total_length/1024) + 1)
			for i in progress.bar(range(expected_size)): 
				chunk = r.read(1024)
				if chunk:
					chunk_count += 1
					f.write(chunk)
					f.flush()

	downloaded_file.write(url + '\n')
	downloaded_file.flush()

with open('latest.txt', 'w') as f:
	f.write(newlatest + '\n')
with open('downloaded.txt', 'w') as f:
	pass

print('Jobs done.')
cookie.save('cookie.txt')
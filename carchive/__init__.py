import os, requests, json, sys, datetime
from copy import deepcopy as dc
from utils import live_link
try:
	import mystring
except:
	os.system(f"{sys.executable} -m pip install --upgrade mystring")
	import mystring

"""
https://pypi.org/project/python-crontab/
https://pypi.org/project/python-cron/
"""

class githuburl(object):
	def __init__(self,url,token=None,verify=True,commit=None,tag=None):
		self.url = mystring.string(dc(url))
		self.token = mystring.string(token)
		self.verify = verify
		self.stringurl = mystring.string(dc(url))
		self.commit = None
		self.tag = None

		url = mystring.string(url).repsies('https://','http://','github.com/').repsies_end('.git', "/")
		self.owner, self.reponame = url.split("/")
		self.owner, self.reponame = mystring.string(self.owner), mystring.string(self.reponame)

		if not mystring.string(tag).empty:
			self.tag = mystring.string(tag)
			self.stringurl += f"<b>{tag}"
		if not mystring.string(self.commit).empty:
			self.commit = mystring.string(commit)
			self.stringurl += f"<#>{self.commit}"

	@property
	def dir(self):
		return mystring.string(self.reponame+"/")

	@property
	def core(self):
		return mystring.string("{0}/{1}".format(self.owner, self.reponame))

	@property
	def furl(self):
		return mystring.string("https://github.com/{0}".format(self.core))

	def filewebinfo(self, filepath, lineno=None):
		baseurl = "https://github.com/{0}/blob/{1}/{2}".format(self.core, self.commit,
															filepath.replace(str(self.reponame) + "/", '', 1))
		if lineno:
			baseurl += "#L{0}".format(int(lineno))

		return mystring.string(baseurl)

	#Transforming this into a cloning function
	def __call__(self,return_error=False, json=True, baserun=False,headers = {}):
		mystring.string("git clone {}".format(self.furl)).exec(True)

		if self.commit:
			with mystring.foldentre()(self.dir):
				mystring.string(f"git checkout {self.commit}").exec(True)
		return self.dir

	def __enter__(self):
		self()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		mystring.string("yes|rm -r {0}".format(self.dir)).exec(True)
		return self

	@property
	def status(self):
		# curl -I https://api.github.com/users/octocat|grep x-ratelimit-reset
		cur_status, now = requests.get("https://api.github.com/users/octocat").json()['data'].headers, datetime.datetime.now()
		return {
			'Reset': cur_status['X-RateLimit-Reset'],
			'Used': cur_status['X-RateLimit-Used'],
			'Total': cur_status['X-RateLimit-Limit'],
			'Remaining': cur_status['X-RateLimit-Remaining'],
			'RemainingDate':datetime.datetime.fromtimestamp(int(cur_status['X-RateLimit-Reset'])),
			'WaitFor':datetime.datetime.fromtimestamp(int(cur_status['X-RateLimit-Reset'])) - now,
			'WaitForSec':(datetime.datetime.fromtimestamp(int(cur_status['X-RateLimit-Reset'])) - now).seconds,
			'WaitForNow':lambda :(datetime.datetime.fromtimestamp(int(cur_status['X-RateLimit-Reset'])) - datetime.datetime.now()).seconds,
		}

	@property
	def timing(self):
		import time
		if not hasattr(self, 'remaining') or self.remaining is None:
			stats = self.status
			print(stats)
			self.remaining = int(stats['Remaining'])
			self.wait_until = stats['WaitForNow']
		elif self.remaining >= 10:
			self.remaining = self.remaining - 1
		else:
			time_to_sleep = self.wait_until
			for itr in range(time_to_sleep):
				print("{}/{}".format(itr,time_to_sleep))
				time.sleep(1)
			delattr(self, 'remaining')
			delattr(self, 'wait_until')
		return

	def find_asset(self,asset_check=None, accept="application/vnd.github+json", print_info=False):
		if asset_check is None:
			asset_check = lambda x:False

		def req(string, verify=self.verify, accept=accept, auth=self.token, print_info=print_info):
			try:
				output = requests.get(string, verify=verify, headers={
					"Accept": accept,
					"Authorization":"Bearer {}".format(auth)
				})
				if print_info:
					print(output)
				return output.json()
			except Exception as e:
				if print_info:
					print(e)
				pass

		latest_version = req("https://api.github.com/repos/{}/releases/latest".format(self.core))
		release_information = req(latest_version['url'])
		for asset in release_information['assets']:
			if asset_check(asset['name']):
				return asset
		return None

	def download_asset(self, url, save_path, chunk_size=128, accept="application/vnd.github+json"):
		r = requests.get(url, stream=True, verify=self.verify, headers={
			"Accept": accept,
			"Authorization":"Bearer {}".format(self.token)
		})
		with open(save_path, 'wb') as fd:
			for chunk in r.iter_content(chunk_size=chunk_size):
				fd.write(chunk)
		return save_path

	def get_date_from_commit_url(self, accept="application/vnd.github+json"):
		req = requests.get(self.furl, headers={
			"Accept": accept,
			"Authorization":"Bearer {}".format(self.token)
		}).json()
		return datetime.datetime.strptime(req['commit']['committer']['date'], "%Y-%m-%dT%H:%M:%SZ")

	def get_commits_of_repo(self, from_date=None, to_date=None, accept="application/vnd.github+json"):
		params = []
		if from_date:
			params += ["since={0}".format(from_date)]
		if from_date:
			params += ["until={0}".format(to_date)]
		request_url = "https://api.github.com/repos/{0}/commits?{1}".format(self.core, '&'.join(params))
		req = requests.get(request_url, headers={
			"Accept": accept,
			"Authorization":"Bearer {}".format(self.token)
		})
		return req.json()

	@property
	def zip_url(self):
		url_builder = self.furl + "/archive"
		if self.commit:
			url_builder += f"/{self.commit}.zip"
		elif self.tag:
			url_builder += f"/{self.tag}.zip"

		self.zip_url_base = url_builder
		return self.zip_url_base

	@property
	def webarchive_save_url(self,):
		return mystring.string("https://web.archive.org/save/" + self.zip_url)


class GRepo(object):
	"""
	Sample usage:
	with GRepo("https://github.com/owner/repo","v1","hash") as repo:
		os.path.exists(repo.reponame) #TRUE
	"""
	def __init__(self, repo: str, tag: str = None, commit: str = 'master', token=None):
		self.repo = githuburl(repo,tag=tag,commit=commit)
		self.token = token
		self.webarchive_url_base = None
		self.zip_url_base = None

	def login(self):
		os.environ['GH_TOKEN'] = self.token
		try:
			with open("~/.bashrc", "a+") as writer:
				writer.write("GH_TOKEN={0}".format(self.token))
		except:
			pass

	def __enter__(self):
		self.repo.__enter__()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.repo.__exit__(exc_type, exc_val, exc_tb)
		return self

	@property
	def webarchive(self):
		from waybackpy import WaybackMachineSaveAPI as checkpoint
		url,save_url = self.repo.zip_url,None
		try:
			if live_link(url):
				saver = checkpoint(url, user_agent="Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0")

				try:
					save_url = saver.save()
					if save_url is None:
						save_url = saver.saved_archive
				except Exception as e:
					print(f"Issue with saving the link {url}: {e}")
					save_url = "NotAvailable"
					pass
		except Exception as e:
			print(f"Issue with saving the link {url}: {e}")
			pass

		return mystring.string(save_url)

	@property
	def info(self):
		return {
			'URL':self.repo.furl,
			'RepoName':self.repo.reponame,
			'Commit':self.repo.commit,
			'FullUrl':self.repo.stringurl,
			'ZipUrl':self.repo.zip_url,
			'WebArchiveSaveUrl':self.repo.webarchive_save_url
		}

	def jsonl(self, exclude_extensions=[], jsonl_file=None):
		output = jsonl_file or []
		if output != []:
			writer = open(output, 'w+')
			writer.write(str(json.dumps({**{'header': True}, **self.info})) + "\n")
		try:
			for root, directories, filenames in os.walk(self.repo.dir):
				for filename in filenames:
					foil = os.path.join(root, filename)
					ext = foil.split('.')[-1].lower()

					if "/.git/" not in foil and (exclude_extensions is None or ext not in exclude_extensions):
						try:
							if output != []:
								writer.write(mystring.foil(foil).structured()+ "\n")
							else:
								output += [mystring.foil(foil).structured()]
						except Exception as e:
							print(">: "+str(e))
							pass
		except Exception as e:
			print(f"Issue with creating the jsonl file: {e}")
		finally:
			if output != []:
				writer.close()

		return output
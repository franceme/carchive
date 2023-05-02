import os, requests, json, base64, hashlib, funbelts as ut, sys, datetime, contextlib
from copy import deepcopy as dc
try:
	import mystring
except:
	os.system(f"{sys.executable} -m pip install --upgrade mystring")
	import mystring
from waybackpy import WaybackMachineSaveAPI as checkpoint
from utils import live_link

"""
https://pypi.org/project/python-crontab/
https://pypi.org/project/python-cron/
"""

class githuburl(object):
	def __init__(self,url,token=None,verify=True,commit=None,tag=None):
		self.url = dc(url)
		self.token = token
		self.verify = verify
		self.remaining = None
		self.total = None
		self.wait_until = None
		self.stringurl = dc(url)
		self.commit = None
		self.tag = None

		url = url.replace('https://','').replace('http://','')
		if url.endswith('.git'):
			url = url[:-1 * len('.git')]
		url = url.replace('github.com/','')
		if url.endswith("/"):
			url = url[:-1]
		self.owner, self.reponame = url.split("/")
		
		if not mystring.string(tag).empty:
			self.tag = tag
			self.cloneurl += f" --branch {tag}"
			self.stringurl += f"<b>{tag}"
		if not mystring.string(self.commit).empty:
			self.commit = commit
			self.stringurl += f"<#>{self.commit}"

	@property
	def dir(self):
		return self.reponame+"/"

	@property
	def core(self):
		return "{0}/{1}".format(self.owner, self.reponame)

	@property
	def furl(self):
		return "https://github.com/{0}".format(self.core)

	def filewebinfo(self, filepath, lineno=None, commit='master'):
		baseurl = "https://github.com/{0}/blob/{1}/{2}".format(self.furl, commit,
															   filepath.replace(str(self.reponame) + "/", '', 1))
		if lineno:
			baseurl += "#L{0}".format(int(lineno))

		return baseurl

	def __call__(self,return_error=False, json=True, baserun=False):
		if not baserun:
			self.timing

		output = {}
		headers = {}

		if self.token is not None:
			headers['Authorization'] = 'Bearer {}'.format(self.token)

		try:
			output['data'] = requests.get(self.furl, verify=self.verify and self.verify, headers=headers)
			if json:
				output['data'] = output['data'].json()
		except Exception as e:
			if return_error:
				output["Error"] = e
			output['data'] = None

		return output

	@property
	def status(self):
		# curl -I https://api.github.com/users/octocat|grep x-ratelimit-reset
		cur_status, now = self("https://api.github.com/users/octocat", json=False, baserun=True)['data'].headers, datetime.datetime.now()
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
		if self.remaining is None:
			stats = self.status
			print(stats)
			self.remaining = int(stats['Remaining'])
			self.total = int(stats['Total'])
			self.wait_until = stats['WaitForNow']
		elif self.remaining >= 10:
			self.remaining = self.remaining - 1
		else: #if self.remaining == 0:
			time_to_sleep = self.wait_until
			for itr in range(time_to_sleep):
				print("{}/{}".format(itr,time_to_sleep))
				time.sleep(1)
			self.remaining = None

	def find(self, repo,asset_check=None, accept="application/vnd.github+json", print_info=False):
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

		// -> look into common converting github url to repo
		latest_version = req("https://api.github.com/repos/{}/releases/latest".format(self.core))
		release_information = req(latest_version['url'])
		for asset in release_information['assets']:
			print(asset['name'])
			print(asset_check(asset['name']))
			if asset_check(asset['name']):
				return asset #['browser_download_url']
		return None

	def download(self, save_path, chunk_size=128, accept="application/vnd.github+json"):
		r = requests.get(self.furl, stream=True, verify=self.verify, headers={
			"Accept": accept,
			"Authorization":"Bearer {}".format(self.token)
		})
		with open(save_path, 'wb') as fd:
			for chunk in r.iter_content(chunk_size=chunk_size):
				fd.write(chunk)
		return save_path

	def newdown(self, save_path, accept="application/vnd.github+json"):
		response = requests.get(self.furl, headers={
			"Accept": accept,
			"Authorization":"Bearer {}".format(self.token)
		}, timeout=50, verify=self.verify)
		if response.status_code == 200:
			with open(save_path, 'wb') as f:
				f.write(response.content)
			return save_path
		else:
			print(response.content)
		return None

	def pull(self, repo,asset_check=None, accept="application/vnd.github+json", print_info=False, save_path=None, chunk_size=128):
		download_url = self.find(repo,asset_check, accept, print_info)
		if download_url:
			print(download_url)
			return self.newdown(download_url['url'], save_path, accept)#, save_path, chunk_size, verify, accept, auth)
		return None

class GRepo(object):
	"""
	Sample usage:
	with GRepo("https://github.com/owner/repo","v1","hash") as repo:
		os.path.exists(repo.reponame) #TRUE
	"""
	def __init__(self, repo: str, tag: str = None, commit: str = None, delete: bool = True, jsonl_file: str = None, git_base_string="git"):
		self.repo = githuburl(repo,tag=tag,commit=commit)
		self.inipath = os.path.abspath(os.curdir)
		self.delete = delete
		self.jsonl_file = jsonl_file
		self.git_base_string = git_base_string
		self.tag = mystring.string(tag)
		self.commit = mystring.string(commit).trim
		self.cloneurl = None
		self.webarchive_url_base = None
		self.zip_url_base = None
		self.login = False
		self.cloned = False

		branches, main_branch = [], None
		with contextlib.suppress(Exception):
			#https://docs.github.com/en/rest/branches/branches#list-branches
			for branch in requests.get(f"https://api.github.com/repos/{self.repo.core}/branches").json():
				branches += [branch['name']]
				if branch['name'].lower() in ['main','master'] and main_branch is None:
					main_branch = "heads/"+branch['name']
		if main_branch is None and len(branches) > 0:
			main_branch = "heads/"+branches[0]

	def login(self, token):
		os.environ['GH_TOKEN'] = token
		try:
			with open("~/.bashrc", "a+") as writer:
				writer.write("GH_TOKEN={0}".format(token))
		except:
			pass

	def get_date_from_repo_commit(self, headers={}):
		return self.get_date_from_commit_url("https://api.github.com/repos/{0}/commits/{1}".format(self.repo.core, self.commit, headers))

	def get_date_from_commit_url(self, headers={}):
		req = requests.get(self.furl, headers=headers).json()
		return datetime.datetime.strptime(req['commit']['committer']['date'], "%Y-%m-%dT%H:%M:%SZ")

	def get_commits_of_repo(self, from_date=None, to_date=None, headers={}):
		params = []
		if from_date:
			params += ["since={0}".format(from_date)]
		if from_date:
			params += ["until={0}".format(to_date)]
		request_url = "https://api.github.com/repos/{0}/commits?{1}".format(self.repo.core, '&'.join(params))
		req = requests.get(request_url, headers=headers)
		return req.json()

	def __clone(self):
		if not self.cloned: #not os.path.exists(self.reponame) and self.url.startswith("https://github.com/"):
			print("Waiting between scanning projects to ensure GitHub Doesn't get angry")
			ut.wait_for(5)
			cmd = "{} clone {}".format(self.git_base_string,self.url)#,'--' if 'gh' in self.git_base_string.lower() else '',self.cloneurl)
			print(cmd);ut.run(cmd)

			if ut.is_not_empty(self.commit):
				with mystring.foldentre()(self.reponame):
					print(os.path.abspath(os.curdir))
					cmd = f"git checkout {self.commit}"
					print(cmd);ut.run(cmd)
			self.cloned = True

	def __enter__(self):
		self.__clone()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		try:
			if self.delete:
				print("Deleting the file")
				ut.run(f"yes|rm -r {self.reponame}")
		except Exception as e:
			print(f"Issue with deleting the file: {e}")
		return self

	@property
	def zip_url(self):
		if self.zip_url_base is not None:
			return self.zip_url_base

		if self.gh_api is not None:
			self.zip_url_base = self.gh_api.commit_zip_url
			return self.zip_url_base

		if not self.url.startswith("https://github.com/"):
			print("NONE")
			return None

		# url_builder = "https://web.archive.org/save/" + repo.url + "/archive"
		url_builder = self.url + "/archive"
		if not mystring.string(self.commit).empty:
			# https://github.com/owner/reponame/archive/hash.zip
			url_builder += f"/{self.commit}.zip"

		if not mystring.string(self.commit).empty:
			# https://web.archive.org/save/https://github.com/owner/reponame/archive/refs/heads/tag.zip
			url_builder += f"/refs/heads"
			if not mystring.string(self.tag).empty:
				for base_branch in ['master', 'main']:
					temp_url = url_builder + f"/{base_branch}.zip"
					if live_link(temp_url):
						url_builder = temp_url
						break
					time.sleep(4)
			elif not mystring.string(self.tag).empty:
				url_builder += f"/{self.tag}.zip"

		self.zip_url_base = url_builder
		return self.zip_url_base

	@property
	def webarchive_save_url(self):
		if self.webarchive_url_base is None:
			self.webarchive_url_base = "https://web.archive.org/save/" + str(self.zip_url)
		return self.webarchive_url_base

	@property
	def webarchive(self):
		import time
		save_url = "NotAvailable"
		url = self.zip_url
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

		return save_url

	@property
	def info(self):
		return {
			'URL':self.url,
			'RepoName':self.reponame,
			'Commit':self.commit or self.gh_api.commit,
			'FullUrl':self.full_url,
			'CloneUrl':self.cloneurl,
			'ZipUrl':self.zip_url,
			'WebArchiveSaveUrl':self.webarchive_save_url
		}

	@property
	def jsonl(self):
		try:
			with open(self.jsonl_file, 'w+') as writer:
				writer.write(str(json.dumps({**{'header':True},**self.info})) + "\n")
				self.__clone()
				for root, directories, filenames in os.walk(self.reponame):
					for filename in filenames:
						foil = os.path.join(root, filename)
						ext = foil.split('.')[-1].lower()

						if "/.git/" not in foil and (self.exclude_extensions is None or ext not in self.exclude_extensions):
							try:
								writer.write(mystring.foil(foil).structured()+ "\n")
							except Exception as e:
								print(">: "+str(e))
								pass
		except Exception as e:
			print(f"Issue with creating the jsonl file: {e}")

		return self.jsonl_file

	@property
	def jsonl_contents(self):
		contents = []
		try:
			self.__clone()
			for root, directories, filenames in os.walk(self.reponame):
				for filename in filenames:
					foil = os.path.join(root, filename)
					ext = foil.split('.')[-1].lower()

					if "/.git/" not in foil and (self.exclude_extensions is None or ext not in self.exclude_extensions):
						try:
							contents += [
								mystring.foil(foil).structured()
							]
						except Exception as e:
							print(">: "+str(e))
							pass
		except Exception as e:
			print(f"Issue with creating the jsonl file: {e}")

		return contents

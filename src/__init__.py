import os, sys, subprocess, json, base64, hashlib
from waybackpy import WaybackMachineSaveAPI as checkpoint

"""
Reference/Aide: https://github.com/franceme/Scripts/blob/master/funbelts/__init__.py

"""

try:
    from cryptography.fernet import Fernet
except:
    os.system(str(sys.executable) + " -m pip install cryptography")
    from cryptography.fernet import Fernet

def live_link(url:str):
    response = False
    try:
        response_type = requests.get(url)
        response = response_type.status_code < 400
        time.sleep(2)
    except:
        pass
    return response

def save_link(url:str):
    save_url = None
    if live_link(url):
        saver = checkpoint(url, user_agent="Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0")
        try:
            save_url = saver.save()
            time.sleep(10)
            if save_url is None:
                save_url = saver.saved_archive
        except Exception as e:
            print(f"Issue with saving the link {url}: {e}")
            pass
    return save_url

def hash(file):
	sha512 = hashlib.sha512()
	with open(file,'rb') as f:
		while True:
			data = f.read(65536)
			if not data:
				break
			sha512.update(data)
	return str(sha512.hexdigest())

def str_to_base64(string, password:bool=False, encoding:str='utf-8'):
    current = base64.b64encode(string.encode(encoding))
    if password:
        key = Fernet.generate_key()
        current = Fernet(key).encrypt(current)
        key = key.decode(encoding)
    return (current.decode(encoding), key or None)

def base64_to_str(b64, password:str=None, encoding:str='utf-8'):
     if password:
         current = Fernet(password.encode(encoding)).decrypt(b64.encode(encoding)).decode(encoding)
     return base64.b64decode(current or b64).decode(encoding)

class GRepo(object):
    """
    Sample usage:
    with GRepo("https://github.com/owner/repo","v1","hash") as repo:
        os.path.exists(repo.reponame) #TRUE
    """
    def __init__(self, reponame:str, repo:str, tag:str=None, commit:str=None,delete:bool=True,silent:bool=True,local_dir:bool=False,jsonl_file:str=None):
        self.delete = delete
        self.tag = None
        self.commit = commit or None
        self.reponame = reponame
        self.cloneurl = None
        self.jsonl = jsonl_file
        if local_dir:
            self.url = "file://" + self.reponame
            self.full_url = repo
        else:
            repo = repo.replace('http://','https://')
            self.url = repo
            self.full_url = repo

            self.cloneurl = "git clone --depth 1"
            if is_not_empty(tag):
                self.tag = tag
                self.cloneurl += f" --branch {tag}"
                self.full_url += "<b>" + tag

            if is_not_empty(self.commit):
                self.full_url += "<#>" + self.commit

    def __enter__(self):
        if not os.path.exists(self.reponame) and self.url.startswith("https://github.com/"):
            self.out(f"Waiting between scanning projects to ensure GitHub Doesn't get angry")
            wait_for(5, silent=not self.print)
            run(f"{self.cloneurl} {self.url}", display=self.print)

            if is_not_empty(self.commit):
                run(f"cd {self.reponame} && git reset --hard {self.commit} && cd ../", display=self.print)

        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.delete:
                if self.print:
                    self.out("Deleting the file")

                run(f"yes|rm -r {self.reponame}", display=self.print)
        except Exception as e:
            if self.print:
                self.out(f"Issue with deleting the file: {e}")

        try:
            if self.write_statistics:
                foil_out = ".github_stats.csv"
                make_header = not os.path.exists(foil_out)

                with open(foil_out,"a+") as writer:
                    if make_header:
                        writer.write("RepoName,RepoURL,RepoTopics,Stars\n")
                    writer.write(','.join( [self.reponame,self.GRepo.url, ':'.join(list(self.GRepo.get_topics())),str(self.GRepo.stargazers_count)] ) + "\n")
        except Exception as e:
            if self.print:
                self.out(f"Issue with writing the statistics: {e}")

        if self.archive_log:
            with open(self.archive_log,"a+") as writer:
                writer.write(f"{self.reponame},{save_link(self.url)}\n")

        return self
    def get_info(self):
        return {
            'URL':self.url,
            'RepoName':self.reponame,
            'Commit':self.commit,
            'FullUrl':self.full_url,
            'CloneUrl':self.cloneurl,
            'datetime':timr.utcnow().strftime('%Y%m%dT%H%M%S')
        }
    def get_info_frame(self):
        return dyct_frame(self.get_info())

    @property
    def zip_url(self):
        if self.zip_url_base is not None:
            return zip_url_base

        if not self.url.startswith("https://github.com/"):
            print("NONE")
            return None

        # url_builder = "https://web.archive.org/save/" + repo.url + "/archive"
        url_builder = self.url + "/archive"
        if is_not_empty(self.commit):
            # https://github.com/owner/reponame/archive/hash.zip
            url_builder += f"/{self.commit}.zip"

        if not is_not_empty(self.commit):
            # https://web.archive.org/save/https://github.com/owner/reponame/archive/refs/heads/tag.zip
            url_builder += f"/refs/heads"
            if not is_not_empty(self.tag):
                for base_branch in ['master', 'main']:
                    temp_url = url_builder + f"/{base_branch}.zip"
                    if live_link(temp_url):
                        url_builder = temp_url
                        break
                    time.sleep(4)
            elif is_not_empty(self.tag):
                url_builder += f"/{self.tag}.zip"

        self.zip_url_base = url_builder
        return self.zip_url_base

    def save_link(self):
        return save_link(self.zip_url)

class GitHubRepo(GRepo):
    def __init__(self, repo:str, tag:str=None, commit:str=None,delete:bool=True,silent:bool=True,write_statistics:bool=False,local_dir:bool=False,logfile:str=".run_logs.txt"):
        reponame = repo.replace("http://", "https://").replace('https://github.com/','').split('/')[-1].replace('.git','')
        super().__init__(reponame, repo, tag, commit, delete, silent, write_statistics, local_dir, logfile)
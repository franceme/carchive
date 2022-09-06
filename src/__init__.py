import os, sys, requests, json, base64, hashlib, time, contextlib, funbelts as ut
from waybackpy import WaybackMachineSaveAPI as checkpoint

"""
Reference/Aide: https://github.com/franceme/Scripts/blob/master/funbelts/__init__.py
"""

try:
    from cryptography.fernet import Fernet
except Exception:
    os.system(f"{str(sys.executable)} -m pip install cryptography")
    from cryptography.fernet import Fernet

def live_link(url: str):
    response = False
    with contextlib.suppress(Exception):
        response_type = requests.get(url)
        response = response_type.status_code < 400
        time.sleep(2)
    return response

def hash(file):
    sha512 = hashlib.sha512()
    with open(file, 'rb') as f:
        while True:
            if data := f.read(65536):
                sha512.update(data)
            else:
                break
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
    def __init__(self, repo: str, tag: str = None, commit: str = None, delete: bool = True, silent: bool = True, local_dir: bool = False, jsonl_file: str = None, huggingface_jsonql: bool = False):
        self.delete = delete
        self.tag = None
        self.commit = commit or None
        self.cloneurl = None
        self.jsonl = jsonl_file
        self.repo = repo

        if local_dir:
            self.url = f"file://{self.repo}"
            self.full_url = repo
        else:
            repo = repo.replace('http://', 'https://')
            self.url = repo
            self.full_url = repo
            self.cloneurl = "git clone --depth 1"
            if ut.is_not_empty(tag):
                self.tag = tag
                self.cloneurl += f" --branch {tag}"
                self.full_url += "<b>" + tag
            if ut.is_not_empty(self.commit):
                self.full_url += "<#>" + self.commit
        
        self.reponame = self.url.split('/')[-1].replace('.git','')

    def __enter__(self):
        if not os.path.exists(self.reponame) and self.url.startswith("https://github.com/"):
            print("Waiting between scanning projects to ensure GitHub Doesn't get angry")
            ut.wait_for(5)
            ut.run(f"{self.cloneurl} {self.url}")

            if ut.is_not_empty(self.commit):
                ut.run(f"cd {self.reponame} && git reset --hard {self.commit} && cd ../")

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
    def file_to_base_64(self, file: str, password: bool = False):
        with open(file,'r') as reader:
            contents = reader.readlines()
        return str_to_base64(contents, password)

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

    @property
    def webarchive(self):
        save_url = None
        url = self.zip_url
        if live_link(url):
            saver = checkpoint(url, user_agent="Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0")

            try:
                save_url = saver.save()
                time.sleep(10)
                if save_url is None:
                    save_url = saver.saved_archive
            except Exception as e:
                print(f"Issue with saving the link {url}: {e}")
                save_url = e
        return save_url
    
    @property
    def jsonl(self):
        jsonl_file = "stub.jsonl"
        with open(jsonl_file, 'w') as writer:
            for root, directories, filenames in os.walk(self.reponame):
                for filename in filenames:
                        foil = os.path.join(root, filename)

                        current_file_info = {
                            'file':foil,
                            'hash':hash(foil),
                            'base64':self.file_to_base_64(foil)
                        }

                        writer.write(f"{json.dump(current_file_info)}\n")
        return jsonl_file

class GitHubRepo(GRepo):
    def __init__(self, repo:str, tag:str=None, commit:str=None,delete:bool=True,silent:bool=True,write_statistics:bool=False,local_dir:bool=False,logfile:str=".run_logs.txt"):
        reponame = repo.replace("http://", "https://").replace('https://github.com/','').split('/')[-1].replace('.git','')
        super().__init__(reponame, repo, tag, commit, delete, silent, write_statistics, local_dir, logfile)
import os, requests, json, base64, hashlib, time, contextlib, funbelts as ut, requests, sys, datetime
try:
    from ghapi.all import GhApi
except:
    os.system(f"{sys.executable} -m pip install ghapi")
from waybackpy import WaybackMachineSaveAPI as checkpoint

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

def str_to_base64(string, encoding:str='utf-8'):
    try:
        return base64.b64encode(string.encode(encoding)).decode(encoding)
    except Exception as e:
        print(e)
        return None

def base64_to_str(b64, encoding:str='utf-8'):
     return base64.b64decode(b64).decode(encoding)

def file_to_base_64(file: str):
    with open(file,'r') as reader:
        contents = reader.readlines()
    return str_to_base64(''.join(contents))

def base_64_to_file(contents,file=None):
    string_contents = base64_to_str(contents)
    if file:
        with open(file,'w+') as writer:
            writer.write(string_contents)
        return 'true'
    else:
        return string_contents

def get_date_from_repo_commit(repo, commit):    
    return get_date_from_commit_url("https://api.github.com/repos/{0}/commits/{1}".format(repo,commit))
    
def get_date_from_commit_url(url):
    req = requests.get(url).json()
    return datetime.datetime.strptime(req['commit']['committer']['date'], "%Y-%m-%dT%H:%M:%SZ")

class GRepo(object):
    """
    Sample usage:
    with GRepo("https://github.com/owner/repo","v1","hash") as repo:
        os.path.exists(repo.reponame) #TRUE
    """
    def __init__(self, repo: str, tag: str = None, commit: str = None, delete: bool = True, local_dir: bool = False, jsonl_file: str = None, exclude_extensions: list = [],self_archive_wait = 5*60, git_base_string="git"):
        self.inipath = os.path.abspath(os.curdir)
        self.delete = delete
        self.tag = None
        self.commit = commit or None
        self.cloneurl = None
        self.jsonl_file = jsonl_file
        self.repo = repo
        self.exclude_extensions = exclude_extensions
        self.self_archive_wait=self_archive_wait
        self.git_base_string = git_base_string
        self.local_dir = None

        if local_dir:
            self.url = f"file://{self.repo}"
            self.full_url = repo
            self.api = None
            self.local_dir = local_dir
        else:
            repo = repo.replace('http://', 'https://').replace('.git','')
            if repo.endswith("/"):
                repo = repo[:-1]
            self.local_dir = str(repo.split("/")[-1])
            self.url = repo
            self.full_url = repo
            #self.cloneurl = "--depth 1"
            if ut.is_not_empty(tag):
                self.tag = tag
                self.cloneurl += f" --branch {tag}"
                self.full_url += f"<b>{tag}"
            if ut.is_not_empty(self.commit):
                self.full_url += f"<#>{self.commit}"

            gh_api = GhApi()
            splitzies = self.url.replace('https://github.com/','').split('/')
            owner,corerepo = splitzies[0], splitzies[1]

            branches = []
            main_branch = None
            try:
                #https://docs.github.com/en/rest/branches/branches#list-branches
                for branch in requests.get(f"https://api.github.com/repos/{owner}/{corerepo}/branches").json():
                    branches += [branch['name']]
                    if branch['name'] in ['main','master'] and main_branch is None:
                        main_branch = "heads/"+branch['name']
            except Exception as e:
                print(f"Error getting branches: {e}")
                pass

            if main_branch is None and len(branches) > 0:
                main_branch = "heads/"+branches[0]

            try:
                self.gh_api = gh_api.git.get_ref(owner=owner, repo=corerepo, ref=main_branch)
            except Exception as e:
                self.gh_api = None
                print(e)
            if self.gh_api is not None:
                self.gh_api.owner = owner
                self.gh_api.repo = corerepo
                self.gh_api.commit = self.gh_api['object']['sha']
                self.gh_api.commit_url = '/'.join([
                    "https://github.com",
                    self.gh_api.owner,
                    self.gh_api.repo,
                    "tree",
                    self.gh_api.commit
                ])
                self.gh_api.commit_zip_url = '/'.join([
                    "https://github.com",
                    self.gh_api.owner,
                    self.gh_api.repo,
                    "archive",
                    str(self.gh_api.commit)+".zip"
                ])

        if self.url.endswith("/"):
            self.url = self.url[:-1]
        self.reponame = self.url.split('/')[-1].replace('.git','')
        self.webarchive_url_base = None
        self.zip_url_base = None
        self.reponame = self.reponame or repo.split('/')[-1]
        self.cloned = False


    def __clone(self):
        if not self.cloned: #not os.path.exists(self.reponame) and self.url.startswith("https://github.com/"):
            print("Waiting between scanning projects to ensure GitHub Doesn't get angry")
            ut.wait_for(5)
            cmd = "{} clone {}".format(self.git_base_string,self.url)#,'--' if 'gh' in self.git_base_string.lower() else '',self.cloneurl)
            print(cmd);ut.run(cmd)

            if ut.is_not_empty(self.commit):
                os.chdir(self.reponame)
                #cmd = f"cd {self.reponame} && git checkout {self.commit} && cd ../"
                print(os.path.abspath(os.curdir))
                cmd = f"git checkout {self.commit}"
                print(cmd);ut.run(cmd)
                os.chdir(self.inipath)
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
        if ut.is_not_empty(self.commit):
            # https://github.com/owner/reponame/archive/hash.zip
            url_builder += f"/{self.commit}.zip"

        if not ut.is_not_empty(self.commit):
            # https://web.archive.org/save/https://github.com/owner/reponame/archive/refs/heads/tag.zip
            url_builder += f"/refs/heads"
            if not ut.is_not_empty(self.tag):
                for base_branch in ['master', 'main']:
                    temp_url = url_builder + f"/{base_branch}.zip"
                    if live_link(temp_url):
                        url_builder = temp_url
                        break
                    time.sleep(4)
            elif ut.is_not_empty(self.tag):
                url_builder += f"/{self.tag}.zip"

        self.zip_url_base = url_builder
        return self.zip_url_base

    @property
    def webarchive_save_url(self):
        if self.webarchive_url_base is not None:
            return self.webarchive_url_base

        self.webarchive_url_base = "https://web.archive.org/save/" + str(self.zip_url)
        return self.webarchive_url_base

    @property
    def webarchive(self):
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
        
        time.sleep(self.self_archive_wait)
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

    def is_bin_file(self,foil):
        #https://stackoverflow.com/questions/898669/how-can-i-detect-if-a-file-is-binary-non-text-in-python
        textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
        is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
        return is_binary_string(open(foil, 'rb').read(1024))

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
                                    try:
                                        mini = file_to_base_64(foil)
                                    except:
                                        mini = None
                                    current_file_info = {
                                        'header':False,
                                        'file':foil,
                                        'hash':hash(foil),
                                        'base64':mini
                                    }
                                    writer.write(str(json.dumps(current_file_info)) + "\n")
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
                            try:
                                mini = file_to_base_64(foil)
                            except:
                                mini = None


                            current_file_info = {
                                'header':False,
                                'file':foil,
                                'hash':hash(foil),
                                'base64':mini
                            }

                            contents += [
                                str(json.dumps(current_file_info))
                            ]

                        except Exception as e:
                            print(">: "+str(e))
                            pass
        except Exception as e:
            print(f"Issue with creating the jsonl file: {e}")

        return contents
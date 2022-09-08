import os, requests, json, base64, hashlib, time, contextlib, funbelts as ut
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

class GRepo(object):
    """
    Sample usage:
    with GRepo("https://github.com/owner/repo","v1","hash") as repo:
        os.path.exists(repo.reponame) #TRUE
    """
    def __init__(self, repo: str, tag: str = None, commit: str = None, delete: bool = True, local_dir: bool = False, jsonl_file: str = None, huggingface_obj: ut.HuggingFace = None, exclude_extensions: list = None):
        self.delete = delete
        self.tag = None
        self.commit = commit or None
        self.cloneurl = None
        self.jsonl_file = jsonl_file
        self.repo = repo
        self.huggerface = huggingface_obj
        self.exclude_extensions = exclude_extensions

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
                self.full_url += f"<b>{tag}"
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
    
    def file_to_base_64(self, file: str):
        with open(file,'r') as reader:
            contents = reader.readlines()
        return str_to_base64(''.join(contents))

    @property
    def info(self):
        return {
            'URL':self.url,
            'RepoName':self.reponame,
            'Commit':self.commit,
            'FullUrl':self.full_url,
            'CloneUrl':self.cloneurl
        }

    @property
    def zip_url(self):
        if self.zip_url_base is not None:
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
        if os.path.exists(self.jsonl_file):
            os.remove(self.jsonl_file)

        try:
            with open(self.jsonl_file, 'w+') as writer:
                writer.write(str(json.dumps({**{'header':True},**self.info})) + "\n")

                for root, directories, filenames in os.walk(self.reponame):
                    for filename in filenames:
                            foil = os.path.join(root, filename)
                            ext = foil.split('.')[-1].lower()

                            if self.exclude_extensions is None or ext not in self.exclude_extensions:

                                mini = self.file_to_base_64(foil)
                                current_file_info = {
                                    'header':False,
                                    'file':foil,
                                    'hash':hash(foil),
                                    'base64':mini
                                }
                                writer.write(f"{json.dumps(current_file_info)}\n")
        except Exception as e:
            print(f"Issue with creating the jsonl file: {e}")

        if os.path.exists(self.jsonl_file) and self.huggerface is not None:
            with self.huggerface as hf:
                hf[self.jsonl_file] = self.jsonl_file

        return self.jsonl_file
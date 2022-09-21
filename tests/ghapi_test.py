import unittest, os, sys, json

sys.path.append('../')
try:
    from carchive import GRepo
except:
    from carchive.carchive import GRepo

smpl = [
    'https://github.com/franceme/WaveNetExploration'
]
latest_hash = [
    'e179d1b095c2549864e2acd0adbcc87096bc0276'
]

def content(file):
    with open(file, 'r') as f:
        return f.readlines()

def content_string(file):
    return ''.join(content(file))

class TestGhaPiCore(unittest.TestCase):

    def test_base_ghapi(self):
        repo = GRepo(smpl[0])
        self.assertTrue(repo.gh_api is not None)
        self.assertTrue(repo.gh_api.owner is not None)
        self.assertTrue(repo.gh_api.repo is not None)
    
    def test_ghapi_get_commit(self):
        repo = GRepo(smpl[0])
        self.assertTrue(repo.gh_api is not None)
        self.assertTrue(repo.gh_api.owner is not None)
        self.assertTrue(repo.gh_api.repo is not None)
        self.assertTrue(repo.gh_api.commit is not None)
        self.assertEquals(repo.gh_api.commit, latest_hash[0])

        self.assertEquals("https://github.com/franceme/WaveNetExploration/tree/e179d1b095c2549864e2acd0adbcc87096bc0276", repo.gh_api.commit_url)
        print(repo.gh_api.commit_url)
        self.assertEquals("https://github.com/franceme/WaveNetExploration/archive/e179d1b095c2549864e2acd0adbcc87096bc0276.zip",repo.gh_api.commit_zip_url)

        #https://web.archive.org/save/https://google.com/test
        self.assertEquals("https://web.archive.org/save/https://github.com/franceme/WaveNetExploration/archive/e179d1b095c2549864e2acd0adbcc87096bc0276.zip",repo.webarchive_save_url)
    
    def test_ghapi_jsonl(self):
        repo = GRepo(smpl[0],jsonl_file="sample.jsonl")
        try:
            os.remove(repo.jsonl)
        except:
            pass
        self.assertTrue(repo.gh_api is not None)
        self.assertTrue(repo.gh_api.owner is not None)
        self.assertTrue(repo.gh_api.repo is not None)
        self.assertTrue(repo.gh_api.commit is not None)
        self.assertEquals(repo.gh_api.commit, latest_hash[0])

        self.assertTrue(os.path.exists(repo.jsonl))
        with open(repo.jsonl,'r') as f:
            lines = f.readlines()
            self.assertTrue(len(lines) > 2)
    
    def test_ghapi_jsonl(self):
        repo = GRepo(smpl[0])
        print(repo.webarchive)



if __name__ == '__main__':
    unittest.main()
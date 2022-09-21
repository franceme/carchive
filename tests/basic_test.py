import unittest, os, sys, json, funbelts as ut

sys.path.append('../')
import carchive

smpl = [
    'https://github.com/franceme/WaveNetExploration'
]

def content(file):
    with open(file, 'r') as f:
        return f.readlines()

def content_string(file):
    return ''.join(content(file))

class TestStringMethods(unittest.TestCase):

    def test_sample_cloning(self):
        with carchive.GRepo(smpl[0]) as repo:
            self.assertTrue(os.path.exists(repo.reponame))

            current_file = repo.jsonl
            self.assertTrue(os.path.exists(current_file))

            with ut.ephfile(current_file) as eph:
                self.assertTrue(len(content(eph())) > 5)

    def test_verify_reconstruction(self):
        with carchive.GRepo(smpl[0]) as repo:
            self.assertTrue(os.path.exists(repo.reponame))

            current_file = repo.jsonl
            self.assertTrue(os.path.exists(current_file))
            self.assertTrue(len(content(current_file)) > 2)

            with ut.ephfile(current_file) as eph:
                with open(eph(),'r') as f:
                    for line in f:
                        try:
                            current_contents = json.loads(line)
                            self.assertTrue(os.path.exists(current_contents['file']))

                            real_content = content_string(current_contents['file'])
                            unhashed_content = carchive.base64_to_str(current_contents['base64'])

                            self.assertEqual(unhashed_content, real_content)
                            print(f"""{current_contents['file']} {'is' if real_content == unhashed_content else ''} same""")
                        except Exception as e:
                            print(f"Error: {e}")


if __name__ == '__main__':
    unittest.main()
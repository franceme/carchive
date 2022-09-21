import os,sys
from ghapi.all import GhApi
api = GhApi()

def get_ref(owner,repo):
    try:
        base = api.git.get_ref(owner=owner, repo=repo, ref='heads/main')
    except:
        try:
            base = api.git.get_ref(owner=owner, repo=repo, ref='heads/master')
        except:
            print("No master or main branch found")
            base = None
    if base is not None:
        base.owner = owner
        base.repo = repo

    return base

base = get_ref('fastai','fastcore')
print(base['object']['sha'])
print(base.owner)
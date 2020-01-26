from django.http import JsonResponse
from django.core.files import File
import os, os.path

def index(request, address):
    print('request: ' + str(request))
    print('address: ' + str(address))
    s = ''
    path = os.path.join('../../acm-problems/problems', address)
    response = {}
    response['content']=None
    response['content_extension']=None
    response['directories']=[]
    # add all present directories and files
    # print(path)
    # print(os.path.isdir(path))
    if os.path.isdir(path):
        dirs = os.listdir(path)
        dirs.sort()
        if 'index.md' in dirs:
            dirs.remove('index.md') # hide index, it will be managed separately
        response['directories']=dirs
    # problem category directory
    try:
        with open(os.path.join(path, 'index.md'), 'r') as f:
            f = File(f)
            s = f.read()
            response['content']=s
            response['content_extension']='.md'
    except (NotADirectoryError, FileNotFoundError): pass
    try:
        print(os.path.isfile(path))
        if os.path.isfile(path):
            with open(os.path.join(path), 'r') as f:
                f = File(f)
                s = f.read()
                response['content']=s
                filename, extension = os.path.splitext(path)
                response['content_extension']=extension
    except FileNotFoundError: pass
    # problem definition

    print('response: ' + str(response))
    return JsonResponse(response)

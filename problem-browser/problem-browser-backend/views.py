from django.http import JsonResponse
from django.core.files import File
import os, os.path
import glob

repo_path = '../../acm-problems/problems'

def check_file(path: str) -> []:
    extensions = ['.c', '.cpp', '.py', '.java']
    for ext in extensions:
        filepath = path + ext
        if os.path.isfile(filepath):
            return [filepath]
    return []

def retrieve(what: str) -> []:
    result = check_file(what)
    if len(result) != 0:
        return result
    elif os.path.isdir(what):
        return os.listdir(what)
    return []

def rename(request):
    rename_from = os.path.join(repo_path, request.GET.get('from'))
    rename_to = os.path.join(repo_path, request.GET.get('to'))
    response = {}
    if os.path.exists(rename_to):
        return JsonResponse({'error': 'target location is not empty'})
    if os.path.isdir(rename_from) or os.path.isfile(rename_from):
        os.rename(rename_from, rename_to)
    return JsonResponse(response)

def search(request):
    query = request.GET.get('query', '')
    response = {}
    found_entries = glob.glob(os.path.join(repo_path, '**', '*' + query + '*'), recursive=True)
    response['found'] = found_entries
    return JsonResponse(response)

def get_directory(request, address):
    print('request: ' + str(request))
    print('address: ' + str(address))
    s = ''
    path = os.path.join(repo_path, address)
    response = {}
    response['content']=None
    response['content_extension']=None
    response['directories']=[]

    # add all present directories and files
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

    # problem definition
    try:
        with open(os.path.join(path, 'def.toml'), 'r') as f:
            f = File(f)
            s = f.read()
            response['parts'] = {
                    'gen': retrieve(os.path.join(path, 'gen')),
                    'val': retrieve(os.path.join(path, 'val')),
                    'jud': retrieve(os.path.join(path, 'jud')),
                    'chk': retrieve(os.path.join(path, 'chk')),
                    'sol': retrieve(os.path.join(path, 'sol')),
                    'pic': retrieve(os.path.join(path, 'pic')),
                    }
    except (NotADirectoryError, FileNotFoundError): pass

    # is some file
    try:
        if os.path.isfile(path):
            with open(os.path.join(path), 'r') as f:
                f = File(f)
                s = f.read()
                response['content'] = s
                filename, extension = os.path.splitext(path)
                response['content_extension'] = extension
    except FileNotFoundError: pass

    print('response: ' + str(response))
    return JsonResponse(response)

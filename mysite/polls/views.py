from django.http import JsonResponse
from django.core.files import File
import os, os.path

def index(request):
    s = ''
    path = '../../acm-problems/problems/arrays/'
    response = {}
    with open(os.path.join(path, 'arrays.md'), 'r') as f:
        dirs = os.listdir(path)
        f = File(f)
        s = f.read()
        response['description']=s
        response['dirs']=dirs
    return JsonResponse(response)

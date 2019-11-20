from django.shortcuts import render, HttpResponse
from django_webssh.settings import TMP_DIR
from .utils import unique
import os


# Create your views here.
def index(request):
    return render(request, 'index.html', {})


def upload_ssh_key(request):
    if request.method == 'POST':
        pkey = request.FILES.get('pkey')
        if not pkey:
            return HttpResponse('')
        ssh_key = pkey.read().decode('utf-8')
        filename = unique()
        ssh_key_path = os.path.join(TMP_DIR, filename)
        if not os.path.isfile(ssh_key_path):
            with open(ssh_key_path, 'w') as f:
                f.write(ssh_key)
        return HttpResponse(filename)

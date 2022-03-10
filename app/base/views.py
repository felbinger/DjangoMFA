import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View


class Home(View):
    @method_decorator(login_required)
    def get(self, request: HttpRequest):
        return render(request, 'home.html')


class Settings(View):
    @method_decorator(login_required)
    def get(self, request: HttpRequest, *args, **kwargs):
        return render(request, 'profile.html', context={
            "user": request.user
        })

    @method_decorator(login_required)
    def post(self, request: HttpRequest, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(json.dumps({}), status=400)

        if 'firstName' in data:
            request.user.first_name = data.get('firstName')
        if 'lastName' in data:
            request.user.last_name = data.get('lastName')
        if 'email' in data:
            request.user.email = data.get('email')

        request.user.save()

        return redirect(reverse('base:settings'))

from django.conf.urls import url

from . import views

app_name = "qr"
urlpatterns = [
    url(r"^$", views.signin, name="login"),
    url(r'^logout/$', views.signout, name='logout'),
    url(r"^home/$", views.home, name="home"),
    url(r'^curso/(?P<id_curso>[0-9]+)/$', views.curso, name='curso'),
]
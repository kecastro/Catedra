from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import locale

from .models import *

# Create your views here.
def signin(request):

    if request.user.is_authenticated:
        return redirect("qr:home")

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if not request.POST.get("remember", None):
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)
                return redirect("qr:home")
            else:
                return render(request, "qr/login.html", {"error_message": "Cuenta suspendida"})
        else:
            return render(request, "qr/login.html", {"error_message": "Usuario y/o contraseña incorrectos"})
    return render(request, "qr/login.html")

def signout(request):
    logout(request)
    return HttpResponseRedirect(reverse('qr:login'))

def home(request):

    if not request.user.is_authenticated():
        return redirect('qr:login')

    context = {
        "cursos": Curso.objects.filter(monitores=request.user),
    }

    return render(request, "qr/home.html", context)

def curso(request, id_curso):

    if not request.user.is_authenticated():
        return redirect('qr:login')

    curso = get_object_or_404(Curso, pk=id_curso)

    if request.user not in curso.monitores.all():
        return redirect('qr:home')

    dateNow = datetime.now(tz=timezone.utc)
    previous = curso.clases.all().filter(fin__lt=dateNow).order_by('fin').reverse()
    next = curso.clases.all().filter(inicio__gt=dateNow)
    now = curso.clases.all().filter(Q(inicio__lte=dateNow)&Q(fin__gt=dateNow))

    context = {
        "curso" : curso,
        "previous": previous,
        "next": next,
        "now": now
    }
    return render(request, "qr/curso.html", context)

def clase(request,id_curso, id_clase):

    if not request.user.is_authenticated():
        return redirect('qr:login')



    curso = get_object_or_404(Curso, pk=id_curso)
    clase = get_object_or_404(Clase, pk=id_clase)
    monitor = get_object_or_404(User, pk=request.user.id)
    asistencias = Asistencia.objects.filter(Q(fecha__gt=clase.inicio) & Q(fecha__lt=clase.fin) & Q(curso=curso))

    if not monitor in curso.monitores.all():
        return redirect('qr:home')

    #locale.setlocale(locale.LC_ALL, "es_ES.UTF-8")

    currentDate = datetime.now() + timedelta(hours=5)
    formato_local = "%d de %B del %Y a las %I:%M"
    if request.user.is_authenticated():
        if request.method == "POST":
            qr_text = request.body.decode("utf-8").split("?")
            estudiante = get_object_or_404(Estudiante, identificacion=qr_text[0])
            response = {}
            print(currentDate.hour,"|",clase.fin.hour,"-",currentDate.minute,"|",clase.fin.minute)
            if len(Asistencia.objects.filter(Q(fecha__gt=clase.inicio) & Q(fecha__lt=clase.fin) & Q(curso=curso) & Q(estudiante=estudiante)))>0:
                response["status"] = -201
                response["message"] = "La persona ya tiene una asistencia creada"
                print("Asistencia rechazada: la persona tiene asistencia")
            elif currentDate.hour>=clase.fin.hour and currentDate.minute>clase.fin.minute:
                response["status"] = -201
                response["message"] = "El tiempo ha finalizado. Ya no se puede registrar"
                print("El tiempo ha finalizado. Ya no se puede registrar")
            elif curso in estudiante.cursos.all() and curso.identificador == int(qr_text[1]) and monitor in curso.monitores.all():
                asistencia = Asistencia.objects.create(curso=curso, estudiante=estudiante, monitor=monitor, fecha=datetime.now(tz=timezone.utc))
                response["status"] = 200
                response["message"] = "Asistencia tomada con exito"
                response["asistencia"] = {"nombre": asistencia.estudiante.nombre, "documento": asistencia.estudiante.identificacion}
                response["fecha"] = currentDate.strftime(formato_local)
                print("Asistencia tomada")
            else:
                response["status"] = -200
                response["message"] = "No se puede tomar la asistencia al estudiante"
                print("Error al tomar asistencia")

            return HttpResponse(JsonResponse(response))

    context = {
        "clase": clase,
        "curso": curso,
        "active": clase.inicio <= datetime.now(tz=timezone.utc) and clase.fin > datetime.now(tz=timezone.utc),
        "asistencias":asistencias
    }
    return render(request, "qr/clase.html", context)
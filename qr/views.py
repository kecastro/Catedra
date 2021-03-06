from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import unidecode
import locale

from .models import *
from .froms import *
from django.http import HttpResponse
from .resources import EstudianteResource
from tablib import Dataset
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

def register(request):

    if request.user.is_authenticated():
        return redirect('qr:home')

    form = CreateUserForm(request.POST or None, prefix='user_form')

    if form.is_valid():
        email = form.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            form.add_error("email", "Ya existe usuario con ese correo")
        elif not Estudiante.objects.filter(correo=email).exists():
            form.add_error("email", "El correo no se encuentra en nuestra base de datos")
        else:
            x = Estudiante.objects.filter(correo=email)
            print(x)

            estudiante = get_object_or_404(Estudiante, correo=email)
            user = form.save(commit=False)
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            estudiante.usuario = user
            estudiante.save()

            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('qr:home')
    context = {
        "form": form,
    }

    return render(request, 'qr/register.html', context)

def home(request):

    if not request.user.is_authenticated():
        return redirect('qr:login')

    context = {
        "cursos_monitor": Curso.objects.filter(monitores=request.user),
        "monitor": request.user.estudiante.monitor,
        "cursos_estudiante":request.user.estudiante.cursos.all()
    }

    return render(request, "qr/home.html", context)

def curso(request, id_curso):

    if not request.user.is_authenticated():
        return redirect('qr:login')

    curso = get_object_or_404(Curso, pk=id_curso)

    if request.user not in curso.monitores.all():
        return redirect('qr:home')

    dateNow = datetime.now(tz=timezone.utc)
    previous = Clase.objects.filter(Q(curso=curso) & Q(fin__lt=dateNow)).order_by('-fin')
    # previous = curso.clases.all().filter(fin__lt=dateNow).order_by('fin').reverse()
    next = Clase.objects.filter(Q(curso=curso) & Q(inicio__gt=dateNow+timedelta(minutes=30)))
    # next = curso.clases.all().filter(inicio__gt=dateNow+timedelta(minutes=30))
    now =  Clase.objects.filter(Q(curso=curso) & Q(inicio__lte=dateNow+timedelta(minutes=30)) & Q(fin__gt=dateNow))
    # now = curso.clases.all().filter(Q(inicio__lte=dateNow+timedelta(minutes=30))&Q(fin__gt=dateNow))

    context = {
        "curso" : curso,
        "previous": previous,
        "next": next,
        "now": now
    }
    return render(request, "qr/curso.html", context)

def clase(request,id_clase):

    if not request.user.is_authenticated():
        return redirect('qr:login')

    clase = get_object_or_404(Clase, pk=id_clase)
    curso = get_object_or_404(Curso, pk=clase.curso.id)
    monitor = get_object_or_404(User, pk=request.user.id)
    asistencias = clase.asistencia_set.all()

    if not monitor in curso.monitores.all():
        return redirect('qr:home')

    #locale.setlocale(locale.LC_ALL, "es_ES.UTF-8")

    currentDate = datetime.now() #+ timedelta(hours=5)
    formato_local = "%d de %B del %Y a las %I:%M"
    if request.user.is_authenticated():
        if request.method == "POST":
            qr_text = request.body.decode("utf-8").split("?")
            print("QR Text: " + str(qr_text))
            estudiante = get_object_or_404(Estudiante, identificacion=qr_text[0])
            #print(estudiante)
            response = {}
            print(currentDate.hour,"|",clase.fin.hour,"-",currentDate.minute,"|",clase.fin.minute)
            print(asistencias)
            if asistencias.filter(estudiante=estudiante).exists():
                response["status"] = -201
                response["message"] = "Asistencia rechazada. La persona ya tiene una asistencia creada"
                print("Asistencia rechazada: la persona tiene asistencia")
            #elif currentDate.hour>=clase.fin.hour and currentDate.minute>clase.fin.minute:
                #response["status"] = -202
                #response["message"] = "Tiempo finalizado. Ya no se puede registrar"
                #print("El tiempo ha finalizado. Ya no se puede registrar")
            elif not curso in estudiante.cursos.all() :
                response["status"] = -203
                response["message"] = "El estudiante no tiene el curso registrado"
                print("El estudiante no tiene el curso registrado")
            elif curso in estudiante.cursos.all() and curso.identificador == int(qr_text[1]) and monitor in curso.monitores.all():
                asistencia = Asistencia.objects.create(clase=clase, estudiante=estudiante, monitor=monitor, fecha=datetime.now(tz=timezone.utc))
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
        "active": clase.inicio <= datetime.now(tz=timezone.utc)+timedelta(minutes=30) and clase.fin > datetime.now(tz=timezone.utc),
        "asistencias":asistencias
    }
    return render(request, "qr/clase.html", context)

def asistencias(request, id_curso):
    if not request.user.is_authenticated():
        return redirect('qr:login')

    estudiante = request.user.estudiante
    curso = get_object_or_404(Curso, pk=id_curso)

    dateNow = datetime.now(tz=timezone.utc)
    previous = Clase.objects.filter(Q(curso=curso) & Q(fin__lt=dateNow)).order_by('-fin')
    next = Clase.objects.filter(Q(curso=curso) & Q(inicio__gt=dateNow + timedelta(minutes=30)))
    now = Clase.objects.filter(Q(curso=curso) & Q(inicio__lte=dateNow + timedelta(minutes=30)) & Q(fin__gt=dateNow))
    asistencias = Asistencia.objects.filter(Q(estudiante=estudiante))
    context = {
        "curso": curso,
        "previous": previous,
        "next": next,
        "asistencias":asistencias,
        "now": now
    }
    return render(request, "qr/asistencias.html", context)


def me(request):

    form = UserForm(request.POST or None, prefix='user')

    context = {}

    if form.is_valid():
        user = request.user
        username = request.user.username
        password = form.cleaned_data['password']
        user.set_password(password)
        user.save()
        u = authenticate(username=username, password=password)
        login(request, u)
        context["mensaje"] = "Contraseña actualizada con exito"

    context["form"] = form

    return render(request, 'qr/perfil.html', context)


def informe(request, id_curso):

    response = HttpResponse(content_type='text/csv')


    curso = get_object_or_404(Curso, pk=id_curso)
    clases = Clase.objects.filter(curso=curso).order_by("inicio")
    estudiantes = Estudiante.objects.filter(cursos=curso)

    response['Content-Disposition'] = 'attachment; filename="informe-' + unidecode.unidecode(curso.nombre) + '.csv"'

    reporte = {}

    for estudiante in estudiantes:
        toma = []

        for clase in clases:
            if Asistencia.objects.filter(Q(clase=clase) & Q(estudiante=estudiante)).exists():
                toma.append("X")
            else:
                toma.append("NA")

        toma.insert( 0,estudiante.nombre + " - " + estudiante.identificacion)
        reporte[estudiante.identificacion] = list(toma)


    fechas = list(clases)
    fechas.insert(0, "Estudiantes\\Horarios")

    writer = csv.writer(response)
    writer.writerow(fechas)

    for registro in reporte:
        writer.writerow(reporte[registro])

    return response

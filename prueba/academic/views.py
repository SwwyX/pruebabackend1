"""
Vistas de la aplicacion 'academic'.

Contiene dos grupos de vistas:

1. Vistas HTML (render): entregan las plantillas que ve el usuario.
2. Vistas API de DRF (@api_view): implementan el CRUD (Create, Read, Update,
   Delete) de cada tabla del modelo ER y devuelven JSON. Las plantillas las
   consumen con fetch(), de manera que la interfaz web "enmascara" la API.

Los datos se leen y se escriben en el archivo
academic/data/academic_data.json, por lo que la aplicacion funciona sin
base de datos.
"""

import json
from pathlib import Path

from django.shortcuts import redirect, render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import (
    CourseSerializer,
    StudentCourseSerializer,
    StudentSerializer,
    TeacherSerializer,
)

# Ruta absoluta al archivo JSON con los datos.
DATA_FILE = Path(__file__).resolve().parent / 'data' / 'academic_data.json'


# ---------------------------------------------------------------------------
# Funciones auxiliares para trabajar con el archivo JSON
# ---------------------------------------------------------------------------

def load_data():
    """
    Lee el archivo JSON y devuelve un diccionario con las colecciones:
    'teachers', 'courses', 'students' y 'student_courses'.
    """
    with open(DATA_FILE, encoding='utf-8') as archivo:
        return json.load(archivo)


def save_data(data):
    """Escribe el diccionario completo de vuelta en el archivo JSON."""
    with open(DATA_FILE, 'w', encoding='utf-8') as archivo:
        json.dump(data, archivo, indent=2, ensure_ascii=False)


def siguiente_id(coleccion):
    """
    Calcula el id para un registro nuevo: el mayor id existente mas uno.
    Reemplaza al autoincremento que normalmente entrega la base de datos.
    """
    if not coleccion:
        return 1
    return max(registro['id'] for registro in coleccion) + 1


def buscar_por_id(coleccion, registro_id):
    """Devuelve el registro con ese id, o None si no existe."""
    for registro in coleccion:
        if registro['id'] == registro_id:
            return registro
    return None


def nombre_completo(registro):
    """Une first_name y last_name en un solo texto."""
    return f"{registro['first_name']} {registro['last_name']}"


# ---------------------------------------------------------------------------
# Vistas HTML (renderizan las plantillas)
# ---------------------------------------------------------------------------

def home(request):
    """
    Vista de la ruta raiz "/". Evita el error 404 al entrar al sitio
    redirigiendo al listado de asignaturas.
    """
    return redirect('courses')


def teachers_page(request):
    """Renderiza la plantilla con el CRUD de docentes."""
    return render(request, 'academic/teachers.html')


def courses_page(request):
    """Renderiza la plantilla con el CRUD de asignaturas."""
    return render(request, 'academic/courses.html')


def students_page(request):
    """Renderiza la plantilla con el CRUD de estudiantes."""
    return render(request, 'academic/students.html')


def enrollments_page(request):
    """Renderiza la plantilla con el CRUD de inscripciones."""
    return render(request, 'academic/enrollments.html')


# ---------------------------------------------------------------------------
# CRUD de Docentes (teacher)
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
def teacher_list(request):
    """
    GET  /api/teachers/ : lista todos los docentes.
    POST /api/teachers/ : crea un docente nuevo.
    """
    data = load_data()

    if request.method == 'GET':
        serializer = TeacherSerializer(data['teachers'], many=True)
        return Response(serializer.data)

    # POST: se validan los datos recibidos antes de guardarlos.
    serializer = TeacherSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    nuevo = {
        'id': siguiente_id(data['teachers']),
        'first_name': serializer.validated_data['first_name'],
        'last_name': serializer.validated_data['last_name'],
    }
    data['teachers'].append(nuevo)
    save_data(data)
    return Response(nuevo, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def teacher_detail(request, teacher_id):
    """
    GET    /api/teachers/<id>/ : devuelve un docente.
    PUT    /api/teachers/<id>/ : actualiza un docente.
    DELETE /api/teachers/<id>/ : elimina un docente.
    """
    data = load_data()
    teacher = buscar_por_id(data['teachers'], teacher_id)

    if teacher is None:
        return Response({'detail': 'Docente no encontrado.'},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(TeacherSerializer(teacher).data)

    if request.method == 'PUT':
        serializer = TeacherSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        teacher['first_name'] = serializer.validated_data['first_name']
        teacher['last_name'] = serializer.validated_data['last_name']
        save_data(data)
        return Response(teacher)

    # DELETE: se replica el on_delete=CASCADE declarado en models.py.
    # Al borrar un docente se borran sus asignaturas y las inscripciones
    # asociadas a esas asignaturas, para no dejar registros huerfanos.
    cursos_del_docente = [c['id'] for c in data['courses']
                          if c['teacher_id'] == teacher_id]

    data['courses'] = [c for c in data['courses'] if c['teacher_id'] != teacher_id]
    data['student_courses'] = [i for i in data['student_courses']
                               if i['course_id'] not in cursos_del_docente]
    data['teachers'] = [t for t in data['teachers'] if t['id'] != teacher_id]

    save_data(data)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# CRUD de Asignaturas (course)
# ---------------------------------------------------------------------------

def armar_cursos(data):
    """
    Arma la lista de asignaturas resolviendo las dos relaciones del ER:
      - 'imparte'  : teacher_id -> nombre del docente (teacher_name).
      - 'contiene' : student_course -> estudiantes inscritos (students).
    """
    # Diccionarios auxiliares {id: "Nombre Apellido"} para buscar rapido.
    teachers_by_id = {t['id']: nombre_completo(t) for t in data['teachers']}
    students_by_id = {s['id']: nombre_completo(s) for s in data['students']}

    # Se recorre la tabla intermedia una sola vez y se agrupan los
    # estudiantes por asignatura: {id_asignatura: ["Nombre Apellido", ...]}.
    students_by_course = {}
    for inscripcion in data['student_courses']:
        nombre = students_by_id.get(inscripcion['student_id'])
        if nombre is not None:
            students_by_course.setdefault(inscripcion['course_id'], []).append(nombre)

    cursos = []
    for course in data['courses']:
        cursos.append({
            'id': course['id'],
            'name': course['name'],
            'teacher_id': course['teacher_id'],
            'teacher_name': teachers_by_id.get(course['teacher_id'], 'Sin asignar'),
            'students': students_by_course.get(course['id'], []),
        })
    return cursos


@api_view(['GET', 'POST'])
def course_list(request):
    """
    GET  /api/courses/ : lista las asignaturas con su docente y sus alumnos.
    POST /api/courses/ : crea una asignatura nueva.
    """
    data = load_data()

    if request.method == 'GET':
        serializer = CourseSerializer(armar_cursos(data), many=True)
        return Response(serializer.data)

    serializer = CourseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Integridad referencial: el docente indicado debe existir.
    teacher_id = serializer.validated_data['teacher_id']
    if buscar_por_id(data['teachers'], teacher_id) is None:
        return Response({'teacher_id': ['El docente indicado no existe.']},
                        status=status.HTTP_400_BAD_REQUEST)

    nuevo = {
        'id': siguiente_id(data['courses']),
        'name': serializer.validated_data['name'],
        'teacher_id': teacher_id,
    }
    data['courses'].append(nuevo)
    save_data(data)
    return Response(nuevo, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def course_detail(request, course_id):
    """
    GET    /api/courses/<id>/ : devuelve una asignatura.
    PUT    /api/courses/<id>/ : actualiza una asignatura.
    DELETE /api/courses/<id>/ : elimina una asignatura.
    """
    data = load_data()
    course = buscar_por_id(data['courses'], course_id)

    if course is None:
        return Response({'detail': 'Asignatura no encontrada.'},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(CourseSerializer(course).data)

    if request.method == 'PUT':
        serializer = CourseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        teacher_id = serializer.validated_data['teacher_id']
        if buscar_por_id(data['teachers'], teacher_id) is None:
            return Response({'teacher_id': ['El docente indicado no existe.']},
                            status=status.HTTP_400_BAD_REQUEST)

        course['name'] = serializer.validated_data['name']
        course['teacher_id'] = teacher_id
        save_data(data)
        return Response(course)

    # DELETE: tambien se eliminan las inscripciones de esa asignatura.
    data['student_courses'] = [i for i in data['student_courses']
                               if i['course_id'] != course_id]
    data['courses'] = [c for c in data['courses'] if c['id'] != course_id]

    save_data(data)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# CRUD de Estudiantes (student)
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
def student_list(request):
    """
    GET  /api/students/ : lista todos los estudiantes.
    POST /api/students/ : crea un estudiante nuevo.
    """
    data = load_data()

    if request.method == 'GET':
        serializer = StudentSerializer(data['students'], many=True)
        return Response(serializer.data)

    serializer = StudentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    nuevo = {
        'id': siguiente_id(data['students']),
        'first_name': serializer.validated_data['first_name'],
        'last_name': serializer.validated_data['last_name'],
    }
    data['students'].append(nuevo)
    save_data(data)
    return Response(nuevo, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def student_detail(request, student_id):
    """
    GET    /api/students/<id>/ : devuelve un estudiante.
    PUT    /api/students/<id>/ : actualiza un estudiante.
    DELETE /api/students/<id>/ : elimina un estudiante.
    """
    data = load_data()
    student = buscar_por_id(data['students'], student_id)

    if student is None:
        return Response({'detail': 'Estudiante no encontrado.'},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(StudentSerializer(student).data)

    if request.method == 'PUT':
        serializer = StudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student['first_name'] = serializer.validated_data['first_name']
        student['last_name'] = serializer.validated_data['last_name']
        save_data(data)
        return Response(student)

    # DELETE: tambien se eliminan sus inscripciones.
    data['student_courses'] = [i for i in data['student_courses']
                               if i['student_id'] != student_id]
    data['students'] = [s for s in data['students'] if s['id'] != student_id]

    save_data(data)
    return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# CRUD de Inscripciones (student_course)
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
def enrollment_list(request):
    """
    GET  /api/enrollments/ : lista las inscripciones con sus nombres.
    POST /api/enrollments/ : inscribe un estudiante en una asignatura.
    """
    data = load_data()

    if request.method == 'GET':
        students_by_id = {s['id']: nombre_completo(s) for s in data['students']}
        courses_by_id = {c['id']: c['name'] for c in data['courses']}

        inscripciones = []
        for inscripcion in data['student_courses']:
            inscripciones.append({
                'student_id': inscripcion['student_id'],
                'course_id': inscripcion['course_id'],
                'student_name': students_by_id.get(inscripcion['student_id'], '?'),
                'course_name': courses_by_id.get(inscripcion['course_id'], '?'),
            })

        serializer = StudentCourseSerializer(inscripciones, many=True)
        return Response(serializer.data)

    serializer = StudentCourseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    student_id = serializer.validated_data['student_id']
    course_id = serializer.validated_data['course_id']

    # Integridad referencial: ambas entidades deben existir.
    if buscar_por_id(data['students'], student_id) is None:
        return Response({'student_id': ['El estudiante indicado no existe.']},
                        status=status.HTTP_400_BAD_REQUEST)
    if buscar_por_id(data['courses'], course_id) is None:
        return Response({'course_id': ['La asignatura indicada no existe.']},
                        status=status.HTTP_400_BAD_REQUEST)

    # Equivale al unique_together del modelo: no se repite la inscripcion.
    for inscripcion in data['student_courses']:
        if (inscripcion['student_id'] == student_id
                and inscripcion['course_id'] == course_id):
            return Response(
                {'detail': 'El estudiante ya esta inscrito en esa asignatura.'},
                status=status.HTTP_400_BAD_REQUEST)

    nueva = {'student_id': student_id, 'course_id': course_id}
    data['student_courses'].append(nueva)
    save_data(data)
    return Response(nueva, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def enrollment_detail(request, student_id, course_id):
    """
    DELETE /api/enrollments/<student_id>/<course_id>/ : elimina una inscripcion.
    Se identifica por los dos campos porque la tabla intermedia no tiene id
    propio: su clave primaria es compuesta.
    """
    data = load_data()

    originales = len(data['student_courses'])
    data['student_courses'] = [
        i for i in data['student_courses']
        if not (i['student_id'] == student_id and i['course_id'] == course_id)
    ]

    if len(data['student_courses']) == originales:
        return Response({'detail': 'Inscripcion no encontrada.'},
                        status=status.HTTP_404_NOT_FOUND)

    save_data(data)
    return Response(status=status.HTTP_204_NO_CONTENT)

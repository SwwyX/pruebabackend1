"""
Serializadores de Django REST Framework.

Como los datos provienen del archivo JSON (no de la base de datos), se usan
serializers.Serializer en lugar de ModelSerializer: reciben diccionarios de
Python y los convierten a la representacion JSON que devuelven los endpoints.
Los campos declarados son los mismos del modelo ER.

Ademas de mostrar datos, estos serializadores validan la informacion que llega
en las operaciones de creacion (POST) y edicion (PUT) del CRUD.
"""

from rest_framework import serializers


class TeacherSerializer(serializers.Serializer):
    """Serializa un docente: id, first_name, last_name."""

    # El id lo asigna el servidor, por eso es de solo lectura.
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)


class CourseSerializer(serializers.Serializer):
    """
    Serializa una asignatura: id, name, teacher_id.

    Ademas incluye dos campos calculados de solo lectura:
      - teacher_name: nombre del docente que imparte la asignatura.
      - students: lista de estudiantes inscritos en la asignatura, obtenida
        desde la tabla intermedia student_course del modelo ER.
    """

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=150)
    teacher_id = serializers.IntegerField()
    teacher_name = serializers.CharField(read_only=True)
    students = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
    )


class StudentSerializer(serializers.Serializer):
    """Serializa un estudiante: id, first_name, last_name."""

    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)


class StudentCourseSerializer(serializers.Serializer):
    """
    Serializa una inscripcion (tabla intermedia student_course).
    No tiene id propio: su clave es la combinacion student_id + course_id.
    Los nombres se agregan solo para mostrarlos en la tabla del frontend.
    """

    student_id = serializers.IntegerField()
    course_id = serializers.IntegerField()
    student_name = serializers.CharField(read_only=True)
    course_name = serializers.CharField(read_only=True)

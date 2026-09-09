"""
Modelos de datos de la aplicacion 'academic'.

Estas clases traducen a Django el modelo ER entregado por el docente:

    teacher (id, first_name, last_name)
    course  (id, name, teacher_id -> teacher.id)
    student (id, first_name, last_name)
    student_course (student_id -> student.id, course_id -> course.id)

Nota: para esta evaluacion los datos se sirven desde el archivo JSON
'academic/data/academic_data.json' (ver serializers.py y views.py), por lo que
no es necesario migrar ni usar la base de datos. Los modelos se definen igual
para dejar declarados los nombres de campo, tipos de datos y relaciones del ER.
"""

from django.db import models


class Teacher(models.Model):
    """Docente. Un docente puede impartir muchas asignaturas (1:N con Course)."""

    # id: Django crea automaticamente la PK entera 'id'.
    first_name = models.CharField(max_length=100)  # varchar first_name
    last_name = models.CharField(max_length=100)   # varchar last_name

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Course(models.Model):
    """Asignatura. Pertenece a un docente (FK teacher_id)."""

    name = models.CharField(max_length=150)  # varchar name
    # teacher_id: clave foranea hacia teacher.id (relacion 'imparte').
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='courses',
    )

    def __str__(self):
        return self.name


class Student(models.Model):
    """Estudiante. Se inscribe en muchas asignaturas a traves de StudentCourse."""

    first_name = models.CharField(max_length=100)  # varchar first_name
    last_name = models.CharField(max_length=100)   # varchar last_name

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class StudentCourse(models.Model):
    """
    Inscripcion: tabla intermedia del ER (student_course).
    Su clave primaria compuesta se representa con unique_together,
    porque Django no admite PK compuestas.
    """

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )

    class Meta:
        # Un estudiante no puede inscribirse dos veces en la misma asignatura.
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} -> {self.course}"

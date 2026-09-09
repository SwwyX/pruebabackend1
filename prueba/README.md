# Sistema de Gestión Académica — Evaluación N°1 (Desarrollo Backend)

Aplicación hecha con **Django + Django REST Framework**.
La interfaz web "enmascara" los endpoints REST: las páginas HTML se renderizan
con Django y las tablas se llenan con `fetch()` asíncrono contra `/api/...`.

Incluye el **CRUD completo de las cuatro tablas** del modelo ER. Los datos se
leen y se escriben en `academic/data/academic_data.json`, por lo que
**el proyecto funciona sin base de datos**: no hay migraciones de la app y las
tablas del ER no existen en SQLite.

## Modelo ER

| Tabla | Campos | Relación |
|---|---|---|
| `teacher` | id, first_name, last_name | imparte muchas asignaturas |
| `course` | id, name, teacher_id | pertenece a un docente |
| `student` | id, first_name, last_name | se inscribe en muchas asignaturas |
| `student_course` | student_id, course_id | tabla intermedia (clave compuesta) |

## Estructura

- `academic_project/` — configuración global (`settings.py` con `rest_framework`).
- `academic/models.py` — clases del modelo ER.
- `academic/data/academic_data.json` — datos (reemplaza a la base de datos).
- `academic/serializers.py` — serializadores DRF, que además validan las altas y ediciones.
- `academic/views.py` — vistas HTML (`render`) y endpoints CRUD de la API.
- `academic/templates/academic/` — `base.html` y una página por tabla.

## Cómo ejecutar

```bash
pip install django djangorestframework
python manage.py migrate     # solo crea las tablas internas de Django (sesiones, auth)
python manage.py runserver
```

Luego abrir http://127.0.0.1:8000/

## Rutas

### Páginas

| Ruta | Descripción |
|------|-------------|
| `/` | Redirige a `/courses/` (evita el error 404) |
| `/teachers/` | CRUD de docentes |
| `/courses/` | CRUD de asignaturas, con su profesor y sus alumnos inscritos |
| `/students/` | CRUD de estudiantes |
| `/enrollments/` | CRUD de inscripciones (relaciona alumnos con asignaturas) |

### API

| Ruta | Métodos |
|------|---------|
| `/api/teachers/` | GET, POST |
| `/api/teachers/<id>/` | GET, PUT, DELETE |
| `/api/courses/` | GET, POST |
| `/api/courses/<id>/` | GET, PUT, DELETE |
| `/api/students/` | GET, POST |
| `/api/students/<id>/` | GET, PUT, DELETE |
| `/api/enrollments/` | GET, POST |
| `/api/enrollments/<student_id>/<course_id>/` | DELETE |

La inscripción no tiene `PUT` ni id propio: su clave primaria es la
combinación `student_id` + `course_id`, igual que en el modelo ER.

## Integridad referencial

Como no hay motor de base de datos que la garantice, se implementa en las vistas:

- No se puede crear una asignatura con un docente inexistente.
- No se puede inscribir dos veces al mismo alumno en la misma asignatura
  (equivale al `unique_together` del modelo).
- Al eliminar se replica el `on_delete=CASCADE`: borrar un docente elimina sus
  asignaturas y las inscripciones de esas asignaturas; borrar una asignatura o
  un estudiante elimina sus inscripciones.

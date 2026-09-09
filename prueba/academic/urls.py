"""
Rutas de la aplicacion 'academic'.

Se separan las rutas HTML (las que ve el usuario) de las rutas /api/ que
entregan el JSON consumido por fetch(). Cada tabla del modelo ER tiene su
CRUD completo: la ruta de lista maneja GET y POST, y la de detalle maneja
GET, PUT y DELETE.
"""

from django.urls import path

from . import views

urlpatterns = [
    # --- Vistas HTML ---
    path('', views.home, name='home'),                          # ruta raiz, sin 404
    path('teachers/', views.teachers_page, name='teachers'),
    path('courses/', views.courses_page, name='courses'),
    path('students/', views.students_page, name='students'),
    path('enrollments/', views.enrollments_page, name='enrollments'),

    # --- Endpoints de la API (DRF) ---
    path('api/teachers/', views.teacher_list, name='api-teachers'),
    path('api/teachers/<int:teacher_id>/', views.teacher_detail, name='api-teacher-detail'),

    path('api/courses/', views.course_list, name='api-courses'),
    path('api/courses/<int:course_id>/', views.course_detail, name='api-course-detail'),

    path('api/students/', views.student_list, name='api-students'),
    path('api/students/<int:student_id>/', views.student_detail, name='api-student-detail'),

    path('api/enrollments/', views.enrollment_list, name='api-enrollments'),
    path('api/enrollments/<int:student_id>/<int:course_id>/',
         views.enrollment_detail, name='api-enrollment-detail'),
]

"""
URL configuration for vfp_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.shortcuts import redirect
from django.urls import include, path, re_path
from rest_framework import routers
from vfp_offline_api.views import (
    SpsalesViewSet,
    analytics_view,
    dashboard_view,
    login_view,
    logout_view,
    not_found_view,
    register_view,
    sales_bulk_delete_view,
    sales_delete_view,
    sales_edit_view,
    server_error_view,
)

router = routers.DefaultRouter()
router.register(r'spsales', SpsalesViewSet, basename='spsales')

urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('dashboard/', analytics_view, name='dashboard'),
    path('analytics/', lambda request: redirect('dashboard'), name='analytics'),
    path('records/', dashboard_view, name='records'),
    path('records/sales/<int:pk>/edit/', sales_edit_view, name='sales_edit'),
    path('records/sales/<int:pk>/delete/', sales_delete_view, name='sales_delete'),
    path('records/sales/bulk-delete/', sales_bulk_delete_view, name='sales_bulk_delete'),
    path('logout/', logout_view, name='logout'),
    path('api/', include(router.urls)),
]

if settings.ENABLE_DJANGO_ADMIN:
    urlpatterns.append(path('admin/', admin.site.urls))

handler404 = 'vfp_offline_api.views.not_found_view'
handler500 = 'vfp_offline_api.views.server_error_view'

urlpatterns.append(re_path(r'^(?P<unmatched_path>.*)$', not_found_view, name='not_found'))

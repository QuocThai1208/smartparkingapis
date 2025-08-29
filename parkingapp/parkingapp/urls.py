from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from parking.admin import admin_site
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Parking API",
        default_version='v1',
        description="APIs for ParkingApp",
        contact=openapi.Contact(email="thai124@gmail.com"),
        license=openapi.License(name="Phạm Quốc Thái"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', include('parking.urls')),
    path('admin/', admin_site.urls),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    re_path(r'^swagger/$',
            schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui'),
    re_path(r'^redoc/$',
            schema_view.with_ui('redoc', cache_timeout=0),
            name='schema-redoc')
]

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('', views.home, name='home'),
    path('', views.fetch_data, name='fetch_data'),
    path('view-data/', views.view_data, name='view_data'),
    path('delete_element_image/', views.delete_element_image, name='delete_element_image'),
    path('upload_element_image/', views.upload_element_image, name='upload_element_image'),
    path('save_timing_log/', views.save_timing_log_endpoint, name='save_timing_log'),
    path('test_logging/', views.test_logging, name='test_logging'),
    # path('force-overwrite-human-image/', views.force_overwrite_human_image, name='force_overwrite_human_image'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
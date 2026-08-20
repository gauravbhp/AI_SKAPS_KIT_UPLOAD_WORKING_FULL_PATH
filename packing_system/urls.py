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
    # path('save_timing_log/', views.save_timing_log_endpoint, name='save_timing_log'),
    # path('test_logging/', views.test_logging, name='test_logging'),
    path(
        "upload_box_capture/",
        views.upload_box_capture,
        name="upload_box_capture"
    ),
    
    # Scheduler management endpoints
    # # path('api/scheduler/status/', views.scheduler_status, name='scheduler_status'),
    # path('api/scheduler/trigger-check/', views.trigger_file_check_now, name='trigger_file_check'),
    # path('api/scheduler/update-interval/', views.update_check_interval, name='update_check_interval'),
    
    # path('api/upload-ply-file/', views.upload_ply_file, name='upload_ply_file'),
    # path('api/ply-files-status/', views.get_ply_files_status, name='ply_files_status'),
    # path('api/move-files/', views.move_files_api, name='move_files_api'),
    # path('force-overwrite-human-image/', views.force_overwrite_human_image, name='force_overwrite_human_image'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
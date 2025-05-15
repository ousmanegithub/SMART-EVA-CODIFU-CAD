from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views
from .views import upload_geojson_eval

urlpatterns = [
    path('map/', views.map_view, name='map_view'),
    path('api/parcelles/', views.parcelle_list, name='parcelle_list'),
    path('api/upload_geojson/', views.upload_geojson, name='upload_geojson'),
    path('api/upload_geojson_eval/', views.upload_geojson_eval, name='upload_geojson_eval'),

    path('home/', views.home_view, name='home_view'),
    path('eval/', views.eval_view, name='eval_view'),
    path('about/', views.about, name='about'),
    path('setup/', views.setup, name='setup'),

    path('login/', LoginView.as_view(template_name='parcelles/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    #path('upload_shapefile/', views.upload_shapefile, name='upload_shapefile'),
    #path('api/generate_bdn/', views.generate_bdn_codes, name='generate_bdn_codes'),

    #path('generate-bdn-codes/', views.generate_bdn_codes, name='generate_bdn_codes'),
    path('list-parcelles/', views.list_parcelles, name='list_parcelles'),
    path('parcelles/', views.get_parcelles_geojson, name='get_parcelles_geojson'),
    #path('import/', views.import_geospatial_file, name='import_geospatial_file'),
    #path('upload/', views.upload_geospatial_file, name='upload_geospatial_file'),
    path('generate/', views.generate_bdn_codes, name='generate_bdn_codes'),
    path('view-data/', views.view_generated_data, name='view_generated_data'),
    path('multi-step-eval/', views.multi_step_eval_view, name='multi_step_eval'),
    path('generate-multi-step-report/', views.generate_multi_step_report, name='generate_multi_step_report'),
    path('generate-street-view/', views.generate_street_view, name='generate_street_view'),
    path('generate-individual-report/', views.generate_individual_report, name='generate_individual_report'),

]

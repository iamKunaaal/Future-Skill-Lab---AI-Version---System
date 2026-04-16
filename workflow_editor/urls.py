from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.editor,               name='workflow_editor'),
    path('api/data/',               views.api_data,             name='workflow_api_data'),
    path('api/save/',               views.api_save_layout,      name='workflow_api_save'),
    path('api/competency/update/',  views.api_update_competency, name='workflow_comp_update'),
    path('api/competency/add/',     views.api_add_competency,   name='workflow_comp_add'),
    path('api/competency/delete/',  views.api_delete_competency,  name='workflow_comp_delete'),
]

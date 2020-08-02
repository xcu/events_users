from django.urls import path
from accounts import views


urlpatterns = [
    path('all', views.all_events, name='home'),
    path('', views.EventView.as_view(), name='create_event'),
    path('<int:event_id>/', views.EventEditView.as_view(), name='edit_event'),
    path('<int:event_id>/join', views.join_event, name='join_event'),
    path('<int:event_id>/withdraw',
         views.withdraw_event, name='withdraw_event'),
]

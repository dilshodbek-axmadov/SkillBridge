from django.urls import path

from . import views

app_name = 'messaging'

urlpatterns = [
    path('threads/', views.ThreadListCreateView.as_view(), name='thread_list_create'),
    path('threads/<int:thread_id>/', views.ThreadDetailView.as_view(), name='thread_detail'),
    path('threads/<int:thread_id>/messages/', views.ThreadMessageListView.as_view(), name='thread_messages'),
    path('threads/<int:thread_id>/send/', views.ThreadSendMessageView.as_view(), name='thread_send'),
]


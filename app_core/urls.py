from django.urls import path
from .views import *


app_name = "app_core"

urlpatterns = [
    path('player-info/<int:tg_id>/<str:name>/<int:referral_id>/', PlayerInfo.as_view(), name='player_info_referral'),
    path('player-info/<int:tg_id>/<str:name>/', PlayerInfo.as_view(), name='player-info'),
    path('all_friends/<int:tg_id>/', PlayerFriendsView.as_view(), name='all_friends'),
    path('referral_bonus/<int:tg_id>/<int:new_player_id>/', FriendBonusView.as_view(), name='ref_bonus'),
    path('generate_link/<int:tg_id>/', GenerateRefLinkView.as_view(), name='generate_link'),
    path('tasks/<int:tg_id>/<str:dop_name>/', TaskPlayerDetailView.as_view(), name='task_detail_with_name'),
    path('tasks/<int:tg_id>/', TaskPlayerDetailView.as_view(), name='task_detail'),
    path('tasks/start/<int:tg_id>/<str:dop_name>/', StartTaskView.as_view(), name='start_task'),
    path('top100/<int:tg_id>/', MonthlyTopPlayersView.as_view(), name='top-100'),

]


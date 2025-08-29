from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register('users', views.UserViewSet, basename='user')
router.register('vehicles', views.VehicleViewSet, basename='vehicle')
router.register('fee-role', views.FeeRoleViewSet, basename='fee-role')
router.register('payments', views.PaymentViewSet, basename='payment')
router.register('parking-logs', views.ParkingLogViewSet, basename='parking-log')
router.register('stats', views.StatsViewSet, basename='stats')
router.register('walletTransactions', views.WalletTransactionViewSet, basename='walletTransaction')

urlpatterns = [
    path('', include(router.urls)),
    path('scan-plate/', views.ScanPlateViewSet.as_view(), name='scan-plate'),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]

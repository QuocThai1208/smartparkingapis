from django.contrib import admin
from .models import (User, Vehicle, FeeRule, Payment, ParkingLog, Wallet, WalletTransaction, UserFace)


class ParkingAppAdminSite(admin.AdminSite):
    site_header = 'Hệ thống quản lý giữ xe tự động'


admin_site = ParkingAppAdminSite(name='myadmin')


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'user_role', 'avatar', 'address', 'birth', 'is_staff', 'is_active')
    search_fields = ('username', 'full_name', 'email')
    list_filter = ('is_staff', 'is_active')


class VehicleAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'vehicle_type', 'name', 'user', 'is_approved', 'image')
    search_fields = ('license_plate', 'name', 'user__full_name')
    list_filter = ('is_approved',)
    autocomplete_fields = ('user',)


class FeeRuleAdmin(admin.ModelAdmin):
    list_display = ('fee_type', 'amount', 'active', 'effective_from', 'effective_to')
    search_fields = ('fee_type',)
    list_filter = ('fee_type',)
    ordering = ('-effective_from',)


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status')
    search_fields = ('id', 'user__full_name')
    list_filter = ('status',)
    autocomplete_fields = ('user',)


class ParkingLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'vehicle', 'user_face', 'check_in', 'check_out', 'duration_minutes', 'fee', 'status')
    search_fields = ('id', 'user__full_name', 'vehicle__license_plate')
    list_filter = ('status',)
    autocomplete_fields = ('user', 'vehicle', 'fee_rule')


class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'active')
    search_fields = ('user__username',)


class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'transaction_type', 'created_date', 'description')
    list_filter = ('transaction_type', 'created_date')
    search_fields = ('wallet__user__username', 'description')


class UserFaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'face_img')
    list_filter = ('created_date',)


admin_site.register(User, UserAdmin)
admin_site.register(Vehicle, VehicleAdmin)
admin_site.register(FeeRule, FeeRuleAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(ParkingLog, ParkingLogAdmin)
admin_site.register(Wallet, WalletAdmin)
admin_site.register(WalletTransaction, WalletTransactionAdmin)
admin_site.register(UserFace, UserFaceAdmin)

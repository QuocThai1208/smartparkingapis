from datetime import date
from typing import Optional
from django.db.models.functions import Coalesce
from django.db.models import Sum

from ..models import (ParkingLog,
                      ParkingStatus,
                      User,
                      UserRole)


def get_total_revenue_range(regimen: str, user: User,
                            date_from: Optional[date] = None,
                            date_to: Optional[date] = None) -> int:
    if regimen == 'my' or user.user_role == UserRole.CUSTOMER:
        parking_logs = ParkingLog.objects.filter(status=ParkingStatus.OUT, user=user)
    else:
        parking_logs = ParkingLog.objects.filter(status=ParkingStatus.OUT)

    if date_from:
        # lấy các bảng ghi có ngày lớn hơn date_from
        parking_logs = parking_logs.filter(created_date__date__gte=date_from)
    if date_to:
        # lấy các bảng ghi có ngày nhỏ lơn date_to
        parking_logs = parking_logs.filter(created_date__date__lte=date_to)

    total_revenue = parking_logs.aggregate(total=Coalesce(Sum("fee"), 0))["total"]
    return total_revenue


def compare_monthly_revenue(user: User, current_start: Optional[date] = None,
                            current_end: Optional[date] = None,
                            prev_start: Optional[date] = None,
                            prev_end: Optional[date] = None):
    current_revenue = get_total_revenue_range('all', user, current_start, current_end)
    prev_revenue = get_total_revenue_range('all', user, prev_start, prev_end)

    if prev_revenue == 0:
        change_percent = 100.0 if current_revenue > 0 else 0.0
    else:
        change_percent = ((current_revenue - prev_revenue) / prev_revenue) * 100
    return {
        "revenue": current_revenue,
        "change_percent": change_percent
    }


def get_revenue_by_user(date_from: Optional[date] = None,
                        date_to: Optional[date] = None):
    parking_logs = ParkingLog.objects.filter(status=ParkingStatus.OUT)
    if date_from:
        parking_logs = parking_logs.filter(created_date__date__gte=date_from)
    if date_to:
        parking_logs = parking_logs.filter(created_date__date__lte=date_to)

    results = parking_logs.values("user__username").annotate(total=Coalesce(Sum('fee'), 0))
    return results


def get_revenue_by_vehicle(date_from: Optional[date] = None,
                           date_to: Optional[date] = None):
    parking_logs = ParkingLog.objects.filter(status=ParkingStatus.OUT)
    if date_from:
        parking_logs = parking_logs.filter(created_date__date__gte=date_from)
    if date_to:
        parking_logs = parking_logs.filter(created_date__date__lte=date_to)

    results = parking_logs.values("user__full_name", "vehicle__name", "vehicle__license_plate").annotate(
        total=Coalesce(Sum('fee'), 0))
    return results

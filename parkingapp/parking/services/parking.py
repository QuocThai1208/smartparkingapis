from datetime import date
from typing import Optional
from django.db.models import Sum
from django.utils import timezone
from .detection_face import cosine_similarity
from .helpers import calculate_fee

from ..models import (Vehicle,
                      ParkingLog,
                      ParkingStatus,
                      FeeRule,
                      User,
                      FeeType,
                      UserRole,
                      UserFace)


def get_total_count_parking(regimen: str, user: User,
                            date_from: Optional[date] = None,
                            date_to: Optional[date] = None) -> int:
    if regimen == 'my' or user.user_role == UserRole.CUSTOMER:
        parking_logs = ParkingLog.objects.filter(user=user, status=ParkingStatus.OUT)
    else:
        parking_logs = ParkingLog.objects.all()

    if date_from:
        # lấy các bảng ghi có ngày lớn hơn date_froms
        parking_logs = parking_logs.filter(created_date__date__gte=date_from)
    if date_to:
        # lấy các bảng ghi có ngày nhỏ lơn date_to
        parking_logs = parking_logs.filter(created_date__date__lte=date_to)

    count = parking_logs.count()
    return count


def get_total_time_parking(regimen: str, user: User,
                           date_from: Optional[date] = None,
                           date_to: Optional[date] = None) -> int:
    if regimen == 'my' or user.user_role == UserRole.CUSTOMER:
        parking_logs = ParkingLog.objects.filter(user=user, status=ParkingStatus.OUT)
    else:
        parking_logs = ParkingLog.objects.all()

    if date_from:
        parking_logs = parking_logs.filter(created_date__date__gte=date_from)
    if date_to:
        parking_logs = parking_logs.filter(created_date__date__lte=date_to)
    total = parking_logs.aggregate(total_minutes=Sum('duration_minutes'))['total_minutes'] or 0
    return total


# HÀM: Tạo mới nhật kí gửi xe
def create_parking(v: Vehicle, fee_type: FeeType, user_face_id) -> tuple[bool, str]:
    exist_p = ParkingLog.objects.filter(user=v.user, vehicle=v, status=ParkingStatus.IN).first()
    if exist_p:
        return False, 'Phương tiện này đang có trong bãi'
    p = ParkingLog.objects.create(
        user=v.user,
        vehicle=v,
        fee_rule=FeeRule.objects.get(fee_type=fee_type),
        status=ParkingStatus.IN,
        user_face=UserFace.objects.get(id=user_face_id)
    )
    if p:
        return True, "Xin mời vào."
    return False, "Không hợp lệ."


# HÀM: Cập nhật nhật kí gửi xe
def update_parking(new_emb, v: Vehicle) -> tuple[bool, ParkingLog or str]:
    try:
        log = (
            ParkingLog.objects
            .select_for_update()  # khóa bảng ghi cho đến khi hoàn tất
            .get(user=v.user,
                 vehicle=v,
                 status=ParkingStatus.IN)
        )
        user_face = log.user_face
        sim = cosine_similarity(new_emb, user_face.embedding)
        if sim < 0.6:
            return False, "Xác thực khuôn mặt thất bại"
    except  ParkingLog.DoesNotExist:
        return False, "Không tìm thấy xe lượt vào bãi"

    now = timezone.now()
    log.check_out = now
    duration = int((log.check_out - log.check_in).total_seconds() // 60)
    log.duration_minutes = duration
    log.status = ParkingStatus.OUT
    log.fee = calculate_fee(duration, log.fee_rule)
    return True, log

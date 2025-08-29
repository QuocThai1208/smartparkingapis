from .detection_face import find_or_create_user_face
from ..models import (Vehicle,
                      ParkingStatus,
                      User,
                      Payment,
                      PaymentStatus)
from django.db import transaction
from .payment import process_payment
from .parking import create_parking, update_parking
from .detection_vehicle import check_vehicle


# HÀM: Tạo mới thanh toán
def create_payment(user: User, fee: int) -> tuple[bool, str]:
    payment = Payment.objects.create(
        user=user,
        amount=fee,
    )
    payment_status, msg = process_payment(user.wallet, fee, description='Thanh toán luợt gửi xe')
    payment.status = payment_status
    payment.save(update_fields=['status'])
    if payment_status in [PaymentStatus.ERROR, PaymentStatus.FAIL]:
        return False, msg
    return True, "Xin mời ra."


def proces(emb, face_img, vehicle_img, plate_text: str, direction: ParkingStatus = "IN") -> tuple[bool, str]:
    vehicle = Vehicle.objects.select_related("user").filter(
        license_plate=plate_text,
        is_approved=True
    ).first()

    if vehicle is None:
        return False, "Không tìm thấy phương tiện khớp với biển số"

    if direction == 'OUT':

        with transaction.atomic():
            ok, log = update_parking(emb, vehicle)
            if not ok:
                return ok, log
            try:
                ok, msg = create_payment(vehicle.user, log.fee)
                if not ok:
                    raise ValueError(msg)
                log.save(
                    update_fields=['check_out', 'duration_minutes', 'status', 'fee']
                )
            except Exception as e:
                return ok, "Có lỗi " + str(e)
        return ok, msg
    ok, msg = check_vehicle(vehicle.image, vehicle_img)
    if not ok:
        return ok, msg
    user_face = find_or_create_user_face(emb, face_img)
    ok, msg = create_parking(vehicle, vehicle.vehicle_type, user_face.id)
    return ok, msg

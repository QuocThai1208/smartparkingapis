import os
import math
import calendar
from datetime import datetime, date
from django.core.files.storage import default_storage
from django.conf import settings

from ..models import (FeeRule,
                      FeeType)

from rest_framework.exceptions import ValidationError


# HÀM upload ảnh
def upload_image(image, name, path):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ext = os.path.splitext(image.name)[1]  # lấy đuôi file
    new_filename = f"{name}_{timestamp}{ext}"
    upload_dir = os.path.join(settings.MEDIA_ROOT, path)
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, new_filename)
    default_storage.save(save_path, image)
    return save_path


# HÀM: tính phí giữ xe
def calculate_fee(minutes: int, fee_rule: FeeRule) -> int:
    if fee_rule.fee_type in [FeeType.MOTORCYCLE, FeeType.CAR]:
        day = max(1, math.ceil(minutes / (24 * 60)))
        return day * fee_rule.amount

    raise ValueError(f"Unsupport fee_type: {fee_rule.fee_type}")


# HÀM tính date_from, date_to
def create_df_dt(day, month, year) -> tuple[date, date]:
    if day and month and year:
        df = dt = date(year, month, day)
    elif month and year and not day:
        last = calendar.monthrange(year, month)[1]  # lấy ngày cuối cùng của tháng
        df = date(year, month, 1)
        dt = date(year, month, last)
    elif year and not month and not day:
        df = date(year, 1, 1)
        dt = date(year, 12, 31)
    elif not any([day, month, year]):  # trả về false nếu cả 3 là none
        df = dt = None
    else:
        raise ValidationError(
            "• Muốn lấy theo ngày: cần ngày, tháng, năm\n"
            "• Muốn theo tháng: cần tháng, năm\n"
            "• Muốn theo năm: chỉ cần năm"
        )
    return df, dt

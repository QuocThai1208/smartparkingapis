from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# ----------  Các hằng & TextChoices  ----------
class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Đang xử lý"
    SUCCESS = "SUCCESS", "Thành công"
    FAIL = "FAIL", "Thất bại"
    ERROR = "ERROR", "Lỗi kết nối"


class TransactionType(models.TextChoices):
    DEPOSIT = "DEPOSIT", "Nạp tiền"
    WITHDRAW = "WITHDRAW", "Rút tiền",
    PAYMENT = "PAYMENT", "Thanh toán",
    REFUND = "REFUND", "Hoàn tiền"


class ParkingStatus(models.TextChoices):
    IN = "IN", "Đang gửi"
    OUT = "OUT", "Đã lấy xe"


class FeeType(models.TextChoices):
    MOTORCYCLE = "MOTORCYCLE", "Xe máy"
    CAR = "CAR", "Ô tô"


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    STAFF = "STAFF", "Staff"
    CUSTOMER = "CUSTOMER", "Khách hàng"


class BaseModel(models.Model):
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-id']


class User(AbstractUser):
    full_name = models.CharField(max_length=100)
    avatar = CloudinaryField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True)
    birth = models.IntegerField(null=True)
    user_role = models.CharField(max_length=10, default=UserRole.CUSTOMER, choices=UserRole.choices)

    def __str__(self):
        return self.full_name


class Vehicle(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vehicles")
    name = models.CharField(max_length=255, help_text="Tên/đời xe – ví dụ: Yamaha Sirius")
    license_plate = models.CharField(max_length=15, unique=True, help_text="Biển số xe")
    image = CloudinaryField(null=True, blank=True, help_text="Ảnh xe")
    vehicle_type = models.CharField(max_length=20, choices=FeeType.choices)
    is_approved = models.BooleanField(default=False, help_text="Đã được admin duyệt chưa")

    def __str__(self):
        return self.license_plate


class UserFace(BaseModel):
    face_img = CloudinaryField(null=True, blank=True, help_text="Ảnh khuôn mặt")
    embedding = models.JSONField(help_text="embedding trung bình")

    def __str__(self):
        return f"{self.id}"


class FeeRule(BaseModel):
    fee_type = models.CharField(max_length=10, choices=FeeType.choices)
    amount = models.PositiveIntegerField(help_text="Giá (VNĐ)")
    effective_from = models.DateField(default=timezone.localdate)
    effective_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.fee_type} ({self.amount}đ)"


class Payment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    amount = models.PositiveIntegerField(help_text="Số tiền giao dịch (VNĐ)")
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    def __str__(self):
        return f"{self.id} - {self.amount}đ ({self.status})"


class ParkingLog(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parking_logs")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="parking_logs")
    fee_rule = models.ForeignKey(FeeRule, on_delete=models.CASCADE, related_name="parking_logs")
    check_in = models.DateTimeField(default=timezone.now)
    check_out = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(editable=False, null=True, blank=True)
    fee = models.PositiveIntegerField(null=True, blank=True, help_text="Phí phải trả cho lượt này")
    status = models.CharField(max_length=4, choices=ParkingStatus.choices, default=ParkingStatus.IN)
    user_face = models.ForeignKey(UserFace, on_delete=models.SET_NULL, related_name="parking_logs", null=True,
                                  blank=True)

    def __str__(self):
        return f"Log {self.id} - {self.vehicle.license_plate}"


class Wallet(BaseModel):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Ví của {self.user.full_name} - {self.balance:.2f}vnđ"

    def can_afford(self, amount):
        return self.balance >= amount

    def deposit(self, amount, description=''):
        if amount <= 0:
            raise ValueError("Số tiền nạp phải lớn hơn 0.")

        self.balance += amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            description=description
        )

    def withdraw(self, amount, description=''):
        if not self.active:
            raise ValueError("Ví đã bị khóa.")

        if amount <= 0:
            raise ValueError("Số tiền rút phải lớn hơn 0.")
        if self.balance < amount:
            raise ValueError("Số dư không đủ.")

        self.balance -= amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=TransactionType.WITHDRAW,
            description=description
        )


class WalletTransaction(BaseModel):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transaction")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.transaction_type} {self.amount}vnđ - {self.created_date.strftime('%d-%m-%Y %H:%M:%S')}"

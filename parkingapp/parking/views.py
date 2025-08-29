from typing import Optional
from datetime import date
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.finance import (get_total_revenue_range,
                               get_revenue_by_user,
                               compare_monthly_revenue,
                               get_revenue_by_vehicle)

from .services.parking import (get_total_count_parking,
                               get_total_time_parking)

from .services.vehicle import get_user_vehicle_stats
from .services.services import proces
from .services.users import get_total_customer
from .services.helpers import upload_image, create_df_dt
from .services.detection_face import math_emb
from .services.detection_plate import detect_license_plates
from .models import User, Vehicle, FeeRule, Payment, UserRole, ParkingLog, ParkingStatus, WalletTransaction
from . import serializers, perms
from . import paginator


class UserViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer

    @action(methods=['get', 'patch'], url_path='current-user', detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def get_current_user(self, request):
        if request.method.__eq__('PATCH'):
            u = request.user
            for key in request.data:
                if key in ['avatar', 'full_name', 'username', 'address']:
                    setattr(u, key, request.data[key])
                elif key == 'birth':
                    value = request.data[key]
                    try:
                        value = int(value)
                    except(ValueError, TypeError):
                        return Response({"birth": "Giá trị không hợp lệ, phải là số."}, status=400)
                    setattr(u, key, value)
                elif key.__eq__('password'):
                    u.set_password(request.data[key])
            u.save()
            return Response(serializers.UserSerializer(u).data, status=status.HTTP_200_OK)
        else:
            return Response(serializers.UserSerializer(request.user).data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='current-user/total-payment',
            permission_classes=[permissions.IsAuthenticated])
    def get_total_payment(self, request):
        user = self.request.user
        regimen = self.request.query_params.get("regimen")
        try:
            day = _to_int_or_none(self.request.query_params.get("day"))
            month = _to_int_or_none(self.request.query_params.get("month"))
            year = _to_int_or_none(self.request.query_params.get("year"))
        except ValueError:
            raise ValidationError("ngày, tháng, năm phải là số dương")

        df, dt = create_df_dt(day, month, year)
        revenue = get_total_revenue_range(regimen, user, df, dt)
        payload = {"TotalPayment": revenue}

        if df and dt and df == dt:
            payload.update({"ngày": df.day, "tháng": df.month, "năm": df.year})
        elif df and dt and df.month == 1 and df.day == 1 and dt.month == 12:
            payload.update({"năm": df.year})
        elif df and dt and df.day == 1:
            payload.update({"tháng": df.month, "năm": df.year})
        return Response(payload, status=status.HTTP_200_OK)

    @action(methods=['GET'], url_path='current-user/wallet', detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def get_wallet(self, request):
        user = request.user
        wallet = user.wallet
        return Response(serializers.WalletSerializer(wallet).data, status=status.HTTP_200_OK)

    @action(methods=['POST'], url_path='current-user/wallet/deposit', detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def wallet_deposit(self, request):
        user = request.user
        amount = request.data.get('amount')
        description = request.data.get('description')
        wallet = user.wallet
        try:
            wallet.deposit(amount, description)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Có lỗi " + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "message": "Nạp tiền thành công",
            "balance": float(wallet.balance)
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], url_path='current-user/wallet/withdraw', detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def wallet_withdraw(self, request):
        user = request.user
        amount = request.data.get('amount')
        description = request.data.get('description')
        wallet = user.wallet
        try:
            wallet.withdraw(amount, description)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Có lỗi " + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "message": "Rút tiền thành công",
            "balance": float(wallet.balance)
        }, status=status.HTTP_200_OK)


class VehicleViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = serializers.VehicleSerializer
    permission_classes = [perms.IsVehicleOwner]

    def get_queryset(self):
        user = self.request.user
        return Vehicle.objects.filter(user=user)

    @action(methods=['get'], detail=False, url_path='stats', permission_classes=[permissions.IsAuthenticated])
    def vehicle_stats(self, request):
        user = request.user
        return Response(get_user_vehicle_stats(user), status=status.HTTP_200_OK)


class FeeRoleViewSet(viewsets.ViewSet, generics.ListAPIView, generics.UpdateAPIView,
                     generics.DestroyAPIView):
    queryset = FeeRule.objects.all()
    serializer_class = serializers.FeeRuleSerializer
    permission_classes = [perms.IsStaffOrReadOnly]


class PaymentViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = serializers.PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Payment.objects.filter(user=user)


class ParkingLogViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = serializers.ParkingLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginator.ItemParkingLog

    def get_queryset(self):
        user = self.request.user
        regimen = self.request.query_params.get("regimen")

        if regimen == 'my' or user.user_role == UserRole.CUSTOMER:
            parking_logs = ParkingLog.objects.filter(user=user, active=True)
        else:
            parking_logs = ParkingLog.objects.filter(active=True)

        try:
            day = _to_int_or_none(self.request.query_params.get("day"))
            month = _to_int_or_none(self.request.query_params.get("month"))
            year = _to_int_or_none(self.request.query_params.get("year"))
        except ValueError:
            raise ValidationError("ngày, tháng, năm phải là số dương")
        df, dt = create_df_dt(day, month, year)
        if df:
            parking_logs = parking_logs.filter(created_date__date__gte=df)
        if dt:
            parking_logs = parking_logs.filter(created_date__date__lte=dt)
        return parking_logs

    @action(methods=['get'], detail=False, url_path="occupancy", permission_classes=[perms.IsStaffOrAdmin])
    def get_parking_occupancy(self, request):
        count_occupancy = ParkingLog.objects.filter(status=ParkingStatus.IN).count()
        return Response({"occupancy": count_occupancy}, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path="count-today")
    def get_parking_count_today(self, request):
        now = date.today()
        count_today = ParkingLog.objects.filter(created_date__date=now).count()
        return Response(count_today, status=status.HTTP_200_OK)


class ScanPlateViewSet(APIView):
    def post(self, request, *args, **kwargs):
        if 'plate_img' not in request.FILES:
            return Response({"ok": False, "error": "Không có ảnh được gửi"}, status=status.HTTP_400_BAD_REQUEST)

        if 'face_img' not in request.FILES:
            return Response({"ok": False, "error": "Không có ảnh được gửi"}, status=status.HTTP_400_BAD_REQUEST)

        if 'vehicle_img' not in request.FILES:
            return Response({"ok": False, "error": "Không có ảnh được gửi"}, status=status.HTTP_400_BAD_REQUEST)

        face_img = request.FILES['face_img']
        save_path_face = upload_image(face_img, 'face', 'faces')

        plate_file = request.FILES['plate_img']
        save_path_plate = upload_image(plate_file, 'plate', 'plates')

        vehicle_file = request.FILES['vehicle_img']
        save_path_vehicle = upload_image(vehicle_file, 'vehicle', 'vehicles')

        direction = self.request.data.get('direction')
        try:
            emb = math_emb(save_path_face)
            plate_text = detect_license_plates(save_path_plate)
            ok, msg = proces(emb, face_img, save_path_vehicle, plate_text, direction)
            return Response({"ok": ok, "msg": msg, "plate_text": plate_text}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatsViewSet(viewsets.ViewSet):
    @action(methods=['get'], detail=False, url_path='revenue', permission_classes=[perms.IsStaffOrAdmin])
    def get_stats_revenue(self, request):
        user = self.request.user
        try:
            day = _to_int_or_none(self.request.query_params.get("day"))
            month = _to_int_or_none(self.request.query_params.get("month"))
            year = _to_int_or_none(self.request.query_params.get("year"))
        except ValueError:
            raise ValidationError("ngày, tháng, năm phải là số dương")

        df, dt = create_df_dt(day, month, year)
        revenue = get_total_revenue_range('all', user, df, dt)
        return Response(revenue, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='revenue/compare-monthly',
            permission_classes=[perms.IsStaffOrAdmin])
    def get_compare_monthly_revenue(self, request):
        user = self.request.user
        try:
            day = _to_int_or_none(self.request.query_params.get("day"))
            month = _to_int_or_none(self.request.query_params.get("month"))
            year = _to_int_or_none(self.request.query_params.get("year"))
        except ValueError:
            raise ValidationError("ngày, tháng, năm phải là số dương")
        current_start, current_end = create_df_dt(day, month, year)
        prev_start, prev_end = create_df_dt(day, month - 1, year)
        payload = compare_monthly_revenue(user, current_start, current_end, prev_start, prev_end)
        return Response(payload, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path="revenue/by-user", permission_classes=[perms.IsStaffOrAdmin])
    def get_revenue_by_user(self, request):
        try:
            day = _to_int_or_none(self.request.query_params.get("day"))
            month = _to_int_or_none(self.request.query_params.get("month"))
            year = _to_int_or_none(self.request.query_params.get("year"))
        except ValueError:
            raise ValidationError("ngày, tháng, năm phải là số dương")

        df, dt = create_df_dt(day, month, year)
        payload = get_revenue_by_user(df, dt)
        return Response(payload, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path="revenue/by-vehicle", permission_classes=[perms.IsStaffOrAdmin])
    def get_revenue_by_vehicle(self, request):
        try:
            day = _to_int_or_none(self.request.query_params.get("day"))
            month = _to_int_or_none(self.request.query_params.get("month"))
            year = _to_int_or_none(self.request.query_params.get("year"))
        except ValueError:
            raise ValidationError("ngày, tháng, năm phải là số dương")

        df, dt = create_df_dt(day, month, year)
        payload = get_revenue_by_vehicle(df, dt)
        return Response(payload, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='parking-logs/count',
            permission_classes=[permissions.IsAuthenticated])
    def get_count_parking_log(self, request):
        user = self.request.user
        regimen = self.request.query_params.get("regimen")
        try:
            day = _to_int_or_none(self.request.query_params.get("day"))
            month = _to_int_or_none(self.request.query_params.get("month"))
            year = _to_int_or_none(self.request.query_params.get("year"))
        except ValueError:
            raise ValidationError("ngày, tháng, năm phải là số dương")

        df, dt = create_df_dt(day, month, year)
        count_parking_log = get_total_count_parking(regimen, user, df, dt)
        payload = {"countParkingLog": count_parking_log}

        if df and dt and df == dt:
            payload.update({"ngày": f"{df.day}/{df.month}/{df.year}"})
        elif df and dt and df.month == 1 and df.day == 1 and dt.month == 12:
            payload.update({"năm": df.year})
        elif df and dt and df.day == 1:
            payload.update({"tháng": f"{df.month}/{df.year}"})
        return Response(payload, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='parking-logs/total-time',
            permission_classes=[permissions.IsAuthenticated])
    def get_total_time_parking_log(self, request):
        user = self.request.user
        regimen = self.request.query_params.get("regimen")
        try:
            day = _to_int_or_none(self.request.query_params.get("day"))
            month = _to_int_or_none(self.request.query_params.get("month"))
            year = _to_int_or_none(self.request.query_params.get("year"))
        except ValueError:
            raise ValidationError("ngày, tháng, năm phải là số dương")

        df, dt = create_df_dt(day, month, year)
        total_time = get_total_time_parking(regimen, user, df, dt)
        payload = {"totalTime": total_time}

        if df and dt and df == dt:
            payload.update({"ngày": f"{df.day}/{df.month}/{df.year}"})
        elif df and dt and df.month == 1 and df.day == 1 and dt.month == 12:
            payload.update({"năm": df.year})
        elif df and dt and df.day == 1:
            payload.update({"tháng": f"{df.month}/{df.year}"})
        return Response(payload, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='total-customer',
            permission_classes=[perms.IsStaffOrAdmin])
    def get_total_customer(self, request):
        payload = get_total_customer()
        return Response(payload, status=status.HTTP_200_OK)


class WalletTransactionViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = serializers.WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = paginator.ItemWalletTransaction

    def get_queryset(self):
        user = self.request.user
        return WalletTransaction.objects.filter(wallet=user.wallet, active=True)


def _to_int_or_none(value: Optional[str]) -> Optional[int]:
    if value is None or value == '':
        return None
    ivalue = int(value)
    if ivalue <= 0:
        raise ValueError
    return ivalue

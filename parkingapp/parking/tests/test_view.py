from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import Vehicle
from unittest.mock import patch
from ..models import FeeRule, ParkingLog, UserRole, ParkingStatus, UserFace
from datetime import datetime, timedelta, date

User = get_user_model()


class UserViewSetTestCase(APITestCase):
    def setUp(self):
        # Tạo user test
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            full_name="Test User",
            address="HN",
            birth=2000
        )
        # Tạo wallet cho user
        self.wallet = self.user.wallet

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)  # auto login

    def test_get_current_user(self):
        url = reverse("users-get-current-user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_patch_current_user(self):
        url = reverse("users-get-current-user")
        data = {"full_name": "Updated Name", "address": "HCM"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")
        self.assertEqual(self.user.address, "HCM")

    def test_patch_current_user_invalid_birth(self):
        url = reverse("users-get-current-user")
        data = {"birth": "invalid"}  # không phải số
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("birth", response.data)

    def test_get_total_payment(self):
        url = reverse("users-get-total-payment")
        response = self.client.get(url, {"day": "1", "month": "1", "year": "2025"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("TotalPayment", response.data)

    def test_get_wallet(self):
        url = reverse("users-get-wallet")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("balance", response.data)

    def test_wallet_deposit(self):
        url = reverse("users-wallet-deposit")
        data = {"amount": 1000, "description": "Nạp tiền test"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("message"), "Nạp tiền thành công")
        # Kiểm tra balance tăng
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 1000)

    def test_wallet_withdraw(self):
        # Nạp trước để có tiền rút
        self.wallet.deposit(1000)
        url = reverse("users-wallet-withdraw")
        data = {"amount": 500, "description": "Rút tiền test"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("message"), "Rút tiền thành công")
        # Kiểm tra balance giảm
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 500)


class VehicleViewSetTestCase(APITestCase):
    def setUp(self):
        # Tạo user và authenticate
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Tạo một vehicle mẫu
        self.vehicle = Vehicle.objects.create(
            user=self.user,
            name='Xe test',
            license_plate='30A-12345',
            is_approved=True
        )

    def test_list_vehicles(self):
        url = reverse('vehicle-list')  # tên url từ router
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(response.data[0]['name'], self.vehicle.name)

    def test_update_vehicle(self):
        url = reverse('vehicle-detail', args=[self.vehicle.id])
        data = {'name': 'Xe updated'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.name, 'Xe updated')

    def test_delete_vehicle(self):
        url = reverse('vehicle-detail', args=[self.vehicle.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Vehicle.objects.filter(id=self.vehicle.id).exists())

    @patch('parking.services.vehicle.get_user_vehicle_stats')
    def test_vehicle_stats(self, mock_get_stats):
        mock_get_stats.return_value = {'total': 1, 'approved': 1}
        url = reverse('vehicle-vehicle-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['approved'], 1)


class FeeRuleViewSetTestCase(APITestCase):
    def setUp(self):
        # Tạo user staff và authenticate
        self.staff_user = User.objects.create_user(username='staff', password='test123', user_role=UserRole.ADMIN)
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff_user)

        # Tạo 2 fee rule để test
        self.fee1 = FeeRule.objects.create(fee_type='hourly', amount=1000, active=True)
        self.fee2 = FeeRule.objects.create(fee_type='daily', amount=20000, active=True)

    def test_list_fee_rules(self):
        url = reverse('fee-rule-list')  # tùy router basename
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn('fee_type', response.data[0])
        self.assertIn('amount', response.data[0])

    def test_update_fee_rule(self):
        url = reverse('fee-rule-detail', args=[self.fee1.id])
        data = {'amount': 1500, 'active': False}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.fee1.refresh_from_db()
        self.assertEqual(self.fee1.amount, 1500)
        self.assertEqual(self.fee1.active, False)

    def test_delete_fee_rule(self):
        url = reverse('fee-rule-detail', args=[self.fee2.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FeeRule.objects.filter(id=self.fee2.id).exists())


class ParkingLogViewSetTestCase(APITestCase):
    def setUp(self):
        # Tạo user và staff
        self.customer = User.objects.create_user(username='customer', password='123', user_role=UserRole.CUSTOMER)
        self.staff = User.objects.create_user(username='staff', password='123', is_staff=True, user_role=UserRole.STAFF)

        # Tạo vehicle và fee_rule
        self.vehicle = Vehicle.objects.create(user=self.customer, name='Xe khách', license_plate='30A-12345',
                                              vehicle_type='car')
        self.fee_rule = FeeRule.objects.create(fee_type='hourly', amount=1000, active=True)

        # Tạo UserFace (nếu cần)
        self.user_face = UserFace.objects.create(embedding='fake_face_data')

        self.client = APIClient()

        # Tạo một số parking log
        now = datetime.now()
        ParkingLog.objects.create(
            user=self.customer, vehicle=self.vehicle, fee_rule=self.fee_rule,
            status=ParkingStatus.IN, active=True, check_in=now, user_face=self.user_face
        )
        ParkingLog.objects.create(
            user=self.customer, vehicle=self.vehicle, fee_rule=self.fee_rule,
            status=ParkingStatus.OUT, active=True, check_in=now - timedelta(days=1)
        )
        ParkingLog.objects.create(
            user=self.staff, vehicle=self.vehicle, fee_rule=self.fee_rule,
            status=ParkingStatus.IN, active=True, check_in=now
        )

    def test_list_parking_logs_customer(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('parking-log-list')
        response = self.client.get(url, {'regimen': 'my'})
        self.assertEqual(response.status_code, 200)
        for log in response.data['results']:
            self.assertEqual(log['user'], self.customer.full_name)  # chỉ có logs của customer

    def test_list_parking_logs_all_staff(self):
        self.client.force_authenticate(user=self.staff)
        url = reverse('parking-log-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results']), 1)  # staff xem tất cả logs

    def test_get_parking_occupancy(self):
        self.client.force_authenticate(user=self.staff)
        url = reverse('parking-log-get-parking-occupancy')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('occupancy', response.data)
        self.assertGreaterEqual(response.data['occupancy'], 1)

    def test_get_parking_count_today(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('parking-log-get-parking-count-today')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, int)


# class StatsViewSetTestCase(APITestCase):
#     def setUp(self):
#         # Tạo user staff
#         self.staff = User.objects.create_user(
#             username="staffuser",
#             password="pass123",
#             user_role=UserRole.ADMIN
#         )
#         self.client = APIClient()
#         self.client.force_authenticate(user=self.staff)
#
#     @patch("parking.services.finance.get_total_revenue_range")
#     def test_get_stats_revenue(self, mock_get_total_revenue_range):
#         mock_get_total_revenue_range.return_value = 10000
#         url = reverse("stats-get-stats-revenue")
#         response = self.client.get(url, {"day": 1, "month": 1, "year": 2025})
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data, 10000)
#
#     @patch("parking.services.finance.compare_monthly_revenue")
#     def test_get_compare_monthly_revenue(self, mock_compare_monthly):
#         mock_compare_monthly.return_value = {"revenue": 10000, "change_percent": 10.0}
#         url = reverse("stats-get-compare-monthly-revenue")
#         response = self.client.get(url, {"day": 1, "month": 8, "year": 2025})
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data, {"revenue": 10000, "change_percent": 10.0})
#
#     @patch("parking.services.finance.get_revenue_by_user")
#     def test_get_revenue_by_user(self, mock_get_by_user):
#         mock_get_by_user.return_value = [{"user": 1, "revenue": 5000}]
#         url = reverse("stats-get-revenue-by-user")
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data, [{"user": 1, "revenue": 5000}])
#
#     @patch("parking.services.finance.get_revenue_by_vehicle")
#     def test_get_revenue_by_vehicle(self, mock_get_by_vehicle):
#         mock_get_by_vehicle.return_value = [{"vehicle": 1, "revenue": 7000}]
#         url = reverse("stats-get-revenue-by-vehicle")
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data, [{"vehicle": 1, "revenue": 7000}])
#
#     @patch("parking.views.get_total_count_parking")
#     def test_get_count_parking_log(self, mock_get_count):
#         mock_get_count.return_value = 5
#         url = reverse("stats-get-count-parking-log")
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data["countParkingLog"], 5)
#
#     @patch("parking.services.parking.get_total_time_parking")
#     def test_get_total_time_parking_log(self, mock_get_time):
#         mock_get_time.return_value = 120
#         url = reverse("stats-get-total-time-parking-log")
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data["totalTime"], 120)
#
#     @patch("parking.services.users.get_total_customer")
#     def test_get_total_customer(self, mock_get_total_customer):
#         mock_get_total_customer.return_value = 50
#         url = reverse("stats-get-total-customer")
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data, 50)

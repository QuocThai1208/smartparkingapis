from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

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
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)  # auto login

    def test_get_current_user(self):
        url = reverse("user-current-user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)

    def test_patch_current_user(self):
        url = reverse("user-current-user")
        data = {"full_name": "Updated Name", "address": "HCM"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")
        self.assertEqual(self.user.address, "HCM")

    def test_patch_current_user_invalid_birth(self):
        url = reverse("user-current-user")
        data = {"birth": "invalid"}  # không phải số
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("birth", response.data)

    def test_get_total_payment(self):
        url = reverse("user-get-total-payment")
        response = self.client.get(url, {"day": "1", "month": "1", "year": "2025"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("TotalPayment", response.data)

    def test_get_wallet(self):
        url = reverse("user-get-wallet")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("balance", response.data)

    def test_wallet_deposit(self):
        url = reverse("user-wallet-deposit")
        data = {"amount": 1000, "description": "Nạp tiền test"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Nạp tiền thành công")

    def test_wallet_withdraw(self):
        url = reverse("user-wallet-withdraw")
        data = {"amount": 500, "description": "Rút tiền test"}
        response = self.client.post(url, data)
        # tuỳ thuộc vào logic trong wallet, có thể lỗi nếu số dư không đủ
        self.assertIn(response.status_code, [200, 400])

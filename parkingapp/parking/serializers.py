import os
from rest_framework import serializers
from datetime import date, datetime

from .models import (User,
                     Vehicle,
                     FeeRule,
                     Payment,
                     ParkingLog,
                     Wallet,
                     WalletTransaction,
                     UserFace)

from .services.helpers import upload_image
from .services.detection_plate import detect_vehicle


class ImageFieldMixin:
    def get_image_url(self, instance, field_name):
        field = getattr(instance, field_name)
        return field.url if field else ''


class UserFullNameMixin:
    def get_user_full_name(self, obj):
        return obj.user.full_name


def format_datetime(dt: datetime):
    return dt.strftime("%H:%M:%S %d/%m/%Y") if dt else None


class UserSerializer(serializers.ModelSerializer, ImageFieldMixin):
    age = serializers.SerializerMethodField(read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['avatar'] = self.get_image_url(instance, 'avatar')
        return data

    def create(self, validated_data):
        data = validated_data.copy()
        u = User(**data)
        u.set_password(u.password)
        u.save()
        return u

    class Meta:
        model = User
        fields = ['username', 'full_name', 'avatar', 'address', 'birth', 'age', 'password', 'user_role']
        extra_kwargs = {
            'password': {'write_only': True},
            'user_role': {'read_only': True}
        }

    def get_age(self, obj):
        if not obj.birth:
            return None
        today = date.today()
        return today.year - obj.birth


class VehicleSerializer(serializers.ModelSerializer, ImageFieldMixin, UserFullNameMixin):
    user = serializers.SerializerMethodField(read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['image'] = self.get_image_url(instance, 'image')
        return data

    class Meta:
        model = Vehicle
        fields = ['id', 'user', 'name', 'license_plate', 'vehicle_type', 'image', 'is_approved']
        extra_kwargs = {
            'user': {'read_only': True},
            'vehicle_type': {'read_only': True}
        }

    def get_user(self, obj):
        return self.get_user_full_name(obj)

    def create(self, validated_data):
        user = self.context['request'].user
        image_file = validated_data.get('image')
        save_path = upload_image(image_file, 'vehicle', 'vehicles')

        try:
            vehicle_type = detect_vehicle(save_path)
            if not vehicle_type:
                raise serializers.ValidationError({'image': 'Không nhận diện được loại xe'})

            validated_data['user'] = user
            validated_data['vehicle_type'] = vehicle_type
            return super().create(validated_data)
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)


class FeeRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeRule
        fields = ['id', 'fee_type', 'amount', 'active', 'effective_from', 'effective_to']


class PaymentSerializer(serializers.ModelSerializer, UserFullNameMixin):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = ['user', 'amount', 'status']
        extra_kwargs = {
            'user': {
                'read_only': True
            }
        }

    def get_user(self, obj):
        return self.get_user_full_name(obj)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['status']


class ParkingLogSerializer(serializers.ModelSerializer, UserFullNameMixin):
    user = serializers.SerializerMethodField(read_only=True)
    check_in = serializers.SerializerMethodField()
    check_out = serializers.SerializerMethodField()
    vehicle = serializers.SerializerMethodField()
    fee_rule = serializers.SerializerMethodField()

    class Meta:
        model = ParkingLog
        fields = ['id', 'user', 'vehicle', 'fee_rule', 'check_in', 'check_out', 'duration_minutes', 'fee', 'status']
        extra_kwargs = {
            'duration_minutes': {'read_only': True},
            'check_in': {'read_only': True}
        }

    def get_fee_rule(self, obj):
        return obj.fee_rule.fee_type

    def get_vehicle(self, obj):
        return {
            "name": obj.vehicle.name,
            "license_plate": obj.vehicle.license_plate
        }

    def get_user(self, obj):
        return self.get_user_full_name(obj)

    def get_check_in(self, obj):
        return format_datetime(obj.check_in)

    def get_check_out(self, obj):
        return format_datetime(obj.check_out)


class WalletSerializer(serializers.ModelSerializer, UserFullNameMixin):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ['user', 'balance', 'active']

    def get_user(self, obj):
        return self.get_user_full_name(obj)


class WalletTransactionSerializer(serializers.ModelSerializer):
    created_date = serializers.SerializerMethodField()

    class Meta:
        model = WalletTransaction
        fields = ['id', 'wallet', 'amount', 'transaction_type', 'description', 'created_date']

    def get_created_date(self, obj):
        return format_datetime(obj.created_date)


class UserFaceSerializer(serializers.ModelSerializer, ImageFieldMixin):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['face_img'] = self.get_image_url(instance, 'face_img')
        return data

    class Meta:
        model = UserFace
        fields = ['id', 'face_img', 'extra_embeddings']

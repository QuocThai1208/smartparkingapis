from rest_framework.pagination import PageNumberPagination


class ItemParkingLog(PageNumberPagination):
    page_size =  3


class ItemWalletTransaction(PageNumberPagination):
    page_size = 5
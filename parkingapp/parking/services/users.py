from ..models import User, UserRole


def get_total_customer():
    total_customer = User.objects.filter(user_role=UserRole.CUSTOMER).count()
    return {"totalCustomer": total_customer}
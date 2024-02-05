from django.conf import settings

from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = getattr(settings, "PAGE_SIZE", 6)
    page_size_query_param = "limit"

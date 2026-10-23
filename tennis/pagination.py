from rest_framework.pagination import PageNumberPagination

class SixPerPagePagination(PageNumberPagination):
    page_size = 6
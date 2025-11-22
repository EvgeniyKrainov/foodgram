from config.constants import DEFAULT_PAGE_SIZE
from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'

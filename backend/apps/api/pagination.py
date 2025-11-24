from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from config.constants import DEFAULT_PAGE_SIZE


class FoodgramPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'

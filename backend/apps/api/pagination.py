from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class FoodgramPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

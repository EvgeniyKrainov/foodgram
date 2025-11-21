from rest_framework.pagination import PageNumberPagination
from config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class FoodgramPagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
    
    def get_page_size(self, request):
        print(f"Pagination debug: page_size_query_param={self.page_size_query_param}")
        print(f"Pagination debug: limit param={request.query_params.get('limit')}")
        return super().get_page_size(request)

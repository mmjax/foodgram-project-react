from rest_framework.pagination import PageNumberPagination


class RecipesSubscriptionsPagination(PageNumberPagination):
    page_size = 6

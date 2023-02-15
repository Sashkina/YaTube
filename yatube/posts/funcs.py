from django.core.paginator import Paginator


PAGES = 10


def get_page_object(request, post_list):
    paginator = Paginator(post_list, PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

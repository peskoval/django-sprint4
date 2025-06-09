from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class AuthorTestsMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user == self.get_object().author

    def handle_no_permission(self):
        return redirect(self.get_success_url())

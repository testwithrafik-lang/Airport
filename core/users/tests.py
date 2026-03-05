from django.test import TestCase
from rest_framework.test import APIClient, APIRequestFactory

from users.models import User
from users.permissions import IsAdmin, IsOwnerOrAdmin
from users.views import UserViewSet


class UserModelTests(TestCase):
    def test_user_roles_and_is_admin_property(self):
        admin = User.objects.create_user(
            email="admin@test.com",
            password="pass1234",
            role=User.Roles.ADMIN,
            is_staff=True,
        )
        user = User.objects.create_user(
            email="user@test.com",
            password="pass1234",
            role=User.Roles.USER,
            is_staff=False,
        )
        self.assertTrue(admin.is_admin)
        self.assertFalse(user.is_admin)


class UserPermissionsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="pass1234",
            role=User.Roles.ADMIN,
            is_staff=True,
        )
        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass1234",
            role=User.Roles.USER,
            is_staff=False,
        )

    def test_is_admin_permission_allows_admin(self):
        request = self.factory.get("/api/users/")
        request.user = self.admin
        view = UserViewSet(action="list")
        perm = IsAdmin()
        self.assertTrue(perm.has_permission(request, view))

    def test_is_admin_permission_denies_regular_user(self):
        request = self.factory.get("/api/users/")
        request.user = self.user
        view = UserViewSet(action="list")
        perm = IsAdmin()
        self.assertFalse(perm.has_permission(request, view))

    def test_is_owner_or_admin_allows_owner(self):
        request = self.factory.get("/api/users/")
        request.user = self.user
        view = UserViewSet(action="retrieve")
        perm = IsOwnerOrAdmin()
        self.assertTrue(perm.has_object_permission(request, view, self.user))

    def test_is_owner_or_admin_allows_admin_for_any_user(self):
        request = self.factory.get("/api/users/")
        request.user = self.admin
        view = UserViewSet(action="retrieve")
        perm = IsOwnerOrAdmin()
        self.assertTrue(perm.has_object_permission(request, view, self.user))


class UserViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="pass1234",
            role=User.Roles.ADMIN,
            is_staff=True,
        )
        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass1234",
            role=User.Roles.USER,
            is_staff=False,
        )

    def test_register_user_uses_register_serializer(self):
        data = {"email": "new@test.com", "password": "StrongPass123!", "phone": "123456789"}
        response = self.client.post("/api/users/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)

    def test_regular_user_sees_only_self_in_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], self.user.email)

    def test_admin_sees_all_users_in_list(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 200)
        emails = {u["email"] for u in response.data}
        self.assertIn(self.user.email, emails)
        self.assertIn(self.admin.email, emails)

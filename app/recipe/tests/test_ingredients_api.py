from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient, Recipe
from recipe.serializers import IngreidentSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngreidentsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'testpassowrd'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='leo')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngreidentSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'leo@gmail.com',
            'testpassword'
        )

        Ingredient.objects.create(user=user2, name='Vinegar')
        ingredient = Ingredient.objects.create(user=self.user, name='Tomy')
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingreident_successful(self):
        payload = {'name': 'Cabbage'}
        self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_ingreident_invalid(self):
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipe(self):
        ingredient1 = Ingredient.objects.create(
            user=self.user, name='Apples'
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user, name='Turkey'
        )

        recipe = Recipe.objects.create(
            title='Apple crumble',
            time_minutes=2,
            price=12,
            user=self.user
        )
        recipe.ingreidents.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        serializer1 = IngreidentSerializer(ingredient1)
        serializer2 = IngreidentSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        ingredient = Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Cheese')
        recipe1 = Recipe.objects.create(
            title='Eggs benedict',
            time_minutes=30,
            price=12.00,
            user=self.user
        )
        recipe1.ingreidents.add(ingredient)
        recipe2 = Recipe.objects.create(
            title='Coriander eggs on toast',
            time_minutes=10,
            price=10,
            user=self.user
        )
        recipe2.ingreidents.add(ingredient)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)

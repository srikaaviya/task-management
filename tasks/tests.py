from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Task

class TaskTestCase(TestCase):
    def setUp(self):
        """Se ejecuta ANTES de cada test - prepara datos"""
        # crear un usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # crear una tarea de prueba
        self.task = Task.objects.create(
            description='Test description',
            user=self.user,
            priority='high',
            status='pending'
        )
        
    def test_task_creation(self):
        """Test 1: Verificar que una tarea se crea correctamente"""
        # verificar que la tarea existe
        self.assertEqual(self.task.user, self.user)
        self.assertEqual(self.task.priority, 'high')
        
        # verificar que se guardo en la base de datos
        saved_task = Task.objects.get(id=self.task.id)
        self.assertEqual(saved_task.description, 'Test description')

        
    

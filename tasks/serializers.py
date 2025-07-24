from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task Model
    Convierte entre instancias de Task y JSON
    """
    is_overdue = serializers.SerializerMethodField()

    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'due_date',
            'created_at',
            'updated_at',
            'user',
            'is_overdue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    def get_is_overdue(self, obj):
        return obj.due_date and obj.due_date < date.today()

class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para crear y actualizar tareas.
    Incluye solo campos editables para formularios.
    """
    priority = serializers.ChoiceField(choices=Task.Priority.choices, default=Task.Priority.LOW)
    status = serializers.ChoiceField(choices=Task.Status.choices, default=Task.Status.PENDING)
    
    class Meta:
        model = Task
        fields = [
            'title',
            'description', 
            'priority',
            'status',
            'due_date'
        ]
        
    def validate_title(self, value):
        """Validación personalizada para título"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()

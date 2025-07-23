from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task Model
    Convierte entre instancias de Task y JSON
    """
    is_overdue = serializers.ReadOnlyField()

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
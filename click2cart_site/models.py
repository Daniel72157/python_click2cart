from django.db import models
from django import forms
from django.forms import Textarea
from django.contrib.auth.models import User

class Usuario(models.Model):
    id_cuenta = models.AutoField(primary_key=True)
    user = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    mail = models.EmailField()
    cellnumber = models.CharField(max_length=10)

    
    class Meta:
        db_table = 'accounts'
class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    linkimage = models.FileField(upload_to='media/',  null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    clase = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=30, decimal_places=2)
    stock = models.IntegerField()
    accounts_id_cuenta = models.IntegerField()
    cantidad = models.IntegerField()
    def __str__(self):
        return self.nombre
    class Meta:
        db_table = 'productos'

class Carrito(models.Model):
    id_carrito = models.AutoField(primary_key=True)
    cantidad_productos = models.IntegerField()
    precio_producto = models.DecimalField(max_digits=30, decimal_places=2)
    productos_id_producto = models.TextField()
    accounts_id_cuenta = models.IntegerField()
    activo = models.IntegerField()
    def __str__(self):
        return str(self.id_carrito)
    class Meta:
        db_table = 'carrito'

class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    direccion_entrega = models.CharField(max_length=225)
    date = models.DateField()
    estado = models.IntegerField()
    accounts_id_cuenta = models.IntegerField()
    carrito_id_carrito = models.IntegerField()
    carrito_id_productos = models.TextField()
    def __str__(self):
        return str(self.id_pedido)
    class Meta:
        db_table = 'pedido'





    
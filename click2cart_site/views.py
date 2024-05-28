from django.shortcuts import render, redirect
from .models import Usuario, Producto, Carrito, Pedido
from django.http import JsonResponse
import json
from datetime import date
from collections import Counter
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

class log (object):
    id_user = 0

def back(request):
    return redirect('home')

def logout(request):
    log.id_user = 0
    return redirect('login')

def home(request):
    if log.id_user == 0:
        return redirect('login')
    else:
        print (log.id_user)
        return render(request, 'home-02.html')
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            usuario = Usuario.objects.get(user=username)
            # Verificar la contraseña
            if usuario.password == password:
                log.id_user = usuario.id_cuenta
                # Contraseña correcta, iniciar sesión y redirigir a la página de inicio
                request.session['username'] = username
                return JsonResponse({'success': True})
            else:
                # Contraseña incorrecta, mostrar mensaje de error
                return JsonResponse({'success': False, 'error_message': 'Usuario o contraseña incorrecto.'})
        except Usuario.DoesNotExist:
            # Si el usuario no existe, mostrar mensaje de error
            return JsonResponse({'success': False, 'error_message': 'Usuario inexistente.'})
    
    # Si no es una solicitud POST, renderizar la página de inicio de sesión
    return render(request, 'login.html')
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        cellnumber = request.POST['cellnumber']
        
        if not all([username, email, password, cellnumber]):
            return JsonResponse({'success': False, 'message': 'Todos los campos son obligatorios'})

        if Usuario.objects.filter(user=username).exists():
            error_message = "Username is already taken"
            return JsonResponse({'success': False, 'message': 'Ese nombre ya esta en uso'})

        if Usuario.objects.filter(mail=email).exists():
            error_message = "Email is already registered"
            return JsonResponse({'success': False, 'message': 'Ese Email ya esta en uso'})

        user = Usuario.objects.create(user=username, mail=email, password=password, cellnumber=cellnumber)

        return JsonResponse({'success': True})
    else:
        return render(request, 'registro.html')


def producto(request):
    if log.id_user == 0:
        return redirect('login')
    else:
        id_cuenta = log.id_user
        if request.method == "POST":
            linkimage = request.FILES.get("imagen")
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion")
            clase = request.POST.get("clase")
            precio = request.POST.get("precio")
            stock = request.POST.get("stock")

            producto = Producto(linkimage=linkimage, nombre=nombre, descripcion=descripcion, clase=clase, precio=precio, stock=stock, accounts_id_cuenta=id_cuenta, cantidad = 0)
            producto.save()
            return JsonResponse({'success': True})
        return render(request, "producto.html")

def product(request):
    if log.id_user == 0:
        return redirect('login')
    else:
        productos = Producto.objects.filter(stock__gt=0)
        return render(request, 'product.html', {'productos': productos})

@csrf_exempt
def agregarcarrito(request):
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad'))
        for _ in range(cantidad):
            carrito = Carrito.objects.filter(accounts_id_cuenta = log.id_user, activo = 1).first()
            id_producto = request.POST.get('idProducto')
            producto = Producto.objects.filter(id_producto = id_producto).first()
            if producto.stock < cantidad:
                return JsonResponse({'message': 'Error: solicitud no válida'}, status=400)
            if log.id_user != producto.accounts_id_cuenta:
                if carrito is not None:
                    productoslist = json.loads(carrito.productos_id_producto)
                    productoslist.append(id_producto)
                    carrito.productos_id_producto = json.dumps(productoslist)
                    carrito.cantidad_productos = len(productoslist)
                    total = sum([float(Producto.objects.get(id_producto = id_producto).precio) for id_producto in productoslist])
                    carrito.precio_producto = total
                    carrito.save()
                else:
                    carritonuevo = Carrito.objects.create(
                        precio_producto=producto.precio,  
                        accounts_id_cuenta=log.id_user,
                        cantidad_productos=1,
                        activo=True,
                        productos_id_producto=json.dumps([id_producto])
                    )
            else:
                return JsonResponse({'message': 'Error: solicitud no válida'}, status=400)
        return JsonResponse({'message': 'Producto agregado al carrito exitosamente'})
    else:
        return JsonResponse({'message': 'Error: solicitud no válida'}, status=400)

def carrito(request):
    if log.id_user == 0:
        return redirect('login')
    else:
        carrito = Carrito.objects.filter(accounts_id_cuenta = log.id_user, activo = 1).first()
        productocarrito = []
        if carrito is not None:
            listaproductos = json.loads(carrito.productos_id_producto)
            cantidad_productos = {}
            precio_final = carrito.precio_producto
            for id_producto in listaproductos:
                cantidad_productos[id_producto] = cantidad_productos.get(id_producto, 0) + 1

            for id_producto, cantidad in cantidad_productos.items():
                producto = Producto.objects.get(id_producto = id_producto)
                producto.cantidad = cantidad
                productocarrito.append(producto)

        else:
            productocarrito = []
            precio_final = 0
        return render(request, "shoping-cart.html", {'productocarrito': productocarrito, 'precio_final': precio_final})
    
def comprar(request):
    if request.method == 'POST':
        direccion_entrega = request.POST.get('direccion')
        if not direccion_entrega:
            return JsonResponse({'error': 'La dirección de entrega es obligatoria.'}, status=400)
        carrito = Carrito.objects.filter(accounts_id_cuenta=log.id_user, activo=1).first()
        if carrito is not None:
            listaproductos = json.loads(carrito.productos_id_producto)
            contador_productos = Counter(listaproductos)
            
            # Iniciamos una transacción
            with transaction.atomic():
                try:
                    for id_producto, cantidad_compra in contador_productos.items():
                        producto = Producto.objects.get(id_producto=id_producto)
                        if cantidad_compra > producto.stock:
                            mensaje_error = f"No hay suficiente stock para {producto.nombre}. Stock disponible: {producto.stock}"
                            return JsonResponse({'error': mensaje_error}, status=400) 
                    
                    # Verificamos que todas las cantidades sean válidas antes de decrementar el stock
                    for id_producto, cantidad_compra in contador_productos.items():
                        producto = Producto.objects.get(id_producto=id_producto)
                        producto.stock -= cantidad_compra
                        producto.save()
                    
                    # Si todas las operaciones tienen éxito, creamos el pedido
                    pedido = Pedido.objects.create(
                        direccion_entrega=direccion_entrega,
                        date=date.today(),
                        estado=1,
                        accounts_id_cuenta=log.id_user,
                        carrito_id_carrito=carrito.id_carrito,
                        carrito_id_productos=carrito.productos_id_producto
                    )
                    
                    carrito.activo = 0
                    carrito.save()
                except Exception as e:
                    # Si hay un error, hacemos rollback de la transacción
                    transaction.set_rollback(True)
                    return JsonResponse({'error': str(e)}, status=500)
                
            return redirect('historial')
        else:
            return JsonResponse({'error': 'No hay productos en el carrito'}, status=400)
def historial(request):
    if log.id_user == 0:
        return redirect('login')
    else:
        pedidos = Pedido.objects.filter(accounts_id_cuenta=log.id_user)
        historial = []
        if pedidos.exists():
            for pedido in pedidos:
                productos_pedido = []
                productos_id = json.loads(pedido.carrito_id_productos)
                for producto_id in productos_id:
                    producto = Producto.objects.get(id_producto=producto_id)
                    productos_pedido.append(producto)
                historial.append({
                    'pedido': pedido,
                    'productos': productos_pedido
                })
        return render(request, "historial.html", {'historial': historial})
            

def eliminar_producto_carrito(request):
    if log.id_user == 0:
        return redirect('login')
    else:
        if request.method == 'POST':
            id_producto = request.POST.get('producto_id')
            carrito = Carrito.objects.filter(accounts_id_cuenta=log.id_user, activo=1).first()
            if carrito:
                lista_productos = json.loads(carrito.productos_id_producto)
                if id_producto in lista_productos:
                    lista_productos.remove(id_producto)
                    carrito.productos_id_producto = json.dumps(lista_productos)
                    carrito.cantidad_productos -= 1
                    precio_total = sum(float(Producto.objects.filter(id_producto=pid).first().precio) for pid in lista_productos)
                    carrito.precio_producto = precio_total
                    carrito.save()
    return redirect('carrito')          

    

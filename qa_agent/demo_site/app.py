from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import os

app = Flask(__name__)
app.secret_key = 'demo-secret-key-for-hackathon'

# Break versioning for live demo site changes
BREAK_ID = 0

USERS = {'demo': 'password123'}
PRODUCTS = [
    {'id': 1, 'name': 'Blue Widget', 'price': 499},
    {'id': 2, 'name': 'Red Gadget', 'price': 799},
    {'id': 3, 'name': 'Green Gizmo', 'price': 299},
]

LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Login - Demo Shop</title>
<style>
body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
input { width: 100%; padding: 10px; margin: 5px 0 15px; box-sizing: border-box; }
button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; cursor: pointer; }
button:hover { background: #0056b3; }
.error { color: red; margin-bottom: 15px; }
</style>
</head>
<body>
<h2>Login to Demo Shop</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="POST">
<input type="text" name="login_{{ break_id }}" placeholder="Username" required>
<input type="password" name="pass_{{ break_id }}" placeholder="Password" required>
<button type="submit">Login</button>
</form>
<p><small>Demo credentials: demo / password123</small></p>
</body>
</html>
'''

SEARCH_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Search - Demo Shop</title>
<style>
body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
.product { border: 1px solid #ddd; padding: 15px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center; }
.product-info h3 { margin: 0 0 5px; }
.product-price { color: #28a745; font-weight: bold; }
button.add-cart { background: #28a745; color: white; border: none; padding: 8px 16px; cursor: pointer; }
button.add-cart:hover { background: #218838; }
.nav { margin-bottom: 20px; }
.nav a { margin-right: 15px; }
</style>
</head>
<body>
<div class="nav">
<a href="{{ url_for('search') }}">Search</a>
<a href="{{ url_for('cart') }}">Cart ({{ cart_count }})</a>
<a href="{{ url_for('logout') }}">Logout</a>
</div>
<h2>Search Products</h2>
<form method="GET">
<input type="text" name="q_{{ break_id }}" placeholder="Search products..." value="{{ query }}">
<button type="submit">Search</button>
</form>
{% if products %}
<h3>Results:</h3>
{% for product in products %}
<div class="product">
<div class="product-info">
<h3>{{ product.name }}</h3>
<div class="product-price">${{ product.price }}</div>
</div>
<form method="POST" action="{{ url_for('add_to_cart') }}">
<input type="hidden" name="product_id_{{ break_id }}" value="{{ product.id }}">
<button class="add-cart" type="submit">Add to Cart</button>
</form>
</div>
{% endfor %}
{% elif query %}
<p>No products found for "{{ query }}"</p>
{% endif %}
</body>
</html>
'''

CART_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Cart - Demo Shop</title>
<style>
body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
.cart-item { display: flex; justify-content: space-between; align-items: center; padding: 15px; border-bottom: 1px solid #eee; }
.item-info h3 { margin: 0 0 5px; }
.item-price { color: #28a745; }
.item-qty { margin: 0 10px; }
.total { font-size: 1.2em; font-weight: bold; margin: 20px 0; }
button.checkout { background: #007bff; color: white; border: none; padding: 12px 24px; font-size: 1em; cursor: pointer; }
button.checkout:hover { background: #0056b3; }
.nav { margin-bottom: 20px; }
.nav a { margin-right: 15px; }
</style>
</head>
<body>
<div class="nav">
<a href="{{ url_for('search') }}">Continue Shopping</a>
<a href="{{ url_for('logout') }}">Logout</a>
</div>
<h2>Shopping Cart</h2>
{% if cart_items %}
{% for item in cart_items %}
<div class="cart-item">
<div class="item-info">
<h3>{{ item.name }}</h3>
<div class="item-price">${{ item.price }} x {{ item.quantity }}</div>
</div>
<div class="item-total">${{ item.price * item.quantity }}</div>
</div>
{% endfor %}
<div class="total">Total: ${{ total }}</div>
<form method="POST" action="{{ url_for('checkout') }}">
<button class="checkout" type="submit">Proceed to Checkout</button>
</form>
{% else %}
<p>Your cart is empty. <a href="{{ url_for('search') }}">Continue shopping</a></p>
{% endif %}
</body>
</html>
'''

CHECKOUT_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Checkout - Demo Shop</title>
<style>
body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
.order-summary { background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
.order-item { display: flex; justify-content: space-between; padding: 5px 0; }
.total { font-weight: bold; font-size: 1.1em; border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px; }
button.confirm { background: #dc3545; color: white; border: none; padding: 12px 24px; font-size: 1em; cursor: pointer; }
button.confirm:hover { background: #c82333; }
.warning { background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
.nav { margin-bottom: 20px; }
.nav a { margin-right: 15px; }
</style>
</head>
<body>
<div class="nav">
<a href="{{ url_for('cart') }}">Back to Cart</a>
<a href="{{ url_for('logout') }}">Logout</a>
</div>
<h2>Checkout Review</h2>
<div class="warning">
<strong>⚠ Human Approval Required:</strong> This is the final step before payment. The agent will pause here and wait for human approval before proceeding.
</div>
<div class="order-summary">
<h3>Order Summary</h3>
{% for item in cart_items %}
<div class="order-item">
<span>{{ item.name }} x {{ item.quantity }}</span>
<span>${{ item.price * item.quantity }}</span>
</div>
{% endfor %}
<div class="order-item total">
<span>Total</span>
<span>${{ total }}</span>
</div>
</div>
<form method="POST" action="{{ url_for('confirm_order') }}">
<button class="confirm" type="submit">Confirm Order (Payment)</button>
</form>
</body>
</html>
'''

CONFIRM_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Order Confirmed - Demo Shop</title>
<style>
body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
.success { color: #28a745; }
.order-id { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
</style>
</head>
<body>
<h1 class="success">✓ Order Confirmed!</h1>
<div class="order-id">
Order ID: {{ order_id }}<br>
Total: ${{ total }}
</div>
<p>Thank you for your purchase! (This is a demo - no real payment was processed)</p>
<a href="{{ url_for('search') }}">Continue Shopping</a>
</body>
</html>
'''

def get_cart():
    if 'cart' not in session:
        session['cart'] = {}
    return session['cart']

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username') or request.form.get('login_')
        password = request.form.get('password') or request.form.get('pass_')
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('search'))
        return render_template_string(LOGIN_HTML, error='Invalid credentials')
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/search')
def search():
    if 'user' not in session:
        return redirect(url_for('login'))
    query = request.args.get('q', '').lower()
    cart = get_cart()
    cart_count = sum(cart.values())
    if query:
        filtered = [p for p in PRODUCTS if query in p['name'].lower()]
    else:
        filtered = PRODUCTS
    return render_template_string(SEARCH_HTML, products=filtered, query=query, cart_count=cart_count)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user' not in session:
        return redirect(url_for('login'))
    product_id = int(request.form.get('product_id'))
    cart = get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session.modified = True
    return redirect(url_for('search'))

@app.route('/cart')
def cart():
    if 'user' not in session:
        return redirect(url_for('login'))
    cart = get_cart()
    cart_items = []
    total = 0
    for pid, qty in cart.items():
        product = next((p for p in PRODUCTS if p['id'] == int(pid)), None)
        if product:
            cart_items.append({'name': product['name'], 'price': product['price'], 'quantity': qty})
            total += product['price'] * qty
    return render_template_string(CART_HTML, cart_items=cart_items, total=total)

@app.route('/checkout')
def checkout():
    if 'user' not in session:
        return redirect(url_for('login'))
    cart = get_cart()
    cart_items = []
    total = 0
    for pid, qty in cart.items():
        product = next((p for p in PRODUCTS if p['id'] == int(pid)), None)
        if product:
            cart_items.append({'name': product['name'], 'price': product['price'], 'quantity': qty})
            total += product['price'] * qty
    return render_template_string(CHECKOUT_HTML, cart_items=cart_items, total=total)

@app.route('/confirm-order', methods=['POST'])
def confirm_order():
    if 'user' not in session:
        return redirect(url_for('login'))
    cart = get_cart()
    total = 0
    for pid, qty in cart.items():
        product = next((p for p in PRODUCTS if p['id'] == int(pid)), None)
        if product:
            total += product['price'] * qty
    order_id = f"ORD-{os.urandom(4).hex().upper()}"
    session['cart'] = {}
    session.modified = True
    return render_template_string(CONFIRM_HTML, order_id=order_id, total=total)

# API endpoint to break the site for demo purposes
@app.route('/admin/break', methods=['POST'])
def break_site():
    break_type = request.json.get('type', 'rename_button')
    session = getattr(g, 'session', {})
    break_id = session.get('break_id', 0)
    
    # Swap between template versions to simulate site changes
    if break_type == 'rename_button':
        break_id = (break_id + 1) % 3
        session['break_id'] = break_id
        g.session = session
        
        # Return the break ID so the frontend can apply corresponding CSS changes
        return jsonify({'status': 'ok', 'break_id': break_id, 'message': f'Button ID renamed (break {break_id+1})'})
    
    elif break_type == 'add_confirm_modal':
        break_id = (break_id + 1) % 2
        session['break_id'] = break_id
        g.session = session
        return jsonify({'status': 'ok', 'break_id': break_id, 'message': f'Confirm modal added (break {break_id+1})'})
    
    elif break_type == 'move_field':
        break_id = (break_id + 1) % 3
        session['break_id'] = break_id
        g.session = session
        return jsonify({'status': 'ok', 'break_id': break_id, 'message': f'Form field moved (break {break_id+1})'})
    
    return jsonify({'status': 'ok', 'break_id': break_id, 'message': 'Break applied'})

@app.route('/admin/reset', methods=['POST'])
def reset_site():
    return jsonify({'status': 'ok', 'message': 'Site reset'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
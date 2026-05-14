from flask import Flask, request, render_template_string, redirect
from datetime import datetime
import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# ==================== KONFIGURASI ====================
STORE_NAME = 'MORAHSHOP'
WHATSAPP_ADMIN = '6285138718594'  # NOMOR BARU ANDA
EMAIL_SENDER = 'morahshop@gmail.com'
EMAIL_PASSWORD = 'ewsv nupx pvem olmq'
FONNTE_API_KEY = 'aM5d4QEx2uEV2bjt3ta3'

# Data produk default
products = {
    'name': 'Produk Digital Premium',
    'price': 50000,
    'description': 'Ebook + Video Tutorial Premium',
    'payment_instructions': 'Transfer ke BCA 1234567890 a.n MORAHSHOP\nKirim bukti transfer ke WhatsApp admin'
}

orders = []

# ==================== FUNGSI KIRIM WA ====================
def send_whatsapp(phone_number, message):
    try:
        phone_number = ''.join(filter(str.isdigit, phone_number))
        if phone_number.startswith('0'):
            phone_number = '62' + phone_number[1:]
        if not phone_number.startswith('62'):
            phone_number = '62' + phone_number
        
        url = "https://api.fonnte.com/send"
        headers = {"Authorization": FONNTE_API_KEY, "Content-Type": "application/x-www-form-urlencoded"}
        data = {"target": phone_number, "message": message, "countryCode": "62"}
        
        response = requests.post(url, headers=headers, data=data)
        return response.json().get('status', False)
    except Exception as e:
        print(f"WA Error: {e}")
        return False

# ==================== FUNGSI KIRIM EMAIL ====================
def send_email(to_email, customer_name, invoice_number, product_name, price, payment_link, qris_url):
    try:
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family:Arial;background:#f3f4f6;padding:20px;">
        <div style="max-width:500px;margin:auto;background:white;border-radius:16px;overflow:hidden;">
            <div style="background:#764ba2;padding:30px;text-align:center;color:white;">
                <h2>🧾 INVOICE PESANAN</h2>
            </div>
            <div style="padding:30px;">
                <p>Halo <b>{customer_name}</b>,</p>
                <p>Terima kasih telah berbelanja di <b>{STORE_NAME}</b>.</p>
                
                <div style="background:#f8f9fa;border-radius:12px;padding:20px;margin:20px 0;">
                    <b>📋 Invoice:</b> {invoice_number}<br><br>
                    <b>📅 Tanggal:</b> {datetime.now().strftime('%d %B %Y %H:%M')}<br><br>
                    <b>📦 Produk:</b> {product_name}<br><br>
                    <b>💰 Total:</b> <span style="font-size:20px;font-weight:bold;color:#764ba2;">Rp {price}</span><br><br>
                    <b>📊 Status:</b> 
                    <span style="background:#fef3c7;padding:5px 15px;border-radius:50px;">⏳ Menunggu Pembayaran</span>
                </div>
                
                <hr style="margin:25px 0;">
                <p style="font-size:12px;color:#999;text-align:center;">
                    Butuh bantuan? Hubungi: wa.me/{WHATSAPP_ADMIN}
                </p>
            </div>
            <div style="background:#111827;padding:15px;text-align:center;color:white;font-size:11px;">
                © 2026 {STORE_NAME}
            </div>
        </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Invoice {invoice_number} - {STORE_NAME}"
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg.attach(MIMEText(email_html, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        server.quit()
        
        print(f"✅ Email terkirim ke {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email gagal: {e}")
        return False

# ==================== TEMPLATE HTML ====================
HOME_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width">
    <title>{{ store }}</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}
        .card{background:white;border-radius:24px;padding:40px;max-width:450px;width:100%;text-align:center;box-shadow:0 20px 40px rgba(0,0,0,0.1)}
        h1{color:#333;margin-bottom:10px}
        .product-box{background:#f8f9fa;border-radius:16px;padding:25px;margin:25px 0}
        .product-name{font-size:22px;font-weight:bold;margin-bottom:10px}
        .price{font-size:32px;color:#764ba2;font-weight:bold;margin:10px 0}
        .btn{display:inline-block;background:#764ba2;color:white;padding:15px 30px;border-radius:50px;text-decoration:none;font-weight:bold;margin-top:15px}
        .admin-link{display:block;margin-top:20px;color:#999;font-size:12px}
    </style>
</head>
<body>
    <div class="card">
        <h1>🏪 {{ store }}</h1>
        <div class="product-box">
            <div class="product-name">{{ product_name }}</div>
            <div class="price">Rp {{ product_price }}</div>
            <p>{{ product_desc }}</p>
        </div>
        <a href="/checkout" class="btn">🛒 Beli Sekarang</a>
        <a href="/admin" class="admin-link">⚙️ Admin</a>
    </div>
</body>
</html>
'''

CHECKOUT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width">
    <title>Checkout - {{ store }}</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:Arial;background:#f0f0f0;padding:20px}
        .container{max-width:500px;margin:auto;background:white;border-radius:20px;padding:30px}
        h2{text-align:center;margin-bottom:20px}
        .product-info{background:#f8f9fa;padding:15px;border-radius:12px;margin-bottom:20px;text-align:center}
        .price{color:#764ba2;font-size:24px;font-weight:bold}
        input{width:100%;padding:14px;margin:10px 0;border:1px solid #ddd;border-radius:10px;font-size:16px}
        button{width:100%;padding:16px;background:#764ba2;color:white;border:none;border-radius:10px;font-size:16px;font-weight:bold;cursor:pointer}
        label{font-weight:bold;display:block;margin-top:10px}
    </style>
</head>
<body>
    <div class="container">
        <h2>🛒 Checkout</h2>
        <div class="product-info">
            <div><strong>{{ product_name }}</strong></div>
            <div class="price">Rp {{ product_price }}</div>
        </div>
        <form method="POST" action="/process-checkout">
            <label>Nama Lengkap</label>
            <input type="text" name="customer" required>
            <label>Email</label>
            <input type="email" name="email" required>
            <label>WhatsApp</label>
            <input type="tel" name="whatsapp" placeholder="08123456789" required>
            <button type="submit">✅ Konfirmasi Pesanan</button>
        </form>
    </div>
</body>
</html>
'''

SUCCESS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width">
    <title>Sukses - {{ store }}</title>
    <style>
        body{font-family:Arial;background:#f0f0f0;display:flex;justify-content:center;align-items:center;min-height:100vh}
        .card{background:white;border-radius:20px;padding:40px;text-align:center;max-width:400px}
        .check{font-size:60px;color:#22c55e}
        .btn{display:inline-block;background:#764ba2;color:white;padding:12px 24px;border-radius:50px;text-decoration:none;margin-top:20px}
        .info{background:#e8f4f8;border-radius:12px;padding:15px;margin:20px 0;text-align:left;font-size:14px}
    </style>
</head>
<body>
    <div class="card">
        <div class="check">✅</div>
        <h2>Pesanan Berhasil!</h2>
        <p>Invoice: <strong>{{ invoice }}</strong></p>
        <div class="info">
            📧 Email invoice sudah dikirim ke email Anda<br>
            📱 WhatsApp juga sudah kami kirim
        </div>
        <a href="/" class="btn">Kembali ke Toko</a>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width">
    <title>Admin Panel - {{ store }}</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:Arial;background:#f0f0f0;padding:20px}
        .container{max-width:700px;margin:auto;background:white;border-radius:20px;padding:30px}
        input,textarea{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px}
        button{background:#764ba2;color:white;padding:14px;border:none;border-radius:8px;width:100%;font-weight:bold;cursor:pointer}
        .orders{margin-top:30px}
        .order-card{background:#f8f9fa;border-radius:12px;padding:15px;margin:10px 0;border-left:4px solid #764ba2}
        .status{display:inline-block;padding:4px 12px;border-radius:50px;font-size:12px;margin-top:8px}
        .status-pending{background:#fef3c7;color:#92400e}
        table{width:100%;border-collapse:collapse}
        th,td{padding:10px;text-align:left;border-bottom:1px solid #ddd}
        th{background:#764ba2;color:white}
    </style>
</head>
<body>
    <div class="container">
        <h2>⚙️ Admin Panel - {{ store }}</h2>
        
        <h3>📦 Edit Produk</h3>
        <form method="POST" action="/update-product">
            <input type="text" name="name" placeholder="Nama Produk" value="{{ product.name }}" required>
            <input type="number" name="price" placeholder="Harga" value="{{ product.price }}" required>
            <textarea name="description" placeholder="Deskripsi" rows="2">{{ product.description }}</textarea>
            <textarea name="payment_instructions" placeholder="Instruksi Pembayaran" rows="3">{{ product.payment_instructions }}</textarea>
            <button type="submit">💾 Simpan Produk</button>
        </form>
        
        <div class="orders">
            <h3>📋 Daftar Pesanan ({{ orders|length }})</h3>
            {% if orders %}
            <table>
                <tr>
                    <th>Invoice</th>
                    <th>Customer</th>
                    <th>Total</th>
                    <th>Status</th>
                </tr>
                {% for order in orders %}
                <tr>
                    <td>{{ order.invoice }}</td>
                    <td>{{ order.customer_name }}</td>
                    <td>Rp {{ order.price }}</td>
                    <td>⏳ {{ order.status }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
                <p>✨ Belum ada pesanan</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

# ==================== ROUTES ====================

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE, 
        store=STORE_NAME,
        product_name=products['name'],
        product_price=f"{products['price']:,}",
        product_desc=products['description']
    )

@app.route('/checkout')
def checkout():
    return render_template_string(CHECKOUT_TEMPLATE, 
        store=STORE_NAME,
        product_name=products['name'],
        product_price=f"{products['price']:,}"
    )

@app.route('/process-checkout', methods=['POST'])
def process_checkout():
    customer = request.form['customer']
    email = request.form['email']
    whatsapp = request.form['whatsapp']
    
    whatsapp_clean = ''.join(filter(str.isdigit, whatsapp))
    if whatsapp_clean.startswith('0'):
        whatsapp_clean = '62' + whatsapp_clean[1:]
    
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Ganti QRIS dan Payment Link di sini sesuai kebutuhan
    payment_link = "https://your-payment-link.com"
    qris_url = "https://upload.wikimedia.org/wikipedia/commons/0/04/QR_Code_Example.svg"
    
    order_data = {
        'invoice': invoice_number,
        'customer_name': customer,
        'customer_email': email,
        'customer_whatsapp': whatsapp_clean,
        'product_name': products['name'],
        'price': f"{products['price']:,}",
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    orders.insert(0, order_data)
    
    # Kirim Email
    send_email(email, customer, invoice_number, products['name'], f"{products['price']:,}", payment_link, qris_url)
    
    # Kirim WhatsApp
    wa_msg = f"""📋 INVOICE PESANAN
    
Halo {customer},

Terima kasih telah berbelanja di {STORE_NAME}

━━━━━━━━━━━━━━━━━━
📦 Produk: {products['name']}
💰 Harga: Rp {products['price']:,}
📋 Invoice: {invoice_number}
📅 Tanggal: {datetime.now().strftime('%d/%m/%Y %H:%M')}
📊 Status: ⏳ Menunggu Pembayaran
━━━━━━━━━━━━━━━━━━

💳 Cara Bayar:
{products['payment_instructions']}

Admin: wa.me/{WHATSAPP_ADMIN}"""
    
    send_whatsapp(whatsapp_clean, wa_msg)
    send_whatsapp(WHATSAPP_ADMIN, f"🔔 PESANAN BARU!\n\n👤 {customer}\n📱 {whatsapp_clean}\n📧 {email}\n📋 {invoice_number}")
    
    return render_template_string(SUCCESS_TEMPLATE, store=STORE_NAME, invoice=invoice_number)

@app.route('/admin')
def admin():
    return render_template_string(ADMIN_TEMPLATE, store=STORE_NAME, product=products, orders=orders)

@app.route('/update-product', methods=['POST'])
def update_product():
    products['name'] = request.form['name']
    products['price'] = int(request.form['price'])
    products['description'] = request.form.get('description', '')
    products['payment_instructions'] = request.form.get('payment_instructions', '')
    return redirect('/admin')

@app.route('/test-wa')
def test_wa():
    result = send_whatsapp(WHATSAPP_ADMIN, "🧪 Test dari MORAHSHOP!")
    return "✅ WA OK" if result else "❌ WA GAGAL"

@app.route('/test-email')
def test_email():
    result = send_email(EMAIL_SENDER, "Test", "TEST-001", "Test", "50000", "", "")
    return "✅ EMAIL OK" if result else "❌ EMAIL GAGAL"

if __name__ == '__main__':
    app.run()

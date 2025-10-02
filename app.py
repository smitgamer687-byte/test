from flask import Flask, request, jsonify, render_template_string
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Configuration - Environment Variables se load hoga
API_KEY = os.environ.get('API_KEY', '86db3795785983d81d077bd7238adbd1')
BASE_URL = "https://pay0.shop"

# HTML Template for Payment Link Generator
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Link Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            font-size: 28px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:active {
            transform: translateY(0);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        .result.show {
            display: block;
        }
        .payment-link {
            word-break: break-all;
            color: #667eea;
            font-weight: 600;
            margin: 10px 0;
            background: white;
            padding: 10px;
            border-radius: 5px;
        }
        .copy-btn {
            padding: 8px 16px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
            width: auto;
        }
        .copy-btn:hover {
            background: #218838;
        }
        .check-btn {
            background: #007bff;
            margin-left: 10px;
        }
        .check-btn:hover {
            background: #0056b3;
        }
        .error {
            color: #dc3545;
            margin-top: 10px;
            padding: 10px;
            background: #f8d7da;
            border-radius: 5px;
        }
        .success {
            color: #28a745;
            margin-top: 10px;
        }
        .order-info {
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .order-info p {
            margin: 5px 0;
            color: #555;
        }
        .webhook-url {
            margin-top: 20px;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        .webhook-url h4 {
            color: #007bff;
            margin-bottom: 10px;
        }
        .webhook-url code {
            background: white;
            padding: 8px;
            border-radius: 4px;
            display: block;
            word-break: break-all;
            color: #333;
            font-size: 14px;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💰 Payment Link Generator</h1>
        
        <div class="webhook-url">
            <h4>📡 Webhook URL (Copy this):</h4>
            <code id="webhookUrl">{{ webhook_url }}</code>
            <button class="copy-btn" onclick="copyWebhook()" style="margin-top: 10px;">📋 Copy Webhook URL</button>
        </div>
        
        <form id="paymentForm" method="post" action="javascript:void(0);" style="margin-top: 20px;">
            <div class="form-group">
                <label for="amount">Amount (₹)</label>
                <input type="number" id="amount" name="amount" required min="1" placeholder="Enter amount" value="50">
            </div>
            <div class="form-group">
                <label for="mobile">Customer Mobile</label>
                <input type="tel" id="mobile" name="mobile" placeholder="10 digit mobile number" pattern="[0-9]{10}" required>
            </div>
            <div class="form-group">
                <label for="remark">Remark (Optional)</label>
                <input type="text" id="remark" name="remark" placeholder="Purpose of payment">
            </div>
            <button type="submit" id="submitBtn">Generate Payment Link</button>
        </form>
        
        <div id="result" class="result">
            <h3>✅ Payment Link Generated!</h3>
            <div class="order-info">
                <p><strong>Order ID:</strong> <span id="orderId"></span></p>
                <p><strong>Amount:</strong> ₹<span id="orderAmount"></span></p>
            </div>
            <p class="payment-link" id="paymentLink"></p>
            <button class="copy-btn" onclick="copyLink()">📋 Copy Payment Link</button>
            <button class="copy-btn check-btn" onclick="checkStatus()">🔍 Check Status</button>
            <div id="statusResult"></div>
        </div>
    </div>

    <script>
        let currentOrderId = '';
        
        // Prevent form from submitting through URL parameters
        document.getElementById('paymentForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const submitBtn = document.getElementById('submitBtn');
            const amount = document.getElementById('amount').value;
            const mobile = document.getElementById('mobile').value;
            const remark = document.getElementById('remark').value;
            
            // Disable button and show loading
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Generating...';
            
            try {
                const response = await fetch('/generate-link', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        amount: amount,
                        mobile: mobile,
                        remark: remark
                    })
                });
                
                const data = await response.json();
                
                if (data.status) {
                    currentOrderId = data.order_id;
                    document.getElementById('orderId').textContent = data.order_id;
                    document.getElementById('orderAmount').textContent = amount;
                    document.getElementById('paymentLink').textContent = data.payment_url;
                    document.getElementById('result').classList.add('show');
                    
                    // Auto scroll to result
                    document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
                } else {
                    alert('❌ Error: ' + data.message);
                }
            } catch (error) {
                alert('❌ Error generating link: ' + error.message);
            } finally {
                // Re-enable button
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Generate Payment Link';
            }
        });
        
        function copyLink() {
            const link = document.getElementById('paymentLink').textContent;
            navigator.clipboard.writeText(link).then(() => {
                alert('✅ Payment link copied to clipboard!');
            }).catch(() => {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = link;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                alert('✅ Payment link copied!');
            });
        }
        
        function copyWebhook() {
            const webhook = document.getElementById('webhookUrl').textContent;
            navigator.clipboard.writeText(webhook).then(() => {
                alert('✅ Webhook URL copied to clipboard!');
            }).catch(() => {
                const textArea = document.createElement('textarea');
                textArea.value = webhook;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                alert('✅ Webhook URL copied!');
            });
        }
        
        async function checkStatus() {
            if (!currentOrderId) return;
            
            const statusDiv = document.getElementById('statusResult');
            statusDiv.innerHTML = '<p style="color: #007bff;">⏳ Checking status...</p>';
            
            try {
                const response = await fetch('/check-status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        order_id: currentOrderId
                    })
                });
                
                const data = await response.json();
                
                if (data.status) {
                    const txnStatus = data.result.txnStatus;
                    let statusColor = txnStatus === 'SUCCESS' ? '#28a745' : txnStatus === 'PENDING' ? '#ffc107' : '#dc3545';
                    let statusEmoji = txnStatus === 'SUCCESS' ? '✅' : txnStatus === 'PENDING' ? '⏳' : '❌';
                    
                    statusDiv.innerHTML = `
                        <div style="margin-top: 15px; padding: 15px; background: ${statusColor}20; border-left: 4px solid ${statusColor}; border-radius: 8px;">
                            <p><strong>${statusEmoji} Status:</strong> ${txnStatus}</p>
                            <p><strong>Amount:</strong> ₹${data.result.amount}</p>
                            <p><strong>Order ID:</strong> ${data.result.orderId}</p>
                            ${data.result.date ? <p><strong>Date:</strong> ${data.result.date}</p> : ''}
                            ${data.result.utr ? <p><strong>UTR:</strong> ${data.result.utr}</p> : ''}
                        </div>
                    `;
                } else {
                    statusDiv.innerHTML = <p class="error">❌ ${data.message}</p>;
                }
            } catch (error) {
                statusDiv.innerHTML = <p class="error">❌ Error: ${error.message}</p>;
            }
        }
        
        // Auto-refresh status every 10 seconds if order is pending
        setInterval(() => {
            if (currentOrderId && document.getElementById('statusResult').innerHTML.includes('PENDING')) {
                checkStatus();
            }
        }, 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Get webhook URL dynamically
    webhook_url = request.host_url.rstrip('/') + '/webhook'
    return render_template_string(HTML_TEMPLATE, webhook_url=webhook_url)

@app.route('/generate-link', methods=['POST'])
def generate_link():
    try:
        data = request.get_json()
        amount = data.get('amount')
        mobile = data.get('mobile')
        remark = data.get('remark', 'Payment')
        
        if not amount or not mobile:
            return jsonify({
                'status': False,
                'message': 'Amount and mobile number are required'
            }), 400
        
        # Generate unique order ID with timestamp
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        
        # Get webhook URL dynamically
        webhook_url = request.host_url.rstrip('/') + '/webhook'
        
        # Create order using API
        endpoint = f"{BASE_URL}/api/create-order"
        payload = {
            "customer_mobile": mobile,
            "user_token": API_KEY,
            "amount": str(amount),
            "order_id": order_id,
            "redirect_url": webhook_url,
            "remark1": remark,
            "remark2": f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
        }
        
        print("=" * 60)
        print("📤 CREATING PAYMENT ORDER:")
        print(f"Order ID: {order_id}")
        print(f"Amount: ₹{amount}")
        print(f"Mobile: {mobile}")
        print(f"Webhook URL: {webhook_url}")
        print("=" * 60)
        
        response = requests.post(
            endpoint, 
            data=payload, 
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        print(f"API Response Status: {response.status_code}")
        print(f"API Response: {response.text}")
        
        # Accept both 200 and 201 status codes (both indicate success)
        if response.status_code in [200, 201]:
            result = response.json()
            if result.get('status'):
                payment_url = result.get('result', {}).get('payment_url', '')
                
                return jsonify({
                    'status': True,
                    'order_id': order_id,
                    'payment_url': payment_url,
                    'message': 'Payment link generated successfully'
                })
            else:
                return jsonify({
                    'status': False,
                    'message': result.get('message', 'Failed to generate payment link')
                }), 400
        else:
            return jsonify({
                'status': False,
                'message': f'API returned status code: {response.status_code}'
            }), 400
        
    except requests.exceptions.Timeout:
        return jsonify({
            'status': False,
            'message': 'Request timeout - API took too long to respond'
        }), 500
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': False,
            'message': f'Network error: {str(e)}'
        }), 500
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            'status': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    try:
        # Handle both POST data and query parameters
        if request.method == 'POST':
            data = request.form.to_dict()
        else:
            data = request.args.to_dict()
        
        status = data.get('status')
        order_id = data.get('order_id')
        amount = data.get('amount')
        utr = data.get('utr')
        customer_mobile = data.get('customer_mobile')
        remark1 = data.get('remark1')
        remark2 = data.get('remark2')
        
        # Log webhook data with proper formatting
        log_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': status,
            'order_id': order_id,
            'amount': amount,
            'utr': utr,
            'customer_mobile': customer_mobile,
            'remark1': remark1,
            'remark2': remark2
        }
        
        print("\n" + "=" * 60)
        print("🔔 WEBHOOK RECEIVED!")
        print("=" * 60)
        for key, value in log_data.items():
            print(f"{key.upper():20s}: {value}")
        print("=" * 60 + "\n")
        
        # Process based on status
        if status == 'SUCCESS':
            # ✅ SUCCESS - Yahan aap apna logic add kar sakte hain
            # Jaise database mein save karna, email bhejana, etc.
            
            print(f"✅ Payment Successful for Order: {order_id}")
            print(f"💰 Amount: ₹{amount}")
            print(f"🔢 UTR: {utr}")
            
            # Example: Database mein save karne ka code yahan aayega
            # save_to_database(order_id, amount, utr, customer_mobile)
            
            return jsonify({
                'status': 'success',
                'message': 'Payment processed successfully',
                'order_id': order_id
            }), 200
            
        elif status == 'PENDING':
            print(f"⏳ Payment Pending for Order: {order_id}")
            return jsonify({
                'status': 'pending',
                'message': 'Payment is pending'
            }), 200
            
        elif status == 'FAILED':
            print(f"❌ Payment Failed for Order: {order_id}")
            return jsonify({
                'status': 'failed',
                'message': 'Payment failed'
            }), 200
        else:
            return jsonify({
                'status': 'received',
                'message': f'Webhook received with status: {status}'
            }), 200
            
    except Exception as e:
        print(f"❌ Webhook Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/check-status', methods=['POST'])
def check_status():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({
                'status': False,
                'message': 'Order ID is required'
            }), 400
        
        url = f"{BASE_URL}/api/check-order-status"
        payload = {
            "user_token": API_KEY,
            "order_id": order_id
        }
        
        print(f"🔍 Checking status for Order: {order_id}")
        
        response = requests.post(url, data=payload, timeout=10)
        
        # Accept both 200 and 201 status codes
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"Status Response: {result}")
            return jsonify(result)
        else:
            return jsonify({
                'status': False,
                'message': f'Status check failed with code: {response.status_code}'
            }), 400
            
    except requests.exceptions.Timeout:
        return jsonify({
            'status': False,
            'message': 'Status check timeout'
        }), 500
    except Exception as e:
        print(f"❌ Status Check Error: {str(e)}")
        return jsonify({
            'status': False,
            'message': str(e)
        }), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'webhook_url': request.host_url.rstrip('/') + '/webhook'
    })

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "=" * 60)
    print("🚀 Payment System Starting...")
    print(f"📡 Port: {port}")
    print(f"🔑 API Key Loaded: {'Yes' if API_KEY != 'your_api_key_here' else 'NO - Please set API_KEY environment variable'}")
    print("=" * 60 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)

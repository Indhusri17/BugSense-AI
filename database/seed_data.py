import os
import sys
import json

# Ensure project root is in sys.path when executed directly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db import get_db, init_db
from services.auth_service import hash_password

SEED_USERS = [
    ("tester1", "password123", "Sarah Jenkins (QA Lead)", "tester"),
    ("dev1", "password123", "Alex Chen (Senior Dev)", "developer"),
    ("dev2", "password123", "Priya Sharma (Frontend Dev)", "developer"),
    ("lead1", "password123", "Dave Miller (Engineering Lead)", "lead"),
    ("admin", "admin123", "System Administrator", "admin")
]

SEED_DEVELOPERS = [
    ("Alex Chen", "alex.chen@bugsense.ai", "Payment, Checkout", 2),
    ("Priya Sharma", "priya.sharma@bugsense.ai", "Cart, Catalog", 1),
    ("Marcus Vance", "marcus.vance@bugsense.ai", "Auth, Profile", 2),
    ("Elena Rostova", "elena.rostova@bugsense.ai", "Orders, Integration", 1)
]

SEED_CATEGORIES = [
    ("Payment / Order", "Payment gateway integration, webhook processing, order status transitions and checkout synchronization."),
    ("Functional", "Core business logic, cart arithmetic, discounts, user workflows, and state transitions."),
    ("UI/UX", "Visual rendering, client-side animations, layouts, responsive design, and CSS styling."),
    ("Security", "Authentication, authorization, token validity, credential handling, and SQL/XSS sanitization."),
    ("Performance", "Database query efficiency, N+1 queries, memory consumption, latency, and throughput."),
    ("Integration", "Third-party APIs, webhooks, OAuth providers, mail delivery, and external gateway contracts.")
]

# 50 Curated E-commerce Mock Application Bugs
SEED_BUGS = [
    # --- PAYMENT BUGS ---
    {
        "title": "Payment successful on Stripe but order status stuck in PENDING_PAYMENT / not displayed in My Orders",
        "description": "After successful payment through payment gateway, customer is charged and transaction succeeds, but the order is not displayed in My Orders and remains stuck in PENDING_PAYMENT instead of transitioning to CONFIRMED.",
        "steps_to_reproduce": "1. Add item to cart\n2. Proceed to checkout\n3. Enter valid test Visa card\n4. Submit payment\n5. Observe order confirmation and My Orders page",
        "expected_result": "Order status should immediately update to CONFIRMED, display in My Orders, and trigger confirmation email.",
        "actual_result": "Payment charged successfully, but order is not displayed in My Orders and status remains in PENDING_PAYMENT indefinitely.",
        "module": "Payment",
        "environment": "Production",
        "error_logs": "StripeWebhookError: Invalid signature header 'Stripe-Signature'. Webhook secret mismatch in prod environment variable.",
        "severity": "Critical",
        "category": "Payment / Order",
        "status": "Resolved",
        "root_cause": "Payment callback/order synchronization failure: The production STRIPE_WEBHOOK_SECRET environment variable was pointing to the sandbox webhook key after weekend deployment, preventing order creation transaction from committing.",
        "resolution_text": "Updated STRIPE_WEBHOOK_SECRET in production config vault to match live Stripe webhook endpoint and added automated signature validation integration tests."
    },
    {
        "title": "Double charge occurs when customer clicks Pay Now button multiple times",
        "description": "If user rapidly double-clicks the Pay Now button on mobile network latency, two separate Stripe payment intents are dispatched simultaneously, resulting in double deduction on customer credit card.",
        "steps_to_reproduce": "1. Go to payment step\n2. Throttle network to Slow 3G\n3. Click 'Pay Now' button twice quickly",
        "expected_result": "Button should disable upon first click and idempotency key should prevent duplicate charges.",
        "actual_result": "Two distinct charges appear on customer statement with two separate transaction IDs.",
        "module": "Payment",
        "environment": "Production",
        "error_logs": "StripeAPI: POST /v1/payment_intents (x2 received 180ms apart with unique client_request_id).",
        "severity": "Critical",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "The client-side Pay button lacked debouncing/disable state and the backend payment service generated an idempotency key based on timestamp rather than cart_id.",
        "resolution_text": "Implemented client-side button disable on submit with spinner, and tied backend Stripe idempotency key strictly to cart_id + user_id."
    },
    {
        "title": "Razorpay webhook signature verification failure on recurring mandate",
        "description": "Subscriptions created via Razorpay auto-debit fail to renew on the 1st of the month due to HMAC SHA256 checksum mismatch.",
        "steps_to_reproduce": "1. Subscribe to Monthly Coffee Box\n2. Wait for auto-renewal webhook trigger\n3. Check server logs",
        "expected_result": "Webhook verified and subscription renewed.",
        "actual_result": "Webhook returns HTTP 400 Bad Request with signature mismatch.",
        "module": "Payment",
        "environment": "Staging",
        "error_logs": "SecurityException: HMAC-SHA256 digest failed for payload payload_raw. Expected: 9a8b... Received: 4c2d...",
        "severity": "High",
        "category": "Security",
        "status": "Resolved",
        "root_cause": "Raw request body was parsed as JSON before computing HMAC digest, which altered whitespace formatting.",
        "resolution_text": "Captured raw byte stream prior to JSON parsing for webhook HMAC verification."
    },
    {
        "title": "Currency symbol mismatch in GBP checkout payload causes rounding error",
        "description": "Orders placed in GBP show £50.00 on front-end, but payment gateway receives 5000 cents treated as USD, resulting in incorrect conversion.",
        "steps_to_reproduce": "1. Change store currency to GBP (£)\n2. Add item costing £50\n3. Inspect Stripe charge payload",
        "expected_result": "Stripe charge currency set to 'gbp' with amount 5000.",
        "actual_result": "Stripe charge currency defaulted to 'usd' causing bank conversion fee.",
        "module": "Payment",
        "environment": "QA",
        "error_logs": "Warning: Currency 'GBP' not mapped in PaymentGatewayService; falling back to DEFAULT_CURRENCY.",
        "severity": "High",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "GBP currency enum code was written in lowercase in database while payment adapter expected uppercase 'GBP'.",
        "resolution_text": "Normalized all currency codes with .upper() in payment adapter payload builder."
    },
    {
        "title": "Payment gateway timeout leaves checkout screen frozen without error toast",
        "description": "When bank 3D-Secure ACS server times out after 60 seconds, modal closes and screen stays locked in dim backdrop with no error message.",
        "steps_to_reproduce": "1. Trigger OTP verification on test card\n2. Let OTP dialog time out\n3. Observe checkout modal",
        "expected_result": "Toast notification: 'Payment session expired. Please retry.' with active Pay button.",
        "actual_result": "Screen remains locked, user forced to hard refresh browser.",
        "module": "Payment",
        "environment": "Production",
        "error_logs": "TimeoutError: 3DS callback not received within 60000ms. Unhandled rejection in PaymentFrame.jsx.",
        "severity": "Medium",
        "category": "UI/UX",
        "status": "Resolved",
        "root_cause": "Unhandled promise rejection in iframe listener when window message '3DS_TIMEOUT' received.",
        "resolution_text": "Added catch handler for 3DS timeout event and restored UI interactive state with user-friendly notification."
    },
    {
        "title": "PayPal sandbox credentials leak in staging frontend network payload",
        "description": "Client ID and client secret are logged in browser console when PayPal button component mounts in staging.",
        "steps_to_reproduce": "1. Open DevTools in Staging\n2. Navigate to Checkout\n3. Check console tab",
        "expected_result": "Only public client-id should be exposed.",
        "actual_result": "Secret key visible in console.debug() output.",
        "module": "Payment",
        "environment": "Staging",
        "error_logs": "Console: [DEBUG] Initializing PayPal SDK with secret: sandbox_sk_8293xxxx",
        "severity": "Critical",
        "category": "Security",
        "status": "Resolved",
        "root_cause": "A debug log statement was accidentally left in PayPalButton.tsx prior to merge.",
        "resolution_text": "Removed debug console logs and rotated staging PayPal sandbox credentials."
    },

    # --- CART BUGS ---
    {
        "title": "Cart quantity decrements to negative numbers on rapid button clicks",
        "description": "Clicking the '-' button repeatedly on cart item allows quantity to reach -1, -2, causing total cart price to become negative.",
        "steps_to_reproduce": "1. Add 1 item to cart\n2. Open Cart drawer\n3. Rapidly click '-' button multiple times",
        "expected_result": "Quantity should not drop below 1, or should trigger item removal dialog at 0.",
        "actual_result": "Quantity shows -2 and cart grand total shows -$45.00.",
        "module": "Cart",
        "environment": "QA",
        "error_logs": "CartService: Updated cart item qty to -2. Total calculation: price * -2.",
        "severity": "High",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Client-side decrement handler lacked Math.max(1, qty - 1) guard and backend accepted negative integers in PATCH /cart/item.",
        "resolution_text": "Added server-side validation rejecting qty < 0 and frontend floor check at 1."
    },
    {
        "title": "Discount coupon code DISCOUNT20 applies multiple times on page refresh",
        "description": "Applying promo code DISCOUNT20 grants 20% off. Refreshing browser tab applies the 20% again recursively on the discounted total.",
        "steps_to_reproduce": "1. Add $100 item\n2. Apply code DISCOUNT20 (total becomes $80)\n3. Refresh browser (F5)\n4. Total becomes $64",
        "expected_result": "Coupon should apply once against original subtotal.",
        "actual_result": "Coupon discount stacks on every HTTP GET /cart request.",
        "module": "Cart",
        "environment": "Production",
        "error_logs": "Audit: Cart #4019 coupon applied 3 times. Cumulative discount: 48.8%.",
        "severity": "Critical",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Cart calculateTotal() method re-applied applied_coupons list directly to current total instead of base subtotal.",
        "resolution_text": "Refactored total calculation to always compute discounts relative to raw un-discounted subtotal."
    },
    {
        "title": "Cart items cleared after switching currency from USD to EUR",
        "description": "User adds items to cart in USD, then changes currency dropdown in header to EUR. Cart empties completely.",
        "steps_to_reproduce": "1. Add 3 items to cart\n2. Click currency picker in top nav\n3. Select EUR\n4. View cart",
        "expected_result": "Cart contents preserved with converted EUR pricing.",
        "actual_result": "Cart shows 'Your cart is empty'.",
        "module": "Cart",
        "environment": "QA",
        "error_logs": "SessionWarning: Cart session ID destroyed during currency cookie re-issue.",
        "severity": "Medium",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Currency change triggered session regeneration without transferring active cart_id session attribute.",
        "resolution_text": "Preserved cart_id when issuing updated currency preference cookie in session middleware."
    },
    {
        "title": "Cart drawer animation stutters and lags on Safari iOS mobile",
        "description": "Sliding open the slide-out cart drawer on iPhone Safari has noticeable frame drops (~15 FPS) and jittery animation.",
        "steps_to_reproduce": "1. Open site on iPhone 13 Safari\n2. Tap cart icon\n3. Observe slide-in transition",
        "expected_result": "Smooth 60fps hardware-accelerated drawer slide.",
        "actual_result": "Laggy animation and repaint spikes.",
        "module": "Cart",
        "environment": "QA",
        "error_logs": "Performance trace: Non-composited animation on left property causing forced reflows.",
        "severity": "Low",
        "category": "UI/UX",
        "status": "Resolved",
        "root_cause": "Cart drawer was animating CSS 'left' property instead of GPU-accelerated 'transform: translateX()'.",
        "resolution_text": "Replaced 'left' animation with CSS transform: translateX() and will-change: transform."
    },
    {
        "title": "Guest cart merge fails upon user login with duplicate item SKU",
        "description": "When guest has SKU-100 in cart and logs into an account that already had SKU-100 saved in DB, API throws 500 error instead of merging quantities.",
        "steps_to_reproduce": "1. Add item SKU-100 as guest\n2. Log in to existing user account containing SKU-100\n3. View cart",
        "expected_result": "Quantities should be summed together into single line item.",
        "actual_result": "Internal Server Error 500: Duplicate key in cart_items table.",
        "module": "Cart",
        "environment": "Staging",
        "error_logs": "sqlite3.IntegrityError: UNIQUE constraint failed: cart_items.cart_id, cart_items.product_id",
        "severity": "High",
        "category": "Integration",
        "status": "Resolved",
        "root_cause": "Cart merge query did a naive INSERT instead of UPSERT / ON CONFLICT DO UPDATE SET quantity.",
        "resolution_text": "Updated cart merge logic to perform UPSERT, combining item quantities up to max inventory limit."
    },

    # --- AUTH BUGS ---
    {
        "title": "OAuth Google login callback fails with 400 redirect_uri_mismatch",
        "description": "Users clicking 'Sign in with Google' receive an OAuth error screen indicating redirect URI mismatch after recent domain migration.",
        "steps_to_reproduce": "1. Click 'Continue with Google' on login modal\n2. Choose Google account\n3. Google returns 400 error",
        "expected_result": "Successful authentication and redirect to dashboard.",
        "actual_result": "Error 400: redirect_uri_mismatch.",
        "module": "Auth",
        "environment": "Production",
        "error_logs": "GoogleAuthException: The redirect URI in the request: https://app.example.com/api/auth/google/callback did not match authorized URIs.",
        "severity": "Critical",
        "category": "Integration",
        "status": "Resolved",
        "root_cause": "Production Google Cloud Console OAuth 2.0 Client credentials was missing the new canonical subdomain in authorized redirect URIs.",
        "resolution_text": "Added new subdomain URI to Google Cloud Console authorized redirect URIs and verified callback handling."
    },
    {
        "title": "JWT access token expiration leads to blank white screen instead of refresh",
        "description": "When 15-minute access token expires, Axios interceptor fails to call refresh endpoint and application crashes with unhandled exception.",
        "steps_to_reproduce": "1. Log in to application\n2. Idle for 16 minutes\n3. Click on Orders tab",
        "expected_result": "Silent token refresh using refresh_token cookie and seamless navigation.",
        "actual_result": "Blank screen with TypeError: Cannot read properties of undefined in App.tsx.",
        "module": "Auth",
        "environment": "Production",
        "error_logs": "Uncaught (in promise) AxiosError: Request failed with status code 401. TypeError at AuthContext.js:42.",
        "severity": "High",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Refresh token interceptor lacked retry queue, causing subsequent requests to fail and clear authentication state prematurely.",
        "resolution_text": "Implemented Axios response interceptor with request queuing and automatic token renewal."
    },
    {
        "title": "Password reset email link expires immediately after generation",
        "description": "Password reset token generation sets expiration timestamp in UTC but token verification compares against local server time (UTC+5:30), causing token to be judged expired instantly.",
        "steps_to_reproduce": "1. Click Forgot Password\n2. Enter registered email\n3. Click link in received email immediately",
        "expected_result": "Reset password page loads allowing new password entry.",
        "actual_result": "Page displays 'Your reset link has expired. Please request a new one.'",
        "module": "Auth",
        "environment": "Production",
        "error_logs": "TokenService: Token generated at 2026-03-01 10:00:00 UTC expired at 2026-03-01 11:00:00 UTC. Current comparison: 15:30:00.",
        "severity": "High",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Timezone mismatch: token creation used datetime.utcnow() while verification used datetime.now().",
        "resolution_text": "Standardized all authentication token timestamps to UTC using datetime.now(timezone.utc)."
    },
    {
        "title": "Brute force attack possible on /api/v1/auth/login due to missing rate limiter",
        "description": "Login API endpoint does not throttle consecutive failed attempts from single IP address, allowing credential stuffing attacks.",
        "steps_to_reproduce": "1. Send 100 POST requests with invalid passwords in 5 seconds via curl\n2. All 100 requests return 401 without 429 Too Many Requests",
        "expected_result": "IP throttled after 5 consecutive failed attempts with HTTP 429.",
        "actual_result": "All attempts processed without delay.",
        "module": "Auth",
        "environment": "Production",
        "error_logs": "SecurityAudit: 120 failed login attempts recorded for username 'admin' from IP 198.51.100.2 in 6 seconds.",
        "severity": "Critical",
        "category": "Security",
        "status": "Resolved",
        "root_cause": "Rate limiting middleware was only enabled on /api/v1/register and omitted on /api/v1/login.",
        "resolution_text": "Applied Redis-backed token bucket rate limiter to /login endpoint (5 attempts/min per IP)."
    },
    {
        "title": "Session remains active after user changes password on another device",
        "description": "When user changes password on desktop, active sessions on mobile phone remain logged in indefinitely.",
        "steps_to_reproduce": "1. Log in on Phone and Laptop\n2. Change password on Laptop\n3. Refresh Phone browser",
        "expected_result": "Phone session invalidated; user prompted to re-login.",
        "actual_result": "Phone session continues to work.",
        "module": "Auth",
        "environment": "QA",
        "error_logs": "AuthWarning: User ID 44 changed password; 2 other active session tokens still valid.",
        "severity": "Medium",
        "category": "Security",
        "status": "Resolved",
        "root_cause": "JWT tokens did not include a token_version claim checked against database user record.",
        "resolution_text": "Added token_version column to users table; incremented upon password change to invalidate existing tokens."
    },

    # --- CHECKOUT BUGS ---
    {
        "title": "Shipping address postal code validation rejects valid 5-digit US zip codes with leading zero",
        "description": "Zip codes such as 01001 (Agawam, MA) or 07001 (Avenel, NJ) are stripped of leading zero or rejected as invalid 4-digit numbers.",
        "steps_to_reproduce": "1. Proceed to shipping step\n2. Enter postal code '01001'\n3. Click Continue",
        "expected_result": "Address validated and accepted.",
        "actual_result": "Validation error: 'Please enter a valid 5-digit ZIP code.'",
        "module": "Checkout",
        "environment": "Production",
        "error_logs": "ValidationError: Field 'zipCode' cast to Number: 1001 failed regex ^[0-9]{5}$.",
        "severity": "High",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Postal code input was parsed as Integer in JSON schema validation, dropping leading zeroes.",
        "resolution_text": "Changed postal code schema data type strictly to String with regex ^\\d{5}(-\\d{4})?$."
    },
    {
        "title": "Taxes calculated incorrectly for California state destination addresses",
        "description": "Checkout tax calculation applies 0% sales tax for California shipping addresses due to missing zip table entry.",
        "steps_to_reproduce": "1. Add item to cart\n2. Enter California shipping address (e.g. 90210)\n3. Check tax line item",
        "expected_result": "Tax computed based on state + county tax rate (~9.5%).",
        "actual_result": "Tax shows $0.00.",
        "module": "Checkout",
        "environment": "Production",
        "error_logs": "TaxEngineException: State 'CA' rate table lookup returned NULL; fallback to 0.0.",
        "severity": "High",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Tax jar API key had expired in production environment.",
        "resolution_text": "Renewed TaxJar API credentials and added automated healthcheck for tax estimation service."
    },
    {
        "title": "Continue to Payment button stays disabled when removing single out-of-stock item",
        "description": "If checkout page warns that one item is out of stock, clicking 'Remove Item' removes it from UI, but the 'Continue' button remains disabled.",
        "steps_to_reproduce": "1. Have 2 items in cart, 1 out of stock\n2. Enter checkout\n3. Click 'Remove' on out-of-stock item",
        "expected_result": "'Continue to Payment' button enables immediately since remaining item is valid.",
        "actual_result": "Button remains grayed out and unclickable.",
        "module": "Checkout",
        "environment": "QA",
        "error_logs": "CheckoutContext: hasOutOfStockItems flag not recomputed on removeItem action.",
        "severity": "Medium",
        "category": "UI/UX",
        "status": "Resolved",
        "root_cause": "hasOutOfStockItems state was only calculated on initial component mount and not in the reducer action REMOVE_ITEM.",
        "resolution_text": "Updated checkout reducer to recalculate stock validity on every cart mutation action."
    },
    {
        "title": "Checkout order summary shows NaN when item has zero-dollar promotional sample",
        "description": "Adding a free promotional gift ($0.00) causes order total calculation to produce 'NaN' in price breakdown.",
        "steps_to_reproduce": "1. Add qualifying item\n2. Select free sample perfume ($0.00)\n3. View checkout summary",
        "expected_result": "Summary shows items total and 'Free' for sample.",
        "actual_result": "Subtotal: $45.00, Sample: NaN, Total: NaN.",
        "module": "Checkout",
        "environment": "QA",
        "error_logs": "Warning: Division by zero or null price property in PriceCalculator.ts line 33.",
        "severity": "Medium",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Code calculated price per unit by dividing total by quantity without checking if price was 0.",
        "resolution_text": "Handled price === 0 edge cases gracefully in PriceCalculator formatting utility."
    },
    {
        "title": "Guest checkout fails to redirect to order confirmation page on slow networks",
        "description": "When guest places an order on 3G network, order creates successfully in backend but frontend navigation times out after 10s and stays on payment page.",
        "steps_to_reproduce": "1. Checkout as guest on 3G\n2. Submit order",
        "expected_result": "Loading indicator remains until navigation completes to /orders/confirm/:id.",
        "actual_result": "App stays on checkout page, causing user to click submit again.",
        "module": "Checkout",
        "environment": "Staging",
        "error_logs": "NavigationTimeout: Route transition to /orders/confirm/ORD-912 aborted after 10000ms.",
        "severity": "High",
        "category": "Performance",
        "status": "Resolved",
        "root_cause": "Confirmation page was synchronously awaiting external analytics script download before rendering.",
        "resolution_text": "Deferred analytics scripts loading with async/defer attributes to avoid blocking page transition."
    },

    # --- ORDERS BUGS ---
    {
        "title": "Order confirmation email sent without tracking link or carrier name",
        "description": "Customer receives automated order shipped email, but tracking URL href is blank and carrier displays as 'undefined'.",
        "steps_to_reproduce": "1. Mark order as Shipped in admin panel\n2. Enter tracking number 1Z999999\n3. Check customer email",
        "expected_result": "Email contains clickable tracking link: https://carrier.com/track/1Z999999.",
        "actual_result": "Email shows 'Track your package: undefined - [blank link]'.",
        "module": "Orders",
        "environment": "Production",
        "error_logs": "TemplateRenderError: Variable 'carrier_url' not found in EmailContext dictionary.",
        "severity": "Medium",
        "category": "Integration",
        "status": "Resolved",
        "root_cause": "Email template referenced carrier.tracking_url instead of shipment.carrier_url.",
        "resolution_text": "Fixed context key mapping in OrderNotificationMailService."
    },
    {
        "title": "Order history pagination throws 500 error when page parameter exceeds total pages",
        "description": "Navigating to /orders?page=99 for a customer with only 2 pages of orders crashes with uncaught 500 server error.",
        "steps_to_reproduce": "1. Log in as user with 5 orders\n2. Manually change URL to /orders?page=15",
        "expected_result": "Display empty state or redirect to page 1.",
        "actual_result": "HTTP 500: IndexError: list index out of range.",
        "module": "Orders",
        "environment": "QA",
        "error_logs": "IndexError: list index out of range at OrderController.listOrders line 88.",
        "severity": "Low",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Backend slice notation orders[(page-1)*limit : page*limit] threw index error on empty offset slice.",
        "resolution_text": "Handled out-of-bounds page requests by returning empty list with valid pagination metadata."
    },
    {
        "title": "Invoice PDF generation fails for orders containing special characters in billing name",
        "description": "Customers with characters like 'Ø', 'ä', 'é', or 'ü' in billing name get 500 error when clicking 'Download Invoice'.",
        "steps_to_reproduce": "1. Create order with billing name 'François Müller'\n2. Click 'Download Invoice'",
        "expected_result": "PDF downloads with characters rendered properly.",
        "actual_result": "500 Internal Server Error: UnicodeEncodeError: 'latin-1' codec can't encode character.",
        "module": "Orders",
        "environment": "Production",
        "error_logs": "UnicodeEncodeError: 'latin-1' codec can't encode character '\\xe7' in position 4: ordinal not in range(256).",
        "severity": "High",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "PDF generation library (FPDF) defaulted to Latin-1 encoding instead of UTF-8 font support.",
        "resolution_text": "Configured PDF generator to use DejaVu Sans font with explicit UTF-8 encoding support."
    },
    {
        "title": "Cancel order button missing for orders in PENDING status within 30-minute grace period",
        "description": "According to policy, customers can cancel orders within 30 minutes of placement. However, 'Cancel Order' button is hidden.",
        "steps_to_reproduce": "1. Place order\n2. Immediately navigate to Order Details\n3. Look for Cancel button",
        "expected_result": "'Cancel Order' button visible until 30 minutes elapse.",
        "actual_result": "Button is completely missing from DOM.",
        "module": "Orders",
        "environment": "Production",
        "error_logs": "UI Check: isCancelable calculated as false because order.created_at was compared as ISO string instead of timestamp.",
        "severity": "Medium",
        "category": "UI/UX",
        "status": "Resolved",
        "root_cause": "String comparison on ISO date strings failed when client machine had non-UTC local clock.",
        "resolution_text": "Converted timestamps to UNIX milliseconds before evaluating 30-minute window."
    },
    {
        "title": "Inventory count not restored when customer cancels order",
        "description": "When customer cancels order, order status changes to CANCELLED, but inventory item count in stock table is not replenished.",
        "steps_to_reproduce": "1. Check stock of SKU-99 (e.g. 10 units)\n2. Place order for 2 units (stock = 8)\n3. Cancel order\n4. Re-check stock",
        "expected_result": "Stock should revert back to 10 units.",
        "actual_result": "Stock remains at 8 units.",
        "module": "Orders",
        "environment": "Staging",
        "error_logs": "InventoryService: No event handler registered for ORDER_CANCELLED event.",
        "severity": "High",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "The message consumer for ORDER_CANCELLED event was missing an inventory restock query.",
        "resolution_text": "Implemented inventory restock transaction inside ORDER_CANCELLED event listener."
    },

    # --- CATALOG BUGS ---
    {
        "title": "Product search query containing single apostrophe causes SQL syntax error",
        "description": "Searching for terms like \"men's shoes\" or \"women's jackets\" triggers an unhandled 500 error in catalog search API.",
        "steps_to_reproduce": "1. Go to homepage\n2. Type \"men's shoes\" into search bar\n3. Press Enter",
        "expected_result": "Search results for men's shoes displayed.",
        "actual_result": "Server returns HTTP 500 Internal Server Error.",
        "module": "Catalog",
        "environment": "Production",
        "error_logs": "sqlite3.OperationalError: near \"s\": syntax error at SELECT * FROM products WHERE name LIKE '%men's shoes%'",
        "severity": "Critical",
        "category": "Security",
        "status": "Resolved",
        "root_cause": "Search query was concatenated into SQL query string without parameterized input binding.",
        "resolution_text": "Replaced string interpolation with parameterized SQL query binding (? placeholder)."
    },
    {
        "title": "Out of stock badge not displaying on product grid view",
        "description": "Products with inventory_count == 0 still appear clickable with normal price tag, only displaying error once user tries to add to cart.",
        "steps_to_reproduce": "1. View Catalog category 'Electronics'\n2. Locate item with 0 stock\n3. Observe card badge",
        "expected_result": "Greyed-out 'Out of Stock' badge overlaid on product card.",
        "actual_result": "Card looks identical to in-stock items.",
        "module": "Catalog",
        "environment": "QA",
        "error_logs": "CSS: .badge-out-of-stock has display: none due to override in theme.css.",
        "severity": "Low",
        "category": "UI/UX",
        "status": "Resolved",
        "root_cause": "A CSS specificity override in theme.css set all .badge elements inside .product-card to display: none.",
        "resolution_text": "Corrected CSS selector hierarchy to preserve visibility of .badge-out-of-stock."
    },
    {
        "title": "Filter by price range slider resets to default range when moving to page 2",
        "description": "Customer filters products between $50 and $100. When clicking next page, filter slider resets to $0-$500 and shows unfiltered products.",
        "steps_to_reproduce": "1. Move price slider to $50 - $100\n2. See 25 results across 2 pages\n3. Click Page 2",
        "expected_result": "Page 2 shows items 11-20 within $50 - $100 range.",
        "actual_result": "Page 2 resets price filter to $0 - $500.",
        "module": "Catalog",
        "environment": "QA",
        "error_logs": "URLQueryManager: min_price and max_price query params dropped during pagination href construction.",
        "severity": "Medium",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "Pagination component only updated 'page' param and did not preserve existing search query params.",
        "resolution_text": "Updated pagination helper to merge current URLSearchParams with new page index."
    },
    {
        "title": "Product image gallery thumbnail click does not update main hero image on Firefox",
        "description": "On product detail page in Mozilla Firefox, clicking gallery thumbnails does not change the enlarged hero preview.",
        "steps_to_reproduce": "1. Open product page on Firefox\n2. Click 2nd thumbnail in gallery\n3. Observe hero preview",
        "expected_result": "Hero image switches to 2nd image.",
        "actual_result": "Main image stays on 1st image.",
        "module": "Catalog",
        "environment": "Production",
        "error_logs": "Firefox Console: window.event is deprecated / undefined in handleThumbnailClick.",
        "severity": "Medium",
        "category": "UI/UX",
        "status": "Resolved",
        "root_cause": "handleThumbnailClick relied on legacy window.event instead of passing the event argument explicitly.",
        "resolution_text": "Passed event parameter explicitly to handleThumbnailClick(e) handler."
    },
    {
        "title": "Catalog page response time exceeds 4 seconds under 50 concurrent requests",
        "description": "Category listing endpoint /api/v1/products?category=apparel experiences severe latency spikes due to N+1 database queries on product variants.",
        "steps_to_reproduce": "1. Run load test: 50 virtual users querying category page\n2. Monitor p95 latency",
        "expected_result": "p95 latency under 200ms.",
        "actual_result": "p95 latency reaches 4200ms with database connection pool exhaustion.",
        "module": "Catalog",
        "environment": "Staging",
        "error_logs": "SlowQueryLog: 250 individual SELECT * FROM product_images WHERE product_id = ? queries executed in single request.",
        "severity": "High",
        "category": "Performance",
        "status": "Resolved",
        "root_cause": "ORM relation was set to lazy loading, causing N+1 query execution for each product's image gallery.",
        "resolution_text": "Refactored query to use eager loading (JOIN) and added Redis caching for category pages with 5-minute TTL."
    },

    # --- PROFILE BUGS ---
    {
        "title": "Uploading profile avatar in WebP format displays broken image icon",
        "description": "User uploads avatar image in .webp format. Avatar saves, but profile header displays broken image thumbnail.",
        "steps_to_reproduce": "1. Go to Profile Settings\n2. Upload avatar.webp file (250KB)\n3. Click Save\n4. View header",
        "expected_result": "Avatar displays properly.",
        "actual_result": "Broken image icon; Content-Type served as application/octet-stream.",
        "module": "Profile",
        "environment": "Production",
        "error_logs": "Nginx: Mime type for .webp missing in legacy mime.types configuration file.",
        "severity": "Low",
        "category": "UI/UX",
        "status": "Resolved",
        "root_cause": "Nginx mime.types lacked image/webp definition, causing browser to fail inline rendering.",
        "resolution_text": "Added image/webp to mime.types and reloaded Nginx configuration."
    },
    {
        "title": "Email notification preferences revert to enabled after logging out and back in",
        "description": "Customer unchecks 'Marketing emails' and saves preferences. After logging out and logging back in, checkbox is checked again.",
        "steps_to_reproduce": "1. Uncheck marketing email preference\n2. Click Save (success toast shows)\n3. Log out\n4. Log back in",
        "expected_result": "Marketing emails preference remains unchecked.",
        "actual_result": "Preference reverts to checked.",
        "module": "Profile",
        "environment": "QA",
        "error_logs": "ProfileService: UPDATE user_preferences query omitted marketing_opt_in field.",
        "severity": "Medium",
        "category": "Functional",
        "status": "Resolved",
        "root_cause": "The UPDATE query column mapping had a typo 'marketing_opt_in' vs 'email_marketing_opt_in'.",
        "resolution_text": "Corrected column name in user preferences update SQL statement."
    },

    # --- ACTIVE / NEW BUGS (FOR DEMO & TEST PURPOSES) ---
    {
        "title": "Payment gateway returns HTTP 502 Bad Gateway during peak flash sale",
        "description": "During the flash sale promotion, multiple users reporting that clicking Pay Now results in a 502 Bad Gateway error from the checkout API.",
        "steps_to_reproduce": "1. Add flash sale item to cart\n2. Complete shipping details\n3. Click Pay Now",
        "expected_result": "Payment intent processed and confirmed.",
        "actual_result": "HTTP 502 Bad Gateway displayed in modal toast.",
        "module": "Payment",
        "environment": "Production",
        "error_logs": "UpstreamGatewayError: Connection reset by peer from payment-proxy.internal:8080.",
        "severity": "Critical",
        "category": "Performance",
        "status": "New",
        "root_cause": "",
        "resolution_text": ""
    },
    {
        "title": "Cart badge count does not increment until full page reload on Chrome",
        "description": "Adding an item to cart displays success message, but top navigation cart badge continues showing 0 until browser is refreshed.",
        "steps_to_reproduce": "1. Browse catalog\n2. Click 'Add to Cart' on any item\n3. Look at cart counter icon in top right",
        "expected_result": "Badge updates to '1' immediately.",
        "actual_result": "Badge stays '0' until user presses F5.",
        "module": "Cart",
        "environment": "QA",
        "error_logs": "React Warning: State dispatch called outside CartContext provider.",
        "severity": "Low",
        "category": "UI/UX",
        "status": "In Progress",
        "root_cause": "",
        "resolution_text": ""
    },
    {
        "title": "Checkout shipping method selection radio buttons jump position on mobile screen",
        "description": "On mobile viewports (< 480px), selecting Express Shipping causes radio button labels to jump vertically, causing accidental clicks on Standard Shipping.",
        "steps_to_reproduce": "1. Open mobile viewport\n2. Go to shipping selection\n3. Tap Express shipping radio option",
        "expected_result": "Smooth selection without layout shift.",
        "actual_result": "Cumulative Layout Shift of 0.42 observed.",
        "module": "Checkout",
        "environment": "QA",
        "error_logs": "Lighthouse: CLS score 0.42 exceeds target 0.1.",
        "severity": "Low",
        "category": "UI/UX",
        "status": "New",
        "root_cause": "",
        "resolution_text": ""
    },
    {
        "title": "Exporting order history to CSV hangs indefinitely when date range exceeds 90 days",
        "description": "In admin orders panel, selecting date range > 90 days and clicking 'Export CSV' causes server memory usage to climb to 100% until gunicorn worker is killed.",
        "steps_to_reproduce": "1. Log in as admin\n2. Go to Orders Export\n3. Select Jan 1 to Dec 31\n4. Click Export CSV",
        "expected_result": "Streaming CSV download initiated within 5 seconds.",
        "actual_result": "Page hangs and worker process is SIGKILLed.",
        "module": "Orders",
        "environment": "Production",
        "error_logs": "MemoryError: Unable to allocate 2.1 GiB for DataFrame array buffer.",
        "severity": "High",
        "category": "Performance",
        "status": "In Progress",
        "root_cause": "",
        "resolution_text": ""
    }
]

def seed_all():
    """Seed users, developers, and historical bugs into the database."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Seed Users
        user_ids = {}
        for username, password, full_name, role in SEED_USERS:
            pwd_hash, salt = hash_password(password)
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, salt, full_name, role)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    password_hash = excluded.password_hash,
                    salt = excluded.salt,
                    full_name = excluded.full_name,
                    role = excluded.role
                """,
                (username, pwd_hash, salt, full_name, role)
            )
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_ids[username] = cursor.fetchone()[0]

        # 2. Seed Developers
        dev_ids = []
        for name, email, expertise, workload in SEED_DEVELOPERS:
            cursor.execute(
                """
                INSERT INTO developers (name, email, expertise_modules, current_workload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    expertise_modules = excluded.expertise_modules,
                    current_workload = excluded.current_workload
                """,
                (name, email, expertise, workload)
            )
            cursor.execute("SELECT id FROM developers WHERE email = ?", (email,))
        # 3. Seed Categories
        for cat_name, cat_desc in SEED_CATEGORIES:
            cursor.execute(
                """
                INSERT INTO categories (name, description)
                VALUES (?, ?)
                ON CONFLICT(name) DO UPDATE SET description = excluded.description
                """,
                (cat_name, cat_desc)
            )

        # 4. Check existing bugs count
        cursor.execute("SELECT COUNT(*) FROM bugs")
        count = cursor.fetchone()[0]

        if count == 0:
            print(f"Seeding {len(SEED_BUGS)} mock e-commerce bugs...")
            reporter_id = user_ids.get("tester1", 1)

            for bug in SEED_BUGS:
                cursor.execute(
                    """
                    INSERT INTO bugs (
                        title, description, steps_to_reproduce, expected_result, actual_result,
                        module, environment, error_logs, severity, category, status,
                        reporter_id, predicted_severity, predicted_category, similarity_flag
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bug["title"], bug["description"], bug.get("steps_to_reproduce", ""),
                        bug.get("expected_result", ""), bug.get("actual_result", ""),
                        bug["module"], bug["environment"], bug.get("error_logs", ""),
                        bug["severity"], bug["category"], bug["status"],
                        reporter_id, bug["severity"], bug["category"], "Clean"
                    )
                )
                bug_id = cursor.lastrowid

                # If bug has resolution, insert resolution
                if bug.get("root_cause") and bug.get("resolution_text"):
                    resolver_id = user_ids.get("dev1", 2)
                    cursor.execute(
                        """
                        INSERT INTO bug_resolutions (bug_id, root_cause, resolution_text, resolved_by)
                        VALUES (?, ?, ?, ?)
                        """,
                        (bug_id, bug["root_cause"], bug["resolution_text"], resolver_id)
                    )

                # Assign to a relevant developer if in progress
                if bug["status"] in ("In Progress", "Resolved", "Closed"):
                    assigned_dev = dev_ids[0] if bug["module"] in ("Payment", "Checkout") else (dev_ids[1] if bug["module"] in ("Cart", "Catalog") else dev_ids[2])
                    cursor.execute(
                        """
                        INSERT INTO bug_assignments (bug_id, developer_id, assigned_by, notes)
                        VALUES (?, ?, ?, ?)
                        """,
                        (bug_id, assigned_dev, user_ids.get("lead1", 4), "Initial triage assignment based on module expertise.")
                    )

            print(f"Successfully seeded {len(SEED_BUGS)} bugs and knowledge base resolutions!")
        else:
            print(f"Database already contains {count} bugs. Skipping duplicate seeding.")

    return True

if __name__ == "__main__":
    seed_all()

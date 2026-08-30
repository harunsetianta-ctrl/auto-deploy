"""
Wrapper tipis untuk AutoKuy Pay API.
Docs: https://payment.kuskuskuy.my.id/api-docs
"""

import hmac
import hashlib
import uuid
import aiohttp

from config import AUTOKUY_BASE_URL, AUTOKUY_API_KEY, AUTOKUY_WEBHOOK_SECRET


class AutoKuyError(Exception):
    pass


def _headers(idempotency_key: str | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {AUTOKUY_API_KEY}",
        "Content-Type": "application/json",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


async def create_invoice(order_id: str, amount: int, customer_name: str, customer_phone: str) -> dict:
    """
    Bikin invoice QRIS baru di AutoKuy Pay.
    order_id HARUS unik per transaksi (dipakai juga sebagai Idempotency-Key
    supaya retry request tidak bikin invoice dobel).
    """
    url = f"{AUTOKUY_BASE_URL}/api/v1/invoices"
    payload = {
        "order_id": order_id,
        "amount": amount,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "include_qr_png": False,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=_headers(order_id)) as resp:
            data = await resp.json()
            if resp.status not in (200, 201):
                raise AutoKuyError(f"Gagal bikin invoice ({resp.status}): {data}")
            return data["data"]


async def get_invoice(invoice_id: str) -> dict:
    """Cek status invoice terbaru langsung dari AutoKuy Pay (buat fallback polling)."""
    url = f"{AUTOKUY_BASE_URL}/api/v1/invoices/{invoice_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_headers()) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise AutoKuyError(f"Gagal ambil invoice ({resp.status}): {data}")
            return data["data"]


def verify_webhook_signature(timestamp: str, raw_body: bytes, signature: str) -> bool:
    """
    Formula sesuai docs: HMAC-SHA256(timestamp + "." + raw_body, webhook_secret)
    Verifikasi pakai raw body SEBELUM di-parse jadi JSON.
    """
    if not timestamp or not signature or not AUTOKUY_WEBHOOK_SECRET:
        return False

    message = timestamp.encode() + b"." + raw_body
    expected = hmac.new(
        AUTOKUY_WEBHOOK_SECRET.encode(), message, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def new_order_id(prefix: str = "INV") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

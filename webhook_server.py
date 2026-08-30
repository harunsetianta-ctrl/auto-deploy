import json
import logging
from aiohttp import web

from config import WEBHOOK_PATH
from payment_gateway import verify_webhook_signature
import database as db

logger = logging.getLogger(__name__)

PACKAGE_DAYS = {
    "1_month": 30,
    "3_months": 90,
    "lifetime": None,
}


def build_webhook_app(bot) -> web.Application:
    """bot = instance telegram.Bot yang sudah jalan, dipakai buat kirim notifikasi."""

    async def handle_webhook(request: web.Request):
        raw_body = await request.read()
        timestamp = request.headers.get("X-AutoKuy-Timestamp", "")
        signature = request.headers.get("X-AutoKuy-Signature", "")
        event_name = request.headers.get("X-AutoKuy-Event", "")

        if not verify_webhook_signature(timestamp, raw_body, signature):
            logger.warning("Webhook signature tidak valid")
            return web.Response(status=401, text="invalid signature")

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return web.Response(status=422, text="invalid json")

        order_id = payload.get("order_id")
        event = payload.get("event", event_name)

        if not order_id:
            return web.Response(status=422, text="missing order_id")

        trans = db.get_transaction_by_order_id(order_id)
        if not trans:
            # Bukan invoice dari bot ini / tenant lain -> tetap balas 2xx biar tidak retry
            return web.Response(status=200, text="ignored")

        if event == "invoice.paid":
            db.mark_transaction_paid(order_id)
            days = PACKAGE_DAYS.get(trans.package)
            db.grant_premium(trans.telegram_id, days=days)

            try:
                await bot.send_message(
                    chat_id=trans.telegram_id,
                    text=(
                        "✅ *Pembayaran berhasil!*\n\n"
                        f"Paket: `{trans.package}`\n"
                        "Silakan lanjut kirim nomor HP untuk mulai deploy userbot kamu."
                    ),
                    parse_mode="Markdown",
                )
            except Exception:
                logger.exception("Gagal kirim notifikasi ke user %s", trans.telegram_id)

        elif event == "invoice.expired":
            db.mark_transaction_expired(order_id)
            try:
                await bot.send_message(
                    chat_id=trans.telegram_id,
                    text="⏰ Invoice kamu sudah expired. Silakan buat pesanan baru lewat /start.",
                )
            except Exception:
                logger.exception("Gagal kirim notifikasi expired ke user %s", trans.telegram_id)

        return web.Response(status=200, text="ok")

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    return app

import logging
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import init_db, get_user, create_user, get_balance, create_request, get_requests, update_request
from config import BOT_TOKEN, ADMIN_TELEGRAM_ID, MIN_DEPOSIT_USD, DEPOSIT_FEE_RATE, SUPPORT_USERNAME

logging.basicConfig(level=logging.INFO)
pending = {}

def money(v): return f"${Decimal(str(v)):,.2f}"
def is_admin(uid): return str(uid) == str(ADMIN_TELEGRAM_ID)

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"), InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("📈 My Trading", callback_data="trading"), InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Transactions", callback_data="transactions"), InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("🆘 Support", callback_data="support"), InlineKeyboardButton("⚠️ Risk", callback_data="risk")]
    ])

async def start(update, context):
    u = update.effective_user
    if not get_user(u.id): create_user(u.id, u.username or "", u.first_name or "")
    await update.message.reply_text(
        "🟡 AURIX TRADE\n\nAutomated Gold & Crypto Trading.\n\n🥇 XAU/USD\n₿ BTC/USDT\n"
        f"💰 Minimum deposit: {money(MIN_DEPOSIT_USD)}\n\n"
        "⚠️ DEMO/TEST MODE: no real deposits or withdrawals are processed.\n"
        "Trading involves risk; profits are not guaranteed.",
        reply_markup=menu())

async def admin(update, context):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ Admin access only.")
    await update.message.reply_text(
        f"🛡 AURIX TRADE ADMIN\n\n⏳ Pending requests: {len(get_requests('pending'))}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Deposit Requests", callback_data="admin_deposits")],
            [InlineKeyboardButton("💵 Withdrawal Requests", callback_data="admin_withdrawals")]
        ]))

async def handle_text(update, context):
    uid = update.effective_user.id
    state = pending.get(uid)
    if not state: return
    try: amount = Decimal(update.message.text.strip())
    except InvalidOperation:
        return await update.message.reply_text("Please enter a valid USD amount, e.g. 50 or 100.")
    if amount <= 0:
        return await update.message.reply_text("Amount must be greater than zero.")
    if state == "deposit":
        if amount < MIN_DEPOSIT_USD:
            return await update.message.reply_text(f"Minimum deposit is {money(MIN_DEPOSIT_USD)}.")
        fee = (amount * DEPOSIT_FEE_RATE).quantize(Decimal("0.01"))
        total = amount + fee
        ref = create_request(uid, "deposit", float(amount), float(fee), f"DEP-{uid}-{int(amount*100)}")
        pending.pop(uid, None)
        await update.message.reply_text(
            f"💰 DEPOSIT REQUEST CREATED\n\nTrading capital: {money(amount)}\n"
            f"Platform fee (5%): {money(fee)}\nTotal shown for this DEMO request: {money(total)}\n\n"
            f"Reference: {ref}\n\n⚠️ DEMO ONLY — do not send funds.",
            reply_markup=menu())
    else:
        balance = Decimal(str(get_balance(uid)))
        if amount > balance:
            pending.pop(uid, None)
            return await update.message.reply_text(f"Insufficient demo balance. Available: {money(balance)}", reply_markup=menu())
        ref = create_request(uid, "withdrawal", float(amount), 0.0, f"WDR-{uid}-{int(amount*100)}")
        pending.pop(uid, None)
        await update.message.reply_text(
            f"💵 WITHDRAWAL REQUEST CREATED\n\nAmount: {money(amount)}\nReference: {ref}\n\n"
            "⚠️ DEMO ONLY — no real funds are transferred.", reply_markup=menu())

async def admin_list(update, context):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    kind = "deposit" if q.data == "admin_deposits" else "withdrawal"
    rows = get_requests("pending", kind)
    if not rows:
        return await q.edit_message_text(f"No pending {kind} requests.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin", callback_data="admin_home")]]))
    lines = [f"📋 PENDING {kind.upper()}S\n"]; buttons=[]
    for r in rows[:20]:
        lines.append(f"#{r['id']} • User {r['telegram_id']} • {money(r['amount'])} • {r['reference']}")
        buttons.append([InlineKeyboardButton(f"✅ Approve #{r['id']}", callback_data=f"approve:{r['id']}"),
                        InlineKeyboardButton(f"❌ Reject #{r['id']}", callback_data=f"reject:{r['id']}")])
    buttons.append([InlineKeyboardButton("🔙 Admin", callback_data="admin_home")])
    await q.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))

async def admin_decision(update, context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    action,rid=q.data.split(":")
    req=update_request(int(rid), "confirmed" if action=="approve" else "rejected")
    if not req: return await q.edit_message_text("Request not found or already processed.")
    await q.edit_message_text(
        f"{'✅ APPROVED' if action=='approve' else '❌ REJECTED'}\n\nRequest #{rid}\n"
        f"User: {req['telegram_id']}\nAmount: {money(req['amount'])}\nReference: {req['reference']}\n\n"
        "⚠️ Demo accounting only; no real funds moved.")

async def callback(update, context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    if q.data=="admin_home":
        if is_admin(uid):
            await q.edit_message_text("🛡 ADMIN", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Deposit Requests", callback_data="admin_deposits")],
                [InlineKeyboardButton("💵 Withdrawal Requests", callback_data="admin_withdrawals")]]))
        return
    if q.data in ("admin_deposits","admin_withdrawals"): return await admin_list(update,context)
    if q.data.startswith(("approve:","reject:")): return await admin_decision(update,context)
    if q.data=="deposit":
        pending[uid]="deposit"
        return await q.edit_message_text(
            f"💰 DEPOSIT\n\nEnter amount in USD.\nMinimum: {money(MIN_DEPOSIT_USD)}\n"
            "5% fee is calculated automatically.\n\n⚠️ DEMO ONLY — do not send money.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back",callback_data="dashboard")]]))
    if q.data=="withdraw":
        pending[uid]="withdraw"
        return await q.edit_message_text("💵 WITHDRAW\n\nEnter amount in USD to create a DEMO withdrawal request.\nNo real funds are transferred.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back",callback_data="dashboard")]]))
    texts={
        "dashboard":f"📊 DASHBOARD\n\n💵 Demo balance: {money(get_balance(uid))}\n📈 Trading: DEMO / NOT LIVE",
        "trading":"📈 MY TRADING\n\n🥇 XAU/USD\n₿ BTC/USDT\n\nStatus: DEMO / NOT LIVE.",
        "transactions":"📜 TRANSACTIONS\n\nUse the admin panel to review demo requests.",
        "referral":"👥 REFERRAL\n\nReferral tracking is not enabled in this test build.",
        "support":f"🆘 SUPPORT\n\n{('@'+SUPPORT_USERNAME) if SUPPORT_USERNAME else 'Configure SUPPORT_USERNAME in Railway Variables.'}",
        "risk":"⚠️ RISK DISCLOSURE\n\nTrading Forex/CFDs and crypto involves substantial risk. Past performance does not guarantee future results. No return or doubling is guaranteed."
    }
    await q.edit_message_text(texts.get(q.data,"AURIX TRADE"),reply_markup=menu())

def main():
    if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN is missing")
    init_db()
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start)); app.add_handler(CommandHandler("admin",admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text))
    app.add_handler(CallbackQueryHandler(callback))
    app.run_polling()

if __name__=="__main__": main()

import logging
from decimal import Decimal, InvalidOperation
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import init_db, get_user, create_user, get_balance, adjust_balance, create_request, get_requests, get_request, update_request, add_transaction, get_transactions, get_stats
from config import BOT_TOKEN, ADMIN_TELEGRAM_ID, MIN_DEPOSIT_USD, DEPOSIT_FEE_RATE, PROFIT_FEE_RATE, SUPPORT_USERNAME

logging.basicConfig(level=logging.INFO)
pending = {}

def money(v): return f"${Decimal(str(v)):,.2f}"
def is_admin(uid): return str(uid) == str(ADMIN_TELEGRAM_ID)
def tier(balance):
    b=Decimal(str(balance))
    if b >= 1000: return "Elite"
    if b >= 500: return "Pro"
    if b >= 250: return "Advanced"
    if b >= 100: return "Standard"
    return "Starter"

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"), InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("📈 My Trading", callback_data="trading"), InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Transactions", callback_data="transactions"), InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("🆘 Support", callback_data="support"), InlineKeyboardButton("⚠️ Risk", callback_data="risk")],
        [InlineKeyboardButton("📢 Official Channel", callback_data="channel")]
    ])

def back(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="dashboard")]])

async def start(update, context):
    u=update.effective_user
    if not get_user(u.id): create_user(u.id,u.username or "",u.first_name or "")
    await update.message.reply_text(
        "🟡 AURIX TRADE\n\nTrade Smarter. Grow With Discipline.\n\n"
        "🤖 Automated Gold & Crypto Trading\n🥇 XAU/USD  •  ₿ BTC/USDT\n\n"
        f"💰 Minimum demo deposit: {money(MIN_DEPOSIT_USD)}\n\n"
        "🧪 DEMO/TEST MODE\nNo real deposits, custody, broker orders or withdrawals are processed by this build.\n\n"
        "⚠️ Trading involves substantial risk. Returns are not guaranteed.", reply_markup=menu())

async def admin(update, context):
    if not is_admin(update.effective_user.id): return await update.message.reply_text("⛔ Admin access only.")
    users,pending_count,volume=get_stats()
    await update.message.reply_text(f"🛡 AURIX TRADE ADMIN\n\n👥 Users: {users}\n⏳ Pending: {pending_count}\n💵 Demo transaction volume: {money(volume)}", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit Requests",callback_data="admin_deposits")],
        [InlineKeyboardButton("💵 Withdrawal Requests",callback_data="admin_withdrawals")]
    ]))

async def handle_text(update, context):
    uid=update.effective_user.id; state=pending.get(uid)
    if not state: return
    try: amount=Decimal(update.message.text.strip())
    except InvalidOperation: return await update.message.reply_text("Enter a valid USD amount, e.g. 50 or 100.")
    if amount <= 0: return await update.message.reply_text("Amount must be greater than zero.")
    if state == "deposit":
        if amount < MIN_DEPOSIT_USD: return await update.message.reply_text(f"Minimum demo deposit is {money(MIN_DEPOSIT_USD)}.")
        fee=(amount*DEPOSIT_FEE_RATE).quantize(Decimal("0.01")); total=amount+fee
        ref=create_request(uid,"deposit",float(amount),float(fee),f"DEP-{uid}-{int(amount*100)}")
        pending.pop(uid,None)
        await update.message.reply_text(f"💰 DEMO DEPOSIT REQUEST\n\nTrading capital: {money(amount)}\nPlatform fee: {money(fee)}\nTotal shown: {money(total)}\n\nReference: {ref}\n\n⚠️ DEMO ONLY — do not send funds.",reply_markup=menu())
    else:
        balance=Decimal(str(get_balance(uid)))
        if amount > balance:
            pending.pop(uid,None); return await update.message.reply_text(f"Insufficient demo balance. Available: {money(balance)}",reply_markup=menu())
        ref=create_request(uid,"withdrawal",float(amount),0.0,f"WDR-{uid}-{int(amount*100)}")
        pending.pop(uid,None)
        await update.message.reply_text(f"💵 DEMO WITHDRAWAL REQUEST\n\nAmount: {money(amount)}\nReference: {ref}\n\n⚠️ DEMO ONLY — no funds are transferred.",reply_markup=menu())

async def admin_list(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    kind="deposit" if q.data=="admin_deposits" else "withdrawal"; rows=get_requests("pending",kind)
    if not rows: return await q.edit_message_text(f"No pending {kind} requests.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin",callback_data="admin_home")]]))
    lines=[f"📋 PENDING {kind.upper()}S\n"]; buttons=[]
    for r in rows[:20]:
        lines.append(f"#{r['id']} • User {r['telegram_id']} • {money(r['amount'])} • {r['reference']}")
        buttons.append([InlineKeyboardButton(f"✅ Approve #{r['id']}",callback_data=f"approve:{r['id']}"),InlineKeyboardButton(f"❌ Reject #{r['id']}",callback_data=f"reject:{r['id']}")])
    buttons.append([InlineKeyboardButton("🔙 Admin",callback_data="admin_home")])
    await q.edit_message_text("\n".join(lines),reply_markup=InlineKeyboardMarkup(buttons))

async def admin_decision(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    action,rid=q.data.split(":"); req=update_request(int(rid),"confirmed" if action=="approve" else "rejected")
    if not req: return await q.edit_message_text("Request not found or already processed.")
    if action=="approve":
        if req["kind"]=="deposit":
            adjust_balance(req["telegram_id"],req["amount"]); add_transaction(req["telegram_id"],"deposit",req["amount"],req["fee"],req["reference"],"Demo deposit approved")
        elif req["kind"]=="withdrawal":
            balance=Decimal(str(get_balance(req["telegram_id"]))); amount=Decimal(str(req["amount"]))
            if amount > balance:
                update_request(int(rid),"rejected"); return await q.edit_message_text("❌ Withdrawal rejected: insufficient demo balance at approval time.")
            adjust_balance(req["telegram_id"],-req["amount"]); add_transaction(req["telegram_id"],"withdrawal",req["amount"],0,req["reference"],"Demo withdrawal approved")
    await q.edit_message_text(f"{'✅ APPROVED' if action=='approve' else '❌ REJECTED'}\n\nRequest #{rid}\nUser: {req['telegram_id']}\nAmount: {money(req['amount'])}\nReference: {req['reference']}\n\n⚠️ Demo accounting only; no real funds moved.")

async def callback(update,context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    if q.data=="admin_home":
        if is_admin(uid): await q.edit_message_text("🛡 ADMIN",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Deposit Requests",callback_data="admin_deposits")],[InlineKeyboardButton("💵 Withdrawal Requests",callback_data="admin_withdrawals")]]))
        return
    if q.data in ("admin_deposits","admin_withdrawals"): return await admin_list(update,context)
    if q.data.startswith(("approve:","reject:")): return await admin_decision(update,context)
    if q.data=="deposit":
        pending[uid]="deposit"; return await q.edit_message_text(f"💰 DEPOSIT\n\nEnter USD amount.\nMinimum: {money(MIN_DEPOSIT_USD)}\nDemo fee: {DEPOSIT_FEE_RATE*100}%\n\n⚠️ DEMO ONLY — do not send money.",reply_markup=back())
    if q.data=="withdraw":
        pending[uid]="withdraw"; return await q.edit_message_text("💵 WITHDRAW\n\nEnter USD amount to create a demo withdrawal request.\nNo real funds are transferred.",reply_markup=back())
    u=get_user(uid); bal=Decimal(str(u["balance"] if u else 0))
    if q.data=="dashboard": text=f"📊 DASHBOARD\n\n💵 Demo balance: {money(bal)}\n🏷 Account tier: {tier(bal)}\n\n📈 Trading status: DEMO / NOT LIVE\n🥇 XAU/USD: monitored\n₿ BTC/USDT: monitored\n\nP/L and execution data become available only when a compliant live trading architecture is connected."
    elif q.data=="trading": text="📈 MY TRADING\n\n🥇 XAU/USD\nStatus: DEMO / NOT LIVE\n\n₿ BTC/USDT\nStatus: DEMO / NOT LIVE\n\nPerformance tracking is designed for transparent P/L reporting; this build does not place broker or exchange orders."
    elif q.data=="transactions":
        rows=get_transactions(uid); text="📜 TRANSACTIONS\n\n"+ ("\n".join([f"• {r['kind'].title()} {money(r['amount'])} — {r['reference'] or '—'}" for r in rows]) if rows else "No completed demo transactions yet.")
    elif q.data=="referral": text=f"👥 REFERRAL\n\nYour referral code: {u['referral_code'] if u else '—'}\n\nReferral analytics are included in the v4 account model. Reward terms should be published only after the commercial/legal model is finalized."
    elif q.data=="support": text=f"🆘 SUPPORT\n\n{('@'+SUPPORT_USERNAME) if SUPPORT_USERNAME else 'Configure SUPPORT_USERNAME in Railway Variables.'}"
    elif q.data=="channel": text="📢 OFFICIAL CHANNEL\n\nConfigure the official Telegram channel URL before publishing this button."
    else: text="⚠️ RISK DISCLOSURE\n\nTrading Forex/CFDs, cryptocurrencies and other financial instruments involves substantial risk and may result in loss of capital. Past performance does not guarantee future results. AURIX TRADE does not guarantee profits or specific returns."
    await q.edit_message_text(text,reply_markup=menu())

def main():
    if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN is missing")
    init_db(); app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start)); app.add_handler(CommandHandler("admin",admin)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text)); app.add_handler(CallbackQueryHandler(callback)); app.run_polling()

if __name__=="__main__": main()

import logging
from decimal import Decimal
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application,CommandHandler,CallbackQueryHandler,ContextTypes
from database import init_db,get_user,create_user,get_balance
from admin import format_stats,format_users,format_transactions
from config import BOT_TOKEN,ADMIN_TELEGRAM_ID,MIN_DEPOSIT_USD,DEPOSIT_FEE_RATE,SUPPORT_USERNAME

logging.basicConfig(level=logging.INFO)

def money(v): return f"${Decimal(str(v)):,.2f}"
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard",callback_data="dashboard"),InlineKeyboardButton("💰 Deposit",callback_data="deposit")],
        [InlineKeyboardButton("📈 My Trading",callback_data="trading"),InlineKeyboardButton("💵 Withdraw",callback_data="withdraw")],
        [InlineKeyboardButton("📜 Transactions",callback_data="transactions"),InlineKeyboardButton("👥 Referral",callback_data="referral")],
        [InlineKeyboardButton("🆘 Support",callback_data="support"),InlineKeyboardButton("⚠️ Risk",callback_data="risk")]])

def is_admin(uid): return str(uid)==str(ADMIN_TELEGRAM_ID)

async def start(update,context):
    u=update.effective_user
    if not get_user(u.id): create_user(u.id,u.username or "",u.first_name or "")
    await update.message.reply_text("🟡 AURIX TRADE\n\nAutomated Gold & Crypto Trading.\n\n🥇 XAU/USD\n₿ BTC/USDT\n💰 Minimum deposit: "+money(MIN_DEPOSIT_USD)+"\n\nTrade Smarter. Grow With Discipline.\n\n⚠️ Trading involves risk. Returns are not guaranteed.",reply_markup=menu())

async def admin(update,context):
    if not is_admin(update.effective_user.id): return await update.message.reply_text("⛔ Admin access only.")
    await update.message.reply_text(format_stats(),reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👥 Users",callback_data="admin_users"),InlineKeyboardButton("📜 Transactions",callback_data="admin_tx")],[InlineKeyboardButton("🔄 Refresh",callback_data="admin_stats")]]))

async def admin_cb(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    text=format_users() if q.data=="admin_users" else format_transactions() if q.data=="admin_tx" else format_stats()
    await q.edit_message_text(text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 Stats",callback_data="admin_stats"),InlineKeyboardButton("👥 Users",callback_data="admin_users")],[InlineKeyboardButton("📜 Transactions",callback_data="admin_tx")]]))

async def cb(update,context):
    q=update.callback_query; await q.answer()
    t={"dashboard":f"📊 DASHBOARD\n\n💵 Available balance: {money(get_balance(q.from_user.id))}\n📈 Trading: DEMO / NOT LIVE",
       "deposit":f"💰 DEPOSIT\n\nMinimum trading capital: {money(MIN_DEPOSIT_USD)}\nDeposit fee: {DEPOSIT_FEE_RATE*100:.0f}%\n\nLive payment processing is disabled.",
       "trading":"📈 MY TRADING\n\nStatus: DEMO / NOT LIVE\n🥇 XAU/USD\n₿ BTC/USDT\n\nLive broker/exchange integration is not enabled.",
       "withdraw":"💵 WITHDRAW\n\nLive withdrawals are disabled in this foundation.",
       "transactions":"📜 TRANSACTIONS\n\nConfirmed deposits, withdrawals and trading fee records will appear here.",
       "referral":"👥 REFERRAL\n\nReferral tracking is not enabled in this foundation.",
       "support":f"🆘 SUPPORT\n\n{('@'+SUPPORT_USERNAME) if SUPPORT_USERNAME else 'Configure SUPPORT_USERNAME in Railway Variables.'}",
       "risk":"⚠️ RISK DISCLOSURE\n\nTrading involves substantial risk. Past performance does not guarantee future results. AURIX TRADE does not guarantee profits or specific returns."}
    await q.edit_message_text(t[q.data],reply_markup=menu())

def main():
    if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN is missing")
    init_db(); app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start)); app.add_handler(CommandHandler("admin",admin))
    app.add_handler(CallbackQueryHandler(admin_cb,pattern="^admin_(stats|users|tx)$"))
    app.add_handler(CallbackQueryHandler(cb,pattern="^(dashboard|deposit|trading|withdraw|transactions|referral|support|risk)$"))
    app.run_polling()

if __name__=="__main__": main()

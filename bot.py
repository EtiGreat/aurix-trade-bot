import os
import logging
from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
from database import init_db, get_user, create_user, get_balance, add_transaction
from fees import calculate_deposit, calculate_profit_fee
from config import BOT_TOKEN, MIN_DEPOSIT_USD, DEPOSIT_FEE_RATE, PROFIT_FEE_RATE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aurix")

def money(v):
    return f"${Decimal(str(v)):,.2f}"

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"),
         InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("📈 My Trading", callback_data="trading"),
         InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Transactions", callback_data="transactions"),
         InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("🆘 Support", callback_data="support"),
         InlineKeyboardButton("⚠️ Risk", callback_data="risk")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    user = get_user(u.id)
    if not user:
        create_user(u.id, u.username or "", u.first_name or "")
    text = (
        "🟡 AURIX TRADE\n\n"
        "Automated Gold & Crypto Trading.\n\n"
        "🥇 XAU/USD\n₿ BTC/USDT\n"
        f"💰 Minimum deposit: {money(MIN_DEPOSIT_USD)}\n\n"
        "Trade Smarter. Grow With Discipline.\n\n"
        "⚠️ Trading involves risk. Returns are not guaranteed."
    )
    await update.message.reply_text(text, reply_markup=menu())

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    balance = get_balance(q.from_user.id)
    await q.edit_message_text(
        f"📊 AURIX TRADE DASHBOARD\n\n"
        f"💵 Available balance: {money(balance)}\n"
        "📈 Trading: Paper/Not Connected\n"
        "🥇 XAU/USD: Ready for broker integration\n"
        "₿ BTC/USDT: Ready for exchange integration\n\n"
        "No live trading is enabled in this build.",
        reply_markup=menu()
    )

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "💰 DEPOSIT\n\n"
        f"Minimum trading capital: {money(MIN_DEPOSIT_USD)}\n"
        f"Deposit fee: {DEPOSIT_FEE_RATE * 100:.0f}%\n\n"
        "Example: to receive $50.00 of trading capital, "
        "the total payment is $52.50.\n\n"
        "Live payment processing is intentionally disabled until "
        "a verified payment provider/wallet is configured.",
        reply_markup=menu()
    )

async def trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📈 MY TRADING\n\n"
        "Status: DEMO / NOT LIVE\n\n"
        "Supported instruments:\n"
        "🥇 XAU/USD\n"
        "₿ BTC/USDT\n\n"
        "The live broker/exchange adapter must be configured and tested "
        "before real-money trading is enabled.",
        reply_markup=menu()
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "💵 WITHDRAWAL\n\n"
        "Withdrawal requests will only be processed against the user's "
        "real available balance after verification.\n\n"
        "Live withdrawals are disabled in this initial build.",
        reply_markup=menu()
    )

async def transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📜 TRANSACTIONS\n\n"
        "Your deposit, withdrawal, fee and trading records will appear here.",
        reply_markup=menu()
    )

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "👥 REFERRAL\n\n"
        "Referral tracking is prepared in the database layer.\n"
        "Any referral reward must be configured transparently and "
        "must not depend on recruiting deposits to pay other users.",
        reply_markup=menu()
    )

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🆘 SUPPORT\n\n"
        "Configure SUPPORT_USERNAME in .env to route users to your support account.",
        reply_markup=menu()
    )

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "⚠️ RISK DISCLOSURE\n\n"
        "Trading Forex, CFDs, cryptocurrencies and other financial instruments "
        "involves substantial risk and may result in the loss of invested capital. "
        "Past performance does not guarantee future results. AURIX TRADE does "
        "not guarantee profits or specific returns.",
        reply_markup=menu()
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Add it to .env")
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(dashboard, pattern="^dashboard$"))
    app.add_handler(CallbackQueryHandler(deposit, pattern="^deposit$"))
    app.add_handler(CallbackQueryHandler(trading, pattern="^trading$"))
    app.add_handler(CallbackQueryHandler(withdraw, pattern="^withdraw$"))
    app.add_handler(CallbackQueryHandler(transactions, pattern="^transactions$"))
    app.add_handler(CallbackQueryHandler(referral, pattern="^referral$"))
    app.add_handler(CallbackQueryHandler(support, pattern="^support$"))
    app.add_handler(CallbackQueryHandler(risk, pattern="^risk$"))
    app.run_polling()

if __name__ == "__main__":
    main()

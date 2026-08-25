import logging, math, time
from decimal import Decimal, InvalidOperation
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import init_db, get_user, create_user, get_balance, adjust_balance, lock_balance, release_trade_balance, create_request, get_requests, update_request, add_transaction, get_transactions, get_stats, create_demo_trade, get_demo_trades, get_demo_trade, close_demo_trade
from config import BOT_TOKEN, ADMIN_TELEGRAM_ID, MIN_DEPOSIT_USD, DEPOSIT_FEE_RATE, SUPPORT_USERNAME

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

def market_price(symbol):
    base = 2400.0 if symbol == "XAU/USD" else 105000.0
    t = time.time()/60
    wave = math.sin(t/9.0)*0.006 + math.sin(t/31.0)*0.004
    return round(base*(1+wave), 2)

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"), InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("📈 Demo Trading", callback_data="trading"), InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Transactions", callback_data="transactions"), InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("🆘 Support", callback_data="support"), InlineKeyboardButton("⚠️ Risk", callback_data="risk")],
        [InlineKeyboardButton("📢 Official Channel", callback_data="channel")]
    ])

def back(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="dashboard")]])

def trading_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥇 XAU/USD", callback_data="asset:XAU/USD"), InlineKeyboardButton("₿ BTC/USDT", callback_data="asset:BTC/USDT")],
        [InlineKeyboardButton("📂 Open Positions", callback_data="positions"), InlineKeyboardButton("📊 Performance", callback_data="performance")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="dashboard")]
    ])

def side_menu(symbol):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 LONG", callback_data=f"side:{symbol}:LONG"), InlineKeyboardButton("🔴 SHORT", callback_data=f"side:{symbol}:SHORT")],
        [InlineKeyboardButton("🔙 Trading", callback_data="trading")]
    ])

async def start(update, context):
    u=update.effective_user
    if not get_user(u.id): create_user(u.id,u.username or "",u.first_name or "")
    await update.message.reply_text(
        "🟡 AURIX TRADE\n\nTrade Smarter. Grow With Discipline.\n\n"
        "🤖 Automated Gold & Crypto Trading\n🥇 XAU/USD  •  ₿ BTC/USDT\n\n"
        f"💰 Minimum demo deposit: {money(MIN_DEPOSIT_USD)}\n\n"
        "🧪 DEMO / PAPER-TRADING MODE\nNo real deposits, custody, broker orders or withdrawals are processed by this build.\n\n"
        "⚠️ Trading involves substantial risk. Returns are not guaranteed.", reply_markup=menu())

async def admin(update, context):
    if not is_admin(update.effective_user.id): return await update.message.reply_text("⛔ Admin access only.")
    users,pending_count,volume=get_stats()
    await update.message.reply_text(f"🛡 AURIX TRADE ADMIN\n\n👥 Users: {users}\n⏳ Pending: {pending_count}\n💵 Demo transaction volume: {money(volume)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Deposit Requests",callback_data="admin_deposits")],[InlineKeyboardButton("💵 Withdrawal Requests",callback_data="admin_withdrawals")]]))

async def handle_text(update, context):
    uid=update.effective_user.id; state=pending.get(uid)
    if not state: return
    text=update.message.text.strip()
    if state[0] == "deposit" or state[0] == "withdraw":
        try: amount=Decimal(text)
        except InvalidOperation: return await update.message.reply_text("Enter a valid USD amount, e.g. 50 or 100.")
        if amount <= 0: return await update.message.reply_text("Amount must be greater than zero.")
        if state[0] == "deposit":
            if amount < MIN_DEPOSIT_USD: return await update.message.reply_text(f"Minimum demo deposit is {money(MIN_DEPOSIT_USD)}.")
            fee=(amount*DEPOSIT_FEE_RATE).quantize(Decimal("0.01")); total=amount+fee
            ref=create_request(uid,"deposit",float(amount),float(fee),f"DEP-{uid}-{int(time.time())}"); pending.pop(uid,None)
            await update.message.reply_text(f"💰 DEMO DEPOSIT REQUEST\n\nTrading capital: {money(amount)}\nPlatform fee: {money(fee)}\nTotal shown: {money(total)}\n\nReference: {ref}\n\n⚠️ DEMO ONLY — do not send funds.",reply_markup=menu())
        else:
            balance=Decimal(str(get_balance(uid)))
            if amount > balance:
                pending.pop(uid,None); return await update.message.reply_text(f"Insufficient demo balance. Available: {money(balance)}",reply_markup=menu())
            ref=create_request(uid,"withdrawal",float(amount),0.0,f"WDR-{uid}-{int(time.time())}"); pending.pop(uid,None)
            await update.message.reply_text(f"💵 DEMO WITHDRAWAL REQUEST\n\nAmount: {money(amount)}\nReference: {ref}\n\n⚠️ DEMO ONLY — no funds are transferred.",reply_markup=menu())
        return
    if state[0] == "trade_stake":
        symbol,side=state[1],state[2]
        try: stake=Decimal(text)
        except InvalidOperation: return await update.message.reply_text("Enter a valid demo stake, e.g. 10 or 25.")
        balance=Decimal(str(get_balance(uid)))
        open_stake=sum(Decimal(str(t["stake"])) for t in get_demo_trades(uid,"open"))
        if stake <= 0: return await update.message.reply_text("Stake must be greater than zero.")
        if stake > balance-open_stake: return await update.message.reply_text(f"Stake exceeds available demo capital. Available: {money(balance-open_stake)}")
        if not lock_balance(uid, float(stake)): return await update.message.reply_text("Unable to reserve that demo stake. Please try again.")
        entry=market_price(symbol); trade_id=create_demo_trade(uid,symbol,side,float(stake),entry); pending.pop(uid,None)
        await update.message.reply_text(f"📈 DEMO POSITION OPENED\n\n{symbol} • {side}\nStake: {money(stake)}\nEntry: {entry:,.2f}\nTrade ID: #{trade_id}\n\nThis is simulated paper trading only; no broker/exchange order was sent.",reply_markup=trading_menu())

async def admin_list(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    kind="deposit" if q.data=="admin_deposits" else "withdrawal"; rows=get_requests("pending",kind)
    if not rows: return await q.edit_message_text(f"No pending {kind} requests.",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin",callback_data="admin_home")]]))
    lines=[f"📋 PENDING {kind.upper()}S\n"]; buttons=[]
    for r in rows[:20]:
        lines.append(f"#{r['id']} • User {r['telegram_id']} • {money(r['amount'])} • {r['reference']}")
        buttons.append([InlineKeyboardButton(f"✅ Approve #{r['id']}",callback_data=f"approve:{r['id']}"),InlineKeyboardButton(f"❌ Reject #{r['id']}",callback_data=f"reject:{r['id']}")])
    buttons.append([InlineKeyboardButton("🔙 Admin",callback_data="admin_home")]); await q.edit_message_text("\n".join(lines),reply_markup=InlineKeyboardMarkup(buttons))

async def admin_decision(update,context):
    q=update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return await q.edit_message_text("⛔ Admin access only.")
    action,rid=q.data.split(":"); req=update_request(int(rid),"confirmed" if action=="approve" else "rejected")
    if not req: return await q.edit_message_text("Request not found or already processed.")
    if action=="approve":
        if req["kind"]=="deposit": adjust_balance(req["telegram_id"],req["amount"]); add_transaction(req["telegram_id"],"deposit",req["amount"],req["fee"],req["reference"],"Demo deposit approved")
        elif req["kind"]=="withdrawal":
            balance=Decimal(str(get_balance(req["telegram_id"]))); amount=Decimal(str(req["amount"]))
            if amount > balance: update_request(int(rid),"rejected"); return await q.edit_message_text("❌ Withdrawal rejected: insufficient demo balance at approval time.")
            adjust_balance(req["telegram_id"],-req["amount"]); add_transaction(req["telegram_id"],"withdrawal",req["amount"],0,req["reference"],"Demo withdrawal approved")
    await q.edit_message_text(f"{'✅ APPROVED' if action=='approve' else '❌ REJECTED'}\n\nRequest #{rid}\nUser: {req['telegram_id']}\nAmount: {money(req['amount'])}\nReference: {req['reference']}\n\n⚠️ Demo accounting only; no real funds moved.")

def trade_pnl(trade):
    current=market_price(trade["symbol"]); entry=Decimal(str(trade["entry_price"])); stake=Decimal(str(trade["stake"])); move=(Decimal(str(current))-entry)/entry; sign=Decimal("1") if trade["side"]=="LONG" else Decimal("-1"); pnl=(stake*move*sign).quantize(Decimal("0.01")); return current,pnl

async def callback(update,context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    if q.data=="admin_home":
        if is_admin(uid): await q.edit_message_text("🛡 ADMIN",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Deposit Requests",callback_data="admin_deposits")],[InlineKeyboardButton("💵 Withdrawal Requests",callback_data="admin_withdrawals")]]))
        return
    if q.data in ("admin_deposits","admin_withdrawals"): return await admin_list(update,context)
    if q.data.startswith(("approve:","reject:")): return await admin_decision(update,context)
    if q.data=="deposit": pending[uid]=( "deposit", ); return await q.edit_message_text(f"💰 DEPOSIT\n\nEnter USD amount.\nMinimum: {money(MIN_DEPOSIT_USD)}\nDemo fee: {DEPOSIT_FEE_RATE*100}%\n\n⚠️ DEMO ONLY — do not send money.",reply_markup=back())
    if q.data=="withdraw": pending[uid]=( "withdraw", ); return await q.edit_message_text("💵 WITHDRAW\n\nEnter USD amount to create a demo withdrawal request.\nNo real funds are transferred.",reply_markup=back())
    if q.data=="trading": return await q.edit_message_text("📈 DEMO TRADING\n\nSelect a market. Prices are simulated for paper-trading demonstrations only.",reply_markup=trading_menu())
    if q.data.startswith("asset:"):
        symbol=q.data.split(":",1)[1]; return await q.edit_message_text(f"{symbol}\n\nSimulated price: {market_price(symbol):,.2f}\n\nChoose a paper-trading direction:",reply_markup=side_menu(symbol))
    if q.data.startswith("side:"):
        _,symbol,side=q.data.split(":",2); pending[uid]=( "trade_stake",symbol,side); bal=Decimal(str(get_balance(uid))); open_stake=sum(Decimal(str(t["stake"])) for t in get_demo_trades(uid,"open")); avail=bal-open_stake
        return await q.edit_message_text(f"{symbol} • {side}\n\nAvailable demo capital: {money(avail)}\nEnter your simulated stake in USD.",reply_markup=trading_menu())
    if q.data=="positions":
        rows=get_demo_trades(uid,"open");
        if not rows: return await q.edit_message_text("📂 OPEN POSITIONS\n\nNo open demo positions.",reply_markup=trading_menu())
        lines=["📂 OPEN DEMO POSITIONS\n"]; buttons=[]
        for t in rows:
            cur,pnl=trade_pnl(t); lines.append(f"#{t['id']} • {t['symbol']} • {t['side']}\nStake {money(t['stake'])} • Entry {t['entry_price']:,.2f} • Now {cur:,.2f} • P/L {money(pnl)}")
            buttons.append([InlineKeyboardButton(f"🔒 Close #{t['id']}",callback_data=f"close:{t['id']}")])
        buttons.append([InlineKeyboardButton("🔙 Trading",callback_data="trading")]); return await q.edit_message_text("\n\n".join(lines),reply_markup=InlineKeyboardMarkup(buttons))
    if q.data.startswith("close:"):
        tid=int(q.data.split(":")[1]); t=get_demo_trade(tid,uid)
        if not t or t["status"]!="open": return await q.edit_message_text("Position is no longer open.",reply_markup=trading_menu())
        cur,pnl=trade_pnl(t);
        if not release_trade_balance(uid, float(t["stake"]), float(pnl)): return await q.edit_message_text("Unable to settle this demo position safely. Please contact support.",reply_markup=trading_menu())
        close_demo_trade(tid,uid,cur,float(pnl)); return await q.edit_message_text(f"🔒 DEMO POSITION CLOSED\n\n#{tid} • {t['symbol']} • {t['side']}\nExit: {cur:,.2f}\nSimulated P/L: {money(pnl)}\n\nNo real funds were moved.",reply_markup=trading_menu())
    if q.data=="performance":
        rows=get_demo_trades(uid); closed=[r for r in rows if r["status"]=="closed"]; pnl=sum(Decimal(str(r["pnl"] or 0)) for r in closed); wins=sum(1 for r in closed if Decimal(str(r["pnl"] or 0))>0); losses=sum(1 for r in closed if Decimal(str(r["pnl"] or 0))<0); win_rate=(Decimal(wins)/Decimal(len(closed))*100 if closed else Decimal(0)); volume=sum(Decimal(str(r["stake"])) for r in closed); return await q.edit_message_text(f"📊 DEMO PERFORMANCE\n\nClosed trades: {len(closed)}\nWinning trades: {wins}\nLosing trades: {losses}\nWin rate: {win_rate:.1f}%\nDemo volume: {money(volume)}\nRealized simulated P/L: {money(pnl)}\n\n⚠️ These are simulated results only and do not represent live performance.",reply_markup=trading_menu())
    u=get_user(uid); bal=Decimal(str(u["balance"] if u else 0)); locked=Decimal(str(u["locked_balance"] if u and "locked_balance" in u else 0)); equity=bal+locked
    if q.data=="dashboard": text=f"📊 DASHBOARD\n\n💵 Available demo balance: {money(bal)}\n🔒 Locked in open trades: {money(locked)}\n💎 Demo equity: {money(equity)}\n🏷 Account tier: {tier(equity)}\n\n📈 Trading status: DEMO / PAPER\n🥇 XAU/USD: simulated\n₿ BTC/USDT: simulated\n\nUse Demo Trading to open and close paper positions and view simulated P/L."
    elif q.data=="transactions":
        rows=get_transactions(uid); text="📜 TRANSACTIONS\n\n"+("\n".join([f"• {r['kind'].title()} {money(r['amount'])} — {r['reference'] or '—'}" for r in rows]) if rows else "No completed demo transactions yet.")
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

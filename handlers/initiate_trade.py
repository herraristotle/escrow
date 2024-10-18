from config import *
from utils import *
from functions import *
import re

@bot.message_handler(regexp="^🤝 Start Escrow")
def start_escrow(msg):
    """
    This starts the escrow process by showing Terms & Conditions
    """
    chat, id = get_received_msg(msg)
    user = UserClient.get_user_by_id(msg.from_user.id)

    terms_link = "https://telegra.ph/Terms--Rules-of-Escrow-Service-Bot-12-17"
    message = f"To continue Escrow, read and validate that you accept the <a href='{terms_link}'>Terms & rules</a> of Escrow Bot."

    bot.send_message(
        user["_id"],
        message,
        reply_markup=terms_and_conditions_menu(),
        parse_mode="html",
        disable_web_page_preview=True
    )


@bot.callback_query_handler(func=lambda call: call.data == "accept_terms")
def terms_accepted(call):
    """
    Handle acceptance of terms and conditions
    """
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    open_trade(call.from_user.id)  # Pass user ID instead of message

@bot.callback_query_handler(func=lambda call: call.data == "decline_terms")
def terms_declined(call):
    """
    Handle declining of terms and conditions
    """
    user = UserClient.get_user_by_id(call.from_user.id)
    keyboard = trade_menu()
    
    bot.answer_callback_query(call.id, "You must accept the terms to use the Escrow service.")
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


@bot.message_handler(func=lambda message: message.text in ["I am buyer 💰", "I am seller 👨‍💼"])
def handle_buyer_seller_selection(message):
    user = UserClient.get_user_by_id(message.from_user.id)
    
    if message.text in ["I am buyer 💰", "I am seller 👨‍💼"]:
        role = "buyer" if message.text == "I am buyer 💰" else "seller"
        # Store the user's role in the database
        TradeClient.update_user_role(user["_id"], role)
        
        keyboard = cancel_keyboard()
        trade_terms(message)

@bot.message_handler(func=lambda message: message.text == "⬅️ Back")
def handle_back_to_main_menu(message):
    user = UserClient.get_user_by_id(message.from_user.id)
    keyboard = trade_menu()
    
    bot.send_message(
        user["_id"],
        "Back to main menu",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text == "Cancel ❌")
def handle_cancel(message):
    user = UserClient.get_user_by_id(message.from_user.id)
    keyboard = trade_menu()
    
    # Cancel the ongoing trade process
    # You may need to implement a function to clear any ongoing trade data
    # For example: TradeClient.cancel_ongoing_trade(user["_id"])
    
    bot.send_message(
        user["_id"],
        "The process has been cancelled!",
        reply_markup=keyboard
    )

##############TRADE CREATION
def open_trade(user_id):
    """
    Ask if the user is a buyer or seller
    """
    user = UserClient.get_user_by_id(user_id)
    keyboard = buyer_seller_menu()
    
    question = bot.send_message(
        user_id,
        "Are you a seller or buyer?",
        reply_markup=keyboard
    )

    bot.register_next_step_handler(question, trade_terms)

def trade_terms(msg):
    """
    Ask for terms of trade
    """
    user = UserClient.get_user(msg)
    keyboard = cancel_keyboard()

    question = bot.send_message(
        user["_id"],
        "📝 Please enter the description of what you want to buy or sell 💬!",
        reply_markup=keyboard
    )

    bot.register_next_step_handler(question, select_currency)

def select_currency(msg):
    """
    Select local currency
    """
    terms = msg.text
    user = UserClient.get_user_by_id(msg.from_user.id)

    if terms == "Cancel ❌":
        return handle_cancel(msg)

    trade = TradeClient.add_terms(user=user, terms=str(terms))

    if trade is None:
        bot.send_message(msg.chat.id, "❌ Unable to create or find your trade. Please start over")
    else:
        keyboard = local_currency_menu()
        bot.send_message(
            user["_id"],
            "💰 Select which is your local currency of choice... ",
            reply_markup=keyboard
        )

# Update the callback handler for currency selection
@bot.callback_query_handler(func=lambda call: call.data == "dollar")
def handle_currency_selection(call):
    user = UserClient.get_user_by_id(call.from_user.id)
    trade = TradeClient.get_most_recent_trade(user)
    
    if trade is None:
        bot.answer_callback_query(call.id, "❌ Unable to find your trade. Please start over")
        return
    
    # Update currency
    TradeClient.update_currency(trade["_id"], "USD")
    
    # Proceed to asking for price
    trade_price(call.message)

def trade_price(msg):
    """
    Receive user input on trade price
    """
    user = UserClient.get_user_by_id(msg.chat.id)
    keyboard = cancel_keyboard()
    
    question = bot.send_message(
        user["_id"],
        "💰 How much are you expecting to be paid in your local currency? ",
        reply_markup=keyboard
    )

    bot.register_next_step_handler(question, handle_price_input)

def handle_price_input(msg):
    price = msg.text
    user = UserClient.get_user_by_id(msg.from_user.id)

    if price == "Cancel ❌":
        return handle_cancel(msg)

    try:
        price_float = float(price)
        trade = TradeClient.add_price(user=user, price=price_float)

        if trade is None:
            bot.send_message(msg.chat.id, "❌ Unable to find your trade. Please start over")
        else:
            ask_for_bitcoin_wallet(msg)
    except ValueError:
        # Handle invalid input
        keyboard = cancel_keyboard()
        question = bot.send_message(
            user["_id"],
            "❌ Invalid input. Please enter a valid number for the price or cancel the process.",
            reply_markup=keyboard
        )
        bot.register_next_step_handler(question, handle_price_input)

def ask_for_bitcoin_wallet(msg):
    user = UserClient.get_user_by_id(msg.from_user.id)
    trade = TradeClient.get_most_recent_trade(user)
    
    if trade is None:
        bot.send_message(msg.chat.id, "❌ Unable to find your trade. Please start over")
        return

    # Get the user's role from the trade data
    role = trade.get("user_role")
    
    if role == "seller":
        prompt = "Please enter your Bitcoin wallet. After completion of the escrow, your money will be credited to that wallet."
    elif role == "buyer":
        prompt = "Please enter your Bitcoin wallet. In case of a dispute, if a refund is issued, your money will be credited back to that wallet."
    else:
        bot.send_message(msg.chat.id, "❌ Unable to determine your role. Please start over")
        return

    keyboard = cancel_keyboard()
    question = bot.send_message(user["_id"], prompt, reply_markup=keyboard)
    bot.register_next_step_handler(question, handle_bitcoin_wallet_input)

def handle_bitcoin_wallet_input(msg):
    wallet_address = msg.text
    user = UserClient.get_user_by_id(msg.from_user.id)

    if wallet_address == "Cancel ❌":
        return handle_cancel(msg)

    # Basic Bitcoin address validation (you might want to use a more robust method)
    btc_address_pattern = r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-zA-HJ-NP-Z0-9]{39,59}$'
    
    if re.match(btc_address_pattern, wallet_address):
        trade = TradeClient.get_most_recent_trade(user)
        if trade is None:
            bot.send_message(msg.chat.id, "❌ Unable to find your trade. Please start over")
            return

        # Update the trade with the wallet address
        TradeClient.update_wallet(trade["_id"], wallet_address)
        
        # Display transaction summary
        display_transaction_summary(msg, trade)
    else:
        keyboard = cancel_keyboard()
        question = bot.send_message(
            user["_id"],
            "❌ Invalid BTC address. Please enter a valid Bitcoin wallet address.",
            reply_markup=keyboard
        )
        bot.register_next_step_handler(question, handle_bitcoin_wallet_input)

def display_transaction_summary(msg, trade):
    """
    Display transaction summary and provide options to create invoice or start over
    """
    user = UserClient.get_user_by_id(msg.from_user.id)
    
    # Fetch the most recent trade data
    updated_trade = TradeClient.get_most_recent_trade(user)
    
    if updated_trade is None:
        bot.send_message(user["_id"], "❌ Unable to find your trade. Please start over")
        return

    # Prepare the summary message with improved formatting
    summary = f"🔽 <b>Here is the information you filled, if everything is correct click Create Invoice. If you want to start over click Start Over</b> 🔽\n\n"
    summary += f"<b>📝 Trade ID:</b> {updated_trade.get('_id', 'N/A')}\n\n"
    summary += f"<b>📝 Description:</b> {updated_trade.get('terms', 'N/A')}\n\n"
    summary += f"<b>💱 Currency:</b> {updated_trade.get('currency', 'N/A')}\n\n"
    summary += f"<b>💰 Transaction Amount:</b> {updated_trade.get('price', 'N/A')} {updated_trade.get('currency', 'N/A')}\n\n"
    summary += f"<b>👛 Bitcoin Wallet:</b> {updated_trade.get('wallet_address', 'N/A')}\n\n"
    
    # Add commission if available
    if 'commission' in updated_trade:
        summary += f"<b>💼 Commission:</b> {updated_trade.get('commission', 'N/A')}\n\n"

    # Create inline keyboard
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    create_invoice_button = types.InlineKeyboardButton("Create an invoice for payment ✅", callback_data="create_invoice")
    start_over_button = types.InlineKeyboardButton("Start Over 🔄", callback_data="start_over")
    keyboard.add(create_invoice_button, start_over_button)

    # Send the summary message with the inline keyboard
    bot.send_message(
        user["_id"],
        summary,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# Add these new callback handlers
@bot.callback_query_handler(func=lambda call: call.data == "create_invoice")
def create_invoice(call):
    # This will call your existing creating_trade function
    creating_trade(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "start_over")
def start_over(call):
    # This will restart the process
    open_trade(call.from_user.id)

def creating_trade(msg):
    """
    Finalize trade creation
    """
    price = msg.text
    user = UserClient.get_user_by_id(msg.from_user.id)

    trade = TradeClient.add_price(user=user, price=float(price))

    if trade is None:
        bot.send_message(msg.chat.id, "❌ Unable to find your trade. Please start over")

    else:
        # Get Payment Url
        payment_url = TradeClient.get_invoice_url(trade=trade)
        trade = TradeClient.get_most_recent_trade(user)

        if payment_url is None:
            bot.send_message(
                msg.chat.id, "❌ Unable to get payment url. Please try again"
            )

        else:

            # Create an inline keyboard with a Forward button
            inline_keyboard = [
                [types.InlineKeyboardButton("Forward", switch_inline_query="")]
            ]
            keyboard_markup = types.InlineKeyboardMarkup(inline_keyboard)

            # Send the message with the inline keyboard
            bot.send_message(
                msg.from_user.id,
                text=Messages.trade_created(trade),
                parse_mode="html",
                reply_markup=keyboard_markup,
            )

from config import *
from database import *


class Messages:

    @staticmethod
    def welcome(name: str) -> str:
        return f"""
🎪 <b>Welcome to the Telegram Escrow Service, {name}!</b>
    
My purpose is to create a safe trade environment for both seller and buyer, subject to my rules.

Your funds are safe with me and will be refunded to you if the other party refuses to comply with the rules.
            """
    

    @staticmethod
    def trade_created(trade: TradeType) -> str:
        return f"""
📝 <b>New Escrow Trade Opened (ID - {trade['_id']})</b> 📝
--------------------------------------------------
<b>Terms of Contract:</b> {trade['terms']}

<b>Transaction Amount:</b> {trade['price']} {trade['currency']}
<b>Preferred Payment Method:</b> Bitcoin
<b>Trade Initiated On:</b> {datetime.strftime(trade['created_at'], "%Y-%m-%d %H:%M:%S")}

Ensure that you only share the unique Trade ID with the counterparty. This will allow them to seamlessly join the trade and complete the transaction. All relevant information will be shared upon joining, or they can proceed with the payment through the portal link above.

The trade window only lasts for 60 minutes. Contact the buyer right away.
            """



    @staticmethod
    def trade_joined(trade: TradeType, status: str) -> str:
        return f"""
📝 <b>Trade Payment Details - {trade['_id']}</b> 
-----------------------------------
<b>Terms of Contract:</b> {trade['terms']}

<b>Transaction Amount:</b> {trade['price']} {trade['currency']}
<b>Preferred Payment Method:</b> Bitcoin
<b>Trade Initiated On:</b> {datetime.strftime(trade['created_at'], "%Y-%m-%d %H:%M:%S")}
<b>Payment Status:</b> {status}

<b>Please follow the URL below to make payment on our secure portal. Click the button to confirm after you make payment.</b>

You can go to the payment portal by clicking the button below.
                """



    @staticmethod
    def trade_details(trade: TradeType, status: str) -> str:
        return f"""
📝 <b>Trade Details - {trade['_id']}</b> 
-----------------------------------
<b>Terms of Contract:</b> {trade['terms']}
<b>Trade State:</b> {'Active' if trade['is_active'] is True else 'Inactive'}

<b>Buyer's ID: </b> {trade['buyer_id'] if 'buyer_id' in trade else "N/A"}
<b>Seller's ID: </b> {trade['seller_id']}

<b>Transaction Amount:</b> {trade['price']} {trade['currency']}
<b>Preferred Payment Method:</b> Bitcoin
<b>Trade Initiated On:</b> {datetime.strftime(trade['created_at'], "%Y-%m-%d %H:%M:%S")}
<b>Payment Status:</b> {status}
            """
"""Telegram notification helper for relay ACKs and other notifications."""

def send_telegram_notification(sender_id: str, message: str):
    """Send a notification to a Telegram user.

    Args:
        sender_id: Telegram sender ID in format "telegram_{chat_id}"
        message: Message to send
    """
    if not sender_id.startswith("telegram_"):
        raise ValueError(f"Invalid Telegram sender_id: {sender_id}")

    try:
        chat_id = int(sender_id.replace("telegram_", ""))
    except ValueError:
        raise ValueError(f"Invalid Telegram chat_id in sender_id: {sender_id}")

    # Import here to avoid circular dependencies
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Get telegram_app from main module
    import importlib
    main_module = sys.modules.get('__main__')
    if not main_module:
        raise RuntimeError("Cannot access main module")

    telegram_app = getattr(main_module, 'telegram_app', None)
    if not telegram_app or not hasattr(telegram_app, 'bot'):
        raise RuntimeError("Telegram app not available")

    # Send via HTTP to avoid async issues
    import requests
    bot_token = telegram_app.bot.token
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": message},
        timeout=10
    )
    response.raise_for_status()

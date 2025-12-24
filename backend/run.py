import os
from app import create_app, db

# Create application instance
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Make db and models available in flask shell."""
    from app.models import (
        Studio, User, Contact, Conversation, Message,
        LeadStatusHistory, StudioKnowledge, MessageTemplate, AnalyticsDaily
    )
    return {
        'db': db,
        'Studio': Studio,
        'User': User,
        'Contact': Contact,
        'Conversation': Conversation,
        'Message': Message,
        'LeadStatusHistory': LeadStatusHistory,
        'StudioKnowledge': StudioKnowledge,
        'MessageTemplate': MessageTemplate,
        'AnalyticsDaily': AnalyticsDaily
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)

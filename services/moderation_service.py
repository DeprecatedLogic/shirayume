from database import database_manager

def import_moderation_logs(**kwargs):

    model = database_manager.initialize_database_model(**kwargs)

    database_manager.add_moderation_logs(model)
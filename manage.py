from app import blog, db, migrate, manager, models
from flask_migrate import MigrateCommand
from flask_script import Shell
from config import SQLALCHEMY_DATABASE_URI

@manager.command
def runserver():
    blog.run()

def _make_context():
    return dict(app = blog, db = db, models = models)


manager.add_command('shell', Shell(make_context = _make_context))
manager.add_command('db', MigrateCommand)

if __name__ == "__main__":
    manager.run()

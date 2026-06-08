import os
import sys

# Append the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.shared.database import engine, Base
from app.modules.p7_seguridad_multitenant.models import TenantSubscriptionHistory

print("Creating missing tables...")
Base.metadata.create_all(bind=engine)
print("Done!")

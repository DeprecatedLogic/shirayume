from discord import app_commands

ECONOMY_GROUP = app_commands.Group(
    name="economy",
    description="Shirayume economy commands"
)

ECONOMY_ADMIN_GROUP = app_commands.Group(
    name="admin",
    description="Shirayume economy admin commands",
    parent=ECONOMY_GROUP
)
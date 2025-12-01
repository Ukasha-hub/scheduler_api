DEFAULT_PRIVILEGES = {
    "Admin": {
        "Scheduler": {"read": True, "write": True, "update": True, "delete": True},
        "Rundown": {"read": True, "write": True, "update": True, "delete": True},
        "User Settings": {"read": True, "write": True, "update": True, "delete": True},
    },

    "Editor": {
        "Scheduler": {"read": True, "write": True, "update": True, "delete": False},
        "Rundown": {"read": True, "write": True, "update": True, "delete": False},
    },

    "Viewer": {
        "Scheduler": {"read": True},
        "Rundown": {"read": True},
    },

    "Guest": {
        "Scheduler": {"read": True},
    }
}
